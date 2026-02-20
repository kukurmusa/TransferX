from datetime import datetime
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Club
from .models import Listing, Offer, OfferEvent, OfferMessage


@transaction.atomic
def create_listing(
    *,
    player,
    actor_club,
    listing_type,
    visibility,
    asking_price=None,
    min_price=None,
    deadline=None,
    notes="",
):
    if player.current_club_id:
        if not actor_club or player.current_club_id != actor_club.id:
            raise ValidationError("You cannot list a player you do not control.")

    Listing.objects.filter(
        player=player, listing_type=listing_type, status=Listing.Status.OPEN
    ).update(status=Listing.Status.CLOSED)

    listing = Listing.objects.create(
        player=player,
        listed_by_club=actor_club,
        listing_type=listing_type,
        visibility=visibility,
        asking_price=asking_price,
        min_price=min_price,
        deadline=deadline,
        status=Listing.Status.OPEN,
        notes=notes,
    )
    return listing


@transaction.atomic
def close_listing(*, listing: Listing, actor_club, reason: str = "closed") -> None:
    if listing.listed_by_club_id and actor_club and listing.listed_by_club_id != actor_club.id:
        raise ValidationError("You cannot close this listing.")
    listing.status = Listing.Status.CLOSED if reason == "closed" else Listing.Status.WITHDRAWN
    listing.save(update_fields=["status", "updated_at"])


def get_actor_club(user) -> Club | None:
    if hasattr(user, "club"):
        return user.club
    return None


def close_offer_if_expired(offer: Offer, now: datetime | None = None) -> bool:
    if offer.status not in {Offer.Status.SENT, Offer.Status.COUNTERED}:
        return False
    if not offer.expires_at:
        return False
    now = now or timezone.now()
    if offer.expires_at > now:
        return False
    offer.status = Offer.Status.EXPIRED
    offer.save(update_fields=["status", "last_action_at"])
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.EXPIRED,
        payload={"expired_at": now.isoformat()},
    )
    return True


@transaction.atomic
def create_draft_offer(
    *,
    player,
    from_club,
    listing: Listing | None = None,
    to_club=None,
    fee_amount=None,
    wage_weekly=None,
    contract_years=None,
    contract_end_date=None,
    add_ons: dict[str, Any] | None = None,
    expires_at=None,
) -> Offer:
    if player.current_club_id:
        if to_club is None or to_club.id != player.current_club_id:
            raise ValidationError("Contracted player offers must target the current club.")
    if listing and listing.player_id != player.id:
        raise ValidationError("Listing does not match player.")

    offer = Offer.objects.create(
        player=player,
        listing=listing,
        from_club=from_club,
        to_club=to_club,
        fee_amount=fee_amount,
        wage_weekly=wage_weekly,
        contract_years=contract_years,
        contract_end_date=contract_end_date,
        add_ons=add_ons or {},
        expires_at=expires_at,
        status=Offer.Status.DRAFT,
    )
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.CREATED,
        actor_club=from_club,
        payload={
            "fee_amount": str(fee_amount) if fee_amount is not None else None,
            "wage_weekly": str(wage_weekly) if wage_weekly is not None else None,
            "contract_years": contract_years,
            "contract_end_date": contract_end_date.isoformat() if contract_end_date else None,
        },
    )
    return offer


@transaction.atomic
def send_offer(offer: Offer, actor_user, actor_club) -> Offer:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    if offer.from_club_id != actor_club.id:
        raise PermissionDenied("Only the buyer can send this offer.")
    if offer.status != Offer.Status.DRAFT:
        raise ValidationError("Only draft offers can be sent.")
    if offer.player.current_club_id and offer.to_club_id != offer.player.current_club_id:
        raise ValidationError("Offer target does not match current club.")
    offer.status = Offer.Status.SENT
    offer.save(update_fields=["status", "last_action_at"])
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.SENT,
        actor_user=actor_user,
        actor_club=actor_club,
    )
    return offer


@transaction.atomic
def counter_offer(
    offer: Offer,
    actor_user,
    actor_club,
    *,
    fee_amount=None,
    wage_weekly=None,
    contract_years=None,
    contract_end_date=None,
    add_ons: dict[str, Any] | None = None,
    expires_at=None,
) -> Offer:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    close_offer_if_expired(offer)
    if offer.status not in {Offer.Status.SENT, Offer.Status.COUNTERED}:
        raise ValidationError("Offer cannot be countered.")
    if actor_club.id not in {offer.from_club_id, offer.to_club_id}:
        raise PermissionDenied("You are not a participant in this offer.")

    previous = {
        "fee_amount": str(offer.fee_amount) if offer.fee_amount is not None else None,
        "wage_weekly": str(offer.wage_weekly) if offer.wage_weekly is not None else None,
        "contract_years": offer.contract_years,
        "contract_end_date": offer.contract_end_date.isoformat()
        if offer.contract_end_date
        else None,
    }
    offer.fee_amount = fee_amount
    offer.wage_weekly = wage_weekly
    offer.contract_years = contract_years
    offer.contract_end_date = contract_end_date
    offer.add_ons = add_ons or {}
    offer.expires_at = expires_at
    offer.status = Offer.Status.COUNTERED
    offer.save(
        update_fields=[
            "fee_amount",
            "wage_weekly",
            "contract_years",
            "contract_end_date",
            "add_ons",
            "expires_at",
            "status",
            "last_action_at",
        ]
    )

    changed_fields = [
        field
        for field, value in previous.items()
        if value
        != (
            str(getattr(offer, field))
            if getattr(offer, field) is not None
            else None
        )
    ]

    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.COUNTERED,
        actor_user=actor_user,
        actor_club=actor_club,
        payload={"previous_terms": previous, "changed_fields": changed_fields},
    )
    return offer


@transaction.atomic
def accept_offer(offer: Offer, actor_user, actor_club) -> Offer:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    close_offer_if_expired(offer)
    if offer.status not in {Offer.Status.SENT, Offer.Status.COUNTERED}:
        raise ValidationError("Offer cannot be accepted.")
    if offer.player.current_club_id is None and offer.to_club_id is None:
        raise ValidationError("Free agent acceptance requires player onboarding.")
    if offer.to_club_id != actor_club.id:
        raise PermissionDenied("Only the selling club can accept this offer.")

    offer.status = Offer.Status.ACCEPTED
    offer.save(update_fields=["status", "last_action_at"])
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.ACCEPTED,
        actor_user=actor_user,
        actor_club=actor_club,
    )
    return offer


@transaction.atomic
def reject_offer(offer: Offer, actor_user, actor_club, reason: str = "") -> Offer:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    close_offer_if_expired(offer)
    if offer.status not in {Offer.Status.SENT, Offer.Status.COUNTERED}:
        raise ValidationError("Offer cannot be rejected.")
    if offer.player.current_club_id and offer.to_club_id != actor_club.id:
        raise PermissionDenied("Only the selling club can reject this offer.")
    offer.status = Offer.Status.REJECTED
    offer.save(update_fields=["status", "last_action_at"])
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.REJECTED,
        actor_user=actor_user,
        actor_club=actor_club,
        payload={"reason": reason},
    )
    return offer


@transaction.atomic
def withdraw_offer(offer: Offer, actor_user, actor_club) -> Offer:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    close_offer_if_expired(offer)
    if offer.status not in {Offer.Status.DRAFT, Offer.Status.SENT, Offer.Status.COUNTERED}:
        raise ValidationError("Offer cannot be withdrawn.")
    if offer.from_club_id != actor_club.id:
        raise PermissionDenied("Only the buyer can withdraw this offer.")
    offer.status = Offer.Status.WITHDRAWN
    offer.save(update_fields=["status", "last_action_at"])
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.WITHDRAWN,
        actor_user=actor_user,
        actor_club=actor_club,
    )
    return offer


@transaction.atomic
def add_message(offer: Offer, actor_user, actor_club, body: str) -> OfferMessage:
    offer = Offer.objects.select_for_update().get(pk=offer.pk)
    if offer.to_club_id is None and offer.player.current_club_id is None:
        if not (actor_user.is_staff or offer.from_club_id == actor_club.id):
            raise PermissionDenied("Not allowed to message this offer.")
    elif actor_club.id not in {offer.from_club_id, offer.to_club_id}:
        raise PermissionDenied("Not allowed to message this offer.")

    message = OfferMessage.objects.create(
        offer=offer,
        sender_user=actor_user,
        sender_club=actor_club,
        body=body,
    )
    OfferEvent.objects.create(
        offer=offer,
        event_type=OfferEvent.EventType.MESSAGE,
        actor_user=actor_user,
        actor_club=actor_club,
        payload={"message_id": message.id},
    )
    return message

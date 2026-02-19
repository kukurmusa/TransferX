from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.marketplace.models import Listing, Offer
from apps.marketplace.services import get_actor_club as marketplace_get_actor_club
from .models import PlayerInterest, Shortlist, ShortlistItem


def get_actor_club(user):
    return marketplace_get_actor_club(user)


def ensure_shortlist(club, name):
    if not name:
        raise ValidationError("Shortlist name is required.")
    shortlist, _ = Shortlist.objects.get_or_create(club=club, name=name)
    return shortlist


def create_shortlist(club, name, description=""):
    if not name:
        raise ValidationError("Shortlist name is required.")
    return Shortlist.objects.create(club=club, name=name, description=description)


def rename_shortlist(shortlist, new_name, description=None):
    if not new_name:
        raise ValidationError("Shortlist name is required.")
    shortlist.name = new_name
    if description is not None:
        shortlist.description = description
    shortlist.save(update_fields=["name", "description", "updated_at"])
    return shortlist


def delete_shortlist(shortlist):
    shortlist.delete()


@transaction.atomic
def add_player_to_shortlist(shortlist, player, priority=3, notes=""):
    item, _ = ShortlistItem.objects.update_or_create(
        shortlist=shortlist,
        player=player,
        defaults={"priority": priority, "notes": notes},
    )
    return item


def remove_player_from_shortlist(shortlist, player):
    ShortlistItem.objects.filter(shortlist=shortlist, player=player).delete()


@transaction.atomic
def set_player_interest(club, player, level, stage=None, notes=None):
    if not level:
        raise ValidationError("Interest level is required.")
    defaults = {"level": level}
    if stage:
        defaults["stage"] = stage
    if notes is not None:
        defaults["notes"] = notes
    interest, _ = PlayerInterest.objects.update_or_create(
        club=club, player=player, defaults=defaults
    )
    return interest


def clear_player_interest(club, player):
    PlayerInterest.objects.filter(club=club, player=player).delete()


def offers_expiring_soon(club, within_hours=72):
    now = timezone.now()
    horizon = now + timedelta(hours=within_hours)
    return Offer.objects.filter(
        Q(from_club=club) | Q(to_club=club),
        status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
        expires_at__isnull=False,
        expires_at__gte=now,
        expires_at__lte=horizon,
    )


def watched_now_available(club):
    interests = (
        PlayerInterest.objects.select_related("player", "player__current_club")
        .filter(
            club=club,
            level__in=[
                PlayerInterest.Level.WATCHING,
                PlayerInterest.Level.INTERESTED,
                PlayerInterest.Level.PRIORITY,
            ],
        )
        .order_by("-last_touched_at")
    )
    player_ids = [interest.player_id for interest in interests]
    open_listing_ids = set(
        Listing.objects.filter(
            player_id__in=player_ids, status=Listing.Status.OPEN
        ).values_list("player_id", flat=True)
    )
    results = []
    for interest in interests:
        player = interest.player
        has_open_listing = player.id in open_listing_ids
        is_free_agent = player.current_club_id is None
        open_to_offers = bool(player.open_to_offers and is_free_agent)
        if has_open_listing or is_free_agent or open_to_offers:
            results.append(
                {
                    "player": player,
                    "interest": interest,
                    "has_open_listing": has_open_listing,
                    "is_free_agent": is_free_agent,
                    "open_to_offers": open_to_offers,
                }
            )
    return results

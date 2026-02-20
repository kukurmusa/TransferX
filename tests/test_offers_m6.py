import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Club
from apps.marketplace.models import Offer
from apps.marketplace.services import (
    accept_offer,
    close_offer_if_expired,
    counter_offer,
    create_draft_offer,
    send_offer,
    withdraw_offer,
)
from apps.players.models import Player


@pytest.mark.django_db
def test_create_and_send_offer_contracted_player_sets_to_club():
    user_seller = get_user_model().objects.create_user(username="sellerM6", password="pass")
    user_buyer = get_user_model().objects.create_user(username="buyerM6", password="pass")
    club_seller = Club.objects.create(user=user_seller, name="Seller Club")
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club")
    player = Player.objects.create(
        name="Contracted",
        created_by=user_seller,
        current_club=club_seller,
        status=Player.Status.CONTRACTED,
    )

    offer = create_draft_offer(
        player=player,
        from_club=club_buyer,
        to_club=club_seller,
        fee_amount=100,
        wage_weekly=10,
    )
    send_offer(offer, user_buyer, club_buyer)
    offer.refresh_from_db()
    assert offer.status == Offer.Status.SENT
    assert offer.to_club == club_seller
    assert offer.events.filter(event_type="CREATED").exists()
    assert offer.events.filter(event_type="SENT").exists()


@pytest.mark.django_db
def test_only_seller_can_accept():
    user_seller = get_user_model().objects.create_user(username="sellerM6b", password="pass")
    user_buyer = get_user_model().objects.create_user(username="buyerM6b", password="pass")
    club_seller = Club.objects.create(user=user_seller, name="Seller Club B")
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club B")
    player = Player.objects.create(
        name="Contracted Two",
        created_by=user_seller,
        current_club=club_seller,
        status=Player.Status.CONTRACTED,
    )
    offer = create_draft_offer(player=player, from_club=club_buyer, to_club=club_seller)
    send_offer(offer, user_buyer, club_buyer)

    with pytest.raises(PermissionDenied):
        accept_offer(offer, user_buyer, club_buyer)

    accept_offer(offer, user_seller, club_seller)
    offer.refresh_from_db()
    assert offer.status == Offer.Status.ACCEPTED


@pytest.mark.django_db
def test_counter_offer_records_event_and_updates_terms():
    user_seller = get_user_model().objects.create_user(username="sellerM6c", password="pass")
    user_buyer = get_user_model().objects.create_user(username="buyerM6c", password="pass")
    club_seller = Club.objects.create(user=user_seller, name="Seller Club C")
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club C")
    player = Player.objects.create(
        name="Contracted Three",
        created_by=user_seller,
        current_club=club_seller,
        status=Player.Status.CONTRACTED,
    )
    offer = create_draft_offer(player=player, from_club=club_buyer, to_club=club_seller)
    send_offer(offer, user_buyer, club_buyer)

    counter_offer(
        offer,
        user_seller,
        club_seller,
        fee_amount=250,
        wage_weekly=20,
        contract_years=4,
    )
    offer.refresh_from_db()
    assert offer.status == Offer.Status.COUNTERED
    event = offer.events.filter(event_type="COUNTERED").last()
    assert event is not None
    assert "fee_amount" in event.payload.get("changed_fields", [])


@pytest.mark.django_db
def test_withdraw_offer_buyer_only():
    user_seller = get_user_model().objects.create_user(username="sellerM6d", password="pass")
    user_buyer = get_user_model().objects.create_user(username="buyerM6d", password="pass")
    club_seller = Club.objects.create(user=user_seller, name="Seller Club D")
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club D")
    player = Player.objects.create(
        name="Contracted Four",
        created_by=user_seller,
        current_club=club_seller,
        status=Player.Status.CONTRACTED,
    )
    offer = create_draft_offer(player=player, from_club=club_buyer, to_club=club_seller)
    send_offer(offer, user_buyer, club_buyer)

    with pytest.raises(PermissionDenied):
        withdraw_offer(offer, user_seller, club_seller)

    withdraw_offer(offer, user_buyer, club_buyer)
    offer.refresh_from_db()
    assert offer.status == Offer.Status.WITHDRAWN


@pytest.mark.django_db
def test_expire_opportunistic(client):
    user_seller = get_user_model().objects.create_user(username="sellerM6e", password="pass")
    user_buyer = get_user_model().objects.create_user(username="buyerM6e", password="pass")
    club_seller = Club.objects.create(user=user_seller, name="Seller Club E")
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club E")
    player = Player.objects.create(
        name="Contracted Five",
        created_by=user_seller,
        current_club=club_seller,
        status=Player.Status.CONTRACTED,
    )
    offer = create_draft_offer(
        player=player,
        from_club=club_buyer,
        to_club=club_seller,
        expires_at=timezone.now() - timezone.timedelta(days=1),
    )
    send_offer(offer, user_buyer, club_buyer)

    client.force_login(user_seller)
    client.get(reverse("marketplace:offer_received"))
    offer.refresh_from_db()
    assert offer.status == Offer.Status.EXPIRED


@pytest.mark.django_db
def test_free_agent_offer_allowed_but_accept_blocked(client):
    user_buyer = get_user_model().objects.create_user(username="buyerM6f", password="pass")
    user_staff = get_user_model().objects.create_user(
        username="adminM6f", password="pass", is_staff=True
    )
    club_buyer = Club.objects.create(user=user_buyer, name="Buyer Club F")
    player = Player.objects.create(
        name="Free Agent",
        created_by=user_buyer,
        current_club=None,
        status=Player.Status.FREE_AGENT,
    )
    offer = create_draft_offer(player=player, from_club=club_buyer, to_club=None)
    send_offer(offer, user_buyer, club_buyer)

    with pytest.raises(ValidationError):
        accept_offer(offer, user_buyer, club_buyer)

    client.force_login(user_staff)
    response = client.get(reverse("marketplace:free_agent_offers"))
    assert response.status_code == 200

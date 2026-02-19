from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from apps.accounts.models import ClubProfile
from apps.auctions.models import Auction, Bid
from apps.players.models import Player


@pytest.fixture
def groups(db):
    buyer_group, _ = Group.objects.get_or_create(name="buyer")
    seller_group, _ = Group.objects.get_or_create(name="seller")
    admin_group, _ = Group.objects.get_or_create(name="admin")
    return {"buyer": buyer_group, "seller": seller_group, "admin": admin_group}


@pytest.fixture
def user_factory(db, groups):
    def _create(username, group_name, club_name):
        user_model = get_user_model()
        user = user_model.objects.create_user(username=username, password="password123")
        user.groups.add(groups[group_name])
        ClubProfile.objects.create(user=user, club_name=club_name)
        return user

    return _create


@pytest.fixture
def seller_user(user_factory):
    return user_factory("seller", "seller", "Seller United")


@pytest.fixture
def buyer_user(user_factory):
    return user_factory("buyer1", "buyer", "Buyer FC")


@pytest.fixture
def buyer_user2(user_factory):
    return user_factory("buyer2", "buyer", "Northside FC")


@pytest.fixture
def auction_with_bids(seller_user, buyer_user, buyer_user2):
    player = Player.objects.create(
        name="Player One",
        age=24,
        position=Player.Position.MID,
        current_club=seller_user.club_profile,
        created_by=seller_user,
    )
    auction = Auction.objects.create(
        player=player,
        seller=seller_user,
        deadline=timezone.now() + timedelta(days=1),
    )
    bid1 = Bid.objects.create(auction=auction, buyer=buyer_user, amount=Decimal("100.00"))
    bid2 = Bid.objects.create(auction=auction, buyer=buyer_user2, amount=Decimal("120.00"))
    return auction, bid1, bid2

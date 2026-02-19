from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import ClubProfile
from apps.players.models import Player
from apps.stats.models import PlayerForm, PlayerStatsSnapshot
from .forms import OfferForm, OfferMessageForm
from .models import Listing, Offer
from .query import club_search_queryset, get_open_listing_for_player, listing_search_queryset, player_search_queryset
from .services import (
    add_message,
    close_offer_if_expired,
    counter_offer,
    create_draft_offer,
    get_actor_club,
    send_offer,
    accept_offer,
    reject_offer,
    withdraw_offer,
)


def listing_list(request):
    listings = (
        Listing.objects.select_related("player", "listed_by_club")
        .filter(status=Listing.Status.OPEN)
        .order_by("-created_at")
    )
    paginator = Paginator(listings, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "marketplace/listing_list.html", {"page_obj": page})


@login_required
def player_market_list(request):
    club = getattr(request.user, "club_profile", None)
    can_scout = bool(club)
    queryset = player_search_queryset(club, request.GET)
    paginator = Paginator(queryset, 25)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    shortlists = []
    interest_map = {}
    if club:
        from apps.scouting.models import PlayerInterest, Shortlist

        shortlists = list(Shortlist.objects.filter(club=club).order_by("name"))
        interest_map = {
            interest.player_id: interest
            for interest in PlayerInterest.objects.filter(
                club=club, player_id__in=[p.id for p in page.object_list]
            )
        }
        for player in page.object_list:
            player.interest = interest_map.get(player.id)
    template = (
        "marketplace/_player_results.html"
        if request.htmx
        else "marketplace/player_list.html"
    )
    return render(
        request,
        template,
        {
            "page_obj": page,
            "filters": request.GET,
            "base_query": base_query.urlencode(),
            "shortlists": shortlists,
            "interest_map": interest_map,
            "can_scout": can_scout,
        },
    )


@login_required
def player_market_detail(request, pk: int):
    player = get_object_or_404(Player, pk=pk)
    listing = get_open_listing_for_player(player)
    club = getattr(request.user, "club_profile", None)
    can_scout = bool(club)
    interest = None
    shortlists = []
    if club:
        from apps.scouting.models import PlayerInterest, Shortlist

        interest = PlayerInterest.objects.filter(club=club, player=player).first()
        shortlists = list(Shortlist.objects.filter(club=club).order_by("name"))
    if listing and listing.visibility == Listing.Visibility.INVITE_ONLY:
        invited = listing.invites.filter(club=club).exists() if club else False
        if not club or (listing.listed_by_club_id != club.id and not invited):
            listing = None
    latest_snapshot = player.stats_snapshots.order_by("-as_of").first()
    form = PlayerForm.objects.filter(player=player).first()
    return render(
        request,
        "marketplace/player_detail.html",
        {
            "player": player,
            "listing": listing,
            "latest_snapshot": latest_snapshot,
            "player_form": form,
            "interest": interest,
            "shortlists": shortlists,
            "can_scout": can_scout,
        },
    )


@login_required
def club_list(request):
    queryset = club_search_queryset(request.GET)
    paginator = Paginator(queryset, 25)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    template = (
        "marketplace/_club_results.html" if request.htmx else "marketplace/club_list.html"
    )
    return render(
        request,
        template,
        {"page_obj": page, "filters": request.GET, "base_query": base_query.urlencode()},
    )


@login_required
def club_detail(request, pk: int):
    club = get_object_or_404(ClubProfile, pk=pk)
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "").strip()

    squad = Player.objects.filter(current_club=club)
    if q:
        squad = squad.filter(name__icontains=q)
    if position:
        squad = squad.filter(position=position)
    squad = squad.order_by("name")
    squad_paginator = Paginator(squad, 25)
    squad_page = squad_paginator.get_page(request.GET.get("page"))

    listings = Listing.objects.filter(listed_by_club=club, status=Listing.Status.OPEN)
    show_contact = hasattr(request.user, "club_profile")

    return render(
        request,
        "marketplace/club_detail.html",
        {
            "club": club,
            "squad_page": squad_page,
            "listings": listings,
            "q": q,
            "position": position,
            "show_contact": show_contact,
        },
    )


@login_required
def listing_hub_list(request):
    club = getattr(request.user, "club_profile", None)
    queryset = listing_search_queryset(club, request.GET)
    paginator = Paginator(queryset, 25)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    template = (
        "marketplace/_listing_results.html"
        if request.htmx
        else "marketplace/listing_hub.html"
    )
    return render(
        request,
        template,
        {"page_obj": page, "filters": request.GET, "base_query": base_query.urlencode()},
    )


@login_required
def listing_detail(request, pk: int):
    listing = get_object_or_404(Listing, pk=pk)
    club = getattr(request.user, "club_profile", None)
    if listing.visibility == Listing.Visibility.INVITE_ONLY:
        if not club:
            raise PermissionDenied("Not allowed.")
        invited = listing.invites.filter(club=club).exists()
        if listing.listed_by_club_id != club.id and not invited:
            raise PermissionDenied("Not allowed.")
    return render(
        request,
        "marketplace/listing_detail.html",
        {"listing": listing, "player": listing.player},
    )


def _require_club(user):
    club = get_actor_club(user)
    if not club:
        raise PermissionDenied("Club profile required.")
    return club


def _expire_inbox_offers(queryset):
    now = timezone.now()
    expirable = queryset.filter(
        status__in=[Offer.Status.SENT, Offer.Status.COUNTERED],
        expires_at__isnull=False,
        expires_at__lte=now,
    )
    for offer in expirable:
        close_offer_if_expired(offer, now=now)


@login_required
def offer_received_list(request):
    club = _require_club(request.user)
    status = request.GET.get("status")
    q = request.GET.get("q", "").strip()
    listing_id = request.GET.get("listing")

    offers = Offer.objects.select_related("player", "from_club", "to_club").filter(
        to_club=club
    )
    if status:
        offers = offers.filter(status=status)
    if q:
        offers = offers.filter(player__name__icontains=q)
    if listing_id:
        offers = offers.filter(listing_id=listing_id)

    _expire_inbox_offers(offers)

    paginator = Paginator(offers.order_by("-created_at"), 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "marketplace/offer_list.html",
        {"page_obj": page, "view_title": "Received offers", "mode": "received"},
    )


@login_required
def offer_sent_list(request):
    club = _require_club(request.user)
    status = request.GET.get("status")
    q = request.GET.get("q", "").strip()
    listing_id = request.GET.get("listing")

    offers = Offer.objects.select_related("player", "from_club", "to_club").filter(
        from_club=club
    )
    if status:
        offers = offers.filter(status=status)
    if q:
        offers = offers.filter(player__name__icontains=q)
    if listing_id:
        offers = offers.filter(listing_id=listing_id)

    _expire_inbox_offers(offers)

    paginator = Paginator(offers.order_by("-created_at"), 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "marketplace/offer_list.html",
        {"page_obj": page, "view_title": "Sent offers", "mode": "sent"},
    )


@login_required
def offer_detail(request, pk: int):
    offer = get_object_or_404(
        Offer.objects.select_related("player", "from_club", "to_club", "listing"), pk=pk
    )
    club = _require_club(request.user)
    if club.id not in {offer.from_club_id, offer.to_club_id} and not request.user.is_staff:
        raise PermissionDenied("Not allowed.")

    close_offer_if_expired(offer)
    messages_form = OfferMessageForm()
    counter_form = OfferForm()
    timeline_events = []
    for event in offer.events.order_by("created_at"):
        timeline_events.append(
            {"label": event.get_event_type_display(), "created_at": event.created_at}
        )
    role = "Staff"
    if club.id == offer.from_club_id:
        role = "Buyer"
    elif club.id == offer.to_club_id:
        role = "Seller"

    shortlists = []
    interest = None
    if club:
        from apps.scouting.models import PlayerInterest, Shortlist

        shortlists = list(Shortlist.objects.filter(club=club).order_by("name"))
        interest = PlayerInterest.objects.filter(club=club, player=offer.player).first()

    return render(
        request,
        "marketplace/offer_detail.html",
        {
            "offer": offer,
            "club": club,
            "role": role,
            "events": timeline_events,
            "messages": offer.messages.select_related("sender_user", "sender_club").order_by(
                "created_at"
            ),
            "message_form": messages_form,
            "offer_counter_form": counter_form,
            "shortlists": shortlists,
            "interest": interest,
            "can_scout": True,
        },
    )


@login_required
def offer_new(request):
    club = _require_club(request.user)
    player_id = request.GET.get("player") or request.POST.get("player")
    listing_id = request.GET.get("listing") or request.POST.get("listing")
    player = get_object_or_404(Player, pk=player_id)
    listing = Listing.objects.filter(pk=listing_id).first() if listing_id else None
    to_club = player.current_club if player.current_club_id else None

    if request.method == "POST":
        form = OfferForm(request.POST)
        if form.is_valid():
            try:
                offer = create_draft_offer(
                    player=player,
                    from_club=club,
                    listing=listing,
                    to_club=to_club,
                    fee_amount=form.cleaned_data["fee_amount"],
                    wage_weekly=form.cleaned_data["wage_weekly"],
                    contract_years=form.cleaned_data["contract_years"],
                    contract_end_date=form.cleaned_data["contract_end_date"],
                    expires_at=form.cleaned_data["expires_at"],
                    add_ons=form.cleaned_data["add_ons_raw"],
                )
                send_offer(offer, request.user, club)
                messages.success(request, "Offer sent.")
                return redirect("marketplace:offer_detail", pk=offer.id)
            except (ValidationError, PermissionDenied) as exc:
                messages.error(request, str(exc))
    else:
        form = OfferForm()

    return render(
        request,
        "marketplace/offer_new.html",
        {"form": form, "player": player, "listing": listing, "to_club": to_club},
    )


@login_required
def offer_counter(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    form = OfferForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid counter offer.")
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        counter_offer(
            offer,
            request.user,
            club,
            fee_amount=form.cleaned_data["fee_amount"],
            wage_weekly=form.cleaned_data["wage_weekly"],
            contract_years=form.cleaned_data["contract_years"],
            contract_end_date=form.cleaned_data["contract_end_date"],
            expires_at=form.cleaned_data["expires_at"],
            add_ons=form.cleaned_data["add_ons_raw"],
        )
        messages.success(request, "Counter offer sent.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def offer_accept(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        accept_offer(offer, request.user, club)
        messages.success(request, "Offer accepted.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def offer_reject(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        reject_offer(offer, request.user, club)
        messages.success(request, "Offer rejected.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def offer_withdraw(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        withdraw_offer(offer, request.user, club)
        messages.success(request, "Offer withdrawn.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def offer_message(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    form = OfferMessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Message cannot be empty.")
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        add_message(offer, request.user, club, form.cleaned_data["body"])
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def free_agent_offers(request):
    if not request.user.is_staff:
        raise PermissionDenied("Staff only.")
    offers = Offer.objects.select_related("player", "from_club").filter(
        to_club__isnull=True, player__current_club__isnull=True
    )
    paginator = Paginator(offers.order_by("-created_at"), 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "marketplace/free_agent_offers.html", {"page_obj": page})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import Club
from apps.players.models import Contract, Player
from apps.stats.models import PlayerForm, PlayerStats, PlayerStatsSnapshot
from .forms import OfferForm, OfferMessageForm
from .models import Listing, Offer, OfferEvent, OfferMessage
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



@login_required
def player_market_list(request):
    club = getattr(request.user, "club", None)
    can_scout = bool(club)
    queryset = player_search_queryset(club, request.GET)
    paginator = Paginator(queryset, 24)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    shortlists = []
    interest_map = {}
    availability = request.GET.getlist("availability")
    if not availability:
        raw = request.GET.get("availability", "")
        availability = [value.strip() for value in raw.split(",") if value.strip()]
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
        "marketplace/_player_market_grid.html"
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
            "selected_availability": availability,
        },
    )


@login_required
def player_market_detail(request, pk: int):
    player = get_object_or_404(Player, pk=pk)
    listing = get_open_listing_for_player(player)
    club = getattr(request.user, "club", None)
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
    club = get_object_or_404(Club, pk=pk)
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
    show_contact = hasattr(request.user, "club")

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
    club = getattr(request.user, "club", None)
    queryset = listing_search_queryset(club, request.GET)
    paginator = Paginator(queryset, 24)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    seller_clubs = (
        Club.objects.filter(listings__status=Listing.Status.OPEN)
        .distinct()
        .order_by("name")
    )
    template = (
        "marketplace/_listing_cards.html"
        if request.htmx
        else "marketplace/listing_hub.html"
    )
    return render(
        request,
        template,
        {
            "page_obj": page,
            "filters": request.GET,
            "base_query": base_query.urlencode(),
            "seller_clubs": seller_clubs,
        },
    )


@login_required
def listing_detail(request, pk: int):
    listing = get_object_or_404(
        Listing.objects.select_related(
            "player", "player__current_club", "player__form", "listed_by_club"
        ),
        pk=pk,
    )
    club = getattr(request.user, "club", None)
    if listing.visibility == Listing.Visibility.INVITE_ONLY:
        if not club:
            raise PermissionDenied("Not allowed.")
        invited = listing.invites.filter(club=club).exists()
        if listing.listed_by_club_id != club.id and not invited:
            raise PermissionDenied("Not allowed.")
    player_stats = (
        PlayerStats.objects.filter(player=listing.player)
        .order_by("-season", "-updated_at", "-id")
        .first()
    )
    contract_end_date = (
        Contract.objects.filter(player=listing.player, is_active=True)
        .order_by("-end_date", "-id")
        .values_list("end_date", flat=True)
        .first()
    )
    recent_form = None
    if listing.player.form and listing.player.form.key_metrics:
        recent_form = listing.player.form.key_metrics.get("recent_results")
    offers_count = listing.offers.exclude(status=Offer.Status.DRAFT).count()
    related = (
        Listing.objects.select_related("player", "player__current_club", "player__form", "listed_by_club")
        .filter(status=Listing.Status.OPEN, player__position=listing.player.position)
        .exclude(id=listing.id)
    )
    if club:
        related = related.filter(
            Q(visibility=Listing.Visibility.PUBLIC)
            | Q(listed_by_club=club)
            | Q(invites__club=club)
        )
    else:
        related = related.filter(visibility=Listing.Visibility.PUBLIC)
    return render(
        request,
        "marketplace/listing_detail.html",
        {
            "listing": listing,
            "player": listing.player,
            "player_stats": player_stats,
            "recent_form": recent_form,
            "offers_count": offers_count,
            "contract_end_date": contract_end_date,
            "related_listings": related[:4],
            "is_seller": bool(club and listing.listed_by_club_id == club.id),
            "club": club,
        },
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


def _group_offers(offers, club, mode: str):
    needs_response = []
    awaiting_reply = []
    closed = []
    for offer in offers:
        pending = offer.status in {Offer.Status.SENT, Offer.Status.COUNTERED}
        last_actor_id = offer.last_actor_club_id
        is_unread = pending and last_actor_id and last_actor_id != club.id
        if mode == "received":
            counterparty = offer.from_club
        else:
            counterparty = offer.to_club
        needs_action = pending and last_actor_id and last_actor_id != club.id

        card = {
            "offer": offer,
            "counterparty": counterparty,
            "latest_fee": offer.fee_amount,
            "latest_wage": offer.wage_weekly,
            "last_message": offer.messages.order_by("-created_at").first(),
            "last_action_at": offer.last_action_at,
            "expires_at": offer.expires_at,
            "unread": is_unread,
        }
        if pending:
            if needs_action:
                needs_response.append(card)
            else:
                awaiting_reply.append(card)
        else:
            closed.append(card)
    return {
        "needs_response": needs_response,
        "awaiting_reply": awaiting_reply,
        "closed": closed,
    }


def _offer_thread_context(
    *,
    offer,
    club,
    role,
    message_form,
    counter_form,
    shortlists,
    interest,
    can_scout,
    request,
):
    events = []
    message_map = {
        message.id: message
        for message in OfferMessage.objects.filter(offer=offer).select_related(
            "sender_user", "sender_club"
        )
    }
    for event in offer.events.select_related("actor_club").order_by("created_at"):
        payload = event.payload or {}
        message = None
        if event.event_type == OfferEvent.EventType.MESSAGE:
            message = message_map.get(payload.get("message_id"))
        terms = payload.get("terms")
        if event.event_type in {
            OfferEvent.EventType.CREATED,
            OfferEvent.EventType.SENT,
            OfferEvent.EventType.COUNTERED,
        } and not terms:
            terms = {
                "fee_amount": str(offer.fee_amount) if offer.fee_amount is not None else None,
                "wage_weekly": str(offer.wage_weekly) if offer.wage_weekly is not None else None,
                "contract_years": offer.contract_years,
                "contract_end_date": offer.contract_end_date.isoformat()
                if offer.contract_end_date
                else None,
            }
        events.append(
            {
                "event": event,
                "direction": "sent" if event.actor_club_id == club.id else "received",
                "actor_name": event.actor_club.name if event.actor_club else "System",
                "message": message.body if message else None,
                "terms": terms,
                "timestamp": event.created_at,
            }
        )

    last_event = events[-1]["event"] if events else None
    pending = offer.status in {Offer.Status.SENT, Offer.Status.COUNTERED}
    is_participant = club.id in {offer.from_club_id, offer.to_club_id}
    your_turn = bool(
        pending
        and is_participant
        and last_event
        and last_event.actor_club_id != club.id
    )
    awaiting_label = None
    if pending and last_event and last_event.actor_club_id == club.id:
        awaiting_label = (
            offer.to_club.name if club.id == offer.from_club_id else offer.from_club.name
        )

    step_labels = ["Interest", "Offer Made", "Negotiation", "Agreement", "Completed"]
    status_step_map = {
        Offer.Status.DRAFT: 0,
        Offer.Status.SENT: 1,
        Offer.Status.COUNTERED: 2,
        Offer.Status.ACCEPTED: 3,
        Offer.Status.REJECTED: 4,
        Offer.Status.WITHDRAWN: 4,
        Offer.Status.EXPIRED: 4,
    }
    current_step = status_step_map.get(offer.status, 0)

    return {
        "offer": offer,
        "club": club,
        "role": role,
        "events": events,
        "message_form": message_form,
        "offer_counter_form": counter_form,
        "shortlists": shortlists,
        "interest": interest,
        "can_scout": can_scout,
        "your_turn": your_turn,
        "awaiting_label": awaiting_label,
        "step_labels": step_labels,
        "current_step": current_step,
        "request": request,
    }


@login_required
def offer_received_list(request):
    club = _require_club(request.user)
    status = request.GET.get("status")
    q = request.GET.get("q", "").strip()
    listing_id = request.GET.get("listing")

    last_event = OfferEvent.objects.filter(offer_id=OuterRef("pk")).order_by("-created_at")
    offers = (
        Offer.objects.select_related("player", "from_club", "to_club")
        .prefetch_related("messages")
        .filter(to_club=club)
        .annotate(
            last_actor_club_id=Subquery(last_event.values("actor_club_id")[:1]),
            last_event_type=Subquery(last_event.values("event_type")[:1]),
        )
        .order_by("-last_action_at")
    )
    if status:
        offers = offers.filter(status=status)
    if q:
        offers = offers.filter(player__name__icontains=q)
    if listing_id:
        offers = offers.filter(listing_id=listing_id)

    _expire_inbox_offers(offers)

    paginator = Paginator(offers, 25)
    page = paginator.get_page(request.GET.get("page"))
    grouped = _group_offers(page.object_list, club, mode="received")
    return render(
        request,
        "marketplace/offer_list.html",
        {
            "page_obj": page,
            "view_title": "Received offers",
            "mode": "received",
            "grouped_offers": grouped,
        },
    )


@login_required
def offer_sent_list(request):
    club = _require_club(request.user)
    status = request.GET.get("status")
    q = request.GET.get("q", "").strip()
    listing_id = request.GET.get("listing")

    last_event = OfferEvent.objects.filter(offer_id=OuterRef("pk")).order_by("-created_at")
    offers = (
        Offer.objects.select_related("player", "from_club", "to_club")
        .prefetch_related("messages")
        .filter(from_club=club)
        .annotate(
            last_actor_club_id=Subquery(last_event.values("actor_club_id")[:1]),
            last_event_type=Subquery(last_event.values("event_type")[:1]),
        )
        .order_by("-last_action_at")
    )
    if status:
        offers = offers.filter(status=status)
    if q:
        offers = offers.filter(player__name__icontains=q)
    if listing_id:
        offers = offers.filter(listing_id=listing_id)

    _expire_inbox_offers(offers)

    paginator = Paginator(offers, 25)
    page = paginator.get_page(request.GET.get("page"))
    grouped = _group_offers(page.object_list, club, mode="sent")
    return render(
        request,
        "marketplace/offer_list.html",
        {
            "page_obj": page,
            "view_title": "Sent offers",
            "mode": "sent",
            "grouped_offers": grouped,
        },
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

    context = _offer_thread_context(
        offer=offer,
        club=club,
        role=role,
        message_form=messages_form,
        counter_form=counter_form,
        shortlists=shortlists,
        interest=interest,
        can_scout=True,
        request=request,
    )
    if request.htmx and request.GET.get("partial") == "counter_form":
        return render(request, "marketplace/_offer_counter_form.html", context)
    return render(request, "marketplace/offer_detail.html", context)


@login_required
def offer_new(request):
    club = _require_club(request.user)
    player_id = request.GET.get("player") or request.POST.get("player")
    listing_id = request.GET.get("listing") or request.POST.get("listing")
    player = get_object_or_404(Player, pk=player_id)
    listing = Listing.objects.filter(pk=listing_id).first() if listing_id else None
    to_club = player.current_club if player.current_club_id else None

    if to_club and to_club.id == club.id:
        messages.error(request, "You cannot make an offer on your own player.")
        return redirect("marketplace:listing_hub_list")

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
        message_body = request.POST.get("message", "").strip()
        if message_body:
            add_message(offer, request.user, club, message_body)
        messages.success(request, "Counter offer sent.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    if request.htmx:
        offer = Offer.objects.select_related("player", "from_club", "to_club", "listing").get(pk=pk)
        role = "Staff"
        if club.id == offer.from_club_id:
            role = "Buyer"
        elif club.id == offer.to_club_id:
            role = "Seller"
        context = _offer_thread_context(
            offer=offer,
            club=club,
            role=role,
            message_form=OfferMessageForm(),
            counter_form=OfferForm(),
            shortlists=[],
            interest=None,
            can_scout=False,
            request=request,
        )
        return render(request, "marketplace/_offer_thread.html", context)
    return redirect("marketplace:offer_detail", pk=pk)


@login_required
def offer_accept(request, pk: int):
    offer = get_object_or_404(Offer, pk=pk)
    club = _require_club(request.user)
    if request.method != "POST":
        return redirect("marketplace:offer_detail", pk=pk)
    try:
        accept_offer(offer, request.user, club)
        offer.refresh_from_db()
        messages.success(request, "Offer accepted.")
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, str(exc))
    if hasattr(offer, "deal"):
        return redirect("deals:detail", pk=offer.deal.id)
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

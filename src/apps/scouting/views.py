from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.marketplace.models import Listing
from apps.players.models import Player
from .forms import ShortlistForm
from .models import PlayerInterest, Shortlist, ShortlistItem
from .services import (
    add_player_to_shortlist,
    clear_player_interest,
    create_shortlist,
    delete_shortlist,
    get_actor_club,
    offers_expiring_soon,
    remove_player_from_shortlist,
    rename_shortlist,
    set_player_interest,
    watched_now_available,
)


def _require_club(user):
    club = get_actor_club(user)
    if not club:
        raise PermissionDenied("Club profile required.")
    return club


@login_required
def shortlist_list(request):
    club = _require_club(request.user)
    shortlists = (
        Shortlist.objects.filter(club=club)
        .annotate(item_count=Count("items"))
        .order_by("name")
    )
    return render(request, "scouting/shortlist_list.html", {"shortlists": shortlists})


@login_required
def shortlist_new(request):
    club = _require_club(request.user)
    if request.method == "POST":
        form = ShortlistForm(request.POST)
        if form.is_valid():
            try:
                create_shortlist(
                    club=club,
                    name=form.cleaned_data["name"],
                    description=form.cleaned_data.get("description", ""),
                )
                messages.success(request, "Shortlist created.")
                return redirect("scouting:shortlist_list")
            except ValidationError as exc:
                messages.error(request, str(exc))
    else:
        form = ShortlistForm()
    return render(request, "scouting/shortlist_form.html", {"form": form})


@login_required
def shortlist_detail(request, pk: int):
    club = _require_club(request.user)
    shortlist = get_object_or_404(Shortlist, pk=pk, club=club)
    q = request.GET.get("q", "").strip()
    priority = request.GET.get("priority", "").strip()
    sort = request.GET.get("sort", "priority")

    items = ShortlistItem.objects.select_related("player", "player__current_club").filter(
        shortlist=shortlist
    )
    if q:
        items = items.filter(player__name__icontains=q)
    if priority:
        try:
            items = items.filter(priority=int(priority))
        except ValueError:
            pass

    if sort == "updated":
        items = items.order_by("-updated_at")
    else:
        items = items.order_by("priority", "-updated_at")

    paginator = Paginator(items, 50)
    page = paginator.get_page(request.GET.get("page"))

    player_ids = [item.player_id for item in page.object_list]
    interest_map = {
        interest.player_id: interest
        for interest in PlayerInterest.objects.filter(club=club, player_id__in=player_ids)
    }
    open_listing_ids = list(
        Listing.objects.filter(
            player_id__in=player_ids, status=Listing.Status.OPEN
        ).values_list("player_id", flat=True)
    )
    for item in page.object_list:
        item.interest = interest_map.get(item.player_id)

    form = ShortlistForm(instance=shortlist)
    return render(
        request,
        "scouting/shortlist_detail.html",
        {
            "shortlist": shortlist,
            "page_obj": page,
            "interest_map": interest_map,
            "open_listing_ids": open_listing_ids,
            "filters": {"q": q, "priority": priority, "sort": sort},
            "form": form,
        },
    )


@login_required
def shortlist_edit(request, pk: int):
    club = _require_club(request.user)
    shortlist = get_object_or_404(Shortlist, pk=pk, club=club)
    if request.method != "POST":
        return redirect("scouting:shortlist_detail", pk=pk)
    form = ShortlistForm(request.POST, instance=shortlist)
    if form.is_valid():
        try:
            rename_shortlist(
                shortlist,
                new_name=form.cleaned_data["name"],
                description=form.cleaned_data.get("description", ""),
            )
            messages.success(request, "Shortlist updated.")
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect("scouting:shortlist_detail", pk=pk)


@login_required
def shortlist_delete(request, pk: int):
    club = _require_club(request.user)
    shortlist = get_object_or_404(Shortlist, pk=pk, club=club)
    if request.method == "POST":
        delete_shortlist(shortlist)
        messages.success(request, "Shortlist deleted.")
    return redirect("scouting:shortlist_list")


@login_required
def shortlist_add(request, pk: int):
    club = _require_club(request.user)
    shortlist = get_object_or_404(Shortlist, pk=pk, club=club)
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        priority = request.POST.get("priority", 3)
        notes = request.POST.get("notes", "")
        player = get_object_or_404(Player, pk=player_id)
        try:
            add_player_to_shortlist(shortlist, player, priority=int(priority), notes=notes)
            messages.success(request, "Player added to shortlist.")
        except (ValidationError, ValueError) as exc:
            messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "scouting:shortlist_detail", pk=pk)


@login_required
def shortlist_add_any(request):
    club = _require_club(request.user)
    if request.method == "POST":
        shortlist_id = request.POST.get("shortlist_id")
        player_id = request.POST.get("player_id")
        priority = request.POST.get("priority", 3)
        notes = request.POST.get("notes", "")
        shortlist = get_object_or_404(Shortlist, pk=shortlist_id, club=club)
        player = get_object_or_404(Player, pk=player_id)
        try:
            add_player_to_shortlist(shortlist, player, priority=int(priority), notes=notes)
            messages.success(request, "Player added to shortlist.")
        except (ValidationError, ValueError) as exc:
            messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "scouting:shortlist_list")


@login_required
def shortlist_remove(request, pk: int):
    club = _require_club(request.user)
    shortlist = get_object_or_404(Shortlist, pk=pk, club=club)
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        player = get_object_or_404(Player, pk=player_id)
        remove_player_from_shortlist(shortlist, player)
        messages.success(request, "Player removed from shortlist.")
    return redirect(request.POST.get("next") or "scouting:shortlist_detail", pk=pk)


@login_required
def shortlist_item_update(request, pk: int):
    club = _require_club(request.user)
    item = get_object_or_404(
        ShortlistItem.objects.select_related("shortlist"),
        pk=pk,
        shortlist__club=club,
    )
    if request.method == "POST":
        priority = request.POST.get("priority", item.priority)
        notes = request.POST.get("notes", item.notes)
        try:
            item.priority = int(priority)
            item.notes = notes
            item.save(update_fields=["priority", "notes", "updated_at"])
            messages.success(request, "Shortlist item updated.")
        except ValueError:
            messages.error(request, "Priority must be a number.")
    return redirect(request.POST.get("next") or "scouting:shortlist_detail", pk=item.shortlist_id)


@login_required
def interest_set(request):
    club = _require_club(request.user)
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        level = request.POST.get("level")
        stage = request.POST.get("stage")
        notes = request.POST.get("notes")
        player = get_object_or_404(Player, pk=player_id)
        try:
            set_player_interest(club, player, level=level, stage=stage, notes=notes)
            messages.success(request, "Interest updated.")
        except ValidationError as exc:
            messages.error(request, str(exc))
    return redirect(request.POST.get("next") or "scouting:targets_dashboard")


@login_required
def interest_clear(request):
    club = _require_club(request.user)
    if request.method == "POST":
        player_id = request.POST.get("player_id")
        player = get_object_or_404(Player, pk=player_id)
        clear_player_interest(club, player)
        messages.success(request, "Interest cleared.")
    return redirect(request.POST.get("next") or "scouting:targets_dashboard")


@login_required
def targets_dashboard(request):
    club = _require_club(request.user)
    shortlists = (
        Shortlist.objects.filter(club=club)
        .annotate(item_count=Count("items"))
        .order_by("name")
    )
    recent_items = (
        ShortlistItem.objects.select_related("player", "shortlist")
        .filter(shortlist__club=club, updated_at__gte=timezone.now() - timedelta(days=7))
        .order_by("-updated_at")[:10]
    )
    expiring_offers = offers_expiring_soon(club).select_related("player")[:10]
    watched_available = watched_now_available(club)[:10]
    return render(
        request,
        "scouting/targets_dashboard.html",
        {
            "shortlists": shortlists,
            "recent_items": recent_items,
            "expiring_offers": expiring_offers,
            "watched_available": watched_available,
        },
    )

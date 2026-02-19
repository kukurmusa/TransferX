from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import seller_required
from .forms import PlayerForm
from .models import Player
from .services import normalize_player_market_flags, normalize_player_status


@seller_required
def player_list(request):
    sort = request.GET.get("sort", "name")
    queryset = (
        Player.objects.select_related("current_club", "form")
        .filter(created_by=request.user)
    )
    if sort == "form_desc":
        queryset = queryset.order_by(F("form__form_score").desc(nulls_last=True), "name")
    else:
        queryset = queryset.order_by("name")

    return render(
        request, "players/player_list.html", {"players": queryset, "sort": sort}
    )


@seller_required
def player_create(request):
    if request.method == "POST":
        form = PlayerForm(request.POST, user=request.user)
        if form.is_valid():
            player = form.save(commit=False)
            player.created_by = request.user
            if hasattr(request.user, "club_profile"):
                player.current_club = request.user.club_profile
            normalize_player_market_flags(player)
            player.save()
            messages.success(request, "Player created.")
            return redirect("players:list")
    else:
        form = PlayerForm(user=request.user)

    return render(request, "players/player_form.html", {"form": form, "is_edit": False})


@seller_required
def player_edit(request, pk: int):
    player = get_object_or_404(Player, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = PlayerForm(request.POST, instance=player, user=request.user)
        if form.is_valid():
            player = form.save(commit=False)
            if hasattr(request.user, "club_profile"):
                player.current_club = request.user.club_profile
            normalize_player_market_flags(player)
            player.save()
            messages.success(request, "Player updated.")
            return redirect("players:list")
    else:
        form = PlayerForm(instance=player, user=request.user)

    return render(request, "players/player_form.html", {"form": form, "is_edit": True})


@login_required
def free_agents(request):
    from apps.marketplace.query import player_search_queryset

    params = request.GET.copy()
    params["free_agent_only"] = "1"
    queryset = player_search_queryset(getattr(request.user, "club_profile", None), params)
    from django.core.paginator import Paginator

    paginator = Paginator(queryset, 25)
    page = paginator.get_page(request.GET.get("page"))
    base_query = request.GET.copy()
    base_query.pop("page", None)
    shortlists = []
    interest_map = {}
    club = getattr(request.user, "club_profile", None)
    can_scout = bool(club)
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
        "marketplace/_free_agent_results.html"
        if request.htmx
        else "marketplace/free_agents.html"
    )
    return render(
        request,
        template,
        {
            "page_obj": page,
            "q": request.GET.get("q", ""),
            "position": request.GET.get("position", ""),
            "base_query": base_query.urlencode(),
            "shortlists": shortlists,
            "interest_map": interest_map,
            "can_scout": can_scout,
        },
    )

from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.accounts.models import Club
from apps.players.models import Player
from apps.stats.models import PlayerStats


def _default_league_season():
    ps = PlayerStats.objects.order_by("-season").first()
    if ps:
        return ps.league_id, ps.season
    return None, None


def club_list(request):
    league_id = request.GET.get("league_id")
    season = request.GET.get("season")
    q = request.GET.get("q", "").strip()

    default_league, default_season = _default_league_season()
    league_id = int(league_id) if league_id else default_league
    season = int(season) if season else default_season

    clubs = Club.objects.filter(vendor_id__isnull=False)
    if q:
        clubs = clubs.filter(name__icontains=q)
    clubs = clubs.order_by("name")

    if league_id and season:
        club_ids = (
            PlayerStats.objects.filter(league_id=league_id, season=season)
            .values_list("current_club_id", flat=True)
            .distinct()
        )
        clubs = clubs.filter(id__in=club_ids)

    paginator = Paginator(clubs, 25)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "world/club_list.html",
        {
            "page_obj": page,
            "league_id": league_id,
            "season": season,
            "q": q,
        },
    )


def club_detail(request, pk: int):
    club = get_object_or_404(Club, pk=pk)
    league_id = request.GET.get("league_id")
    season = request.GET.get("season")
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "").strip()
    sort = request.GET.get("sort", "form_desc")

    default_league, default_season = _default_league_season()
    league_id = int(league_id) if league_id else default_league
    season = int(season) if season else default_season

    stats_qs = PlayerStats.objects.filter(
        current_club=club,
    ).select_related("player")
    if league_id:
        stats_qs = stats_qs.filter(league_id=league_id)
    if season:
        stats_qs = stats_qs.filter(season=season)
    if q:
        stats_qs = stats_qs.filter(player__name__icontains=q)
    if position:
        stats_qs = stats_qs.filter(position__iexact=position)

    if sort == "name":
        stats_qs = stats_qs.order_by("player__name")
    else:
        stats_qs = stats_qs.order_by("-form_score", "player__name")

    paginator = Paginator(stats_qs, 25)
    page = paginator.get_page(request.GET.get("page"))

    agg = stats_qs.aggregate(avg_age=Avg("player__age"), squad_size=Count("id"))

    return render(
        request,
        "world/club_detail.html",
        {
            "club": club,
            "page_obj": page,
            "league_id": league_id,
            "season": season,
            "q": q,
            "position": position,
            "sort": sort,
            "stats": agg,
        },
    )


def player_list(request):
    league_id = request.GET.get("league_id")
    season = request.GET.get("season")
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "").strip()
    sort = request.GET.get("sort", "form_desc")
    min_form = request.GET.get("min_form")
    club_id = request.GET.get("club")

    default_league, default_season = _default_league_season()
    league_id = int(league_id) if league_id else default_league
    season = int(season) if season else default_season

    stats_qs = PlayerStats.objects.select_related("player", "current_club")
    if league_id:
        stats_qs = stats_qs.filter(league_id=league_id)
    if season:
        stats_qs = stats_qs.filter(season=season)
    if q:
        stats_qs = stats_qs.filter(player__name__icontains=q)
    if position:
        stats_qs = stats_qs.filter(position__iexact=position)
    if club_id:
        stats_qs = stats_qs.filter(current_club_id=club_id)
    if min_form:
        try:
            stats_qs = stats_qs.filter(form_score__gte=float(min_form))
        except ValueError:
            pass

    if sort == "name":
        stats_qs = stats_qs.order_by("player__name")
    else:
        stats_qs = stats_qs.order_by("-form_score", "player__name")

    paginator = Paginator(stats_qs, 25)
    page = paginator.get_page(request.GET.get("page"))

    clubs = Club.objects.filter(vendor_id__isnull=False).order_by("name")

    return render(
        request,
        "world/player_list.html",
        {
            "page_obj": page,
            "league_id": league_id,
            "season": season,
            "q": q,
            "position": position,
            "sort": sort,
            "min_form": min_form,
            "club_id": club_id,
            "clubs": clubs,
        },
    )


def player_detail(request, pk: int):
    player = get_object_or_404(Player, pk=pk)
    stats = (
        PlayerStats.objects.select_related("player", "current_club")
        .filter(player=player)
        .first()
    )
    club = stats.current_club if stats else None

    return render(
        request,
        "world/player_detail.html",
        {
            "player": player,
            "profile": stats,
            "club": club,
            "offer_link": f"{reverse('marketplace:offer_new')}?player={player.id}",
        },
    )

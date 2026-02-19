from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import WorldClub, WorldClubProfile, WorldPlayer, WorldPlayerProfile, WorldSquadMembership


def _default_league_season():
    profile = WorldClubProfile.objects.order_by("-season").first()
    if profile:
        return profile.league_id, profile.season
    club = WorldClub.objects.order_by("-season").first()
    if club:
        return club.league_id, club.season
    return None, None


def club_list(request):
    league_id = request.GET.get("league_id")
    season = request.GET.get("season")
    q = request.GET.get("q", "").strip()

    default_league, default_season = _default_league_season()
    league_id = int(league_id) if league_id else default_league
    season = int(season) if season else default_season

    clubs = WorldClubProfile.objects.select_related("club")
    if league_id:
        clubs = clubs.filter(league_id=league_id)
    if season:
        clubs = clubs.filter(season=season)
    if q:
        clubs = clubs.filter(club__name__icontains=q)

    clubs = clubs.order_by("club__name")
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
    club = get_object_or_404(WorldClub, pk=pk)
    league_id = request.GET.get("league_id", club.league_id)
    season = request.GET.get("season", club.season)
    q = request.GET.get("q", "").strip()
    position = request.GET.get("position", "").strip()
    sort = request.GET.get("sort", "form_desc")

    profile = (
        WorldClubProfile.objects.filter(club=club, league_id=league_id, season=season)
        .select_related("club")
        .first()
    )

    memberships = WorldSquadMembership.objects.filter(
        club=club, league_id=league_id, season=season
    ).select_related("player")
    if q:
        memberships = memberships.filter(player__name__icontains=q)
    if position:
        memberships = memberships.filter(position__iexact=position)

    if sort == "name":
        memberships = memberships.order_by("player__name")
    else:
        memberships = memberships.order_by("-player__profile__form_score", "player__name")

    paginator = Paginator(memberships, 25)
    page = paginator.get_page(request.GET.get("page"))

    stats = memberships.aggregate(avg_age=Avg("player__age"), squad_size=Count("id"))

    return render(
        request,
        "world/club_detail.html",
        {
            "club": club,
            "profile": profile,
            "page_obj": page,
            "league_id": league_id,
            "season": season,
            "q": q,
            "position": position,
            "sort": sort,
            "stats": stats,
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

    players = WorldPlayerProfile.objects.select_related("player", "current_club")
    if league_id:
        players = players.filter(league_id=league_id)
    if season:
        players = players.filter(season=season)
    if q:
        players = players.filter(player__name__icontains=q)
    if position:
        players = players.filter(position__iexact=position)
    if club_id:
        players = players.filter(current_club_id=club_id)
    if min_form:
        try:
            players = players.filter(form_score__gte=float(min_form))
        except ValueError:
            pass

    if sort == "name":
        players = players.order_by("player__name")
    else:
        players = players.order_by("-form_score", "player__name")

    paginator = Paginator(players, 25)
    page = paginator.get_page(request.GET.get("page"))

    clubs = WorldClub.objects.order_by("name")
    if league_id:
        clubs = clubs.filter(league_id=league_id)
    if season:
        clubs = clubs.filter(season=season)

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
    player = get_object_or_404(WorldPlayer, pk=pk)
    profile = (
        WorldPlayerProfile.objects.select_related("player", "current_club")
        .filter(player=player)
        .first()
    )
    club = profile.current_club if profile else None
    club_profile = None
    if club and profile:
        club_profile = WorldClubProfile.objects.filter(
            club=club, league_id=profile.league_id, season=profile.season
        ).first()

    return render(
        request,
        "world/player_detail.html",
        {
            "player": player,
            "profile": profile,
            "club": club,
            "club_profile": club_profile,
            "offer_link": f"{reverse('marketplace:offer_new')}?player={player.id}",
        },
    )

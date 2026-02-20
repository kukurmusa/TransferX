from django.db.models import Min, Q

from apps.accounts.models import Club
from apps.players.models import Player
from .models import Listing, ListingInvite


def player_search_queryset(actor_club: Club | None, params):
    queryset = Player.objects.select_related("current_club", "form")
    if actor_club:
        queryset = queryset.exclude(visibility=Player.Visibility.PRIVATE)
    else:
        queryset = queryset.filter(visibility=Player.Visibility.PUBLIC)

    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(name__icontains=q)

    position = params.get("position")
    if position:
        queryset = queryset.filter(position=position)

    nationality = params.get("nationality")
    if nationality:
        queryset = queryset.filter(nationality__icontains=nationality)

    club_id = params.get("club")
    if club_id:
        queryset = queryset.filter(current_club_id=club_id)

    if params.get("free_agent_only") in {"1", "true", "True"}:
        queryset = queryset.filter(current_club__isnull=True)

    if params.get("listed_only") in {"1", "true", "True"}:
        queryset = queryset.filter(listings__status=Listing.Status.OPEN).distinct()

    min_form = params.get("min_form")
    if min_form:
        try:
            queryset = queryset.filter(form__form_score__gte=float(min_form))
        except ValueError:
            pass

    min_age = params.get("min_age")
    if min_age:
        try:
            queryset = queryset.filter(age__gte=int(min_age))
        except ValueError:
            pass

    max_age = params.get("max_age")
    if max_age:
        try:
            queryset = queryset.filter(age__lte=int(max_age))
        except ValueError:
            pass

    sort = params.get("sort", "performance")
    if sort == "age_asc":
        queryset = queryset.order_by("age", "name")
    elif sort == "minutes_desc":
        queryset = queryset.order_by("-form__minutes", "name")
    elif sort == "rating_desc":
        queryset = queryset.order_by("-form__avg_rating", "name")
    elif sort == "asking_price_asc":
        queryset = queryset.annotate(
            min_asking=Min("listings__asking_price", filter=Q(listings__status=Listing.Status.OPEN))
        ).order_by("min_asking", "name")
    else:
        queryset = queryset.order_by("-form__form_score", "name")

    return queryset


def listing_search_queryset(actor_club: Club | None, params):
    listings = Listing.objects.select_related("player", "listed_by_club").filter(
        status=Listing.Status.OPEN
    )
    if actor_club:
        invite_ids = ListingInvite.objects.filter(club=actor_club).values_list(
            "listing_id", flat=True
        )
        listings = listings.filter(
            Q(visibility=Listing.Visibility.PUBLIC)
            | Q(listed_by_club=actor_club)
            | Q(id__in=invite_ids)
        )
    else:
        listings = listings.filter(visibility=Listing.Visibility.PUBLIC)

    q = params.get("q", "").strip()
    if q:
        listings = listings.filter(player__name__icontains=q)

    sort = params.get("sort", "deadline")
    if sort == "asking_price_asc":
        listings = listings.order_by("asking_price", "deadline")
    elif sort == "deadline":
        listings = listings.order_by("deadline")
    else:
        listings = listings.order_by("-created_at")

    return listings


def club_search_queryset(params):
    queryset = Club.objects.all()
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(name__icontains=q)

    country = params.get("country")
    if country:
        queryset = queryset.filter(country__icontains=country)

    league = params.get("league_name")
    if league:
        queryset = queryset.filter(league_name__icontains=league)

    verified = params.get("verified_status")
    if verified:
        queryset = queryset.filter(verified_status=verified)

    return queryset.order_by("name")


def get_open_listing_for_player(player: Player):
    return (
        Listing.objects.filter(player=player, status=Listing.Status.OPEN)
        .order_by("-created_at")
        .first()
    )

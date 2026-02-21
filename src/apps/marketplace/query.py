from django.db.models import Count, F, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce

from apps.accounts.models import Club
from apps.players.models import Contract, Player
from apps.stats.models import PlayerStats
from .models import Listing, ListingInvite, Offer


def _get_multi_values(params, key: str) -> list[str]:
    if hasattr(params, "getlist"):
        values = params.getlist(key)
    else:
        values = []
    if not values:
        raw = params.get(key, "")
        if raw:
            values = [value.strip() for value in raw.split(",") if value.strip()]
    return values


def _listing_access_filter(actor_club: Club | None) -> Q:
    base = Q(listings__status=Listing.Status.OPEN)
    if actor_club:
        return base & (
            Q(listings__visibility=Listing.Visibility.PUBLIC)
            | Q(listings__listed_by_club=actor_club)
            | Q(listings__invites__club=actor_club)
        )
    return base & Q(listings__visibility=Listing.Visibility.PUBLIC)


def player_search_queryset(actor_club: Club | None, params):
    queryset = Player.objects.select_related("current_club", "form")
    if actor_club:
        queryset = queryset.exclude(visibility=Player.Visibility.PRIVATE)
    else:
        queryset = queryset.filter(visibility=Player.Visibility.PUBLIC)

    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) | Q(current_club__name__icontains=q)
        )

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

    max_form = params.get("max_form")
    if max_form:
        try:
            queryset = queryset.filter(form__form_score__lte=float(max_form))
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

    latest_stats = PlayerStats.objects.filter(player=OuterRef("pk")).order_by(
        "-season", "-updated_at", "-id"
    )
    queryset = queryset.annotate(
        latest_rating=Subquery(latest_stats.values("avg_rating")[:1]),
        latest_goals=Subquery(latest_stats.values("goals")[:1]),
        latest_assists=Subquery(latest_stats.values("assists")[:1]),
        latest_minutes=Subquery(latest_stats.values("minutes")[:1]),
    ).annotate(
        goals_assists=Coalesce(F("latest_goals"), Value(0))
        + Coalesce(F("latest_assists"), Value(0))
    )

    listing_base = Listing.objects.filter(player=OuterRef("pk"), status=Listing.Status.OPEN)
    if actor_club:
        listing_base = listing_base.filter(
            Q(visibility=Listing.Visibility.PUBLIC)
            | Q(listed_by_club=actor_club)
            | Q(invites__club=actor_club)
        )
    else:
        listing_base = listing_base.filter(visibility=Listing.Visibility.PUBLIC)
    queryset = queryset.annotate(
        listing_type=Subquery(listing_base.order_by("-created_at").values("listing_type")[:1]),
        market_value=Subquery(
            listing_base.order_by(
                F("asking_price").desc(nulls_last=True), "-created_at"
            ).values("asking_price")[:1]
        ),
    )

    availability = {value.lower() for value in _get_multi_values(params, "availability")}
    if availability:
        listing_access = _listing_access_filter(actor_club)
        availability_filter = Q()
        if "transfer" in availability:
            availability_filter |= listing_access & Q(
                listings__listing_type=Listing.ListingType.TRANSFER
            )
        if "loan" in availability:
            availability_filter |= listing_access & Q(
                listings__listing_type=Listing.ListingType.LOAN
            )
        if "free_agent" in availability:
            availability_filter |= Q(status=Player.Status.FREE_AGENT)
            availability_filter |= listing_access & Q(
                listings__listing_type=Listing.ListingType.FREE_AGENT
            )
        if "open_to_offers" in availability:
            availability_filter |= Q(open_to_offers=True)
        queryset = queryset.filter(availability_filter).distinct()

    sort = params.get("sort", "form_desc")
    if sort in {"performance", "form_desc"}:
        queryset = queryset.order_by(F("form__form_score").desc(nulls_last=True), "name")
    elif sort == "market_desc":
        queryset = queryset.order_by(F("market_value").desc(nulls_last=True), "name")
    elif sort == "age_asc":
        queryset = queryset.order_by("age", "name")
    elif sort == "age_desc":
        queryset = queryset.order_by(F("age").desc(nulls_last=True), "name")
    elif sort == "name":
        queryset = queryset.order_by("name")
    elif sort == "minutes_desc":
        queryset = queryset.order_by(F("latest_minutes").desc(nulls_last=True), "name")
    elif sort == "rating_desc":
        queryset = queryset.order_by(F("latest_rating").desc(nulls_last=True), "name")
    else:
        queryset = queryset.order_by(F("form__form_score").desc(nulls_last=True), "name")

    return queryset


def listing_search_queryset(actor_club: Club | None, params):
    listings = (
        Listing.objects.select_related("player", "player__current_club", "player__form", "listed_by_club")
        .filter(status=Listing.Status.OPEN)
        .annotate(
            offers_count=Count(
                "offers",
                filter=~Q(offers__status=Offer.Status.DRAFT),
            )
        )
    )
    active_contract = Contract.objects.filter(
        player=OuterRef("player_id"), is_active=True
    ).order_by("-end_date", "-id")
    listings = listings.annotate(
        contract_end_date=Subquery(active_contract.values("end_date")[:1])
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

    listing_type = params.get("type")
    if listing_type:
        listings = listings.filter(listing_type=listing_type)

    position = params.get("position")
    if position:
        listings = listings.filter(player__position=position)

    club_id = params.get("club")
    if club_id:
        listings = listings.filter(listed_by_club_id=club_id)

    min_price = params.get("min_price")
    if min_price:
        try:
            listings = listings.filter(asking_price__gte=float(min_price))
        except ValueError:
            pass

    max_price = params.get("max_price")
    if max_price:
        try:
            listings = listings.filter(asking_price__lte=float(max_price))
        except ValueError:
            pass

    sort = params.get("sort", "newest")
    if sort == "price_asc":
        listings = listings.order_by(F("asking_price").asc(nulls_last=True), "-created_at")
    elif sort == "price_desc":
        listings = listings.order_by(F("asking_price").desc(nulls_last=True), "-created_at")
    elif sort == "form_desc":
        listings = listings.order_by(F("player__form__form_score").desc(nulls_last=True), "-created_at")
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

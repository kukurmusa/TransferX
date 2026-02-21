from django.db.models import OuterRef, Subquery

from .models import Offer, OfferEvent


def offer_unread_counts(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not hasattr(user, "club"):
        return {"offer_unread_count": 0}

    club = user.club
    last_event = OfferEvent.objects.filter(offer_id=OuterRef("pk")).order_by("-created_at")
    unread = (
        Offer.objects.filter(
            to_club=club, status__in=[Offer.Status.SENT, Offer.Status.COUNTERED]
        )
        .annotate(last_actor_club_id=Subquery(last_event.values("actor_club_id")[:1]))
        .exclude(last_actor_club_id=club.id)
        .count()
    )
    return {"offer_unread_count": unread}

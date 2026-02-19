from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("listings/", views.listing_list, name="listing_list"),
    path("offers/", views.offer_received_list, name="offer_received"),
    path("offers/received/", views.offer_received_list, name="offer_received"),
    path("offers/sent/", views.offer_sent_list, name="offer_sent"),
    path("offers/new/", views.offer_new, name="offer_new"),
    path("offers/free-agents/", views.free_agent_offers, name="free_agent_offers"),
    path("offers/<int:pk>/", views.offer_detail, name="offer_detail"),
    path("offers/<int:pk>/counter/", views.offer_counter, name="offer_counter"),
    path("offers/<int:pk>/accept/", views.offer_accept, name="offer_accept"),
    path("offers/<int:pk>/reject/", views.offer_reject, name="offer_reject"),
    path("offers/<int:pk>/withdraw/", views.offer_withdraw, name="offer_withdraw"),
    path("offers/<int:pk>/message/", views.offer_message, name="offer_message"),
]

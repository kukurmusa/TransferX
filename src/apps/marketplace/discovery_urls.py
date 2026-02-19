from django.urls import path

from . import views

urlpatterns = [
    path("players/market/", views.player_market_list, name="player_market_list"),
    path("players/market/<int:pk>/", views.player_market_detail, name="player_market_detail"),
    path("clubs/", views.club_list, name="club_list"),
    path("clubs/<int:pk>/", views.club_detail, name="club_detail"),
    path("listings/", views.listing_hub_list, name="listing_hub_list"),
    path("listings/<int:pk>/", views.listing_detail, name="listing_detail"),
]

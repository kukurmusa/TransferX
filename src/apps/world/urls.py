from django.urls import path

from . import views

app_name = "world"

urlpatterns = [
    path("clubs/", views.club_list, name="club_list"),
    path("clubs/<int:pk>/", views.club_detail, name="club_detail"),
    path("players/", views.player_list, name="player_list"),
    path("players/<int:pk>/", views.player_detail, name="player_detail"),
]

from django.urls import path

from . import views

app_name = "players"

urlpatterns = [
    path("", views.player_list, name="list"),
    path("free-agents/", views.free_agents, name="free_agents"),
    path("new/", views.player_create, name="create"),
    path("<int:pk>/edit/", views.player_edit, name="edit"),
]

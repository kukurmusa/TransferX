from django.urls import path

from . import views

app_name = "scouting"

urlpatterns = [
    path("shortlists/", views.shortlist_list, name="shortlist_list"),
    path("shortlists/new/", views.shortlist_new, name="shortlist_new"),
    path("shortlists/<int:pk>/", views.shortlist_detail, name="shortlist_detail"),
    path("shortlists/<int:pk>/edit/", views.shortlist_edit, name="shortlist_edit"),
    path("shortlists/<int:pk>/delete/", views.shortlist_delete, name="shortlist_delete"),
    path("shortlists/<int:pk>/add/", views.shortlist_add, name="shortlist_add"),
    path("shortlists/<int:pk>/remove/", views.shortlist_remove, name="shortlist_remove"),
    path("shortlists/add/", views.shortlist_add_any, name="shortlist_add_any"),
    path(
        "shortlist-items/<int:pk>/update/",
        views.shortlist_item_update,
        name="shortlist_item_update",
    ),
    path("interest/set/", views.interest_set, name="interest_set"),
    path("interest/clear/", views.interest_clear, name="interest_clear"),
    path("targets/", views.targets_dashboard, name="targets_dashboard"),
]

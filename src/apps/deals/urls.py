from django.urls import path

from . import views

app_name = "deals"

urlpatterns = [
    path("", views.deal_list, name="list"),
    path("<int:pk>/", views.deal_detail, name="detail"),
    path("<int:pk>/advance/", views.deal_advance, name="advance"),
    path("<int:pk>/collapse/", views.deal_collapse, name="collapse"),
    path("<int:pk>/notes/", views.deal_add_note, name="add_note"),
    path("<int:pk>/staff/complete/", views.staff_complete_deal, name="staff_complete"),
    path("<int:pk>/staff/collapse/", views.staff_collapse_deal, name="staff_collapse"),
]

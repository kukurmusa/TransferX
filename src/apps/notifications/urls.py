from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("count/", views.notification_count, name="count"),
    path("mark-all-read/", views.mark_all_read, name="mark_all_read"),
    path("<int:pk>/go/", views.notification_go, name="go"),
]

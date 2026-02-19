from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", dashboard, name="home"),
    path("", include("apps.marketplace.discovery_urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("players/", include("apps.players.urls")),
    path("auctions/", include("apps.auctions.urls")),
    path("stats/", include("apps.stats.urls")),
    path("world/", include("apps.world.urls")),
    path("marketplace/", include("apps.marketplace.urls")),
    path("scouting/", include("apps.scouting.urls")),
]

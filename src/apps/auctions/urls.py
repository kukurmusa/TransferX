from django.urls import path

from . import views

app_name = "auctions"

urlpatterns = [
    path("", views.auction_list, name="list"),
    path("new/", views.auction_create, name="create"),
    path("<int:pk>/", views.auction_detail, name="detail"),
    path("<int:pk>/bid/", views.place_bid_view, name="place_bid"),
    path("<int:pk>/accept/<int:bid_id>/", views.accept_bid_view, name="accept_bid"),
    path("<int:pk>/bids.csv", views.bids_csv, name="bids_csv"),
    path("<int:pk>/bids/partial/", views.bid_ladder_partial, name="bids_partial"),
    path(
        "<int:pk>/seller/bids/partial/",
        views.seller_bid_table_partial,
        name="seller_bids_partial",
    ),
]

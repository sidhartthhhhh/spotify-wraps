from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/top-tracks/", views.list_page, {"kind": "top-tracks"}),
    path("dashboard/top-artists/", views.list_page, {"kind": "top-artists"}),
    path("dashboard/recently-played/", views.list_page, {"kind": "recently-played"}),
    path("dashboard/playlists/", views.list_page, {"kind": "playlists"}),
    path("dashboard/saved-tracks/", views.list_page, {"kind": "saved-tracks"}),
    path("dashboard/wrapped/", views.wrapped, name="wrapped"),
    path("dashboard/wrapped/monthly/", views.wrapped, {"period": "monthly"}),
    path("dashboard/wrapped/yearly/", views.wrapped, {"period": "yearly"}),
    path("dashboard/wrapped/share/", views.share_generate, name="share-generate"),
    path("dashboard/wrapped/share/disable/", views.share_disable, name="share-disable"),
    path("wrapped/share/<slug:slug>/", views.shared_wrapped, name="wrapped-share"),
]

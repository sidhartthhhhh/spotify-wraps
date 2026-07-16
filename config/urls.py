from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("spotify/", include("spotify_auth.urls")),
    path("api/", include("listening.api_urls")),
    path("", include("dashboard.urls")),
]

from django.urls import path
from .api_views import AnalyticsView, PlaylistsView, ProfileView, RecentView, SavedTracksView, TopArtistsView, TopTracksView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="api-profile"),
    path("top-tracks/", TopTracksView.as_view()),
    path("top-artists/", TopArtistsView.as_view()),
    path("recently-played/", RecentView.as_view()),
    path("playlists/", PlaylistsView.as_view()),
    path("saved-tracks/", SavedTracksView.as_view()),
    path("analytics/summary/", AnalyticsView.as_view()),
    path("analytics/monthly/", AnalyticsView.as_view(mode="monthly")),
    path("analytics/yearly/", AnalyticsView.as_view(mode="yearly")),
]

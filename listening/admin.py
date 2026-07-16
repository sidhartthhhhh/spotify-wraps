from django.contrib import admin
from .models import Album, Artist, ListeningHistory, Playlist, SavedTrack, Track, UserTopArtist, UserTopTrack

@admin.register(Artist, Album, Track)
class CatalogAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(ListeningHistory)
class HistoryAdmin(admin.ModelAdmin):
    list_display = ("spotify_account", "track", "played_at", "context_type")
    list_filter = ("context_type", "played_at")
    search_fields = ("track__name", "spotify_account__display_name")
    readonly_fields = ("created_at",)

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ("name", "spotify_account", "public", "collaborative", "total_tracks", "updated_at")
    list_filter = ("public", "collaborative")
    search_fields = ("name", "owner_spotify_id")

admin.site.register(UserTopTrack)
admin.site.register(UserTopArtist)
admin.site.register(SavedTrack)

from django.db import models

from spotify_auth.models import SpotifyAccount


class Artist(models.Model):
    spotify_artist_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    genres = models.JSONField(default=list, blank=True)
    popularity = models.PositiveSmallIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True)
    spotify_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    spotify_album_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    album_type = models.CharField(max_length=32, blank=True)
    release_date = models.CharField(max_length=32, blank=True)
    total_tracks = models.PositiveIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True)
    spotify_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.name


class Track(models.Model):
    spotify_track_id = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=255)
    duration_ms = models.PositiveIntegerField(default=0)
    explicit = models.BooleanField(default=False)
    popularity = models.PositiveSmallIntegerField(default=0)
    preview_url = models.URLField(max_length=500, blank=True, null=True)
    spotify_url = models.URLField(max_length=500, blank=True)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, related_name="tracks")
    artists = models.ManyToManyField(Artist, related_name="tracks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ListeningHistory(models.Model):
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="listening_history")
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="plays")
    played_at = models.DateTimeField()
    context_type = models.CharField(max_length=64, blank=True)
    context_uri = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["spotify_account", "track", "played_at"], name="unique_playback_event")]
        ordering = ["-played_at"]


class Playlist(models.Model):
    spotify_playlist_id = models.CharField(max_length=128)
    owner_spotify_id = models.CharField(max_length=128, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    public = models.BooleanField(null=True)
    collaborative = models.BooleanField(default=False)
    total_tracks = models.PositiveIntegerField(default=0)
    image_url = models.URLField(max_length=500, blank=True)
    spotify_url = models.URLField(max_length=500, blank=True)
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="playlists")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["spotify_account", "spotify_playlist_id"], name="unique_account_playlist")]


class SavedTrack(models.Model):
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="saved_tracks")
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="saved_by")
    added_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["spotify_account", "track"], name="unique_saved_track")]
        ordering = ["-added_at"]


class TimeRange(models.TextChoices):
    SHORT = "short_term", "Short term"
    MEDIUM = "medium_term", "Medium term"
    LONG = "long_term", "Long term"


class UserTopTrack(models.Model):
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="top_tracks")
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    time_range = models.CharField(max_length=16, choices=TimeRange.choices)
    rank = models.PositiveSmallIntegerField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["spotify_account", "time_range", "rank"], name="unique_top_track_rank")]


class UserTopArtist(models.Model):
    spotify_account = models.ForeignKey(SpotifyAccount, on_delete=models.CASCADE, related_name="top_artists")
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    time_range = models.CharField(max_length=16, choices=TimeRange.choices)
    rank = models.PositiveSmallIntegerField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["spotify_account", "time_range", "rank"], name="unique_top_artist_rank")]

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from analytics.services import summary
from spotify_auth.models import SpotifyAccount
from .models import Album, Artist, ListeningHistory, Track
from .services import upsert_artist, upsert_track
from .services import sync_recent


def spotify_track(track_id="track-1"):
    return {
        "id": track_id, "name": "A Track", "duration_ms": 180000, "explicit": False,
        "popularity": 50, "external_urls": {"spotify": "https://example.com/track"},
        "artists": [{"id": "artist-1", "name": "An Artist", "external_urls": {}}],
        "album": {"id": "album-1", "name": "An Album", "images": [], "external_urls": {}},
    }


class DataTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("one")
        self.account = SpotifyAccount.objects.create(
            user=self.user, spotify_user_id="one", access_token="x",
            token_expiry=timezone.now() + timedelta(hours=1),
        )

    def test_track_creation_and_duplicate_history_protection(self):
        track = upsert_track(spotify_track())
        self.assertEqual(track.artists.get().name, "An Artist")
        played_at = timezone.now()
        ListeningHistory.objects.create(spotify_account=self.account, track=track, played_at=played_at)
        with self.assertRaises(IntegrityError), transaction.atomic():
            ListeningHistory.objects.create(spotify_account=self.account, track=track, played_at=played_at)

    def test_partial_artist_payload_preserves_photo(self):
        artist = upsert_artist({"id": "artist", "name": "Artist", "images": [{"url": "https://example.com/photo.jpg"}]})
        upsert_artist({"id": "artist", "name": "Artist"})
        artist.refresh_from_db()
        self.assertEqual(artist.image_url, "https://example.com/photo.jpg")

    def test_analytics_summary(self):
        track = upsert_track(spotify_track())
        ListeningHistory.objects.create(spotify_account=self.account, track=track, played_at=timezone.now())
        data = summary(self.account)
        self.assertEqual(data["estimated_minutes"], 3)
        self.assertEqual(data["most_played_track"]["track__name"], "A Track")

    def test_api_requires_auth_and_isolates_users(self):
        other = get_user_model().objects.create_user("other")
        other_account = SpotifyAccount.objects.create(
            user=other, spotify_user_id="other", access_token="x",
            token_expiry=timezone.now() + timedelta(hours=1),
        )
        ListeningHistory.objects.create(spotify_account=other_account, track=upsert_track(spotify_track()), played_at=timezone.now())
        api = APIClient()
        self.assertIn(api.get("/api/recently-played/").status_code, (401, 403))
        api.force_authenticate(self.user)
        self.assertEqual(api.get("/api/recently-played/").json(), [])

    def test_dashboard_without_spotify_account_redirects_home(self):
        user = get_user_model().objects.create_user("unconnected")
        self.client.force_login(user)
        self.assertRedirects(self.client.get("/dashboard/"), "/")

    def test_recent_sync_skips_unavailable_tracks(self):
        from unittest.mock import patch

        with patch("listening.services.SpotifyAPIService.get_recently_played", return_value={"items": [{"track": None}], "cursors": None, "next": None}):
            self.assertEqual(sync_recent(self.account), 0)

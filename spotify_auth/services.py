import logging
import time
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class SpotifyAPIError(Exception):
    pass


class SpotifyAPIService:
    API_URL = "https://api.spotify.com/v1"
    TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(self, account=None):
        self.account = account

    @staticmethod
    def exchange_code(code):
        response = requests.post(
            SpotifyAPIService.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
            },
            auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            timeout=15,
        )
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpotifyAPIError("Spotify authorization failed.") from exc
        return response.json()

    def refresh_access_token(self):
        if not self.account or not self.account.refresh_token:
            raise SpotifyAPIError("Spotify access expired; reconnect the account.")
        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": self.account.refresh_token},
            auth=(settings.SPOTIFY_CLIENT_ID, settings.SPOTIFY_CLIENT_SECRET),
            timeout=15,
        )
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SpotifyAPIError("Could not refresh Spotify access.") from exc
        data = response.json()
        self.account.access_token = data["access_token"]
        self.account.refresh_token = data.get("refresh_token") or self.account.refresh_token
        self.account.token_expiry = timezone.now() + timedelta(seconds=data.get("expires_in", 3600))
        self.account.save(update_fields=["access_token", "refresh_token", "token_expiry", "updated_at"])
        return self.account.access_token

    def make_authenticated_request(self, path, params=None, retry=True):
        if self.account.token_expiry <= timezone.now() + timedelta(seconds=30):
            self.refresh_access_token()
        response = requests.get(
            path if path.startswith("http") else f"{self.API_URL}{path}",
            params=params,
            headers={"Authorization": f"Bearer {self.account.access_token}"},
            timeout=15,
        )
        if response.status_code == 401 and retry:
            self.refresh_access_token()
            return self.make_authenticated_request(path, params, retry=False)
        if response.status_code == 429 and retry:
            time.sleep(min(int(response.headers.get("Retry-After", "1")), 10))
            return self.make_authenticated_request(path, params, retry=False)
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Spotify API request failed: path=%s status=%s", path, response.status_code)
            raise SpotifyAPIError("Spotify API request failed.") from exc
        return response.json()

    def get_current_user_profile(self):
        return self.make_authenticated_request("/me")

    def get_top_tracks(self, time_range="medium_term", limit=50):
        return self.make_authenticated_request("/me/top/tracks", {"time_range": time_range, "limit": limit})

    def get_top_artists(self, time_range="medium_term", limit=50):
        return self.make_authenticated_request("/me/top/artists", {"time_range": time_range, "limit": limit})

    def get_recently_played(self, limit=50, after=None, before=None):
        params = {"limit": limit}
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        return self.make_authenticated_request("/me/player/recently-played", params)

    def get_saved_tracks(self, limit=50, offset=0):
        return self.make_authenticated_request("/me/tracks", {"limit": limit, "offset": offset})

    def get_user_playlists(self, limit=50, offset=0):
        return self.make_authenticated_request("/me/playlists", {"limit": limit, "offset": offset})

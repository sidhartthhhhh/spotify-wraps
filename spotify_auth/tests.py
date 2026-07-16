from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import SpotifyAccount
from .services import SpotifyAPIService


@override_settings(SPOTIFY_CLIENT_ID="client", SPOTIFY_CLIENT_SECRET="secret")
class OAuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("me", password="x")
        self.client.force_login(self.user)

    def test_login_redirect_contains_state(self):
        response = self.client.get(reverse("spotify-login"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("state=", response.url)
        self.assertTrue(self.client.session["spotify_oauth_state"])

    @override_settings(SPOTIFY_CLIENT_ID="", SPOTIFY_CLIENT_SECRET="")
    def test_login_without_credentials_returns_home(self):
        self.assertRedirects(self.client.get(reverse("spotify-login")), reverse("home"))

    def test_invalid_state_is_rejected(self):
        session = self.client.session
        session["spotify_oauth_state"] = "expected"
        session.save()
        self.assertEqual(self.client.get(reverse("spotify-callback"), {"state": "wrong", "code": "x"}).status_code, 400)

    @patch("spotify_auth.views.requests.get")
    @patch("spotify_auth.views.SpotifyAPIService.exchange_code")
    def test_callback_connects_account(self, exchange, get):
        exchange.return_value = {"access_token": "access", "refresh_token": "refresh", "expires_in": 3600}
        get.return_value = Mock(status_code=200, json=lambda: {"id": "sid", "display_name": "Me", "email": "private@example.com", "country": "IN", "product": "premium"})
        get.return_value.raise_for_status.return_value = None
        session = self.client.session
        session["spotify_oauth_state"] = "valid"
        session.save()
        response = self.client.get(reverse("spotify-callback"), {"state": "valid", "code": "code"})
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(self.user.spotify_account.spotify_user_id, "sid")


class SpotifyServiceTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("service")
        self.account = SpotifyAccount.objects.create(
            user=user, spotify_user_id="service", access_token="old", refresh_token="refresh",
            token_expiry=timezone.now() + timedelta(hours=1),
        )

    @patch("spotify_auth.services.requests.post")
    def test_refresh_updates_expired_token(self, post):
        post.return_value = Mock(json=lambda: {"access_token": "new", "expires_in": 3600})
        post.return_value.raise_for_status.return_value = None
        self.account.token_expiry = timezone.now() - timedelta(seconds=1)
        self.account.save()
        SpotifyAPIService(self.account).get_current_user_profile = Mock()
        SpotifyAPIService(self.account).refresh_access_token()
        self.account.refresh_from_db()
        self.assertEqual(self.account.access_token, "new")

    @patch("spotify_auth.services.time.sleep")
    @patch.object(SpotifyAPIService, "refresh_access_token")
    @patch("spotify_auth.services.requests.get")
    def test_401_refreshes_once_and_429_waits_once(self, get, refresh, sleep):
        ok = Mock(status_code=200, json=lambda: {"ok": True})
        ok.raise_for_status.return_value = None
        get.side_effect = [Mock(status_code=401), ok]
        self.assertEqual(SpotifyAPIService(self.account).make_authenticated_request("/me"), {"ok": True})
        refresh.assert_called_once()
        get.side_effect = [Mock(status_code=429, headers={"Retry-After": "2"}), ok]
        self.assertEqual(SpotifyAPIService(self.account).make_authenticated_request("/me"), {"ok": True})
        sleep.assert_called_once_with(2)

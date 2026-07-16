import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils import timezone

from .models import SpotifyAccount
from .services import SpotifyAPIError, SpotifyAPIService

SCOPES = " ".join([
    "user-read-private", "user-read-email", "user-top-read",
    "user-read-recently-played", "user-library-read",
    "playlist-read-private", "playlist-read-collaborative",
])


@login_required
def spotify_login(request):
    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        messages.error(request, "I need to add my Spotify client ID and secret to .env first.")
        return redirect("home")
    state = secrets.token_urlsafe(32)
    request.session["spotify_oauth_state"] = state
    query = urlencode({
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    })
    return redirect(f"https://accounts.spotify.com/authorize?{query}")


@login_required
def spotify_callback(request):
    expected = request.session.pop("spotify_oauth_state", None)
    if not expected or not secrets.compare_digest(request.GET.get("state", ""), expected):
        return HttpResponseBadRequest("Invalid OAuth state.")
    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("Spotify authorization was not completed.")
    try:
        token = SpotifyAPIService.exchange_code(code)
        profile_response = requests.get(
            f"{SpotifyAPIService.API_URL}/me",
            headers={"Authorization": f"Bearer {token['access_token']}"},
            timeout=15,
        )
        profile_response.raise_for_status()
        profile = profile_response.json()
    except (SpotifyAPIError, requests.RequestException, KeyError):
        messages.error(request, "Could not connect Spotify. Please try again.")
        return redirect("home")
    SpotifyAccount.objects.update_or_create(
        user=request.user,
        defaults={
            "spotify_user_id": profile["id"],
            "display_name": profile.get("display_name") or "",
            "email": profile.get("email") or "",
            "country": profile.get("country") or "",
            "product_type": profile.get("product") or "",
            "access_token": token["access_token"],
            "refresh_token": token.get("refresh_token", ""),
            "token_expiry": timezone.now() + timedelta(seconds=token.get("expires_in", 3600)),
        },
    )
    return redirect("dashboard")


@login_required
def spotify_logout(request):
    SpotifyAccount.objects.filter(user=request.user).delete()
    return redirect("home")


@login_required
def spotify_profile(request):
    return redirect("api-profile")

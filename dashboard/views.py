from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from analytics.models import WrappedShare
from analytics.services import monthly_summary, summary, yearly_summary
from listening.models import ListeningHistory, Playlist, SavedTrack, UserTopArtist, UserTopTrack


def home(request):
    return render(request, "home.html", {
        "spotify_configured": bool(settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET),
    })


def spotify_connected(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not hasattr(request.user, "spotify_account"):
            messages.info(request, "I need to connect Spotify before opening my dashboard.")
            return redirect("home")
        return view(request, *args, **kwargs)

    return wrapped


def account_for(request):
    return request.user.spotify_account


@login_required
@spotify_connected
def dashboard(request):
    account = account_for(request)
    return render(request, "dashboard.html", {
        "account": account,
        "analytics": summary(account),
        "top_tracks": UserTopTrack.objects.filter(spotify_account=account, time_range="medium_term").select_related("track", "track__album").prefetch_related("track__artists")[:10],
        "top_artists": UserTopArtist.objects.filter(spotify_account=account, time_range="medium_term").select_related("artist")[:10],
        "recent": ListeningHistory.objects.filter(spotify_account=account).select_related("track")[:10],
    })


@login_required
@spotify_connected
def list_page(request, kind):
    account = account_for(request)
    choices = {
        "top-tracks": ("My top tracks", UserTopTrack.objects.filter(spotify_account=account).select_related("track", "track__album").prefetch_related("track__artists").order_by("time_range", "rank")),
        "top-artists": ("My top artists", UserTopArtist.objects.filter(spotify_account=account).select_related("artist").order_by("time_range", "rank")),
        "recently-played": ("My recent plays", ListeningHistory.objects.filter(spotify_account=account).select_related("track", "track__album")),
        "playlists": ("My playlists", Playlist.objects.filter(spotify_account=account)),
        "saved-tracks": ("My saved tracks", SavedTrack.objects.filter(spotify_account=account).select_related("track", "track__album")),
    }
    title, objects = choices[kind]
    return render(request, "list.html", {"title": title, "objects": objects, "kind": kind})


@login_required
@spotify_connected
def wrapped(request, period="yearly"):
    account = account_for(request)
    data = monthly_summary(account) if period == "monthly" else yearly_summary(account)
    return render(request, "wrapped.html", {"analytics": data, "period": period})


@login_required
@spotify_connected
@require_POST
def share_generate(request):
    account = account_for(request)
    WrappedShare.objects.filter(spotify_account=account, is_active=True).update(is_active=False)
    share = WrappedShare.objects.create(
        spotify_account=account, year=timezone.localdate().year, summary=yearly_summary(account)
    )
    return redirect("wrapped-share", slug=share.slug)


@login_required
@spotify_connected
@require_POST
def share_disable(request):
    WrappedShare.objects.filter(spotify_account=account_for(request)).update(is_active=False)
    return redirect("wrapped")


def shared_wrapped(request, slug):
    share = get_object_or_404(WrappedShare, slug=slug, is_active=True)
    return render(request, "wrapped.html", {"analytics": share.summary, "period": "shared", "public": True})

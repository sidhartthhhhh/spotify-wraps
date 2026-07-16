from django.utils.dateparse import parse_date
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from analytics.services import monthly_summary, summary, yearly_summary
from .models import ListeningHistory, Playlist, SavedTrack, UserTopArtist, UserTopTrack
from .serializers import HistorySerializer, PlaylistSerializer, SavedTrackSerializer, SpotifyAccountSerializer, TopArtistSerializer, TopTrackSerializer


class AccountMixin:
    def account(self):
        try:
            return self.request.user.spotify_account
        except AttributeError as exc:
            raise NotFound("I need to connect Spotify first.") from exc


class ProfileView(AccountMixin, APIView):
    def get(self, request):
        return Response(SpotifyAccountSerializer(self.account()).data)


class TopTracksView(AccountMixin, APIView):
    def get(self, request):
        qs = UserTopTrack.objects.filter(spotify_account=self.account()).select_related("track", "track__album").prefetch_related("track__artists")
        if request.GET.get("time_range"):
            qs = qs.filter(time_range=request.GET["time_range"])
        return Response(TopTrackSerializer(qs.order_by("time_range", "rank"), many=True).data)


class TopArtistsView(AccountMixin, APIView):
    def get(self, request):
        qs = UserTopArtist.objects.filter(spotify_account=self.account()).select_related("artist")
        if request.GET.get("time_range"):
            qs = qs.filter(time_range=request.GET["time_range"])
        return Response(TopArtistSerializer(qs.order_by("time_range", "rank"), many=True).data)


class RecentView(AccountMixin, APIView):
    def get(self, request):
        qs = ListeningHistory.objects.filter(spotify_account=self.account()).select_related("track", "track__album").prefetch_related("track__artists")
        filters = {
            "played_at__date__gte": parse_date(request.GET.get("start", "")),
            "played_at__date__lte": parse_date(request.GET.get("end", "")),
            "track__artists__spotify_artist_id": request.GET.get("artist"),
            "track__spotify_track_id": request.GET.get("track"),
            "context_uri": request.GET.get("playlist"),
        }
        return Response(HistorySerializer(qs.filter(**{k: v for k, v in filters.items() if v})[:200], many=True).data)


class PlaylistsView(AccountMixin, APIView):
    def get(self, request):
        return Response(PlaylistSerializer(Playlist.objects.filter(spotify_account=self.account()), many=True).data)


class SavedTracksView(AccountMixin, APIView):
    def get(self, request):
        qs = SavedTrack.objects.filter(spotify_account=self.account()).select_related("track", "track__album").prefetch_related("track__artists")
        return Response(SavedTrackSerializer(qs, many=True).data)


class AnalyticsView(AccountMixin, APIView):
    mode = "summary"

    def get(self, request):
        account = self.account()
        if self.mode == "monthly":
            data = monthly_summary(account, int(request.GET["year"]) if request.GET.get("year") else None, int(request.GET["month"]) if request.GET.get("month") else None)
        elif self.mode == "yearly":
            data = yearly_summary(account, int(request.GET["year"]) if request.GET.get("year") else None)
        else:
            data = summary(account, parse_date(request.GET.get("start", "")), parse_date(request.GET.get("end", "")))
        return Response(data)

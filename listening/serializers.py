from rest_framework import serializers

from spotify_auth.models import SpotifyAccount
from .models import Artist, ListeningHistory, Playlist, SavedTrack, Track, UserTopArtist, UserTopTrack


class SpotifyAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotifyAccount
        fields = ["spotify_user_id", "display_name", "country", "product_type", "created_at", "updated_at"]


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ["spotify_artist_id", "name", "genres", "popularity", "image_url", "spotify_url"]


class TrackSerializer(serializers.ModelSerializer):
    artists = ArtistSerializer(many=True)
    album = serializers.StringRelatedField()

    class Meta:
        model = Track
        fields = ["spotify_track_id", "name", "duration_ms", "explicit", "popularity", "preview_url", "spotify_url", "album", "artists"]


class TopTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer()

    class Meta:
        model = UserTopTrack
        fields = ["track", "time_range", "rank", "fetched_at"]


class TopArtistSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer()

    class Meta:
        model = UserTopArtist
        fields = ["artist", "time_range", "rank", "fetched_at"]


class HistorySerializer(serializers.ModelSerializer):
    track = TrackSerializer()

    class Meta:
        model = ListeningHistory
        fields = ["track", "played_at", "context_type", "context_uri"]


class PlaylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        exclude = ["id", "spotify_account"]


class SavedTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer()

    class Meta:
        model = SavedTrack
        fields = ["track", "added_at"]

from django.db import transaction
from django.utils.dateparse import parse_datetime

from .models import Album, Artist, ListeningHistory, Playlist, SavedTrack, TimeRange, Track, UserTopArtist, UserTopTrack
from spotify_auth.services import SpotifyAPIService


def image_url(data):
    return (data.get("images") or [{}])[0].get("url", "")


def upsert_artist(data):
    artist, created = Artist.objects.get_or_create(
        spotify_artist_id=data["id"],
        defaults={
            "name": data["name"],
            "genres": data.get("genres", []),
            "popularity": data.get("popularity", 0),
            "image_url": image_url(data),
            "spotify_url": data.get("external_urls", {}).get("spotify", ""),
        },
    )
    if not created:
        artist.name = data["name"]
        artist.spotify_url = data.get("external_urls", {}).get("spotify", artist.spotify_url)
        if "genres" in data:
            artist.genres = data["genres"]
        if "popularity" in data:
            artist.popularity = data["popularity"]
        if "images" in data:
            artist.image_url = image_url(data)
        artist.save()
    return artist


def upsert_track(data):
    album_data = data.get("album") or {}
    album, _ = Album.objects.update_or_create(
        spotify_album_id=album_data.get("id") or f"unknown-{data['id']}",
        defaults={
            "name": album_data.get("name", "Unknown album"),
            "album_type": album_data.get("album_type", ""),
            "release_date": album_data.get("release_date", ""),
            "total_tracks": album_data.get("total_tracks", 0),
            "image_url": image_url(album_data),
            "spotify_url": album_data.get("external_urls", {}).get("spotify", ""),
        },
    )
    track, _ = Track.objects.update_or_create(
        spotify_track_id=data["id"],
        defaults={
            "name": data["name"],
            "duration_ms": data.get("duration_ms", 0),
            "explicit": data.get("explicit", False),
            "popularity": data.get("popularity", 0),
            "preview_url": data.get("preview_url"),
            "spotify_url": data.get("external_urls", {}).get("spotify", ""),
            "album": album,
        },
    )
    track.artists.set([upsert_artist(artist) for artist in data.get("artists", [])])
    return track


@transaction.atomic
def sync_profile(account):
    data = SpotifyAPIService(account).get_current_user_profile()
    for field, key in [
        ("spotify_user_id", "id"), ("display_name", "display_name"), ("email", "email"),
        ("country", "country"), ("product_type", "product"),
    ]:
        setattr(account, field, data.get(key) or "")
    account.save()
    return 1


@transaction.atomic
def sync_recent(account):
    service, before, pages = SpotifyAPIService(account), None, 0
    created = 0
    while pages < 10:
        data = service.get_recently_played(before=before)
        for item in data.get("items", []):
            if not item.get("track"):
                continue
            track = upsert_track(item["track"])
            context = item.get("context") or {}
            _, was_created = ListeningHistory.objects.get_or_create(
                spotify_account=account,
                track=track,
                played_at=parse_datetime(item["played_at"]),
                defaults={"context_type": context.get("type", ""), "context_uri": context.get("uri", "")},
            )
            created += was_created
        before = (data.get("cursors") or {}).get("before")
        pages += 1
        if not data.get("next") or not before:
            break
    return created


@transaction.atomic
def sync_top_tracks(account):
    count = 0
    service = SpotifyAPIService(account)
    for time_range in TimeRange.values:
        for rank, data in enumerate(service.get_top_tracks(time_range).get("items", []), 1):
            UserTopTrack.objects.update_or_create(
                spotify_account=account, time_range=time_range, rank=rank,
                defaults={"track": upsert_track(data)},
            )
            count += 1
    return count


@transaction.atomic
def sync_top_artists(account):
    count = 0
    service = SpotifyAPIService(account)
    for time_range in TimeRange.values:
        for rank, data in enumerate(service.get_top_artists(time_range).get("items", []), 1):
            UserTopArtist.objects.update_or_create(
                spotify_account=account, time_range=time_range, rank=rank,
                defaults={"artist": upsert_artist(data)},
            )
            count += 1
    return count


@transaction.atomic
def sync_playlists(account):
    service, offset, count = SpotifyAPIService(account), 0, 0
    while True:
        data = service.get_user_playlists(offset=offset)
        for item in data.get("items", []):
            Playlist.objects.update_or_create(
                spotify_account=account,
                spotify_playlist_id=item["id"],
                defaults={
                    "owner_spotify_id": item.get("owner", {}).get("id", ""),
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "public": item.get("public"),
                    "collaborative": item.get("collaborative", False),
                    "total_tracks": item.get("tracks", {}).get("total", 0),
                    "image_url": image_url(item),
                    "spotify_url": item.get("external_urls", {}).get("spotify", ""),
                },
            )
            count += 1
        if not data.get("next"):
            break
        offset += len(data.get("items", []))
    return count


@transaction.atomic
def sync_saved_tracks(account):
    service, offset, count = SpotifyAPIService(account), 0, 0
    while True:
        data = service.get_saved_tracks(offset=offset)
        for item in data.get("items", []):
            SavedTrack.objects.update_or_create(
                spotify_account=account,
                track=upsert_track(item["track"]),
                defaults={"added_at": parse_datetime(item["added_at"])},
            )
            count += 1
        if not data.get("next"):
            break
        offset += len(data.get("items", []))
    return count


SYNC_FUNCTIONS = {
    "profile": sync_profile,
    "recently played": sync_recent,
    "top tracks": sync_top_tracks,
    "top artists": sync_top_artists,
    "playlists": sync_playlists,
    "saved tracks": sync_saved_tracks,
}

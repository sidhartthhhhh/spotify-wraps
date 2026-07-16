from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Synchronize all Spotify data"

    def add_arguments(self, parser):
        parser.add_argument("--account-id", type=int)

    def handle(self, *args, **options):
        args = ["--account-id", str(options["account_id"])] if options["account_id"] else []
        for command in ["sync_spotify_profile", "sync_recently_played", "sync_top_tracks", "sync_top_artists", "sync_playlists", "sync_saved_tracks"]:
            call_command(command, *args)

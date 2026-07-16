from listening.management.base import SpotifySyncCommand

class Command(SpotifySyncCommand):
    help = "Synchronize playlists"
    sync_name = "playlists"

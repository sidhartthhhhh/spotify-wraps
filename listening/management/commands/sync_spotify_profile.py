from listening.management.base import SpotifySyncCommand

class Command(SpotifySyncCommand):
    help = "Synchronize Spotify profiles"
    sync_name = "profile"

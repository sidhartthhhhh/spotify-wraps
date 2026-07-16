from listening.management.base import SpotifySyncCommand

class Command(SpotifySyncCommand):
    help = "Synchronize recently played tracks"
    sync_name = "recently played"

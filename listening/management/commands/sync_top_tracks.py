from listening.management.base import SpotifySyncCommand

class Command(SpotifySyncCommand):
    help = "Synchronize top tracks"
    sync_name = "top tracks"

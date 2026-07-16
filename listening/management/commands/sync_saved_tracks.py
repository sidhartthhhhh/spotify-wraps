from listening.management.base import SpotifySyncCommand

class Command(SpotifySyncCommand):
    help = "Synchronize saved tracks"
    sync_name = "saved tracks"

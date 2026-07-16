from django.core.management.base import BaseCommand

from spotify_auth.models import SpotifyAccount


class SpotifySyncCommand(BaseCommand):
    sync_name = ""

    def add_arguments(self, parser):
        parser.add_argument("--account-id", type=int)

    def handle(self, *args, **options):
        from listening.services import SYNC_FUNCTIONS

        accounts = SpotifyAccount.objects.all()
        if options["account_id"]:
            accounts = accounts.filter(pk=options["account_id"])
        total = 0
        for account in accounts:
            try:
                count = SYNC_FUNCTIONS[self.sync_name](account)
                total += count
                self.stdout.write(self.style.SUCCESS(f"{account}: {count} {self.sync_name} records synced"))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"{account}: {exc}"))
        self.stdout.write(self.style.SUCCESS(f"Finished: {total} records synced"))

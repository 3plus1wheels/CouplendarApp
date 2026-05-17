from django.core.management.base import BaseCommand

from apps.discovery.tasks import sync_place_enrichment


class Command(BaseCommand):
    help = "Sync Google Maps place enrichment for trending places."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--photos-only", action="store_true")
        parser.add_argument("--force-photos", action="store_true")
        parser.add_argument("--spot-id", type=int, default=None)

    def handle(self, *args, **options):
        synced = sync_place_enrichment(
            limit=options["limit"],
            photos_only=options["photos_only"],
            force_photos=options["force_photos"],
            spot_id=options["spot_id"],
        )
        self.stdout.write(self.style.SUCCESS(f"Synced enrichment for {synced} locations"))

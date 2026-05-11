from django.core.management.base import BaseCommand

from apps.discovery.tasks import sync_place_enrichment


class Command(BaseCommand):
    help = "Sync Google review enrichment and related video metadata for trending places."

    def handle(self, *args, **options):
        synced = sync_place_enrichment()
        self.stdout.write(self.style.SUCCESS(f"Synced enrichment for {synced} locations"))

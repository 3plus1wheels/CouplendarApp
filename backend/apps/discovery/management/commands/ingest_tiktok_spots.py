import os

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.tasks import ingest_tiktok_spots_task


class Command(BaseCommand):
    help = "Ingest TikTok-driven spot list and verify via Google Places."

    def handle(self, *args, **options):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise CommandError("GOOGLE_PLACES_API_KEY is required to ingest TikTok spots.")

        task = ingest_tiktok_spots_task.delay()
        self.stdout.write(self.style.SUCCESS(f"Queued TikTok ingestion task {task.id}"))

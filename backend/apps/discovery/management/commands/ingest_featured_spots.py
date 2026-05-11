import os

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.tasks import ingest_featured_spots


class Command(BaseCommand):
    help = "Ingest featured spot list and verify via Google Places."

    def handle(self, *args, **options):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise CommandError("GOOGLE_PLACES_API_KEY is required to ingest featured spots.")

        ingested = ingest_featured_spots()
        self.stdout.write(self.style.SUCCESS(f"Ingested {ingested} featured spots"))

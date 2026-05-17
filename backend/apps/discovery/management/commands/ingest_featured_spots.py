import os

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.tasks import ingest_featured_spots


class Command(BaseCommand):
    help = "Ingest featured spot list and verify via Google Places."

    def add_arguments(self, parser):
        parser.add_argument("--names", nargs="+", default=None)
        parser.add_argument("--file", type=str, default=None, help="Text file with one spot name per line.")

    def handle(self, *args, **options):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise CommandError("GOOGLE_PLACES_API_KEY is required to ingest featured spots.")

        spot_names = options["names"]
        if options["file"]:
            with open(options["file"], encoding="utf-8") as handle:
                spot_names = [line.strip() for line in handle if line.strip()]

        ingested = ingest_featured_spots(spot_names=spot_names)
        self.stdout.write(self.style.SUCCESS(f"Ingested {ingested} featured spots"))

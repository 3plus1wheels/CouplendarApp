import os

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.tasks import seed_trending_locations_task


class Command(BaseCommand):
    help = "Seed trending locations from Google Places Text Search."

    def add_arguments(self, parser):
        parser.add_argument("--max-per-type", type=int, default=3)
        parser.add_argument("--city", type=str, default="Calgary, AB")

    def handle(self, *args, **options):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise CommandError("GOOGLE_PLACES_API_KEY is required to seed places.")

        max_per_type = options["max_per_type"]
        city = options["city"]
        task = seed_trending_locations_task.delay(max_per_type=max_per_type, city=city)
        self.stdout.write(self.style.SUCCESS(f"Queued seed task {task.id}"))

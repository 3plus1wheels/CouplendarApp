from django.core.management.base import BaseCommand

from apps.discovery.tasks import sync_place_enrichment_task


class Command(BaseCommand):
    help = "Sync Google review enrichment and TikTok fallback metadata for trending places."

    def handle(self, *args, **options):
        task = sync_place_enrichment_task.delay()
        self.stdout.write(self.style.SUCCESS(f"Queued enrichment task {task.id}"))

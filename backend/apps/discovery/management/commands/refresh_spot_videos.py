from pathlib import Path
import logging

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.models import TrendLocation
from apps.discovery.tasks import _refresh_lock_path, _release_refresh_lock, refresh_spot_videos

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Refresh YouTube videos for a single discovery spot in a separate process."

    def add_arguments(self, parser):
        parser.add_argument("--spot-id", type=int, required=True)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        spot_id = options["spot_id"]
        force = options["force"]
        lock_path = _refresh_lock_path(spot_id)

        try:
            try:
                location = TrendLocation.objects.get(pk=spot_id)
            except TrendLocation.DoesNotExist as exc:
                raise CommandError(f"Spot {spot_id} not found") from exc

            try:
                result = refresh_spot_videos(location=location, force=force)
            except Exception as exc:
                logger.exception("Discovery refresh failed for spot %s", spot_id)
                location.tiktok_sync_error = f"scrape_failed: {exc}"
                location.save(update_fields=["tiktok_sync_error"])
                raise
            detail = f" error={result.error}" if result.error else ""
            self.stdout.write(self.style.SUCCESS(f"Refresh status for spot {spot_id}: {result.status}{detail}"))
        finally:
            _release_refresh_lock(lock_path)

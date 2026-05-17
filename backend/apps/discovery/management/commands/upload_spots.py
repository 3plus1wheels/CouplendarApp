from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.discovery.tasks import _upsert_location


class Command(BaseCommand):
    help = "Upload normalized spots from JSON and upsert by Google place id or normalized name/location key."

    def add_arguments(self, parser):
        parser.add_argument("path", help="JSON file containing a list of spots, or an object with a spots array.")
        parser.add_argument("--place-type", default="Featured")

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"Spot upload file not found: {path}")

        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON: {exc}") from exc

        spots = payload.get("spots") if isinstance(payload, dict) else payload
        if not isinstance(spots, list):
            raise CommandError("JSON must be a list of spots, or an object with a spots array.")

        upserted = 0
        for item in spots:
            if not isinstance(item, dict):
                continue
            location = _upsert_location(item, options["place_type"], client=None)
            if location is not None:
                upserted += 1

        self.stdout.write(self.style.SUCCESS(f"Upserted {upserted} spots"))

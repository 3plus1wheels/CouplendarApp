from django.core.management.base import BaseCommand, CommandError

from apps.discovery.models import TrendLocation
from apps.discovery.search import GeminiEmbeddingClient, GeminiEmbeddingError, rebuild_spot_search_embedding


class Command(BaseCommand):
    help = "Rebuild semantic search documents and embeddings for discovery spots."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--spot-id", type=int, default=None)

    def handle(self, *args, **options):
        queryset = TrendLocation.objects.order_by("id")
        if options["spot_id"] is not None:
            queryset = queryset.filter(id=options["spot_id"])
        elif not options["force"]:
            queryset = queryset.filter(search_embedding__isnull=True)
        if options["limit"] is not None:
            queryset = queryset[: max(0, options["limit"])]

        client = GeminiEmbeddingClient()
        updated = 0
        try:
            for location in queryset:
                updated += int(rebuild_spot_search_embedding(location, embedding_client=client, force=options["force"]))
        except GeminiEmbeddingError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Rebuilt semantic search embeddings for {updated} spots"))

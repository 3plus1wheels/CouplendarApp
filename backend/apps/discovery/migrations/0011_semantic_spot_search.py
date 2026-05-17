from django.conf import settings
from django.db import migrations, models
from pgvector.django import VectorExtension, VectorField


def build_initial_search_documents(apps, schema_editor):
    TrendLocation = apps.get_model("discovery", "TrendLocation")
    for location in TrendLocation.objects.all().iterator():
        parts = [
            location.name,
            location.category,
            location.primary_type,
            location.primary_type_display_name,
            " ".join(location.place_types or []),
            " ".join(location.suggestion_badges or []),
            location.suggestion_reason,
            location.editorial_summary,
            location.generative_summary,
            location.review_summary,
            " ".join(location.opening_hours or []),
            " ".join(str(key) for key, enabled in (location.amenities or {}).items() if enabled),
        ]
        reviews = location.top_reviews or []
        for review in reviews:
            if isinstance(review, dict):
                parts.append(str(review.get("text") or ""))
        location.search_document = "\n".join(part.strip() for part in parts if str(part).strip())
        location.search_embedding_model = settings.GEMINI_EMBEDDING_MODEL
        location.save(update_fields=["search_document", "search_embedding_model"])


class Migration(migrations.Migration):
    dependencies = [
        ("discovery", "0010_spot_media_and_dedupe_key"),
    ]

    operations = [
        VectorExtension(),
        migrations.AddField(
            model_name="trendlocation",
            name="search_document",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="search_embedding",
            field=VectorField(blank=True, dimensions=768, null=True),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="search_embedding_model",
            field=models.CharField(blank=True, default="gemini-embedding-2", max_length=80),
        ),
        migrations.AddField(
            model_name="trendlocation",
            name="search_embedding_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(build_initial_search_documents, migrations.RunPython.noop),
    ]

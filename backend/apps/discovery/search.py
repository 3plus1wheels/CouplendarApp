from __future__ import annotations

from typing import Any

import requests
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.utils import timezone
from pgvector.django import CosineDistance

from .models import TrendLocation

SEARCH_RESULT_LIMIT = 20
SEMANTIC_CANDIDATE_LIMIT = 50
KEYWORD_CANDIDATE_LIMIT = 80


class GeminiEmbeddingError(RuntimeError):
    pass


class GeminiEmbeddingClient:
    endpoint_template = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"

    def __init__(self, api_key: str | None = None, timeout_seconds: int = 15) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.dimensions = settings.GEMINI_EMBEDDING_DIMENSIONS
        self.timeout_seconds = timeout_seconds

    def embed_query(self, query: str) -> list[float]:
        return self._embed(f"task: search result | query: {query}")

    def embed_document(self, title: str, document: str) -> list[float]:
        return self._embed(f"title: {title or 'none'} | text: {document}")

    def _embed(self, text: str) -> list[float]:
        if not self.api_key:
            raise GeminiEmbeddingError("Gemini API key is not configured.")

        try:
            response = requests.post(
                self.endpoint_template.format(model=self.model),
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json={
                    "content": {"parts": [{"text": text}]},
                    "output_dimensionality": self.dimensions,
                },
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise GeminiEmbeddingError("Gemini embedding request failed.") from exc
        if response.status_code >= 400:
            raise GeminiEmbeddingError("Gemini embedding request failed.")

        payload = response.json()
        values = (
            payload.get("embedding", {}).get("values")
            or (payload.get("embeddings") or [{}])[0].get("values")
            or (payload.get("embeddings") or [{}])[0].get("embedding", {}).get("values")
        )
        if not isinstance(values, list) or not values:
            raise GeminiEmbeddingError("Gemini embedding response was empty.")
        return [float(value) for value in values[: settings.GEMINI_EMBEDDING_DIMENSIONS]]


def search_trend_locations(
    query: str,
    *,
    center: Point,
    embedding_client: GeminiEmbeddingClient | None = None,
    limit: int = SEARCH_RESULT_LIMIT,
):
    cleaned = " ".join(query.strip().split())
    base_queryset = (
        TrendLocation.objects
        .annotate(distance_m=Distance("location", center))
        .annotate(prefetched_video_count=Count("spot_videos"))
    )
    if not cleaned:
        return list(base_queryset.order_by("-trend_score", "name")[:6])

    scores: dict[int, float] = {}
    objects: dict[int, TrendLocation] = {}

    keyword_queryset = (
        base_queryset
        .filter(_keyword_filter(cleaned))
        .annotate(keyword_rank=_keyword_rank(cleaned))
        .order_by("keyword_rank", "-trend_score", "name")
    )
    for location in keyword_queryset[:KEYWORD_CANDIDATE_LIMIT]:
        scores[location.id] = scores.get(location.id, 0.0) + _keyword_score(location, cleaned)
        objects[location.id] = location

    client = embedding_client or GeminiEmbeddingClient()
    try:
        query_embedding = client.embed_query(cleaned)
    except Exception:
        query_embedding = None

    if query_embedding:
        semantic_queryset = (
            base_queryset
            .filter(search_embedding__isnull=False)
            .annotate(vector_distance=CosineDistance("search_embedding", query_embedding))
            .order_by("vector_distance", "-trend_score", "name")
        )
        for location in semantic_queryset[:SEMANTIC_CANDIDATE_LIMIT]:
            distance = float(getattr(location, "vector_distance", 1.0) or 1.0)
            similarity = max(0.0, min(1.0, 1.0 - distance))
            scores[location.id] = scores.get(location.id, 0.0) + (similarity * 100.0)
            objects[location.id] = location

    ranked_ids = sorted(
        scores,
        key=lambda location_id: (
            -scores[location_id],
            -float(objects[location_id].trend_score),
            objects[location_id].name.lower(),
        ),
    )
    return [objects[location_id] for location_id in ranked_ids[:limit]]


def rebuild_spot_search_embedding(
    location: TrendLocation,
    *,
    embedding_client: GeminiEmbeddingClient | None = None,
    force: bool = False,
) -> bool:
    document = build_spot_search_document(location)
    stale_document = document != (location.search_document or "")
    if not force and location.search_embedding is not None and not stale_document:
        return False

    location.search_document = document
    client = embedding_client or GeminiEmbeddingClient()
    location.search_embedding = client.embed_document(location.name, document)
    location.search_embedding_model = settings.GEMINI_EMBEDDING_MODEL
    location.search_embedding_updated_at = timezone.now()
    location.save(
        update_fields=[
            "search_document",
            "search_embedding",
            "search_embedding_model",
            "search_embedding_updated_at",
            "updated_at",
        ]
    )
    return True


def refresh_spot_search_document(location: TrendLocation, *, reset_embedding: bool = True) -> None:
    document = build_spot_search_document(location)
    if document == (location.search_document or ""):
        return
    location.search_document = document
    if reset_embedding:
        location.search_embedding = None
        location.search_embedding_updated_at = None


def build_spot_search_document(location: TrendLocation) -> str:
    parts: list[str] = [
        location.name,
        location.category,
        location.primary_type,
        location.primary_type_display_name,
        " ".join(location.place_types or []),
        location.business_status,
        location.price_level,
        "open now" if location.open_now else "",
        " ".join(location.opening_hours or []),
        " ".join(location.photo_urls or []),
        location.website_url,
        location.google_maps_url,
        location.google_uri,
        location.editorial_summary,
        location.generative_summary,
        location.review_summary,
        " ".join(location.suggestion_badges or []),
        location.suggestion_reason,
    ]
    for key, enabled in (location.amenities or {}).items():
        if enabled:
            parts.append(str(key))
    for review in location.top_reviews or []:
        if isinstance(review, dict):
            parts.extend([str(review.get("author_name") or ""), str(review.get("text") or "")])
    for link in location.spot_videos.select_related("video").all():
        video = link.video
        parts.extend(
            [
                video.caption,
                video.creator_username,
                video.creator_display_name,
                " ".join(video.hashtags or []),
                link.match_reason,
                link.discovered_from_value,
            ]
        )
    return "\n".join(_dedupe_text_parts(parts))[:12000]


def _keyword_filter(query: str) -> Q:
    words = [word for word in query.split() if word]
    q_filter = (
        Q(name__icontains=query)
        | Q(category__icontains=query)
        | Q(primary_type__icontains=query)
        | Q(primary_type_display_name__icontains=query)
        | Q(suggestion_reason__icontains=query)
        | Q(search_document__icontains=query)
    )
    for word in words:
        q_filter |= Q(name__icontains=word) | Q(category__icontains=word) | Q(search_document__icontains=word)
    return q_filter


def _keyword_rank(query: str) -> Case:
    return Case(
        When(name__iexact=query, then=Value(0)),
        When(name__istartswith=query, then=Value(1)),
        When(name__icontains=query, then=Value(2)),
        When(category__icontains=query, then=Value(3)),
        When(primary_type_display_name__icontains=query, then=Value(4)),
        default=Value(5),
        output_field=IntegerField(),
    )


def _keyword_score(location: TrendLocation, query: str) -> float:
    haystack = " ".join(
        [
            location.name,
            location.category,
            location.primary_type_display_name,
            location.suggestion_reason,
            location.search_document or "",
        ]
    ).lower()
    query_lower = query.lower()
    score = 20.0
    if location.name.lower() == query_lower:
        score += 45.0
    elif location.name.lower().startswith(query_lower):
        score += 35.0
    elif query_lower in location.name.lower():
        score += 30.0
    if query_lower in haystack:
        score += 20.0
    score += sum(5.0 for word in query_lower.split() if word in haystack)
    return score


def _dedupe_text_parts(parts: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for part in parts:
        text = str(part or "").strip()
        key = text.lower()
        if not text or key in seen or key == "none":
            continue
        if len(text) > 1000:
            text = text[:1000]
        seen.add(key)
        result.append(text)
    return result

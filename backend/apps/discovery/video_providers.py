from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import os
import re
from typing import Any
from urllib.parse import quote_plus

import requests
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:  # pragma: no cover - exercised in runtime environments without the extra dependency
    YouTubeTranscriptApi = None

logger = logging.getLogger(__name__)

MAX_SHORTS_QUERIES = 3
MAX_TRANSCRIPT_CANDIDATES = 5
MAX_SEARCH_RESULTS_PER_QUERY = 8
TRANSCRIPT_MIN_CONFIDENCE = 80
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
REQUEST_TIMEOUT_SECONDS = 20


@dataclass
class VideoProviderResult:
    videos: list[dict]
    error: str | None = None


class VideoSourceAdapter:
    def search_spot_videos(
        self,
        *,
        spot_name: str,
        city: str | None = None,
        region: str | None = None,
        country: str | None = None,
        categories: list[str] | None = None,
        limit: int = 10,
    ) -> VideoProviderResult:
        raise NotImplementedError


class NoOfficialDataProvider(VideoSourceAdapter):
    def search_spot_videos(
        self,
        *,
        spot_name: str,
        city: str | None = None,
        region: str | None = None,
        country: str | None = None,
        categories: list[str] | None = None,
        limit: int = 10,
    ) -> VideoProviderResult:
        return VideoProviderResult(videos=[], error="No official video provider configured.")


class YouTubeSearchProvider(VideoSourceAdapter):
    def __init__(self, *, api_key: str | None = None, max_videos: int = 10, session: requests.Session | None = None) -> None:
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY", "")
        self.max_videos = max_videos
        self.session = session or requests.Session()

    def search_spot_videos(
        self,
        *,
        spot_name: str,
        city: str | None = None,
        region: str | None = None,
        country: str | None = None,
        categories: list[str] | None = None,
        limit: int = 10,
    ) -> VideoProviderResult:
        if not self.api_key:
            return VideoProviderResult(videos=[], error="YOUTUBE_API_KEY is required.")
        if YouTubeTranscriptApi is None:
            return VideoProviderResult(videos=[], error="youtube_transcript_api is required.")

        target_count = min(self.max_videos, limit)
        candidates: list[dict] = []
        seen_urls: set[str] = set()
        errors: list[str] = []

        query_plan = _build_shorts_query_plan(spot_name=spot_name, city=city, categories=categories or [])
        for query, prefer_shorts in query_plan:
            result = self._search_query(query=query, limit=MAX_TRANSCRIPT_CANDIDATES, prefer_shorts=prefer_shorts)
            if result.error and not result.videos:
                errors.append(result.error)

            for video in result.videos:
                if not (video.get("raw_metadata") or {}).get("is_short"):
                    continue
                source_url = str(video.get("source_url") or "")
                if not source_url or source_url in seen_urls:
                    continue
                seen_urls.add(source_url)
                candidates.append(video)
                if len(candidates) >= MAX_TRANSCRIPT_CANDIDATES:
                    break

            if len(candidates) >= MAX_TRANSCRIPT_CANDIDATES:
                break

        relevant_videos = self._filter_relevant_candidates(
            candidates=candidates,
            spot_name=spot_name,
            city=city,
            categories=categories or [],
            limit=target_count,
        )
        if not relevant_videos and not errors and candidates:
            errors.append("youtube_transcript_confidence_below_threshold")

        relevant_videos.sort(key=_video_sort_key)
        error = "; ".join(errors) if errors and not relevant_videos else None
        return VideoProviderResult(videos=relevant_videos[:target_count], error=error)

    def _search_query(self, *, query: str, limit: int, prefer_shorts: bool) -> VideoProviderResult:
        try:
            search_items = self._search_youtube(query=query, prefer_shorts=prefer_shorts, limit=limit)
            if not search_items:
                return VideoProviderResult(videos=[], error=f"youtube_search_empty query={query!r}")

            video_ids = [item.get("id", {}).get("videoId") for item in search_items if item.get("id", {}).get("videoId")]
            if not video_ids:
                return VideoProviderResult(videos=[], error=f"youtube_video_ids_missing query={query!r}")

            details_by_id = self._fetch_video_details(video_ids)
            videos: list[dict[str, Any]] = []
            for item in search_items:
                video_id = item.get("id", {}).get("videoId")
                if not video_id:
                    continue
                detail = details_by_id.get(video_id)
                if not detail:
                    continue
                normalized = _normalize_youtube_video(
                    search_item=item,
                    detail_item=detail,
                    discovered_from_value=query,
                    prefer_shorts=prefer_shorts,
                )
                if normalized is not None:
                    videos.append(normalized)

            return VideoProviderResult(videos=videos, error=None if videos else f"youtube_details_empty query={query!r}")
        except requests.RequestException as exc:
            logger.exception("YouTube API query failed for %r", query)
            return VideoProviderResult(videos=[], error=f"youtube_api_error: {exc}")
        except Exception as exc:
            logger.exception("YouTube provider failed for %r", query)
            return VideoProviderResult(videos=[], error=f"youtube_provider_error: {exc}")

    def _search_youtube(self, *, query: str, prefer_shorts: bool, limit: int) -> list[dict[str, Any]]:
        params = {
            "key": self.api_key,
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(MAX_SEARCH_RESULTS_PER_QUERY, max(limit, 1)),
            "order": "relevance",
            "regionCode": "CA",
            "safeSearch": "none",
        }
        if prefer_shorts:
            params["videoDuration"] = "short"
        response = self.session.get(YOUTUBE_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        return list(payload.get("items") or [])

    def _fetch_video_details(self, video_ids: list[str]) -> dict[str, dict[str, Any]]:
        response = self.session.get(
            YOUTUBE_VIDEOS_URL,
            params={
                "key": self.api_key,
                "part": "snippet,contentDetails,statistics",
                "id": ",".join(video_ids),
                "maxResults": len(video_ids),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        return {
            str(item.get("id")): item
            for item in (payload.get("items") or [])
            if item.get("id")
        }

    def _filter_relevant_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
        spot_name: str,
        city: str | None,
        categories: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []

        for candidate in candidates[:MAX_TRANSCRIPT_CANDIDATES]:
            video_id = str(candidate.get("external_id") or "").strip()
            if not video_id:
                continue

            transcript_text = self._fetch_transcript_text(video_id)
            if not transcript_text:
                continue

            score = _score_video_relevance(
                spot_name=spot_name,
                city=city,
                categories=categories,
                title=str(candidate.get("caption") or ""),
                creator_display_name=str(candidate.get("creator_display_name") or ""),
                transcript_text=transcript_text,
            )
            if score < TRANSCRIPT_MIN_CONFIDENCE:
                continue

            raw_metadata = dict(candidate.get("raw_metadata") or {})
            raw_metadata.update(
                {
                    "relevance_confidence": score,
                    "transcript_excerpt": transcript_text[:400],
                }
            )
            candidate = dict(candidate)
            candidate["raw_metadata"] = raw_metadata
            candidate["relevance_score"] = max(float(candidate.get("relevance_score") or 0), float(score))
            candidate["match_reason"] = "transcript_confidence"
            filtered.append(candidate)

        filtered.sort(key=_video_sort_key)
        return filtered[:limit]

    def _fetch_transcript_text(self, video_id: str) -> str:
        transcript_items = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-CA"])  # type: ignore[union-attr]
        return " ".join(str(item.get("text") or "").strip() for item in transcript_items if str(item.get("text") or "").strip())


def _build_shorts_query_plan(*, spot_name: str, city: str | None, categories: list[str]) -> list[tuple[str, bool]]:
    city_part = (city or "").strip()
    shorts_queries = [
        _join_parts(spot_name, city_part, "shorts"),
        _join_parts(spot_name, city_part, "youtube shorts"),
        _join_parts(spot_name, "shorts"),
    ]

    categories_lower = {category.strip().lower() for category in categories if category.strip()}
    if "cafe" in categories_lower:
        shorts_queries.append(_join_parts(spot_name, city_part, "cafe shorts"))
    if "restaurant" in categories_lower:
        shorts_queries.append(_join_parts(spot_name, city_part, "restaurant shorts"))

    plan: list[tuple[str, bool]] = []
    seen: set[tuple[str, bool]] = set()
    for query in shorts_queries[:MAX_SHORTS_QUERIES]:
        normalized = " ".join(query.split())
        if normalized and (normalized, True) not in seen:
            seen.add((normalized, True))
            plan.append((normalized, True))
    return plan


def _normalize_youtube_video(
    *,
    search_item: dict[str, Any],
    detail_item: dict[str, Any],
    discovered_from_value: str,
    prefer_shorts: bool,
) -> dict[str, Any] | None:
    video_id = str(detail_item.get("id") or search_item.get("id", {}).get("videoId") or "").strip()
    if not video_id:
        return None

    snippet = detail_item.get("snippet") or search_item.get("snippet") or {}
    statistics = detail_item.get("statistics") or {}
    content_details = detail_item.get("contentDetails") or {}
    title = str(snippet.get("title") or "").strip()
    description = str(snippet.get("description") or "").strip()
    channel_id = str(snippet.get("channelId") or "").strip()
    channel_title = str(snippet.get("channelTitle") or "").strip()
    duration = str(content_details.get("duration") or "")
    duration_seconds = _parse_youtube_duration_seconds(duration)
    hashtags = _extract_hashtags_from_text(f"{title}\n{description}")
    posted_at = _parse_datetime(snippet.get("publishedAt"))
    is_short = _is_youtube_short(
        duration_seconds=duration_seconds,
        title=title,
        description=description,
        prefer_shorts=prefer_shorts,
    )
    source_url = _build_youtube_source_url(video_id=video_id, is_short=is_short)
    thumbnail_url = _best_thumbnail_url(snippet.get("thumbnails") or {})
    relevance_score = 200.0 if is_short else 100.0

    return {
        "source": "youtube",
        "source_url": source_url,
        "external_id": video_id,
        "caption": title,
        "creator_username": channel_id,
        "creator_display_name": channel_title,
        "hashtags": hashtags,
        "thumbnail_url": thumbnail_url,
        "likes_count": _optional_int(statistics.get("likeCount")),
        "comments_count": _optional_int(statistics.get("commentCount")),
        "shares_count": None,
        "views_count": _optional_int(statistics.get("viewCount")),
        "posted_at": posted_at.isoformat() if posted_at else None,
        "discovered_from": {
            "type": "youtube_search",
            "value": discovered_from_value,
        },
        "relevance_score": relevance_score,
        "match_reason": "youtube_short" if is_short else "youtube_video",
        "raw_metadata": {
            "provider": "youtube_data_api_v3",
            "video_id": video_id,
            "channel_id": channel_id,
            "channel_title": channel_title,
            "duration": duration,
            "duration_seconds": duration_seconds,
            "is_short": is_short,
            "query_mode": "shorts" if prefer_shorts else "video",
            "youtube_watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "description": description,
        },
    }


def _build_youtube_source_url(*, video_id: str, is_short: bool) -> str:
    if is_short:
        return f"https://www.youtube.com/shorts/{video_id}"
    return f"https://www.youtube.com/watch?v={quote_plus(video_id)}"


def _best_thumbnail_url(thumbnails: dict[str, Any]) -> str:
    for key in ("maxres", "standard", "high", "medium", "default"):
        item = thumbnails.get(key) or {}
        url = str(item.get("url") or "").strip()
        if url:
            return url
    return ""


def _extract_hashtags_from_text(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"#([A-Za-z0-9_]+)", text or "")))


def _parse_youtube_duration_seconds(duration: str) -> int | None:
    if not duration:
        return None
    match = re.fullmatch(r"PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?", duration)
    if not match:
        return None
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def _is_youtube_short(*, duration_seconds: int | None, title: str, description: str, prefer_shorts: bool) -> bool:
    normalized_text = f"{title}\n{description}".lower()
    if "#shorts" in normalized_text or " shorts" in normalized_text:
        return True
    if duration_seconds is not None and duration_seconds <= 180:
        return True
    return prefer_shorts and duration_seconds is not None and duration_seconds <= 240


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _join_parts(*parts: str) -> str:
    return " ".join(part for part in parts if part)


def _video_sort_key(video: dict[str, Any]) -> tuple[float, int, int]:
    raw_metadata = video.get("raw_metadata") or {}
    is_short = 1 if raw_metadata.get("is_short") else 0
    relevance = float(video.get("relevance_score") or 0)
    views = int(video.get("views_count") or 0)
    return (-is_short, -relevance, -views)


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _significant_tokens(value: str) -> list[str]:
    return [token for token in _normalize_text(value).split() if len(token) >= 3]


def _score_video_relevance(
    *,
    spot_name: str,
    city: str | None,
    categories: list[str],
    title: str,
    creator_display_name: str,
    transcript_text: str,
) -> int:
    spot_normalized = _normalize_text(spot_name)
    city_normalized = _normalize_text(city or "")
    transcript_normalized = _normalize_text(transcript_text)
    title_normalized = _normalize_text(title)
    creator_normalized = _normalize_text(creator_display_name)

    score = 0

    if spot_normalized and spot_normalized in transcript_normalized:
        score += 55
    elif spot_normalized and spot_normalized in title_normalized:
        score += 35

    spot_tokens = _significant_tokens(spot_name)
    if spot_tokens:
        transcript_hits = sum(1 for token in spot_tokens if token in transcript_normalized)
        title_hits = sum(1 for token in spot_tokens if token in title_normalized)
        creator_hits = sum(1 for token in spot_tokens if token in creator_normalized)
        score += min(25, transcript_hits * 8)
        score += min(12, title_hits * 6)
        score += min(8, creator_hits * 4)

    if city_normalized:
        if city_normalized in transcript_normalized:
            score += 15
        elif any(token in transcript_normalized for token in _significant_tokens(city_normalized)):
            score += 8

    category_hits = sum(1 for category in categories if _normalize_text(category) and _normalize_text(category) in transcript_normalized)
    score += min(10, category_hits * 5)

    transcript_length_bonus = min(5, len(_significant_tokens(transcript_text)) // 20)
    score += transcript_length_bonus

    return min(score, 100)

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
from typing import Any
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

MAX_QUERIES_PER_SPOT = 3
MAX_VIDEOS_PER_QUERY = 5


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
        return VideoProviderResult(
            videos=[],
            error="No official TikTok place feed available.",
        )


class TikTokSearchScraperProvider(VideoSourceAdapter):
    def __init__(self, *, max_videos: int = 10, headless: bool = True) -> None:
        self.max_videos = max_videos
        self.headless = headless

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
        queries = _build_queries(
            spot_name=spot_name,
            city=city,
            categories=categories or [],
        )

        collected: list[dict] = []
        seen_urls: set[str] = set()
        errors: list[str] = []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                try:
                    context = browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        locale="en-US",
                    )
                    try:
                        page = context.new_page()
                        try:
                            stealth_sync(page)

                            for query in queries[:MAX_QUERIES_PER_SPOT]:
                                batch = self._search_query(page=page, query=query, limit=min(MAX_VIDEOS_PER_QUERY, limit))
                                if not batch.videos and batch.error:
                                    errors.append(batch.error)

                                for video in batch.videos:
                                    source_url = str(video.get("source_url") or "")
                                    if not source_url or source_url in seen_urls:
                                        continue
                                    seen_urls.add(source_url)
                                    collected.append(video)
                                    if len(collected) >= min(self.max_videos, limit):
                                        break

                                if len(collected) >= min(self.max_videos, limit):
                                    break
                        finally:
                            page.close()
                    finally:
                        context.close()
                finally:
                    browser.close()
        except Exception as exc:
            return VideoProviderResult(videos=[], error=str(exc))

        error = "; ".join(errors) if errors and not collected else None
        return VideoProviderResult(videos=collected[: min(self.max_videos, limit)], error=error)

    def _search_query(self, *, page, query: str, limit: int) -> VideoProviderResult:
        url = f"https://www.tiktok.com/search?q={quote_plus(query)}"
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            script_content = page.locator("script#category-item-list-rehydrate").text_content()
            if not script_content:
                return VideoProviderResult(videos=[], error=f"TikTok script payload not found for query: {query}")

            data = json.loads(script_content)
            videos = _extract_videos_from_payload(data, max_videos=limit, discovered_from_value=query)
            return VideoProviderResult(videos=videos, error=None)
        except Exception as exc:
            return VideoProviderResult(videos=[], error=str(exc))


def _build_queries(*, spot_name: str, city: str | None, categories: list[str]) -> list[str]:
    city_part = (city or "").strip()
    queries = [
        _join_parts(spot_name, city_part),
        f"{spot_name} review".strip(),
        f"{spot_name} food".strip(),
        f"{spot_name} hidden gem".strip(),
        _join_parts(spot_name, city_part, "TikTok"),
    ]

    categories_lower = {category.strip().lower() for category in categories if category.strip()}
    if "restaurant" in categories_lower:
        queries.append(_join_parts(spot_name, "restaurant", city_part))
        queries.append(f"{spot_name} must try".strip())
    if "cafe" in categories_lower:
        queries.append(_join_parts(spot_name, "cafe", city_part))

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        normalized = " ".join(query.split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _extract_videos_from_payload(payload: Any, max_videos: int, discovered_from_value: str) -> list[dict]:
    raw_items = _collect_video_candidates(payload)
    seen_ids: set[str] = set()
    videos: list[dict] = []

    for item in raw_items:
        video_id = str(item.get("id") or item.get("videoId") or "").strip()
        if not video_id or video_id in seen_ids:
            continue

        author = item.get("author") or item.get("authorInfo") or {}
        stats = item.get("stats") or {}
        description = (item.get("desc") or item.get("description") or "").strip()
        thumbnail_url = item.get("cover") or item.get("thumbnail") or item.get("videoCover") or ""
        creator_username = str(author.get("uniqueId") or author.get("unique_id") or "").strip()
        creator_display_name = str(author.get("nickname") or author.get("displayName") or "").strip()
        source_url = _build_source_url(video_id=video_id, creator_username=creator_username)
        posted_at = _parse_posted_at(item.get("createTime"))
        hashtags = _extract_hashtags(item, description)

        videos.append(
            {
                "source": "tiktok",
                "source_url": source_url,
                "external_id": video_id,
                "caption": description,
                "creator_username": creator_username,
                "creator_display_name": creator_display_name,
                "hashtags": hashtags,
                "thumbnail_url": thumbnail_url,
                "likes_count": _parse_int(stats.get("diggCount")),
                "comments_count": _parse_int(stats.get("commentCount")),
                "shares_count": _parse_int(stats.get("shareCount")),
                "views_count": _parse_int(stats.get("playCount")),
                "posted_at": posted_at.isoformat() if posted_at else None,
                "discovered_from": {
                    "type": "search",
                    "value": discovered_from_value,
                },
                "match_reason": "query_match",
                "raw_metadata": {
                    "video_id": video_id,
                    "thumbnail_url": thumbnail_url,
                },
            }
        )
        seen_ids.add(video_id)
        if len(videos) >= max_videos:
            break

    return videos


def _collect_video_candidates(node: Any) -> list[dict]:
    matches: list[dict] = []
    if isinstance(node, dict):
        if _looks_like_video_dict(node):
            matches.append(node)
        for value in node.values():
            matches.extend(_collect_video_candidates(value))
    elif isinstance(node, list):
        for item in node:
            matches.extend(_collect_video_candidates(item))
    elif isinstance(node, str):
        if "video" in node and _might_be_json(node):
            try:
                parsed = json.loads(node)
                matches.extend(_collect_video_candidates(parsed))
            except Exception:
                return matches
    return matches


def _looks_like_video_dict(item: dict) -> bool:
    if not item.get("id") and not item.get("videoId"):
        return False
    stats = item.get("stats") or {}
    return "playCount" in stats or "desc" in item or "description" in item


def _parse_posted_at(value: Any) -> datetime | None:
    timestamp = _parse_int(value)
    if timestamp <= 0:
        return None
    try:
        return datetime.fromtimestamp(timestamp, tz=UTC)
    except (OSError, OverflowError, ValueError):
        return None


def _extract_hashtags(item: dict, description: str) -> list[str]:
    tags: list[str] = []
    text_extra = item.get("textExtra") or item.get("text_extra") or []
    for extra in text_extra:
        hashtag = str(extra.get("hashtagName") or extra.get("hashtag_name") or "").strip()
        if hashtag:
            tags.append(hashtag)

    if not tags and description:
        tags = re.findall(r"#([A-Za-z0-9_]+)", description)
    return list(dict.fromkeys(tags))


def _build_source_url(*, video_id: str, creator_username: str) -> str:
    if creator_username:
        return f"https://www.tiktok.com/@{creator_username}/video/{video_id}"
    return f"https://www.tiktok.com/v/{video_id}"


def _join_parts(*parts: str) -> str:
    return " ".join(part for part in parts if part)


def _parse_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9]", "", value)
        return int(cleaned or 0)
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _might_be_json(text: str) -> bool:
    return text.strip().startswith("{") or text.strip().startswith("[")

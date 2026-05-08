from dataclasses import dataclass
import json
import re
from typing import Any
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


@dataclass
class VideoProviderResult:
    videos: list[dict]
    error: str | None = None


class VideoProvider:
    def fetch_for_place(self, *, place_name: str, place_id: str) -> VideoProviderResult:
        raise NotImplementedError


class NoOfficialDataProvider(VideoProvider):
    def fetch_for_place(self, *, place_name: str, place_id: str) -> VideoProviderResult:
        return VideoProviderResult(
            videos=[],
            error="No official TikTok place feed available.",
        )


class TikTokSearchScraperProvider(VideoProvider):
    def __init__(self, *, max_videos: int = 6, headless: bool = True) -> None:
        self.max_videos = max_videos
        self.headless = headless

    def fetch_for_place(self, *, place_name: str, place_id: str) -> VideoProviderResult:
        query = quote_plus(f"{place_name} Calgary")
        url = f"https://www.tiktok.com/search?q={query}"

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="en-US",
                )
                page = context.new_page()
                stealth_sync(page)
                page.goto(url, wait_until="networkidle", timeout=60000)

                script_content = page.locator("script#category-item-list-rehydrate").text_content()
                browser.close()

            if not script_content:
                return VideoProviderResult(videos=[], error="TikTok script payload not found.")

            data = json.loads(script_content)
            videos = _extract_videos_from_payload(data, max_videos=self.max_videos)
            return VideoProviderResult(videos=videos, error=None)
        except Exception as exc:
            return VideoProviderResult(videos=[], error=str(exc))


def _extract_videos_from_payload(payload: Any, max_videos: int) -> list[dict]:
    raw_items = _collect_video_candidates(payload)
    seen_ids: set[str] = set()
    videos: list[dict] = []

    for item in raw_items:
        video_id = str(item.get("id") or item.get("videoId") or "").strip()
        if not video_id or video_id in seen_ids:
            continue

        stats = item.get("stats") or {}
        views = _parse_int(stats.get("playCount"))
        description = (item.get("desc") or item.get("description") or "").strip()
        cover = item.get("cover") or item.get("thumbnail") or item.get("videoCover") or ""

        videos.append(
            {
                "id": video_id,
                "title": description or "TikTok video",
                "url": f"https://www.tiktok.com/v/{video_id}",
                "thumbnail_url": cover,
                "views": views,
                "description": description,
                "source": "tiktok_search",
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

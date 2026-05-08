from dataclasses import dataclass


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

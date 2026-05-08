from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"


@dataclass(frozen=True)
class LocationBias:
    lat: float
    lng: float
    radius_m: int = 20000

    def as_param(self) -> str:
        return f"circle:{self.radius_m}@{self.lat},{self.lng}"


class GooglePlacesClient:
    def __init__(self, api_key: str, timeout: int = 12, retries: int = 2, backoff_seconds: float = 0.8) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = backoff_seconds

    def text_search(
        self,
        *,
        query: str,
        place_type: str | None = None,
        location_bias: LocationBias | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"query": query, "key": self.api_key}
        if place_type:
            params["type"] = place_type
        if location_bias:
            params["locationbias"] = location_bias.as_param()
        payload = self._get(PLACES_TEXT_SEARCH_URL, params=params)
        return payload.get("results", [])

    def place_details(self, *, place_id: str, fields: str) -> dict[str, Any]:
        params = {"place_id": place_id, "fields": fields, "key": self.api_key}
        payload = self._get(PLACES_DETAILS_URL, params=params)
        if payload.get("status") != "OK":
            raise RuntimeError(payload.get("error_message") or payload.get("status") or "Google place details failed")
        return payload.get("result") or {}

    def build_photo_url(self, *, photo_reference: str, max_width: int = 900) -> str:
        params = {
            "maxwidth": max_width,
            "photo_reference": photo_reference,
            "key": self.api_key,
        }
        return f"{PLACES_PHOTO_URL}?{requests.compat.urlencode(params)}"

    def _get(self, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if payload.get("status") in {"OVER_QUERY_LIMIT", "RESOURCE_EXHAUSTED"}:
                    raise RuntimeError("Google Places quota exceeded")
                return payload
            except Exception as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.backoff_seconds * (2 ** attempt))
                    continue
                raise
        if last_error:
            raise last_error
        return {}

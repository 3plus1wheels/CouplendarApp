from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

PLACES_TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"
PLACES_NEW_BASE_URL = "https://places.googleapis.com/v1"


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

    def text_search_new(
        self,
        *,
        query: str,
        field_mask: str,
        location_bias: LocationBias | None = None,
        max_result_count: int = 10,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "textQuery": query,
            "maxResultCount": max(1, min(max_result_count, 20)),
        }
        if location_bias:
            body["locationBias"] = _circle(location_bias)
        payload = self._post_new(
            f"{PLACES_NEW_BASE_URL}/places:searchText",
            json_body=body,
            field_mask=field_mask,
        )
        return payload.get("places", [])

    def nearby_search_new(
        self,
        *,
        field_mask: str,
        location_bias: LocationBias,
        included_types: list[str] | None = None,
        max_result_count: int = 10,
        rank_preference: str = "POPULARITY",
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "maxResultCount": max(1, min(max_result_count, 20)),
            "locationRestriction": _circle(location_bias),
            "rankPreference": rank_preference,
        }
        if included_types:
            body["includedTypes"] = included_types[:50]
        payload = self._post_new(
            f"{PLACES_NEW_BASE_URL}/places:searchNearby",
            json_body=body,
            field_mask=field_mask,
        )
        return payload.get("places", [])

    def place_details(self, *, place_id: str, fields: str) -> dict[str, Any]:
        params = {"place_id": place_id, "fields": fields, "key": self.api_key}
        payload = self._get(PLACES_DETAILS_URL, params=params)
        if payload.get("status") != "OK":
            raise RuntimeError(payload.get("error_message") or payload.get("status") or "Google place details failed")
        return payload.get("result") or {}

    def place_details_new(self, *, place_id: str, field_mask: str) -> dict[str, Any]:
        resource_name = place_id if place_id.startswith("places/") else f"places/{place_id}"
        return self._get_new(f"{PLACES_NEW_BASE_URL}/{resource_name}", field_mask=field_mask)

    def build_photo_url(self, *, photo_reference: str, max_width: int = 900) -> str:
        if photo_reference.startswith("places/") and "/photos/" in photo_reference:
            params = {
                "maxWidthPx": max_width,
                "key": self.api_key,
            }
            return f"{PLACES_NEW_BASE_URL}/{photo_reference}/media?{requests.compat.urlencode(params)}"
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

    def _get_new(self, url: str, *, field_mask: str) -> dict[str, Any]:
        return self._request_new("GET", url, field_mask=field_mask)

    def _post_new(self, url: str, *, json_body: dict[str, Any], field_mask: str) -> dict[str, Any]:
        return self._request_new("POST", url, json_body=json_body, field_mask=field_mask)

    def _request_new(
        self,
        method: str,
        url: str,
        *,
        field_mask: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=headers,
                    json=json_body,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("error"):
                    error = payload["error"]
                    raise RuntimeError(error.get("message") or error.get("status") or "Google Places request failed")
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


def _circle(location_bias: LocationBias) -> dict[str, Any]:
    return {
        "circle": {
            "center": {
                "latitude": location_bias.lat,
                "longitude": location_bias.lng,
            },
            "radius": float(location_bias.radius_m),
        }
    }

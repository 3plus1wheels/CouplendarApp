from __future__ import annotations

from django.core.cache import cache

DISCOVERY_LIST_CACHE_KEY = "discovery:v1:trending:list"
DISCOVERY_DETAIL_CACHE_KEY_TEMPLATE = "discovery:v1:trending:detail:{spot_id}"


def discovery_detail_cache_key(spot_id: int) -> str:
    return DISCOVERY_DETAIL_CACHE_KEY_TEMPLATE.format(spot_id=spot_id)


def invalidate_discovery_cache(spot_id: int | None = None) -> None:
    keys = [DISCOVERY_LIST_CACHE_KEY]
    if spot_id is not None:
        keys.append(discovery_detail_cache_key(spot_id))
    cache.delete_many(keys)

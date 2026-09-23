"""One reading of CoinMarketCap's response shapes, shared by every caller.

CMC returns the same logical collection three ways depending on the endpoint:
a bare list, an object keyed by id, or an object wrapping the list under a
named key (`rwa_assets`, `market_pairs`, `holders`, `pools`). Every module here
needed the same tolerance, and each had grown its own copy under the same name
with slightly different fallbacks - which is worse than duplication, because a
reader who has understood one has not understood the others.

This module is the single definition. It performs no I/O, so the replay path
can import it without a key or a network.
"""
from __future__ import annotations

from typing import Any


def payload_data(response: dict[str, Any]) -> Any:
    """Unwrap CMC's `data` envelope, tolerating a payload that is already inner."""
    return response.get("data", response)


def as_list(data: Any) -> list[dict[str, Any]]:
    """Coerce a list, a single object, or anything else into a list of objects."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def records(data: Any, *keys: str) -> list[dict[str, Any]]:
    """Extract list-shaped records from CMC's object-or-list response variants.

    `keys` are the wrapper names to try, in order. An object whose values are
    all objects is read as an id-keyed collection.
    """
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
        values = [value for value in data.values() if isinstance(value, dict)]
        if values and len(values) == len(data):
            return values
    return as_list(data)

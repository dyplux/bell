"""Persistence checks for independent Bell session receipts.

This module deliberately refuses to call a two-window delta a trend. It is a
small offline gate that can be run once four or more independently dated
receipts exist for the same asset.
"""

from __future__ import annotations

from statistics import median
from typing import Any, Iterable


SESSION_NAMES = ("cash", "after_hours", "weekend")


def assess_persistence(receipts: Iterable[dict[str, Any]], minimum_windows: int = 4) -> dict[str, Any]:
    rows = list(receipts)
    windows = {
        (item.get("window", {}).get("start_utc"), item.get("window", {}).get("end_utc"))
        for item in rows
    }
    distinct_windows = sorted(window for window in windows if all(window))
    eligible = len(distinct_windows) >= minimum_windows
    by_symbol: dict[str, dict[str, dict[str, Any]]] = {}
    for receipt in rows:
        for wrapper in receipt.get("wrappers", []):
            symbol = str(wrapper.get("symbol") or "unknown")
            target = by_symbol.setdefault(symbol, {})
            for session in SESSION_NAMES:
                value = wrapper.get("sessions", {}).get(session, {}).get("median_range_pct")
                if value is not None:
                    target.setdefault(session, {}).setdefault("values", []).append(float(value))
    summaries = []
    for symbol in sorted(by_symbol):
        for session in SESSION_NAMES:
            values = by_symbol[symbol].get(session, {}).get("values", [])
            summaries.append({
                "symbol": symbol,
                "session": session,
                "observations": len(values),
                "median": round(float(median(values)), 8) if values else None,
                "min": round(min(values), 8) if values else None,
                "max": round(max(values), 8) if values else None,
                "spread": round(max(values) - min(values), 8) if values else None,
                "persistent_claim_allowed": eligible and len(values) >= minimum_windows,
            })
    return {
        "schema_version": "bell.persistence.v1",
        "minimum_windows": minimum_windows,
        "windows_supplied": len(rows),
        "distinct_windows": [{"start_utc": start, "end_utc": end} for start, end in distinct_windows],
        "eligible_for_persistence_claim": eligible,
        "summaries": summaries,
        "limitations": [
            "Distinct date windows do not remove source-data or market-regime differences.",
            "A persistent range pattern is not a liquidity, price-discovery or return forecast.",
            "Receipts with missing session values remain incomplete rather than zero-filled.",
        ],
    }


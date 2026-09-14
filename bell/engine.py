"""Deterministic session analysis for Bell.

The engine is deliberately independent from the network and the browser.  It accepts
normalised CMC-like records, classifies hourly bars using an IANA timezone, and returns a
serialisable report/receipt.  The live adapter lives in bell.py so these rules remain easy to test.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import math
from statistics import median
from typing import Any, Iterable
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "bell.receipt.v1"
DEFAULT_TIMEZONE = "America/New_York"
SESSION_NAMES = ("cash", "after_hours", "weekend")


class BellDataError(ValueError):
    """Raised when a record cannot be interpreted without inventing data."""


def parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError as exc:
            raise BellDataError(f"invalid timestamp: {value!r}") from exc
    else:
        raise BellDataError(f"timestamp must be ISO string or datetime: {value!r}")
    if parsed.tzinfo is None:
        raise BellDataError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def classify_session(
    timestamp: Any,
    timezone_name: str = DEFAULT_TIMEZONE,
    cash_start: time = time(9, 30),
    cash_end: time = time(16, 0),
) -> str:
    """Classify a bar by its opening timestamp.

    A bar belongs to the bucket determined by ``time_open`` after conversion to New York.
    The 16:00 boundary is after-hours; holidays are intentionally not removed.
    """

    local = parse_timestamp(timestamp).astimezone(ZoneInfo(timezone_name))
    if local.weekday() >= 5:
        return "weekend"
    if cash_start <= local.time() < cash_end:
        return "cash"
    return "after_hours"


def _number(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise BellDataError(f"{field} must be numeric") from exc
    if not math.isfinite(result):
        raise BellDataError(f"{field} must be finite")
    return result


def normalise_bar(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BellDataError("OHLCV bar must be an object")
    opened = record.get("time_open", record.get("timestamp"))
    if opened is None:
        raise BellDataError("OHLCV bar is missing time_open")
    opened_at = parse_timestamp(opened)
    opened_price = _number(record.get("open"), "open")
    high = _number(record.get("high"), "high")
    low = _number(record.get("low"), "low")
    close = _number(record.get("close"), "close") if record.get("close") is not None else None
    if opened_price <= 0:
        raise BellDataError("open must be greater than zero")
    if high < low or low < 0:
        raise BellDataError("OHLC values are inconsistent")
    if close is not None and close < 0:
        raise BellDataError("close must not be negative")
    return {
        "time_open": opened_at.isoformat().replace("+00:00", "Z"),
        "open": opened_price,
        "high": high,
        "low": low,
        "close": close,
        "range_pct": (high - low) / opened_price * 100,
    }


def _expected_session_counts(start: datetime, end: datetime, timezone_name: str) -> dict[str, int]:
    counts = {name: 0 for name in SESSION_NAMES}
    cursor = start
    while cursor < end:
        counts[classify_session(cursor, timezone_name)] += 1
        cursor += timedelta(hours=1)
    return counts


def _session_stats(bars: Iterable[dict[str, Any]], timezone_name: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in SESSION_NAMES}
    for bar in bars:
        grouped[classify_session(bar["time_open"], timezone_name)].append(bar)
    stats: dict[str, dict[str, Any]] = {}
    for name in SESSION_NAMES:
        values = [bar["range_pct"] for bar in grouped[name]]
        stats[name] = {
            "count": len(values),
            "median_range_pct": round(float(median(values)), 8) if values else None,
        }
    return stats


def _venue_context(wrapper: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    venue = wrapper.get("venue")
    if not isinstance(venue, dict):
        warnings.append("venue totals unavailable; this is unknown, not zero")
        return {"status": "unavailable", "cex_volume_24h": None, "dex_volume_24h": None, "cex_share_pct": None}
    cex = venue.get("cex_volume_24h")
    dex = venue.get("dex_volume_24h")
    if cex is None or dex is None:
        warnings.append("venue totals incomplete; composition unavailable")
        return {"status": "unavailable", "cex_volume_24h": cex, "dex_volume_24h": dex, "cex_share_pct": None}
    cex_number = _number(cex, "cex_volume_24h")
    dex_number = _number(dex, "dex_volume_24h")
    denominator = cex_number + dex_number
    if cex_number < 0 or dex_number < 0 or denominator <= 0:
        warnings.append("venue totals have no positive denominator")
        return {"status": "unavailable", "cex_volume_24h": cex_number, "dex_volume_24h": dex_number, "cex_share_pct": None}
    return {
        "status": "available",
        "cex_volume_24h": cex_number,
        "dex_volume_24h": dex_number,
        "cex_share_pct": round(cex_number / denominator * 100, 8),
    }


def analyse_wrapper(
    wrapper: dict[str, Any],
    window_start: datetime,
    window_end: datetime,
    timezone_name: str = DEFAULT_TIMEZONE,
    min_bars_per_session: int = 1,
) -> dict[str, Any]:
    window_start = parse_timestamp(window_start)
    window_end = parse_timestamp(window_end)
    symbol = str(wrapper.get("symbol") or wrapper.get("name") or "unknown")
    issuer = str(wrapper.get("issuer") or wrapper.get("issuer_name") or "unknown")
    warnings: list[str] = []
    valid: list[dict[str, Any]] = []
    invalid_count = 0
    seen: set[str] = set()
    for raw in wrapper.get("bars", []):
        try:
            bar = normalise_bar(raw)
        except BellDataError as exc:
            invalid_count += 1
            warnings.append(f"excluded invalid bar: {exc}")
            continue
        if bar["time_open"] in seen:
            invalid_count += 1
            warnings.append(f"excluded duplicate bar: {bar['time_open']}")
            continue
        seen.add(bar["time_open"])
        valid.append(bar)
    valid.sort(key=lambda bar: bar["time_open"])
    if invalid_count:
        warnings.append(f"{invalid_count} bar(s) excluded")

    expected = _expected_session_counts(window_start, window_end, timezone_name)
    actual = _session_stats(valid, timezone_name)
    for name in SESSION_NAMES:
        actual[name]["expected_count"] = expected[name]
        actual[name]["coverage_pct"] = round(
            actual[name]["count"] / expected[name] * 100, 4
        ) if expected[name] else None
        if actual[name]["count"] < min_bars_per_session:
            warnings.append(f"insufficient {name} bars: {actual[name]['count']} < {min_bars_per_session}")

    gaps = []
    for previous, current in zip(valid, valid[1:]):
        delta = parse_timestamp(current["time_open"]) - parse_timestamp(previous["time_open"])
        if delta > timedelta(hours=1):
            gaps.append({"from": previous["time_open"], "to": current["time_open"], "missing_hours": int(delta.total_seconds() // 3600 - 1)})
    if gaps:
        warnings.append(f"{sum(gap['missing_hours'] for gap in gaps)} hourly gap(s) detected")

    venue = _venue_context(wrapper, warnings)
    enough = all(actual[name]["count"] >= min_bars_per_session for name in SESSION_NAMES)
    coverage_values = [actual[name]["coverage_pct"] for name in SESSION_NAMES if actual[name]["coverage_pct"] is not None]
    state = "ready" if enough and all(value == 100 for value in coverage_values) and not invalid_count else "partial"
    if not valid:
        state = "insufficient-data"
    return {
        "symbol": symbol,
        "issuer": issuer,
        "state": state,
        "bars_received": len(wrapper.get("bars", [])),
        "bars_valid": len(valid),
        "sessions": actual,
        "gaps": gaps,
        "venue": venue,
        "warnings": warnings,
    }


def analyse_dataset(payload: dict[str, Any], *, min_bars_per_session: int = 1) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise BellDataError("dataset must be an object")
    timezone_name = str(payload.get("timezone") or DEFAULT_TIMEZONE)
    try:
        ZoneInfo(timezone_name)
    except Exception as exc:
        raise BellDataError(f"unknown timezone: {timezone_name}") from exc
    wrappers = payload.get("wrappers")
    if not isinstance(wrappers, list) or not wrappers:
        raise BellDataError("dataset needs a non-empty wrappers list")

    all_times = [
        parse_timestamp(bar.get("time_open", bar.get("timestamp")))
        for wrapper in wrappers if isinstance(wrapper, dict)
        for bar in wrapper.get("bars", []) if isinstance(bar, dict)
        if bar.get("time_open", bar.get("timestamp")) is not None
    ]
    start = parse_timestamp(payload["window_start"]) if payload.get("window_start") else (min(all_times) if all_times else None)
    end = parse_timestamp(payload["window_end"]) if payload.get("window_end") else ((max(all_times) + timedelta(hours=1)) if all_times else None)
    if start is None or end is None or end <= start:
        raise BellDataError("dataset needs a valid window_start/window_end or valid bars")

    analysed = [analyse_wrapper(wrapper, start, end, timezone_name, min_bars_per_session) for wrapper in wrappers]
    top_warnings = list(payload.get("warnings") or [])
    for result in analysed:
        top_warnings.extend(f"{result['symbol']}: {warning}" for warning in result["warnings"])
    states = {result["state"] for result in analysed}
    if states == {"ready"}:
        state = "ready"
    elif states == {"insufficient-data"}:
        state = "insufficient-data"
    else:
        state = "partial"
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": payload.get("mode", "offline_fixture"),
        "state": state,
        "asset": payload.get("asset", {"name": "unknown"}),
        "window": {
            "start_utc": start.isoformat().replace("+00:00", "Z"),
            "end_utc": end.isoformat().replace("+00:00", "Z"),
            "timezone": timezone_name,
            "duration_hours": int((end - start).total_seconds() // 3600),
        },
        "methodology": {
            "session_assignment": "time_open converted to timezone; no holiday calendar",
            "cash": "weekdays 09:30 <= local time < 16:00",
            "after_hours": "remaining weekday hours",
            "weekend": "Saturday and Sunday",
            "hourly_range_pct": "((high - low) / open) * 100",
            "aggregate": "median of hourly ranges by session",
            "hourly_volume": "not used; documented CMC hourly volume is rolling 24h",
        },
        "wrappers": analysed,
        "warnings": top_warnings,
        "provenance": payload.get("provenance", {}),
    }


def load_payload(path: str) -> dict[str, Any]:
    import json
    from pathlib import Path

    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_receipt(receipt: dict[str, Any], path: str) -> None:
    import json
    from pathlib import Path

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

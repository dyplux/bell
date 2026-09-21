#!/usr/bin/env python3
"""Bell command line interface.

Offline mode is safe by default. Live mode is intentionally explicit and requires CMC_API_KEY from
the process environment; the key is never printed or persisted by this CLI.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from engine import BellDataError, analyse_dataset, load_payload, parse_timestamp, save_receipt


ROOT = Path(__file__).resolve().parent
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "offline.json"
CMC_BASE = "https://pro-api.coinmarketcap.com"


class CMCClient:
    def __init__(self, api_key: str, base_url: str = CMC_BASE) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.calls: list[dict[str, Any]] = []

    def get(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urlencode({key: value for key, value in params.items() if value is not None})
        url = f"{self.base_url}{endpoint}?{query}" if query else f"{self.base_url}{endpoint}"
        request = Request(url, headers={"X-CMC_PRO_API_KEY": self.api_key, "Accept": "application/json"})
        observed_at = datetime.now(timezone.utc).isoformat()
        try:
            with urlopen(request, timeout=30) as response:
                status = int(response.status)
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            self.calls.append({"endpoint": endpoint, "params": params, "status": exc.code, "error": type(exc).__name__, "observed_at": observed_at})
            raise BellDataError(f"CMC request failed for {endpoint}: HTTP {exc.code}") from exc
        except Exception as exc:
            self.calls.append({"endpoint": endpoint, "params": params, "status": "error", "error": type(exc).__name__, "observed_at": observed_at})
            raise BellDataError(f"CMC request failed for {endpoint}: {type(exc).__name__}") from exc
        api_status = body.get("status") if isinstance(body.get("status"), dict) else {}
        self.calls.append({
            "endpoint": endpoint,
            "params": params,
            "status": status,
            "observed_at": observed_at,
            "api_timestamp": api_status.get("timestamp"),
            "credit_count": api_status.get("credit_count"),
            "elapsed_ms": api_status.get("elapsed"),
            "error_code": api_status.get("error_code"),
        })
        if status >= 400:
            raise BellDataError(f"CMC returned HTTP {status} for {endpoint}")
        return body


def _as_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _records(data: Any, *keys: str) -> list[dict[str, Any]]:
    """Extract list-shaped records from CMC's object-or-list response variants."""
    if isinstance(data, dict):
        for key in keys:
            if isinstance(data.get(key), list):
                return [item for item in data[key] if isinstance(item, dict)]
        values = [value for value in data.values() if isinstance(value, dict)]
        if values and len(values) == len(data):
            return values
    return _as_list(data)


def _payload_data(response: dict[str, Any]) -> Any:
    return response.get("data", response)


def _extract_quote_value(record: dict[str, Any], field: str) -> Any:
    if field in record:
        return record[field]
    for quote_key in ("USD", "usd", "quote"):
        quote = record.get(quote_key)
        if isinstance(quote, dict):
            if field in quote:
                return quote[field]
            nested = quote.get("USD", quote.get("usd"))
            if isinstance(nested, dict) and field in nested:
                return nested[field]
    return None


def _normalise_ohlcv_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "time_open": record.get("time_open", record.get("timestamp")),
        "open": _extract_quote_value(record, "open"),
        "high": _extract_quote_value(record, "high"),
        "low": _extract_quote_value(record, "low"),
        "close": _extract_quote_value(record, "close"),
    }


def fetch_live_catalog(client: CMCClient, page_size: int = 100) -> dict[str, Any]:
    """Fetch the zero-credit RWA map and return a compact, searchable catalogue."""
    if page_size < 1 or page_size > 100:
        raise BellDataError("catalog page_size must be between 1 and 100")
    assets: list[dict[str, Any]] = []
    start = 1
    total_size: int | None = None
    while True:
        response = client.get("/v5/real-world-assets/map", {"start": start, "limit": page_size})
        data = _payload_data(response)
        page = _records(data, "rwa_assets", "assets")
        if not page:
            break
        if isinstance(data, dict) and total_size is None and isinstance(data.get("total_size"), int):
            total_size = data["total_size"]
        assets.extend(
            {
                "rwa_id": item.get("rwa_id"),
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "slug": item.get("slug"),
                "asset_type": item.get("asset_type"),
                "rwa_rank": item.get("rwa_rank"),
                "has_tokens": item.get("has_tokens"),
                "first_historical_data": item.get("first_historical_data"),
                "last_historical_data": item.get("last_historical_data"),
            }
            for item in page
        )
        has_more = bool(data.get("has_more")) if isinstance(data, dict) else False
        if not has_more or (total_size is not None and len(assets) >= total_size):
            break
        next_start = start + len(page)
        if next_start <= start:
            raise BellDataError("CMC RWA map pagination did not advance")
        start = next_start
    if not assets:
        raise BellDataError("CMC RWA map returned no assets")
    return {
        "schema_version": "bell.catalog.v1",
        "mode": "live_cmc",
        "total_size": total_size or len(assets),
        "assets": assets,
        "provenance": {
            "source": "CoinMarketCap Pro API",
            "endpoints": sorted({call["endpoint"] for call in client.calls}),
            "calls": client.calls,
            "raw_responses_included": False,
        },
    }


def fetch_live_asset(client: CMCClient, asset_slug: str) -> dict[str, Any]:
    """Fetch one RWA dossier without spending credits on historical OHLCV."""
    response = client.get("/v5/real-world-assets/quotes/latest", {"rwa_slug": asset_slug})
    records = _records(_payload_data(response), "rwa_assets", "assets")
    asset = records[0] if records else (_payload_data(response) if isinstance(_payload_data(response), dict) else {})
    if not isinstance(asset, dict) or not asset:
        raise BellDataError(f"CMC returned no RWA asset for {asset_slug}")
    tokens = _records(asset.get("tokens"), "tokens")
    return {
        "schema_version": "bell.asset.v1",
        "mode": "live_cmc",
        "asset": {
            key: asset.get(key)
            for key in (
                "rwa_id",
                "name",
                "symbol",
                "slug",
                "asset_type",
                "rwa_rank",
                "has_tokens",
                "average_tokenized_price",
                "tokenized_market_cap",
                "tokenized_volume_24h",
                "last_updated",
            )
        },
        "tokens": [
            {
                key: token.get(key)
                for key in ("name", "symbol", "price", "crypto_id", "issuer_id", "issuer_name", "market_cap", "volume_24h")
            }
            for token in tokens
        ],
        "tradfi_markets": asset.get("tradfi_markets") if isinstance(asset.get("tradfi_markets"), list) else [],
        "provenance": {
            "source": "CoinMarketCap Pro API",
            "endpoints": sorted({call["endpoint"] for call in client.calls}),
            "calls": client.calls,
            "raw_responses_included": False,
        },
    }


def fetch_live_dataset(client: CMCClient, asset_slug: str, days: int, end: datetime | None = None) -> dict[str, Any]:
    end = end or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    end = end.astimezone(timezone.utc)
    start = end - timedelta(days=days)
    rwa_response = client.get("/v5/real-world-assets/quotes/latest", {"rwa_slug": asset_slug})
    asset_records = _records(_payload_data(rwa_response), "rwa_assets", "assets")
    asset = asset_records[0] if asset_records else (_payload_data(rwa_response) if isinstance(_payload_data(rwa_response), dict) else {})
    token_records = _records(asset.get("tokens"), "tokens") if isinstance(asset, dict) else []
    if not token_records:
        raise BellDataError("CMC RWA response contained no token wrappers")

    wrappers: list[dict[str, Any]] = []
    # CMC treats time_start as exclusive. Request one preceding hourly period so
    # the requested observation window contains the first candle at `start`.
    request_start = start - timedelta(hours=1)
    for token in token_records:
        crypto_id = token.get("crypto_id") or token.get("id")
        if crypto_id is None:
            continue
        bars_response = client.get(
            "/v2/cryptocurrency/ohlcv/historical",
            {
                "id": crypto_id,
                "time_start": request_start.isoformat(),
                "time_end": end.isoformat(),
                "time_period": "hourly",
                "interval": "hourly",
                "count": days * 24 + 1,
            },
        )
        bars_data = _payload_data(bars_response)
        bars = [_normalise_ohlcv_record(record) for record in _records(bars_data, "quotes", "data")]
        # The preceding candle protects the exclusive CMC time_start boundary, but it is
        # outside the declared research window and must never enter the session statistics.
        bars = [
            bar for bar in bars
            if start <= parse_timestamp(bar["time_open"]) < end
        ]
        quote_response = client.get("/v2/cryptocurrency/quotes/latest", {"id": crypto_id})
        quote_data = _payload_data(quote_response)
        quote_records = _records(quote_data)
        quote = quote_records[0] if quote_records else {}
        wrappers.append(
            {
                "symbol": token.get("symbol") or token.get("name") or str(crypto_id),
                "issuer": token.get("issuer_name") or "unknown",
                "crypto_id": crypto_id,
                "bars": bars,
                "venue": {
                    "cex_volume_24h": _extract_quote_value(quote, "cex_volume_24h"),
                    "dex_volume_24h": _extract_quote_value(quote, "dex_volume_24h"),
                },
            }
        )
    if not wrappers:
        raise BellDataError("no wrappers with crypto_id were returned by CMC")
    return {
        "mode": "live_cmc",
        "asset": {"name": asset.get("name", asset_slug), "slug": asset.get("slug", asset_slug), "rwa_id": asset.get("rwa_id")},
        "window_start": start.isoformat().replace("+00:00", "Z"),
        "window_end": end.isoformat().replace("+00:00", "Z"),
        "timezone": "America/New_York",
        "wrappers": wrappers,
        "provenance": {
            "source": "CoinMarketCap Pro API",
            "endpoints": sorted({call["endpoint"] for call in client.calls}),
            "calls": client.calls,
            "raw_responses_included": False,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Bell's deterministic RWA session analysis")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--offline", action="store_true", help="analyse a local fixture/receipt (default)")
    mode.add_argument("--live", action="store_true", help="fetch from CMC using CMC_API_KEY")
    mode.add_argument("--catalog", action="store_true", help="fetch the complete searchable RWA map")
    parser.add_argument("--input", type=Path, default=DEFAULT_FIXTURE, help="offline JSON input")
    parser.add_argument("--asset", default="tesla", help="CMC RWA slug for live mode")
    parser.add_argument("--days", type=int, default=7, help="hours to request in live mode")
    parser.add_argument("--end", help="live mode observation end in ISO-8601 UTC, for reproducible snapshots")
    parser.add_argument("--min-bars", type=int, default=1, help="minimum bars required per session")
    parser.add_argument("--output", type=Path, help="write receipt JSON to this path")
    parser.add_argument(
        "--payload-output",
        type=Path,
        help="live mode: write the normalised, credential-free dataset for offline recomputation",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.live:
            api_key = os.environ.get("CMC_API_KEY")
            if not api_key:
                raise BellDataError("live mode requires CMC_API_KEY in the environment")
            if args.days < 1 or args.days > 30:
                raise BellDataError("days must be between 1 and 30")
            end = None
            if args.end:
                try:
                    end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise BellDataError("--end must be an ISO-8601 timestamp") from exc
            client = CMCClient(api_key)
            payload = fetch_live_dataset(client, args.asset, args.days, end=end)
        elif args.catalog:
            api_key = os.environ.get("CMC_API_KEY")
            if not api_key:
                raise BellDataError("catalog mode requires CMC_API_KEY in the environment")
            payload = fetch_live_catalog(CMCClient(api_key))
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            return 0
        else:
            payload = load_payload(str(args.input))
        if args.payload_output:
            args.payload_output.parent.mkdir(parents=True, exist_ok=True)
            args.payload_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt = analyse_dataset(payload, min_bars_per_session=args.min_bars)
        if args.output:
            save_receipt(receipt, str(args.output))
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        return 0
    except (BellDataError, OSError, json.JSONDecodeError) as exc:
        print(f"bell: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

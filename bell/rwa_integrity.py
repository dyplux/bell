#!/usr/bin/env python3
"""RWA Surface Integrity Monitor.

The monitor checks whether CoinMarketCap's RWA surfaces can safely be joined
before a user compares wrappers. It is deliberately a rule engine, not an
opaque risk score. The same receipt can be produced from a live CMC run or
replayed from credential-free JSON responses.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_ROOT = "https://pro-api.coinmarketcap.com"


def records(payload: dict) -> list[dict]:
    data = payload.get("data", payload)
    if isinstance(data, dict) and isinstance(data.get("rwa_assets"), list):
        return [item for item in data["rwa_assets"] if isinstance(item, dict)]
    return []


def surface_has_records(payload: dict) -> bool:
    data = payload.get("data") if isinstance(payload, dict) else None
    return isinstance(data, dict) and isinstance(data.get("rwa_assets"), list)


def number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def api_get(path: str, params: dict[str, object], key: str) -> dict:
    query = urlencode({key_: str(value) for key_, value in params.items() if value is not None})
    request = Request(f"{API_ROOT}{path}?{query}", headers={"X-CMC_PRO_API_KEY": key, "Accept": "application/json"})
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response:
                return json.load(response)
        except HTTPError as exc:
            last_error = exc
            if exc.code not in (408, 425, 429) and exc.code < 500:
                raise
        except URLError as exc:
            last_error = exc
        if attempt < 2:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"CMC request failed after retries: {path}") from last_error


def collect_live(key: str) -> tuple[dict, dict, dict, dict, dict, dict]:
    map_pages = []
    list_pages = []
    for start in range(1, 10001, 250):
        page = api_get("/v5/real-world-assets/map", {"start": start, "limit": 250}, key)
        map_pages.append(page)
        if not page.get("data", {}).get("has_more"):
            break
    for start in range(1, 10001, 250):
        page = api_get("/v5/real-world-assets/assets/list", {"start": start, "limit": 250, "convert": "USD"}, key)
        list_pages.append(page)
        if not page.get("data", {}).get("has_more"):
            break
    map_rows = records({"data": {"rwa_assets": sum((records(page) for page in map_pages), [])}})
    list_rows = records({"data": {"rwa_assets": sum((records(page) for page in list_pages), [])}})
    token_ids = [str(row["rwa_id"]) for row in map_rows if row.get("has_tokens") is True and row.get("rwa_id") is not None]
    info_pages = []
    quote_pages = []
    crypto_info_pages = []
    for index in range(0, len(token_ids), 250):
        info_pages.append(api_get("/v5/real-world-assets/info", {"rwa_id": ",".join(token_ids[index:index + 250])}, key))
        quote_pages.append(api_get("/v5/real-world-assets/quotes/latest", {"rwa_id": ",".join(token_ids[index:index + 250]), "convert": "USD", "skip_invalid": "true"}, key))
    crypto_ids = sorted({str(token.get("crypto_id")) for page in quote_pages for asset in records(page) for token in asset.get("tokens", []) if isinstance(token, dict) and token.get("crypto_id") is not None})
    crypto_info_invalid_ids = []
    for index in range(0, len(crypto_ids), 100):
        batch = crypto_ids[index:index + 100]
        try:
            crypto_info_pages.append(api_get("/v2/cryptocurrency/info", {"id": ",".join(batch), "skip_invalid": "true"}, key))
        except HTTPError as exc:
            if exc.code != 400:
                raise
            # CMC rejects a batch made entirely of unknown/retired IDs even
            # with skip_invalid. Split only that failing batch and retain the
            # unresolved IDs in the receipt instead of hiding the gap.
            for crypto_id in batch:
                try:
                    crypto_info_pages.append(api_get("/v2/cryptocurrency/info", {"id": crypto_id, "skip_invalid": "true"}, key))
                except HTTPError as item_error:
                    if item_error.code != 400:
                        raise
                    crypto_info_invalid_ids.append(crypto_id)
    issuer_pages = []
    for start in range(1, 10001, 250):
        page = api_get("/v5/real-world-assets/issuers/list", {"start": start, "limit": 250}, key)
        issuer_pages.append(page)
        if not page.get("data", {}).get("has_more"):
            break
    info_rows = records({"data": {"rwa_assets": sum((records(page) for page in info_pages), [])}})
    quote_rows = records({"data": {"rwa_assets": sum((records(page) for page in quote_pages), [])}})
    issuer_rows = [issuer for page in issuer_pages for issuer in (page.get("data", {}).get("issuers", []) if isinstance(page.get("data", {}).get("issuers", []), list) else [])]
    crypto_info_rows = {str(crypto_id): item for page in crypto_info_pages for crypto_id, item in (page.get("data", {}) if isinstance(page.get("data", {}), dict) else {}).items() if isinstance(item, dict)}
    return (
        {"data": {"rwa_assets": map_rows}},
        {"data": {"rwa_assets": list_rows}},
        {"data": {"rwa_assets": quote_rows}},
        {"data": {"rwa_assets": info_rows}},
        {"data": {"issuers": issuer_rows}},
        {"data": crypto_info_rows, "unresolved_ids": sorted(set(crypto_info_invalid_ids))},
    )


def token_summary(token: dict, issuer_lookup: dict | None = None, crypto_lookup: dict | None = None) -> dict:
    summary = {key: token.get(key) for key in ("crypto_id", "symbol", "name", "asset_type", "token_type", "category", "is_derivative", "issuer_id", "issuer_name", "price", "market_cap", "volume_24h")}
    issuer = (issuer_lookup or {}).get(str(token.get("issuer_id")), {})
    crypto = (crypto_lookup or {}).get(str(token.get("crypto_id")), {})
    summary["issuer_website"] = issuer.get("website")
    summary["issuer_catalogue_name"] = issuer.get("name")
    summary["crypto_slug"] = crypto.get("slug")
    summary["cmc_url"] = f"https://coinmarketcap.com/currencies/{crypto['slug']}/" if crypto.get("slug") else None
    urls = crypto.get("urls") or {}
    summary["project_url"] = (urls.get("website") or [None])[0] if isinstance(urls.get("website"), list) else None
    summary["explorer_urls"] = [url for url in (urls.get("explorer") or []) if isinstance(url, str) and url]
    summary["technical_doc_urls"] = [url for url in (urls.get("technical_doc") or []) if isinstance(url, str) and url]
    summary["platforms"] = [
        {
            "name": (entry.get("platform") or {}).get("name"),
            "slug": (entry.get("platform") or {}).get("coin", {}).get("slug"),
            "contract_address": entry.get("contract_address"),
        }
        for entry in (crypto.get("contract_address") or [])
        if isinstance(entry, dict) and isinstance(entry.get("platform"), dict)
    ]
    summary["crypto_info_resolved"] = bool(crypto)
    return summary


def index_evidence(evidence: dict) -> dict:
    """Keep enough numerical evidence in the population index for triage."""
    compact = {}
    for key in ("max_min_ratio", "count", "prices", "symbols", "derivatives", "other"):
        if key in evidence:
            compact[key] = evidence[key]
    if isinstance(evidence.get("tokens"), list):
        compact["tokens"] = [
            {key: token.get(key) for key in ("crypto_id", "symbol", "name", "price", "market_cap", "volume_24h")}
            if isinstance(token, dict) else token
            for token in evidence["tokens"]
        ]
    return compact


def asset_scan(asset: dict, issuer_lookup: dict | None = None, crypto_lookup: dict | None = None, crypto_info_checked: bool = False) -> dict:
    tokens = [token_summary(token, issuer_lookup, crypto_lookup) for token in asset.get("tokens", []) if isinstance(token, dict)]
    prices = [number(token.get("price")) for token in tokens]
    prices = [price for price in prices if price is not None and price > 0]
    ratio = max(prices) / min(prices) if prices else None
    symbols = [token.get("symbol") for token in tokens if token.get("symbol")]
    symbol_counts = Counter(symbols)
    repeated_symbols = sorted(symbol for symbol, count in symbol_counts.items() if count > 1)
    zero_mcap_volume = [token for token in tokens if number(token.get("market_cap")) == 0 and (number(token.get("volume_24h")) or 0) > 0]
    missing_fields = [token.get("symbol") or token.get("crypto_id") for token in tokens if any(token.get(key) is None for key in ("price", "market_cap", "volume_24h"))]
    missing_crypto_info = [token.get("crypto_id") for token in tokens if crypto_info_checked and token.get("crypto_id") is not None and token.get("crypto_info_resolved") is not True]
    derivative_tokens = [token for token in tokens if token.get("is_derivative") is True or any("derivative" in str(token.get(key) or "").lower() for key in ("name", "asset_type", "token_type", "category"))]
    non_derivative_tokens = [token for token in tokens if token not in derivative_tokens]
    signals = []

    def add(code: str, severity: str, message: str, evidence: dict):
        signals.append({"code": code, "severity": severity, "message": message, "evidence": evidence})

    if ratio is not None and ratio >= 10:
        add("PRICE_DENOMINATION_BREAK", "critical", "Token prices span at least 10x inside one CMC reference; comparison may be a unit or claim mismatch.", {"max_min_ratio": float(ratio), "prices": [float(price) for price in prices]})
    elif ratio is not None and ratio >= 2:
        add("PRICE_DISPERSION", "warning", "Token prices span at least 2x inside one CMC reference; resolve units and claim type before ranking.", {"max_min_ratio": float(ratio), "prices": [float(price) for price in prices]})
    if zero_mcap_volume:
        add("ZERO_MCAP_POSITIVE_VOLUME", "critical", "At least one representation reports positive 24h volume with zero market cap.", {"tokens": zero_mcap_volume})
    if derivative_tokens and non_derivative_tokens:
        add("DERIVATIVE_MIX", "warning", "Derivative-labelled and non-derivative representations are grouped under one reference.", {"derivatives": [token.get("symbol") for token in derivative_tokens], "other": [token.get("symbol") for token in non_derivative_tokens]})
    if repeated_symbols:
        add("SYMBOL_COLLISION", "warning", "A ticker is reused by multiple representations; symbol is not a safe identity key.", {"symbols": repeated_symbols})
    if missing_fields:
        add("MARKET_FIELDS_MISSING", "warning", "One or more token representations are missing price, market cap or volume.", {"tokens": missing_fields, "count": len(missing_fields)})
    if missing_crypto_info:
        add("TOKEN_INFO_MISSING", "warning", "One or more crypto IDs could not be resolved through CMC cryptocurrency/info; chain and contract identity remains incomplete.", {"tokens": missing_crypto_info, "count": len(missing_crypto_info)})
    if not asset.get("tradfi_markets"):
        add("NO_TRADFI_MARKET", "info", "No tracked TradFi market was returned for this reference.", {})
    state = "do_not_compare" if any(signal["severity"] == "critical" for signal in signals) else "investigate" if any(signal["severity"] == "warning" for signal in signals) else "no_flags"
    if any(signal["code"] == "PRICE_DENOMINATION_BREAK" for signal in signals):
        next_action = "Resolve unit, wrapper claim and quote identity before comparing prices."
    elif any(signal["code"] == "ZERO_MCAP_POSITIVE_VOLUME" for signal in signals):
        next_action = "Verify the token quote by crypto_id; do not turn volume into an investable market claim."
    elif any(signal["code"] == "DERIVATIVE_MIX" for signal in signals):
        next_action = "Split derivative-labelled representations from spot or wrapper representations."
    elif any(signal["code"] == "MARKET_FIELDS_MISSING" for signal in signals):
        next_action = "Keep nulls visible and re-check the missing token fields before ranking."
    elif any(signal["code"] == "TOKEN_INFO_MISSING" for signal in signals):
        next_action = "Resolve the crypto_id through CMC cryptocurrency/info before relying on chain or contract identity."
    elif any(signal["code"] == "SYMBOL_COLLISION" for signal in signals):
        next_action = "Join on crypto_id and issuer_id, never on the ticker alone."
    else:
        next_action = "No rule hit in this scan; this is not proof of backing, liquidity or eligibility."
    if state == "do_not_compare":
        decision = {
            "state": "blocked",
            "label": "DO NOT SELECT A WRAPPER",
            "consequence": "A research desk must not rank or substitute these representations until the contradiction is resolved.",
            "allocation_effect": "NO WRAPPER SELECTED until identity, denomination and market state are cleared.",
        }
    elif state == "investigate":
        decision = {
            "state": "hold",
            "label": "HOLD COMPARISON",
            "consequence": "Keep issuer comparison open, but do not treat the current rows as equivalent exposure.",
            "allocation_effect": "NO EQUIVALENCE CLAIM published while the investigation is open.",
        }
    else:
        decision = {
            "state": "unresolved",
            "label": "NO RULE HIT, NOT APPROVED",
            "consequence": "The published rules did not fire; backing, liquidity and legal diligence are still outside this monitor.",
            "allocation_effect": "No allocation status is produced by this monitor.",
        }
    return {
        "rwa_id": asset.get("rwa_id"),
        "name": asset.get("name"),
        "symbol": asset.get("symbol"),
        "asset_type": asset.get("asset_type"),
        "token_count": len(tokens),
        "issuer_count": len({token.get("issuer_id") for token in tokens if token.get("issuer_id")}),
        "state": state,
        "signals": signals,
        "next_action": next_action,
        "decision": decision,
        "tokens": tokens,
        "tradfi_market_count": len(asset.get("tradfi_markets") or []),
    }


def scan(map_payload: dict, list_payload: dict, quotes_payload: dict, info_payload: dict | None = None, issuers_payload: dict | None = None, observed_at: str | None = None, crypto_info_payload: dict | None = None) -> dict:
    required_surfaces = {"map": map_payload, "asset_list": list_payload, "quotes": quotes_payload}
    input_issues = [name for name, payload in required_surfaces.items() if not surface_has_records(payload)]
    scan_status = "incomplete" if input_issues else "ready"
    map_rows = records(map_payload)
    list_rows = records(list_payload)
    quote_rows = records(quotes_payload)
    info_rows = records(info_payload or {})
    issuer_data = (issuers_payload or {}).get("data", {})
    issuer_rows = issuer_data.get("issuers", []) if isinstance(issuer_data.get("issuers", []), list) else []
    crypto_data = (crypto_info_payload or {}).get("data", {})
    crypto_rows = [item for item in crypto_data.values() if isinstance(item, dict)] if isinstance(crypto_data, dict) else []
    crypto_invalid_ids = [str(value) for value in (crypto_info_payload or {}).get("unresolved_ids", [])]
    map_ids = {row.get("rwa_id") for row in map_rows if row.get("rwa_id") is not None}
    list_ids = [row.get("rwa_id") for row in list_rows if row.get("rwa_id") is not None]
    id_counts = Counter(list_ids)
    missing_id_rows = [row for row in list_rows if row.get("rwa_id") is None]
    duplicate_ids = {str(rwa_id): count for rwa_id, count in id_counts.items() if count > 1}
    issuer_catalogue = [
        {
            key: issuer.get(key)
            for key in ("issuer_id", "name", "website", "num_tokens", "total_size")
        }
        for issuer in issuer_rows
        if issuer.get("issuer_id") is not None
    ]
    issuer_lookup = {str(issuer["issuer_id"]): issuer for issuer in issuer_catalogue}
    crypto_lookup = {str(item.get("id")): item for item in crypto_rows if item.get("id") is not None}
    assets = [asset_scan(asset, issuer_lookup, crypto_lookup, crypto_info_checked=crypto_info_payload is not None) for asset in quote_rows]
    tokenized_map_ids = {row.get("rwa_id") for row in map_rows if row.get("has_tokens") is True and row.get("rwa_id") is not None}
    info_ids = {row.get("rwa_id") for row in info_rows if row.get("rwa_id") is not None}
    issuer_ids = {row.get("issuer_id") for row in issuer_rows if row.get("issuer_id") is not None}
    quote_issuer_ids = {token.get("issuer_id") for asset in assets for token in asset["tokens"] if token.get("issuer_id")}
    quote_crypto_ids = {str(token.get("crypto_id")) for asset in assets for token in asset["tokens"] if token.get("crypto_id") is not None}
    signal_counts = Counter(signal["code"] for asset in assets for signal in asset["signals"])
    critical = [asset for asset in assets if asset["state"] == "do_not_compare"]
    warnings = [asset for asset in assets if asset["state"] == "investigate"]
    alerts = sorted(
        assets,
        key=lambda asset: (
            -sum(1 for signal in asset["signals"] if signal["severity"] == "critical"),
            -sum(1 for signal in asset["signals"] if signal["severity"] == "warning"),
            -asset["token_count"],
            asset["name"] or "",
        ),
    )
    alert_index = [
        {
            "rwa_id": asset["rwa_id"],
            "name": asset["name"],
            "symbol": asset["symbol"],
            "asset_type": asset["asset_type"],
            "state": asset["state"],
            "token_count": asset["token_count"],
            "issuer_count": asset["issuer_count"],
            "signal_codes": [signal["code"] for signal in asset["signals"]],
            "signal_severities": [signal["severity"] for signal in asset["signals"]],
            "signal_evidence": {signal["code"]: index_evidence(signal.get("evidence") or {}) for signal in asset["signals"]},
            # Keep the shortlist usable for every reference, not only the 50
            # expanded alert rows. These are CMC observations, not diligence
            # or approval, and deliberately exclude issuer/legal documents.
            "representations": asset["tokens"],
            "next_action": asset["next_action"],
            "decision": asset["decision"],
        }
        for asset in alerts
    ]
    return {
        "schema_version": "rwa_surface_integrity.v1",
        "observed_at": observed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "question": "Can CMC's RWA surfaces be joined into a trustworthy comparison without resolving identity, unit and market-data contradictions?",
        "method": {
            "map": "/v5/real-world-assets/map",
            "asset_list": "/v5/real-world-assets/assets/list",
            "quotes": "/v5/real-world-assets/quotes/latest",
            "info": "/v5/real-world-assets/info",
            "issuers": "/v5/real-world-assets/issuers/list",
            "crypto_info": "/v2/cryptocurrency/info",
            "market_pairs": "not called in Startup scan; CMC documents this endpoint for Growth and above",
            "join_key": "rwa_id",
            "token_join_key": "crypto_id",
            "refresh_profiles": {
                "map": "30 seconds",
                "asset_list": "60 seconds",
                "quotes": "60 seconds",
            },
            "surface_drift_note": "The endpoints have separate update and caching cadences. A row without rwa_id is unjoinable in this run; it is not, by itself, proof of a CMC defect.",
            "rules": ["10x price spread is a critical denomination break", "positive volume with zero market cap is a critical market contradiction", "derivative mixing, symbol collision, missing fields and missing token identity require investigation", "never join by ticker when crypto_id or issuer_id exists"],
            "scan_status": scan_status,
            "input_integrity": {
                "required_surfaces": list(required_surfaces),
                "invalid_or_missing_surfaces": input_issues,
                "decision_note": "Incomplete input is not a clean scan and must not be published as no rule hit." if input_issues else "Required RWA surfaces have the expected list shape.",
            },
        },
        "catalogue_integrity": {
            "map_rows": len(map_rows),
            "map_unique_ids": len(map_ids),
            "asset_list_rows": len(list_rows),
            "asset_list_unique_ids": len(id_counts),
            "asset_list_rows_without_rwa_id": len(missing_id_rows),
            "asset_list_duplicate_ids": duplicate_ids,
            "map_ids_not_in_asset_list": sorted(map_ids - set(list_ids)),
            "asset_list_ids_not_in_map": sorted(set(list_ids) - map_ids),
            "unaddressable_examples": [{key: row.get(key) for key in ("name", "symbol", "slug", "asset_type", "rwa_rank")} for row in missing_id_rows[:12]],
        },
        "identity_integrity": {
            "tokenised_map_ids": len(tokenized_map_ids),
            "info_rows": len(info_rows),
            "info_unique_ids": len(info_ids),
            "tokenised_ids_missing_info": sorted(tokenized_map_ids - info_ids),
            "issuer_catalogue_rows": len(issuer_rows),
            "quote_issuer_ids": len(quote_issuer_ids),
            "quote_issuer_ids_missing_from_catalogue": sorted(quote_issuer_ids - issuer_ids),
            "crypto_info_rows": len(crypto_rows),
            "quote_crypto_ids": len(quote_crypto_ids),
            "quote_crypto_ids_missing_from_info": sorted(quote_crypto_ids - set(crypto_lookup)),
            "crypto_info_invalid_ids": crypto_invalid_ids,
        },
        "universe": {
            "tokenised_references_scanned": len(quote_rows),
            "tokens_scanned": sum(asset["token_count"] for asset in assets),
            "states": {"do_not_compare": len(critical), "investigate": len(warnings), "no_flags": len(assets) - len(critical) - len(warnings)},
            "signals": dict(signal_counts),
        },
        "alert_index": alert_index,
        "alerts": alerts[:50],
        "issuer_catalogue": issuer_catalogue,
        "source_hashes": {"map": digest(map_payload), "asset_list": digest(list_payload), "quotes": digest(quotes_payload), "info": digest(info_payload or {}), "issuers": digest(issuers_payload or {}), "crypto_info": digest(crypto_info_payload or {})},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan CoinMarketCap RWA surfaces for join and comparability breaks")
    parser.add_argument("--map", dest="map_path", type=Path, help="credential-free map response JSON")
    parser.add_argument("--list", dest="list_path", type=Path, help="credential-free assets/list response JSON")
    parser.add_argument("--quotes", dest="quotes_path", type=Path, help="credential-free quotes response JSON")
    parser.add_argument("--info", dest="info_path", type=Path, help="credential-free info response JSON")
    parser.add_argument("--issuers", dest="issuers_path", type=Path, help="credential-free issuers/list response JSON")
    parser.add_argument("--crypto-info", dest="crypto_info_path", type=Path, help="credential-free cryptocurrency/info response JSON")
    parser.add_argument("--live", action="store_true", help="fetch the map, asset list and all tokenised quotes with CMC_API_KEY")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.live:
        key = os.environ.get("CMC_API_KEY")
        if not key:
            parser.error("--live requires CMC_API_KEY in the process environment")
        map_payload, list_payload, quotes_payload, info_payload, issuers_payload, crypto_info_payload = collect_live(key)
    elif args.map_path and args.list_path and args.quotes_path:
        map_payload = json.loads(args.map_path.read_text(encoding="utf-8"))
        list_payload = json.loads(args.list_path.read_text(encoding="utf-8"))
        quotes_payload = json.loads(args.quotes_path.read_text(encoding="utf-8"))
        info_payload = json.loads(args.info_path.read_text(encoding="utf-8")) if args.info_path else {}
        issuers_payload = json.loads(args.issuers_path.read_text(encoding="utf-8")) if args.issuers_path else {}
        crypto_info_payload = json.loads(args.crypto_info_path.read_text(encoding="utf-8")) if args.crypto_info_path else {}
    else:
        parser.error("provide --live or all three replay payloads")
    result = scan(map_payload, list_payload, quotes_payload, info_payload, issuers_payload, crypto_info_payload=crypto_info_payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "universe": result["universe"], "catalogue_integrity": result["catalogue_integrity"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

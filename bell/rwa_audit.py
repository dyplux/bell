#!/usr/bin/env python3
"""CMC RWA comparability and integrity audit.

This module deliberately separates evidence collection from deterministic findings.
The LLM-facing layer can explain a finding later, but it must not invent the
underlying observations or the rule that produced the conclusion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from bell import BellDataError, CMCClient
from cmc_shapes import payload_data as _payload_data, records as _records


MAX_DEX_TOKEN_PROBES = 20



def _first_record(response: dict[str, Any], *keys: str) -> dict[str, Any]:
    records = _records(_payload_data(response), *keys)
    return records[0] if records else {}


def _unique(values: list[Any]) -> list[Any]:
    return list(dict.fromkeys(value for value in values if value is not None))


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalise_token(token: dict[str, Any]) -> dict[str, Any]:
    return {
        key: token.get(key)
        for key in (
            "crypto_id",
            "name",
            "symbol",
            "issuer_id",
            "issuer_name",
            "price",
            "market_cap",
            "volume_24h",
        )
    }


def _normalise_market_pair(pair: dict[str, Any]) -> dict[str, Any]:
    exchange = pair.get("exchange") if isinstance(pair.get("exchange"), dict) else {}
    base = pair.get("market_pair_base") if isinstance(pair.get("market_pair_base"), dict) else {}
    quote = pair.get("market_pair_quote") if isinstance(pair.get("market_pair_quote"), dict) else {}
    reported = pair.get("exchange_reported_quotes")
    reported_quote = reported[0] if isinstance(reported, list) and reported and isinstance(reported[0], dict) else {}
    converted = pair.get("quotes")
    converted_quote = converted[0] if isinstance(converted, list) and converted and isinstance(converted[0], dict) else {}
    return {
        "market_id": pair.get("market_id"),
        "exchange": exchange.get("name"),
        "exchange_id": exchange.get("exchange_id"),
        "market_pair": pair.get("market_pair"),
        "category": pair.get("category"),
        "fee_type": pair.get("fee_type"),
        "base": {key: base.get(key) for key in ("crypto_id", "symbol", "exchange_symbol", "currency_type")},
        "quote": {key: quote.get(key) for key in ("crypto_id", "symbol", "exchange_symbol", "currency_type")},
        "reported": {
            key: reported_quote.get(key)
            for key in ("symbol", "price", "volume_24h_base", "volume_24h_quote", "last_updated")
        },
        "converted": {
            key: converted_quote.get(key)
            for key in ("symbol", "price", "volume_24h", "last_updated")
        },
    }


def _normalise_issuer(response: dict[str, Any]) -> dict[str, Any]:
    issuer = _first_record(response)
    return {
        key: issuer.get(key)
        for key in ("issuer_id", "name", "website", "logo", "num_tokens", "total_size", "has_more")
    } | {
        "tokens": [
            {key: token.get(key) for key in ("name", "symbol", "crypto_id", "rwa_id")}
            for token in _records(issuer.get("tokens"), "tokens")
        ]
    }


def _normalise_crypto_info(response: dict[str, Any]) -> list[dict[str, Any]]:
    records = _records(_payload_data(response))
    result = []
    for crypto in records:
        urls = crypto.get("urls") if isinstance(crypto.get("urls"), dict) else {}
        platform = crypto.get("platform") if isinstance(crypto.get("platform"), dict) else None
        result.append(
            {
                "id": crypto.get("id"),
                "name": crypto.get("name"),
                "symbol": crypto.get("symbol"),
                "slug": crypto.get("slug"),
                "description": crypto.get("description"),
                "category": crypto.get("category"),
                "platform": {
                    key: platform.get(key)
                    for key in ("id", "name", "symbol", "slug", "token_address")
                } if platform else None,
                "contract_address": platform.get("token_address") if platform else crypto.get("contract_address"),
                "tags": crypto.get("tags") if isinstance(crypto.get("tags"), list) else [],
                "website": (urls.get("website") or [None])[0] if isinstance(urls.get("website"), list) else None,
            }
        )
    return result


def _dex_platform(info: dict[str, Any]) -> str | None:
    platform = info.get("platform") if isinstance(info.get("platform"), dict) else {}
    value = platform.get("slug") or platform.get("name") or platform.get("symbol")
    if not value:
        return None
    return str(value).strip().lower().replace(" ", "-")


def _normalise_dex_leg(leg: Any) -> dict[str, Any]:
    if not isinstance(leg, dict):
        return {}
    return {
        "address": leg.get("addr"),
        "name": leg.get("n"),
        "symbol": leg.get("sym"),
        "liquidity": leg.get("liq"),
        "liquidity_usd": leg.get("liqUsd"),
    }


def _normalise_dex_detail(response: dict[str, Any]) -> dict[str, Any]:
    record = _first_record(response)
    return {
        "name": record.get("n"),
        "symbol": record.get("sym"),
        "address": record.get("addr"),
        "platform": record.get("plt"),
        "price": record.get("p"),
        "price_change_24h": record.get("pl24h"),
        "volume_24h": record.get("v24h"),
        "market_cap": record.get("mcap"),
        "liquidity_usd": record.get("liqUsd"),
        "holders": record.get("hld"),
        "pool_count": record.get("nps"),
        "primary_dex": record.get("pdex"),
    }


def _normalise_dex_price(response: dict[str, Any]) -> dict[str, Any]:
    record = _first_record(response)
    return {
        "price": record.get("p"),
        "price_change_24h": record.get("pc24h"),
        "volume_24h": record.get("v24h"),
        "market_cap": record.get("mc"),
        "liquidity_usd": record.get("l"),
        "primary_dex": record.get("pdex"),
        "timestamp": record.get("ts"),
    }


def _normalise_dex_pool(pool: dict[str, Any]) -> dict[str, Any]:
    return {
        "address": pool.get("addr"),
        "exchange": pool.get("exn"),
        "exchange_id": pool.get("exid"),
        "factory_address": pool.get("fa"),
        "liquidity_usd": pool.get("liqUsd"),
        "volume_24h": pool.get("v24"),
        "published_at": pool.get("pubAt"),
        "is_top": pool.get("top"),
        "is_multichain": pool.get("mi"),
        "base": _normalise_dex_leg(pool.get("t0")),
        "quote": _normalise_dex_leg(pool.get("t1")),
    }


def _normalise_dex_security(response: dict[str, Any]) -> dict[str, Any]:
    record = _first_record(response)
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    items = record.get("securityItems") if isinstance(record.get("securityItems"), list) else []
    return {
        "platform": record.get("platformName"),
        "address": record.get("tokenContractAddress"),
        "security_level": record.get("securityLevel"),
        "category_level": record.get("categoryLevel"),
        "buy_tax": extra.get("buyTax"),
        "sell_tax": extra.get("sellTax"),
        "source": extra.get("source"),
        "tags": record.get("tags") if isinstance(record.get("tags"), list) else [],
        "security_item_count": len(items),
        "hit_count": sum(1 for item in items if isinstance(item, dict) and item.get("isHit")),
    }


def _normalise_dex_holders(response: dict[str, Any]) -> dict[str, Any]:
    record = _first_record(response)
    return {
        "count": record.get("count"),
        "platform_id": record.get("platformId"),
        "address": record.get("tokenAddress"),
    }


def _normalise_dex_holder_tags(response: dict[str, Any]) -> dict[str, Any]:
    data = _payload_data(response)
    record = data if isinstance(data, dict) else {}
    return {
        "platform_id": record.get("platformId"),
        "address": record.get("tokenAddress"),
        "tags": [
            {
                "tag": item.get("tag"),
                "holder_count": item.get("hc"),
                "token_balance": item.get("tb"),
                "holder_ratio": item.get("hr"),
            }
            for item in _records(record.get("holders"), "holders")
        ],
    }


def _collect_dex_evidence(
    client: CMCClient,
    tokens: list[dict[str, Any]],
    crypto_info: list[dict[str, Any]],
) -> dict[str, Any]:
    """Probe the DEX surfaces for every resolvable wrapper in the dossier.

    DEX endpoints are optional enrichment. A wrapper without a platform or
    contract is recorded as ``no_contract``; a contract that the DEX surface
    cannot resolve is recorded as ``unavailable``. Neither state is silently
    converted into zero liquidity, zero holders or an empty market.
    """

    crypto_by_id = {str(item.get("id")): item for item in crypto_info if item.get("id") is not None}
    rows: list[dict[str, Any]] = []
    for token in tokens[:MAX_DEX_TOKEN_PROBES]:
        info = crypto_by_id.get(str(token.get("crypto_id")), {})
        platform = _dex_platform(info)
        contract = info.get("contract_address")
        row: dict[str, Any] = {
            "crypto_id": token.get("crypto_id"),
            "symbol": token.get("symbol"),
            "name": token.get("name"),
            "network": platform,
            "contract_address": contract,
            "state": "no_contract" if not platform or not contract else "unavailable",
            "surfaces": [],
            "errors": [],
            "detail": {},
            "price": {},
            "pools": [],
            "security": {},
            "holders": {},
            "holder_tags": {},
        }
        if not platform or not contract:
            rows.append(row)
            continue

        requests = (
            ("detail", "/v1/dex/token", {"platform": platform, "address": contract}, _normalise_dex_detail),
            ("price", "/v1/dex/token/price", {"platform": platform, "address": contract}, _normalise_dex_price),
            ("pools", "/v1/dex/token/pools", {"platform": platform, "address": contract, "size": 3}, None),
            ("security", "/v1/dex/security/detail", {"platformName": platform, "address": contract}, _normalise_dex_security),
            ("holders", "/v1/dex/holders/count", {"platform": platform, "tokenAddress": contract}, _normalise_dex_holders),
            ("holder_tags", "/v1/dex/holders/tag_count", {"platform": platform, "tokenAddress": contract}, _normalise_dex_holder_tags),
        )
        for surface, endpoint, params, normaliser in requests:
            try:
                response = client.get(endpoint, params)
                if surface == "pools":
                    records = _records(_payload_data(response), "pools", "data")
                    row["pools"] = [_normalise_dex_pool(pool) for pool in records]
                    if row["pools"]:
                        row["surfaces"].append(surface)
                else:
                    value = normaliser(response) if normaliser else {}
                    row[surface] = value
                    if value:
                        row["surfaces"].append(surface)
            except BellDataError as exc:
                row["errors"].append({"surface": surface, "error": str(exc)})
        if row["surfaces"]:
            row["state"] = "available"
        rows.append(row)
    omitted_count = max(0, len(tokens) - len(rows))
    contract_rows = [row for row in rows if row.get("contract_address")]
    return {
        "schema_version": "bell.rwa.dex.evidence.v1",
        "tokens": rows,
        "requested_token_count": len(tokens),
        "probed_token_count": len(rows),
        "omitted_token_count": omitted_count,
        "contract_token_count": len(contract_rows),
        "covered_token_count": sum(row.get("state") == "available" for row in rows),
        "unavailable_token_count": sum(row.get("state") == "unavailable" for row in rows),
        "no_contract_token_count": sum(row.get("state") == "no_contract" for row in rows),
        "surface_counts": {
            surface: sum(surface in row.get("surfaces", []) for row in rows)
            for surface in ("detail", "price", "pools", "security", "holders", "holder_tags")
        },
        "coverage_limited": omitted_count > 0,
    }


def collect_rwa_evidence(client: CMCClient, asset_slug: str) -> dict[str, Any]:
    """Collect the RWA evidence needed for an integrity audit.

    The calls intentionally use stable identifiers returned by the RWA quotes
    response. A missing optional resource is recorded as an error in provenance
    rather than silently converted into an empty observation.
    """

    observed_at = datetime.now(timezone.utc).isoformat()
    quotes_response = client.get(
        "/v5/real-world-assets/quotes/latest",
        {"rwa_slug": asset_slug, "convert": "USD"},
    )
    asset = _first_record(quotes_response, "rwa_assets", "assets")
    if not asset:
        raise BellDataError(f"CMC returned no RWA asset for {asset_slug}")

    info_response = client.get(
        "/v5/real-world-assets/info",
        {"rwa_slug": asset_slug},
    )
    info = _first_record(info_response, "rwa_assets", "assets")

    market_pairs_error: str | None = None
    try:
        pair_response = client.get(
            "/v5/real-world-assets/market-pairs/list",
            {"rwa_slug": asset_slug, "convert": "USD"},
        )
        pair_data = _payload_data(pair_response)
        pairs = _records(pair_data, "market_pairs", "markets")
        if not pairs and isinstance(pair_data, dict):
            pairs = _records(pair_data.get("data"), "market_pairs", "markets")
    except BellDataError as exc:
        pairs = []
        market_pairs_error = str(exc)

    tokens = [_normalise_token(token) for token in _records(asset.get("tokens"), "tokens")]
    issuer_ids = _unique([token.get("issuer_id") for token in tokens])
    issuers: list[dict[str, Any]] = []
    for issuer_id in issuer_ids:
        try:
            issuer_response = client.get(
                "/v5/real-world-assets/issuers",
                {"issuer_id": issuer_id},
            )
            issuers.append(_normalise_issuer(issuer_response))
        except BellDataError as exc:
            issuers.append({"issuer_id": issuer_id, "error": str(exc), "tokens": []})

    crypto_ids = _unique([token.get("crypto_id") for token in tokens])
    crypto_info: list[dict[str, Any]] = []
    if crypto_ids:
        try:
            crypto_response = client.get(
                "/v2/cryptocurrency/info",
                {"id": ",".join(str(crypto_id) for crypto_id in crypto_ids)},
            )
            crypto_info = _normalise_crypto_info(crypto_response)
        except BellDataError as exc:
            crypto_info = [{"error": str(exc)}]

    dex_evidence = _collect_dex_evidence(client, tokens, crypto_info)
    optional_errors = []
    if market_pairs_error:
        optional_errors.append({"surface": "market_pairs", "error": market_pairs_error})
    dex_errors = sum(len(row.get("errors", [])) for row in dex_evidence["tokens"])
    if dex_errors:
        optional_errors.append({
            "surface": "dex",
            "error": f"{dex_errors} optional DEX request(s) failed; see dex_evidence.tokens[].errors",
        })

    return {
        "schema_version": "bell.rwa.audit.evidence.v1",
        "mode": "live_cmc",
        "observed_at": observed_at,
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
        "metadata": {
            key: info.get(key)
            for key in (
                "rwa_id",
                "name",
                "symbol",
                "slug",
                "asset_type",
                "website",
                "employees",
                "founded",
                "industry",
                "cik",
                "primary_exchange",
                "about",
            )
        },
        "tokens": tokens,
        "market_pairs": [_normalise_market_pair(pair) for pair in pairs],
        "market_pairs_error": market_pairs_error,
        "issuers": issuers,
        "crypto_info": crypto_info,
        "dex_evidence": dex_evidence,
        "provenance": {
            "source": "CoinMarketCap Pro API",
            "observed_at": observed_at,
            "endpoints": sorted({call["endpoint"] for call in client.calls}),
            "calls": client.calls,
            "optional_errors": optional_errors,
            "raw_responses_included": False,
        },
    }


def _finding(code: str, severity: str, message: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "evidence": evidence}


def audit_rwa_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Apply explainable, non-financial integrity rules to collected evidence."""

    tokens = [token for token in evidence.get("tokens", []) if isinstance(token, dict)]
    findings: list[dict[str, Any]] = []
    prices = [(token.get("symbol"), _number(token.get("price"))) for token in tokens]
    priced = [(symbol, price) for symbol, price in prices if price is not None and price > 0]
    if not tokens:
        findings.append(_finding("no_tokens", "critical", "No token representation was returned for this RWA.", {}))
    if tokens and not priced:
        findings.append(_finding("no_token_prices", "critical", "Token representations exist but no token price is available.", {"token_count": len(tokens)}))

    missing_issuer = [token.get("symbol") for token in tokens if not token.get("issuer_id") or not token.get("issuer_name")]
    if missing_issuer:
        findings.append(_finding("missing_issuer", "warning", "Some token representations have no tracked issuer identity.", {"symbols": missing_issuer}))

    duplicate_symbols: dict[str, list[str | None]] = defaultdict(list)
    for token in tokens:
        symbol = token.get("symbol")
        if symbol:
            duplicate_symbols[str(symbol)].append(token.get("issuer_name"))
    collisions = {symbol: issuers for symbol, issuers in duplicate_symbols.items() if len(issuers) > 1}
    if collisions:
        findings.append(_finding("symbol_collision", "warning", "The same ticker is used by multiple token issuers.", {"symbols": collisions}))

    if len(priced) >= 2:
        sorted_prices = sorted(price for _, price in priced)
        ratio = sorted_prices[-1] / sorted_prices[0] if sorted_prices[0] else None
        if ratio is not None and ratio >= 10:
            findings.append(_finding(
                "denomination_unresolved",
                "critical",
                "Token prices span at least 10x; unit or claim denomination must be resolved before comparing prices.",
                {"min_price": sorted_prices[0], "max_price": sorted_prices[-1], "price_ratio": round(ratio, 6)},
            ))

    volume_without_mcap = [
        token.get("symbol")
        for token in tokens
        if (_number(token.get("volume_24h")) or 0) > 0 and (_number(token.get("market_cap")) in (None, 0))
    ]
    if volume_without_mcap:
        findings.append(_finding(
            "volume_without_mcap",
            "warning",
            "A token reports positive 24h volume while market cap is missing or zero.",
            {"symbols": volume_without_mcap},
        ))

    market_pairs = [pair for pair in evidence.get("market_pairs", []) if isinstance(pair, dict)]
    derivative_pairs = [
        pair.get("market_pair")
        for pair in market_pairs
        if str(pair.get("category") or "").lower() in {"derivatives", "perpetual"}
    ]
    if derivative_pairs:
        findings.append(_finding(
            "derivative_markets_present",
            "warning",
            "Derivative or perpetual markets are present and must not be compared as spot representations without qualification.",
            {"pairs": derivative_pairs},
        ))
    if not market_pairs:
        if evidence.get("market_pairs_error"):
            findings.append(_finding(
                "market_pairs_unavailable",
                "warning",
                "The CMC market-pair surface is unavailable for this API plan; this is not evidence that the RWA has no market.",
                {"error": evidence.get("market_pairs_error")},
            ))
        else:
            findings.append(_finding("no_market_pairs", "warning", "No active market pair was returned for this RWA.", {}))

    dex = evidence.get("dex_evidence") if isinstance(evidence.get("dex_evidence"), dict) else {}
    contract_count = int(dex.get("contract_token_count") or 0)
    covered_count = int(dex.get("covered_token_count") or 0)
    if contract_count and covered_count < contract_count:
        findings.append(_finding(
            "dex_coverage_partial",
            "warning",
            "DEX evidence was resolved for only part of the token wrappers with a contract address.",
            {
                "covered_token_count": covered_count,
                "contract_token_count": contract_count,
                "unavailable_token_count": dex.get("unavailable_token_count", 0),
                "no_contract_token_count": dex.get("no_contract_token_count", 0),
            },
        ))

    metadata_signals = []
    for token in tokens:
        label = f"{token.get('name') or ''} {token.get('symbol') or ''}".lower()
        if any(signal in label for signal in ("gram", "wrapped", "derivative", "synthetic")):
            metadata_signals.append({"symbol": token.get("symbol"), "signals": [signal for signal in ("gram", "wrapped", "derivative", "synthetic") if signal in label]})
    if metadata_signals:
        findings.append(_finding(
            "representation_signals",
            "warning",
            "Token names contain representation signals that require separate comparability treatment.",
            {"tokens": metadata_signals},
        ))

    critical = any(item["severity"] == "critical" for item in findings)
    warning = any(item["severity"] == "warning" for item in findings)
    if not tokens or not priced:
        conclusion = "insufficient_evidence"
    elif critical:
        conclusion = "do_not_compare"
    elif warning:
        conclusion = "investigate"
    else:
        conclusion = "provisionally_comparable"
    return {
        "schema_version": "bell.rwa.audit.v1",
        "asset": evidence.get("asset", {}),
        "conclusion": conclusion,
        "findings": findings,
        "evidence": evidence,
    }


def run_live(asset_slug: str) -> dict[str, Any]:
    api_key = os.environ.get("CMC_API_KEY")
    if not api_key:
        raise BellDataError("live RWA audit requires CMC_API_KEY in the environment")
    evidence = collect_rwa_evidence(CMCClient(api_key), asset_slug)
    return audit_rwa_evidence(evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit one RWA's comparability using CMC evidence")
    parser.add_argument("--asset", default="tesla", help="CMC RWA slug")
    parser.add_argument("--output", type=Path, help="write the credential-free audit JSON")
    args = parser.parse_args(argv)
    try:
        result = run_live(args.asset)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (BellDataError, OSError, json.JSONDecodeError) as exc:
        print(f"bell-rwa-audit: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

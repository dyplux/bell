#!/usr/bin/env python3
"""Run Bell's public RWA decision rules against credential-free fixtures."""

from __future__ import annotations

import json
from typing import Any

from rwa_integrity import scan


def payloads(*tokens: dict[str, Any], tradfi_markets: list[dict[str, Any]] | None = None):
    base = {"data": {"rwa_assets": [{"rwa_id": 1, "name": "Boundary reference", "has_tokens": True}]}}
    quotes = {
        "data": {
            "rwa_assets": [{
                "rwa_id": 1,
                "name": "Boundary reference",
                "symbol": "BOUND",
                "tokens": list(tokens),
                "tradfi_markets": tradfi_markets or [],
            }]
        }
    }
    return base, base, quotes


def first(result: dict[str, Any]) -> dict[str, Any]:
    return result["alerts"][0]


def run() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    result = scan(*payloads(
        {"crypto_id": 1, "symbol": "LOW", "price": 1, "market_cap": 10, "volume_24h": 1},
        {"crypto_id": 2, "symbol": "HIGH", "price": 9.99, "market_cap": 10, "volume_24h": 1},
        tradfi_markets=[{}],
    ))
    codes = {signal["code"] for signal in first(result)["signals"]}
    checks.append({"name": "9.99x stays a warning", "pass": "PRICE_DISPERSION" in codes and "PRICE_DENOMINATION_BREAK" not in codes})

    result = scan(*payloads(
        {"crypto_id": 1, "symbol": "LOW", "price": 1, "market_cap": 10, "volume_24h": 1},
        {"crypto_id": 2, "symbol": "HIGH", "price": 10, "market_cap": 10, "volume_24h": 1},
    ))
    alert = first(result)
    checks.append({
        "name": "10x is an inclusive critical stop",
        "pass": "PRICE_DENOMINATION_BREAK" in {signal["code"] for signal in alert["signals"]}
        and alert["decision"]["label"] == "DO NOT SELECT A WRAPPER",
    })

    result = scan(*payloads(
        {"crypto_id": 1, "symbol": "ONLY", "price": 1, "market_cap": 10, "volume_24h": 1},
    ))
    alert = first(result)
    checks.append({
        "name": "single representation does not become a comparison",
        "pass": not {signal["code"] for signal in alert["signals"]}.intersection({"PRICE_DISPERSION", "PRICE_DENOMINATION_BREAK"})
        and alert["decision"]["label"] == "NO RULE HIT, NOT APPROVED",
    })

    base, listing, quotes = payloads(
        {"crypto_id": 12, "symbol": "WRAP", "price": 1, "market_cap": 10, "volume_24h": 1},
    )
    unresolved = scan(base, listing, quotes, crypto_info_payload={"data": {}, "unresolved_ids": ["12"]})
    unresolved_alert = first(unresolved)
    checks.append({
        "name": "unresolved crypto identity stays visible",
        "pass": "TOKEN_INFO_MISSING" in {signal["code"] for signal in unresolved_alert["signals"]}
        and unresolved["identity_integrity"]["quote_crypto_ids_missing_from_info"] == ["12"],
    })

    resolved = scan(
        base,
        listing,
        quotes,
        crypto_info_payload={
            "data": {"12": {
                "id": 12,
                "slug": "wrapper",
                "contract_address": [{
                    "contract_address": "0xabc",
                    "platform": {"name": "Ethereum", "coin": {"slug": "ethereum"}},
                }],
            }},
        },
    )
    resolved_token = first(resolved)["tokens"][0]
    checks.append({
        "name": "resolved crypto identity exposes chain and contract",
        "pass": resolved["identity_integrity"]["quote_crypto_ids_missing_from_info"] == []
        and resolved_token["platforms"][0]["contract_address"] == "0xabc"
        and resolved_token["crypto_info_resolved"] is True,
    })
    return checks


def main() -> int:
    checks = run()
    failed = [check for check in checks if not check["pass"]]
    print(json.dumps({"schema_version": "bell.rule_boundary_verifier.v1", "checks": checks, "status": "fail" if failed else "pass"}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Thirty-second human-readable path for the RWA Surface Integrity Monitor."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from rwa_integrity import collect_live, scan

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "docs/proof/rwa-surface-integrity-2026-09-15.json"


def receipt_hash(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def render(result: dict) -> str:
    universe = result["universe"]
    catalogue = result["catalogue_integrity"]
    identity = result.get("identity_integrity", {})
    signals = universe["signals"]
    lines = [
        "RWA SURFACE INTEGRITY MONITOR",
        "=" * 32,
        f"Observed: {result['observed_at']}",
        "",
        "Question:",
        result["question"],
        "",
        "Universe:",
        f"{universe['tokenised_references_scanned']:,} tokenised references · {universe['tokens_scanned']:,} token representations",
        f"{universe['states']['do_not_compare']:,} DO NOT COMPARE · {universe['states']['investigate']:,} INVESTIGATE · {universe['states']['no_flags']:,} no rule hit",
        "",
        "Surface drift:",
        f"map: {catalogue['map_rows']:,} rows / {catalogue['map_unique_ids']:,} stable IDs",
        f"assets/list: {catalogue['asset_list_rows']:,} rows / {catalogue['asset_list_unique_ids']:,} stable IDs",
        f"{catalogue['asset_list_rows_without_rwa_id']:,} rows cannot be joined by the documented stable RWA ID",
        "separate endpoint cadences: map 30s · assets/list 60s · quotes 60s",
        "",
        "Identity cross-check:",
        f"info: {identity.get('info_rows', 0):,} rows / {identity.get('info_unique_ids', 0):,} stable IDs",
        f"issuers: {identity.get('issuer_catalogue_rows', 0):,} listed · {identity.get('quote_issuer_ids', 0):,} seen in quotes · {len(identity.get('quote_issuer_ids_missing_from_catalogue', [])):,} missing",
        "",
        "Integrity breaks:",
        f"{signals.get('PRICE_DENOMINATION_BREAK', 0)} price groups over 10x",
        f"{signals.get('ZERO_MCAP_POSITIVE_VOLUME', 0)} groups with positive volume and zero market cap",
        f"{signals.get('DERIVATIVE_MIX', 0)} groups mixing derivative-labelled representations",
        f"{signals.get('SYMBOL_COLLISION', 0)} groups with repeated symbols across representations",
        "",
        "Top alerts:",
    ]
    for alert in result["alerts"][:3]:
        codes = ", ".join(signal["code"] for signal in alert["signals"] if signal["severity"] != "info")
        lines.append(f"{alert['name']} ({alert['symbol']}) · {alert['state'].upper()} · {codes}")
        lines.append(f"  effect: {alert.get('decision', {}).get('label', 'REVIEW')}")
        lines.append(f"  next: {alert['next_action']}")
    lines += [
        "",
        "Decision rule:",
        "Do not compare or rank wrappers until identity, denomination and market-data contradictions are resolved.",
        "",
        f"Receipt hash: {receipt_hash(result)}",
        "CMC fields are observations. This monitor does not prove backing, redemption, legal eligibility or executable liquidity.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the RWA Surface Integrity Monitor")
    parser.add_argument("--live", action="store_true", help="fetch current CMC RWA surfaces with CMC_API_KEY")
    parser.add_argument("--receipt", type=Path, default=FIXTURE, help="replay a saved integrity receipt")
    args = parser.parse_args()
    if args.live:
        import os
        key = os.environ.get("CMC_API_KEY")
        if not key:
            parser.error("--live requires CMC_API_KEY")
        map_payload, list_payload, quotes_payload, info_payload, issuers_payload = collect_live(key)
        result = scan(map_payload, list_payload, quotes_payload, info_payload, issuers_payload)
    else:
        result = json.loads(args.receipt.read_text(encoding="utf-8"))
    result.setdefault("read_at", datetime.now(timezone.utc).isoformat())
    print(render(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

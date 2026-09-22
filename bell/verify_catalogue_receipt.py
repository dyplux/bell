#!/usr/bin/env python3
"""Verify the public credential-free RWA catalogue and its refresh receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path("bell/site/catalog.json"))
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("bell/site/proof/rwa-catalogue-refresh-2026-09-22.json"),
    )
    args = parser.parse_args()

    catalog = load(args.catalog)
    receipt = load(args.receipt)
    assets = catalog.get("assets")
    if not isinstance(assets, list):
        raise ValueError("catalogue assets must be a list")
    if catalog.get("schema_version") != "bell.catalog.v1":
        raise ValueError("unexpected catalogue schema")
    if catalog.get("total_size") != len(assets):
        raise ValueError("catalogue total_size does not match asset count")
    if receipt.get("schema_version") != "bell.catalog.refresh.v1":
        raise ValueError("unexpected refresh receipt schema")

    digest = hashlib.sha256(args.catalog.read_bytes()).hexdigest()
    if digest != receipt.get("catalog_sha256"):
        raise ValueError("catalogue SHA-256 does not match refresh receipt")
    if catalog.get("observed_at") != receipt.get("observed_at"):
        raise ValueError("catalogue observation time does not match refresh receipt")

    types = dict(sorted(Counter(asset.get("asset_type") for asset in assets).items()))
    expected_types = receipt.get("asset_types")
    if types != expected_types:
        raise ValueError(f"asset type counts do not reconcile: {types} != {expected_types}")

    token_count = sum(bool(asset.get("has_tokens")) for asset in assets)
    if token_count != receipt.get("references_with_tokens"):
        raise ValueError("tokenised reference count does not reconcile")
    latest = max((asset.get("last_historical_data") or "") for asset in assets)
    if latest != receipt.get("latest_historical_data"):
        raise ValueError("latest historical-data timestamp does not reconcile")
    if receipt.get("all_calls_status_200") is not True or receipt.get("calls") != 79:
        raise ValueError("refresh call evidence is incomplete")

    print(json.dumps({
        "status": "ok",
        "catalog": str(args.catalog),
        "receipt": str(args.receipt),
        "references": len(assets),
        "asset_types": types,
        "references_with_tokens": token_count,
        "observed_at": catalog["observed_at"],
        "catalog_sha256": digest,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"CATALOGUE RECEIPT CHECK FAILED: {exc}")

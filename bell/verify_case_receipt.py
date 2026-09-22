#!/usr/bin/env python3
"""Verify a credential-free Bell case receipt exported by the public UI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version", "observed_at", "published_at", "source", "credential_free",
    "question", "reference", "decision", "next_action", "signals", "tokens",
    "method", "source_hashes", "limits",
}
REQUIRED_REFERENCE = {"rwa_id", "name", "symbol", "asset_type", "token_count", "issuer_count", "tradfi_market_count"}
REQUIRED_METHOD = {"join_key", "token_join_key", "rules"}


def verify(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("receipt must be a JSON object")
    missing = REQUIRED_TOP_LEVEL - payload.keys()
    if missing:
        raise ValueError(f"missing top-level fields: {', '.join(sorted(missing))}")
    if payload["schema_version"] != "bell.case-receipt.v1":
        raise ValueError("unsupported schema_version")
    if payload["source"] != "/api/integrity":
        raise ValueError("source must be /api/integrity")
    if payload["credential_free"] is not True:
        raise ValueError("receipt is not marked credential_free")
    if not isinstance(payload["question"], str) or not payload["question"].strip():
        raise ValueError("question must be a non-empty string")
    reference = payload["reference"]
    if not isinstance(reference, dict):
        raise ValueError("reference must be an object")
    missing_reference = REQUIRED_REFERENCE - reference.keys()
    if missing_reference:
        raise ValueError(f"missing reference fields: {', '.join(sorted(missing_reference))}")
    tokens = payload["tokens"]
    if not isinstance(tokens, list):
        raise ValueError("tokens must be an array")
    if not isinstance(payload["signals"], list):
        raise ValueError("signals must be an array")
    if not isinstance(payload["source_hashes"], dict):
        raise ValueError("source_hashes must be an object")
    if not isinstance(payload["limits"], list) or not payload["limits"]:
        raise ValueError("limits must be a non-empty array")
    method = payload["method"]
    if not isinstance(method, dict):
        raise ValueError("method must be an object")
    missing_method = REQUIRED_METHOD - method.keys()
    if missing_method:
        raise ValueError(f"missing method fields: {', '.join(sorted(missing_method))}")
    if method["join_key"] != "rwa_id":
        raise ValueError("method.join_key must be rwa_id")
    if method["token_join_key"] != "crypto_id":
        raise ValueError("method.token_join_key must be crypto_id")
    if not isinstance(method["rules"], list):
        raise ValueError("method.rules must be an array")
    token_count = reference["token_count"]
    if isinstance(token_count, bool) or not isinstance(token_count, int) or token_count < 1:
        raise ValueError("reference.token_count must be a positive integer")
    if len(tokens) != token_count:
        raise ValueError("reference.token_count does not match tokens length")
    return {
        "schema_version": payload["schema_version"],
        "reference": reference.get("name") or reference.get("symbol") or reference.get("rwa_id"),
        "decision": payload["decision"],
        "token_rows": len(tokens),
        "source_hashes": len(payload["source_hashes"]),
        "status": "valid public case receipt",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        with args.receipt.open(encoding="utf-8") as handle:
            result = verify(json.load(handle))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"case receipt verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check Bell's dated Alphabet pair review against its shipped CMC capture."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
REVIEW_PATH = SITE / "proof/alphabet-class-a-pair-review-2026-09-29.json"


def verify() -> dict[str, object]:
    review = json.loads(REVIEW_PATH.read_text())
    if review.get("schema_version") != "bell.pairwise-terms-review.v1":
        raise ValueError("unsupported pair review schema")
    if review.get("review_id") != "alphabet-class-a-googlx-googlon-2026-09-29":
        raise ValueError("unexpected review identity")

    observation = review.get("cmc_observation") or {}
    relative = observation.get("source")
    if not isinstance(relative, str) or Path(relative).name != relative:
        raise ValueError("CMC source must be a shipped proof filename")
    source_path = SITE / "proof" / relative
    if not source_path.is_file():
        raise ValueError(f"CMC source is not shipped: {relative}")
    source_bytes = source_path.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()
    if actual_hash != observation.get("sha256"):
        raise ValueError("CMC source SHA-256 does not match the pair review")

    capture = json.loads(source_bytes)
    if capture.get("observed_at") != observation.get("observed_at"):
        raise ValueError("CMC observation timestamp does not match the cited capture")
    ref_id = review.get("reference", {}).get("rwa_id")
    ref = next((row for row in capture.get("alert_index", [])
                if row.get("rwa_id") == ref_id), None)
    if ref is None:
        raise ValueError("review reference is absent from the cited CMC capture")

    routes = observation.get("routes")
    if not isinstance(routes, list) or [row.get("crypto_id") for row in routes] != [37013, 38001]:
        raise ValueError("pair must contain GOOGLX 37013 and GOOGLon 38001 in order")
    source_rows = {row.get("crypto_id"): row for row in ref.get("representations", [])}
    fields = ("crypto_id", "symbol", "name", "issuer_name", "price", "volume_24h",
              "market_cap", "cmc_url", "project_url")
    for row in routes:
        original = source_rows.get(row.get("crypto_id"))
        if original is None or any(row.get(field) != original.get(field) for field in fields):
            raise ValueError(f"route {row.get('crypto_id')} does not match the shipped CMC row")

    decision = review.get("decision") or {}
    if decision.get("state") != "do_not_compare_as_like_for_like":
        raise ValueError("pair review must withhold like-for-like price comparison")
    issuer_ids = [row.get("crypto_id") for row in review.get("issuer_evidence", [])
                  if row.get("crypto_id") is not None]
    if not {37013, 38001}.issubset(set(issuer_ids)):
        raise ValueError("issuer evidence must map to both exact CMC crypto IDs")
    if review.get("issuer_sources_checked_at") != "2026-09-29":
        raise ValueError("issuer source review date is missing")

    return {
        "review": review["review_id"],
        "cmc_observed_at": observation["observed_at"],
        "route_ids_verified": [row["crypto_id"] for row in routes],
        "source_sha256_verified": actual_hash,
        "decision": decision["state"],
        "issuer_source_archive": "not included; linked issuer pages are dated references",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))

#!/usr/bin/env python3
"""Verify the credential-free public Bell surface without CMC credentials."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rwa_integrity import RULES_VERSION


def fetch(base: str, path: str) -> tuple[int, str, object]:
    url = base.rstrip("/") + path
    request = Request(url, headers={"User-Agent": "bell-public-surface-check/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("content-type", "")
            status = response.status
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GET {url} failed: {exc}") from exc
    if "json" in content_type or body.lstrip().startswith(("{", "[")):
        try:
            return status, content_type, json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"GET {url} returned invalid JSON") from exc
    return status, content_type, body


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://bell.dyplux.com", help="public Bell origin")
    args = parser.parse_args()

    status, _, html = fetch(args.base, "/")
    require(status == 200 and isinstance(html, str), "public page did not return HTML 200")
    require("separate from live receipt" in html, "map/live-receipt boundary is not visible")
    require("CMC_PRO_API_KEY" not in html and "XAI_API_KEY" not in html, "credential name leaked into HTML")
    require("Explore RWA" in html, "single-page RWA explorer is not present")

    health_status, _, health = fetch(args.base, "/api/health")
    require(health_status == 200 and isinstance(health, dict) and health.get("ok") is True, "health endpoint failed")

    receipt_status, _, receipt = fetch(args.base, "/api/integrity")
    require(receipt_status == 200 and isinstance(receipt, dict), "integrity endpoint did not return JSON 200")
    require(receipt.get("schema_version") == "rwa_surface_integrity.v1", "unexpected receipt schema")
    publication = receipt.get("_publication") or {}
    require(publication.get("credential_free") is True, "receipt is not credential-free")
    require(publication.get("status") in {"fresh", "stale"}, "receipt freshness state is missing")
    universe = receipt.get("universe") or {}
    states = universe.get("states") or {}
    tokenised = int(universe.get("tokenised_references_scanned") or 0)
    tokens = int(universe.get("tokens_scanned") or 0)
    require(tokenised > 0 and tokens > 0, "receipt has no measured RWA population")
    require(sum(int(value or 0) for value in states.values()) == tokenised, "receipt state totals do not reconcile")

    # The scheduled publisher runs from its own checkout. When that checkout
    # stopped being updated, it kept republishing every fifteen minutes under an
    # older rule set, and the only symptom was a live state distribution that
    # quietly disagreed with the one this repository produces. Drift in the
    # runtime is now a named failure rather than something you notice by eye.
    live_rules = universe.get("rules_version")
    require(live_rules == RULES_VERSION,
            f"the live receipt was produced under {live_rules!r} but this repository is {RULES_VERSION!r}: "
            "the scheduled publisher is running a different version of the rules")

    # Folded in from a second public verifier that checked the same endpoint
    # with a different set of assertions. Two scripts auditing one surface meant
    # neither was the answer to "how do I check this", and the union of what
    # they checked was in nobody's head.
    calibration = receipt.get("rule_calibration") or {}
    for field in ("reference_count", "observed_ratio_bands", "thresholds"):
        require(field in calibration, f"receipt does not publish rule calibration: {field}")
    thresholds = calibration.get("thresholds") or {}
    for rule in ("price_dispersion", "price_denomination_break"):
        require((thresholds.get(rule) or {}).get("inclusive") is True,
                f"receipt does not publish inclusive threshold semantics for {rule}")
    attribution = receipt.get("population_attribution") or {}
    concentration = attribution.get("concentration") or {}
    for field in ("top_1_share", "top_3_share", "top_5_share", "hhi", "effective_issuer_count"):
        require(isinstance(concentration.get(field), (int, float)),
                f"population concentration is missing {field}")
    reconciliation = attribution.get("asset_level_reconciliation") or {}
    for field in ("matched_reference_rows", "exact_within_usd_cent", "non_exact_rows", "residual_sum"):
        require(isinstance(reconciliation.get(field), (int, float)),
                f"population reconciliation is missing {field}")
    alerts = receipt.get("alerts") or []
    require(bool(alerts), "receipt has no alert queue")
    require(bool(receipt.get("alert_index")), "receipt has no population alert index")
    first_decision = alerts[0].get("decision") or {}
    require(bool(first_decision.get("label")) and bool(first_decision.get("allocation_effect")),
            "the first alert states no decision or no allocation effect")

    comparisons = sum(1 for row in receipt.get("alert_index") or [] if row.get("comparison"))
    require(comparisons > 0,
            "no reference on the live surface carries a published comparison: the monitor can only refuse")

    dossier_status, _, dossier = fetch(args.base, "/api/published?slug=gold")
    require(dossier_status == 200 and isinstance(dossier, dict), "published Gold dossier did not return JSON 200")
    require(isinstance(dossier.get("_publication"), dict), "published dossier lacks publication metadata")

    print(json.dumps({
        "base": args.base.rstrip("/"),
        "page": "ok",
        "health": "ok",
        "receipt": {
            "status": publication.get("status"),
            "observed_at": receipt.get("observed_at"),
            "tokenised_references": tokenised,
            "representations": tokens,
            "states": states,
        },
        "gold_dossier": "ok",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"PUBLIC SURFACE CHECK FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

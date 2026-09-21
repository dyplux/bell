#!/usr/bin/env python3
"""Verify the credential-free public Bell surface without CMC credentials."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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

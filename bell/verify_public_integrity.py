#!/usr/bin/env python3
"""Credential-free smoke verifier for Bell's published RWA integrity receipt."""

from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen


def verify(url: str) -> dict:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "Bell-Public-Receipt-Verifier/1.1"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
        status = response.status
    if status != 200:
        raise RuntimeError(f"expected HTTP 200, received {status}")
    if payload.get("schema_version") != "rwa_surface_integrity.v1":
        raise RuntimeError("unexpected receipt schema")
    method = payload.get("method") or {}
    if method.get("scan_status") != "ready" or (method.get("input_integrity") or {}).get("invalid_or_missing_surfaces"):
        raise RuntimeError("published receipt does not confirm complete required surfaces")
    publication = payload.get("_publication") or {}
    required = ("source", "observed_at", "published_at", "status", "stale_after_seconds")
    missing = [key for key in required if not publication.get(key)]
    if missing:
        raise RuntimeError(f"publication metadata missing: {', '.join(missing)}")
    states = payload.get("universe", {}).get("states", {})
    for key in ("do_not_compare", "investigate", "no_flags"):
        if not isinstance(states.get(key), int):
            raise RuntimeError(f"invalid state count: {key}")
    alerts = payload.get("alerts")
    if not isinstance(alerts, list) or not alerts:
        raise RuntimeError("receipt has no alert queue")
    alert_index = payload.get("alert_index")
    if not isinstance(alert_index, list) or len(alert_index) < len(alerts):
        raise RuntimeError("receipt has no population alert index")
    first_decision = alerts[0].get("decision") or {}
    if not first_decision.get("label") or not first_decision.get("allocation_effect"):
        raise RuntimeError("alert decision is missing its operational effect")
    return {
        "url": url,
        "http_status": status,
        "schema_version": payload["schema_version"],
        "publication": publication,
        "states": states,
        "alert_index": len(alert_index),
        "first_alert": {
            "name": alerts[0].get("name"),
            "state": alerts[0].get("state"),
            "decision": first_decision,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Bell's credential-free public integrity receipt")
    parser.add_argument("url", nargs="?", default="https://bell.dyplux.com/api/integrity")
    args = parser.parse_args()
    print(json.dumps(verify(args.url), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

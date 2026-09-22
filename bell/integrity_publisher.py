#!/usr/bin/env python3
"""Collect and publish the current population-wide RWA integrity receipt.

The CMC key stays in the Mac mini process. The public Worker receives only the
normalised receipt, source hashes and deterministic findings.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rwa_integrity import collect_live, digest, scan


USER_AGENT = "Dyplux-Bell-Integrity-Publisher/1.0"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_local(receipt: dict, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(output)


def write_public_inputs(payloads: tuple[dict, dict, dict, dict, dict, dict], observed_at: str, output: Path, surface_times: dict | None = None) -> None:
    """Write the normalized CMC surfaces needed to recompute a dated receipt.

    The collector has already removed transport credentials. This artifact is
    intentionally a public input package, not a dump of request headers or
    authenticated HTTP metadata.
    """
    names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
    endpoints = {
        "map": "/v5/real-world-assets/map",
        "asset_list": "/v5/real-world-assets/assets/list",
        "quotes": "/v5/real-world-assets/quotes/latest",
        "info": "/v5/real-world-assets/info",
        "issuers": "/v5/real-world-assets/issuers/list",
        "crypto_info": "/v2/cryptocurrency/info",
    }
    surface_times = surface_times or {}
    collection_manifest = {
        "mode": "server_side_authenticated_collection",
        "observed_at": observed_at,
        "timestamp_granularity": "surface request window",
        "provider": "CoinMarketCap Pro API",
        "request_outcome": "all collected requests returned JSON successfully",
        "transport_headers_published": False,
        "surfaces": {
            name: {
                "endpoint": endpoints[name],
                "payload_sha256": digest(payload),
                "first_request_at": surface_times.get(name, {}).get("first_request_at"),
                "last_response_at": surface_times.get(name, {}).get("last_response_at"),
                "request_count": surface_times.get(name, {}).get("request_count", 0),
                "successful_response_count": surface_times.get(name, {}).get("successful_response_count", 0),
                "status_codes": surface_times.get(name, {}).get("status_codes", []),
                "response_sha256": surface_times.get(name, {}).get("response_sha256", []),
            }
            for name, payload in zip(names, payloads)
        },
    }
    package = {
        "schema_version": "bell.rwa_surface_integrity.inputs.v1",
        "observed_at": observed_at,
        "source": "CoinMarketCap RWA and cryptocurrency API surfaces collected server-side",
        "credential_free": True,
        "replay_note": "These normalized input payloads contain no API key or request headers. Run the documented verifier with this package and the same code to recompute the deterministic receipt.",
        "collection_manifest": collection_manifest,
        "surfaces": dict(zip(names, payloads)),
    }
    write_local(package, output)


def remote_endpoint() -> str | None:
    explicit = os.environ.get("BELL_INTEGRITY_PUBLICATION_URL")
    if explicit:
        return explicit
    general = os.environ.get("BELL_PUBLICATION_URL")
    if general and "/internal/publish" in general:
        return general.replace("/internal/publish", "/internal/integrity")
    return None


def publish_remote(receipt: dict) -> dict:
    endpoint = remote_endpoint()
    token = os.environ.get("PUBLISHER_TOKEN")
    if not endpoint:
        return {"remote_published": False, "remote": "not_configured"}
    if not token:
        raise RuntimeError("PUBLISHER_TOKEN is required for remote integrity publication")
    body = json.dumps({"receipt": receipt, "observed_at": receipt.get("observed_at"), "stale_after_seconds": 900}).encode("utf-8")
    request = Request(endpoint, data=body, method="POST", headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    })
    try:
        with urlopen(request, timeout=45) as response:
            if response.status < 200 or response.status >= 300:
                raise RuntimeError(f"remote publication returned HTTP {response.status}")
    except HTTPError as exc:
        raise RuntimeError(f"remote publication returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"remote publication failed: {exc.reason}") from exc
    return {"remote_published": True, "remote": endpoint}


def add_public_provenance(receipt: dict) -> None:
    """Make the live-versus-replay boundary machine-readable."""
    receipt["collection_provenance"] = {
        "mode": "server_side_authenticated_collection",
        "credential_free": True,
        "api_key_published": False,
        "transport_headers_published": False,
        "replay_index_url": "/proof/rwa-surface-integrity-replay-index.md",
        "replay_package_note": "The live receipt is current; the linked replay package is a dated credential-free recomputation artifact.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the current CMC RWA integrity receipt")
    parser.add_argument("--output", type=Path, help="local receipt path; defaults to BELL_STORE_DIR/integrity/latest.json")
    parser.add_argument("--inputs-output", type=Path, help="optional credential-free normalized CMC input package")
    parser.add_argument("--no-remote", action="store_true", help="write locally without calling the Worker")
    args = parser.parse_args()
    key = os.environ.get("CMC_API_KEY")
    if not key:
        parser.error("CMC_API_KEY must be set in the publisher process")
    observed_at = now()
    surface_times = {}
    payloads = collect_live(key, surface_times)
    map_payload, list_payload, quotes_payload, info_payload, issuers_payload, crypto_info_payload = payloads
    receipt = scan(map_payload, list_payload, quotes_payload, info_payload, issuers_payload, observed_at=observed_at, crypto_info_payload=crypto_info_payload)
    add_public_provenance(receipt)
    output = args.output or Path(os.environ.get("BELL_STORE_DIR", str(Path(__file__).resolve().parent / "runtime"))) / "integrity/latest.json"
    write_local(receipt, output)
    if args.inputs_output:
        write_public_inputs(payloads, observed_at, args.inputs_output, surface_times)
    publication = {"remote_published": False, "remote": "disabled"} if args.no_remote else publish_remote(receipt)
    summary = {
        "schema_version": "bell.integrity.publisher.v1",
        "output": str(output),
        "observed_at": observed_at,
        "universe": receipt["universe"],
        "identity_integrity": receipt["identity_integrity"],
        **publication,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

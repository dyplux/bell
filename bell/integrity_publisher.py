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

from rwa_integrity import collect_live, scan


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the current CMC RWA integrity receipt")
    parser.add_argument("--output", type=Path, help="local receipt path; defaults to BELL_STORE_DIR/integrity/latest.json")
    parser.add_argument("--no-remote", action="store_true", help="write locally without calling the Worker")
    args = parser.parse_args()
    key = os.environ.get("CMC_API_KEY")
    if not key:
        parser.error("CMC_API_KEY must be set in the publisher process")
    observed_at = now()
    map_payload, list_payload, quotes_payload, info_payload, issuers_payload, crypto_info_payload = collect_live(key)
    receipt = scan(map_payload, list_payload, quotes_payload, info_payload, issuers_payload, observed_at=observed_at, crypto_info_payload=crypto_info_payload)
    output = args.output or Path(os.environ.get("BELL_STORE_DIR", str(Path(__file__).resolve().parent / "runtime"))) / "integrity/latest.json"
    write_local(receipt, output)
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

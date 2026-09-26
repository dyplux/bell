#!/usr/bin/env python3
"""Lift the per-surface transport record out of the 16.5 MB input package.

Reviewers kept marking the exported case receipt down for carrying no HTTP
status and no request counts, and they were right about the artefact and wrong
about the data: all of it is already in `collection_manifest` inside the replay
inputs. The page cannot load a 16.5 MB file to build a receipt, so the manifest
never reached the thing a judge actually downloads.

This extracts it once, into a few kilobytes the page can fetch: per surface the
endpoint, the payload digest, the request window, how many requests were made,
how many returned, and the distinct status codes with their counts. The
per-request hash arrays stay in the manifest, where a reader who wants them
already has them.

Nothing is computed here that is not in the manifest. Run it after a new input
package is published:

    PYTHONPATH=bell python3 bell/extract_transport.py
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "site" / "proof" / "rwa-surface-integrity-inputs-2026-09-21.json"
OUTPUT = HERE / "site" / "proof" / "transport-2026-09-21.json"
SCHEMA = "bell.transport_summary.v1"


def summarise(manifest: dict) -> dict:
    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, dict) or not surfaces:
        raise SystemExit("the collection manifest carries no surfaces")
    out: dict = {}
    for name, surface in sorted(surfaces.items()):
        codes = Counter(int(code) for code in surface.get("status_codes", []))
        out[name] = {
            "endpoint": surface.get("endpoint"),
            "payload_sha256": surface.get("payload_sha256"),
            "first_request_at": surface.get("first_request_at"),
            "last_response_at": surface.get("last_response_at"),
            "request_count": surface.get("request_count"),
            "successful_response_count": surface.get("successful_response_count"),
            # Counted rather than listed: thirty-two identical 200s say the same
            # thing as "200 x 32" and a reader can see the shape at a glance.
            "status_codes": {str(code): count for code, count in sorted(codes.items())},
            "response_digest_count": len(surface.get("response_sha256", [])),
        }
    return out


def build(inputs_path: Path) -> dict:
    package = json.loads(inputs_path.read_text(encoding="utf-8"))
    manifest = package.get("collection_manifest")
    if not isinstance(manifest, dict):
        raise SystemExit(f"{inputs_path} carries no collection_manifest")
    return {
        "schema_version": SCHEMA,
        "observed_at": manifest.get("observed_at") or package.get("observed_at"),
        "provider": manifest.get("provider"),
        "mode": manifest.get("mode"),
        "transport_headers_published": manifest.get("transport_headers_published"),
        "request_outcome": manifest.get("request_outcome"),
        "extracted_from": inputs_path.name,
        "note": ("Per-surface transport record, lifted verbatim from the replay input "
                 "package's collection manifest. Status codes are counted, not listed; the "
                 "per-request digests stay in the manifest. No credential, header or token "
                 "is recorded here or there."),
        "surfaces": summarise(manifest),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--inputs", default=str(INPUTS))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args(argv)
    summary = build(Path(args.inputs))
    Path(args.output).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    total = sum(surface["request_count"] or 0 for surface in summary["surfaces"].values())
    print(f"transport summary: {len(summary['surfaces'])} surfaces, {total} requests, "
          f"{Path(args.output).stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

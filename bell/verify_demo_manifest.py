#!/usr/bin/env python3
"""Verify a credential-free Bell demo manifest and its video artifact."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from urllib.parse import urlparse


LONG_STEPS = {
    "hero",
    "silver-search",
    "silver-evidence",
    "population-shape",
    "population-concentration",
    "facts-open",
    "gold-repeat-window",
    "map-only",
    "receipt",
}


def parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is missing")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} is not an ISO-8601 timestamp") from exc


def verify(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    if manifest.get("schema_version") != "bell.demo-video.v1":
        raise ValueError("unexpected demo manifest schema")
    if manifest.get("mode") not in {"short", "long"}:
        raise ValueError("demo mode must be short or long")

    base = manifest.get("base")
    parsed_base = urlparse(base or "")
    if parsed_base.scheme != "https" or not parsed_base.netloc:
        raise ValueError("demo base must be an HTTPS public origin")

    receipt = manifest.get("receipt")
    if not isinstance(receipt, dict):
        raise ValueError("receipt metadata is missing")
    if receipt.get("status") not in {"fresh", "stale"}:
        raise ValueError("receipt metadata must record a fresh or stale publication")
    observed_at = parse_time(receipt.get("observed_at"), "receipt.observed_at")
    published_at = parse_time(receipt.get("published_at"), "receipt.published_at")
    captured_at = parse_time(manifest.get("captured_at"), "captured_at")
    if published_at < observed_at:
        raise ValueError("receipt published_at precedes observed_at")
    if captured_at < observed_at:
        raise ValueError("capture predates the observed receipt")
    for field in ("tokenised_references", "representations"):
        if not isinstance(receipt.get(field), int) or receipt[field] <= 0:
            raise ValueError(f"receipt.{field} must be a positive integer")

    if manifest.get("console_errors") != []:
        raise ValueError("browser console errors are present")
    steps = manifest.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("demo steps are missing")
    step_ids = [step.get("id") for step in steps if isinstance(step, dict)]
    if len(step_ids) != len(set(step_ids)):
        raise ValueError("demo steps contain duplicate ids")
    if manifest["mode"] == "long" and not LONG_STEPS.issubset(step_ids):
        missing = sorted(LONG_STEPS - set(step_ids))
        raise ValueError(f"long demo is missing steps: {', '.join(missing)}")
    for step in steps:
        if not isinstance(step, dict) or not step.get("selector"):
            raise ValueError("every demo step needs a selector")

    video_name = manifest.get("video")
    if not isinstance(video_name, str) or Path(video_name).name != video_name:
        raise ValueError("manifest video must be a filename in the manifest directory")
    video_path = manifest_path.parent / video_name
    if not video_path.is_file() or video_path.stat().st_size <= 0:
        raise ValueError(f"video artifact is missing or empty: {video_path}")

    return {
        "status": "ok",
        "manifest": str(manifest_path),
        "video": str(video_path),
        "mode": manifest["mode"],
        "receipt_status": receipt["status"],
        "observed_at": receipt["observed_at"],
        "captured_at": manifest["captured_at"],
        "steps": len(steps),
        "video_bytes": video_path.stat().st_size,
        "console_errors": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.manifest), ensure_ascii=False, indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"DEMO MANIFEST CHECK FAILED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

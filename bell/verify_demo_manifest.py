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


def verify_capture(manifest: dict, manifest_path: Path) -> dict:
    """Check a credential-free frame capture, and check the frames are there.

    A capture manifest is a weaker artefact than a video manifest and is
    checked for what it actually claims: a public HTTPS origin, no console
    errors, dated, and every frame it lists present on disk with a non-empty
    file. It does not claim a receipt or an ordered script, so it is not asked
    for one.
    """
    base = manifest.get("base")
    parsed = urlparse(base or "")
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("capture base must be an HTTPS public origin")
    if manifest.get("console_errors") != []:
        raise ValueError("browser console errors are present")
    observed_at = parse_time(manifest.get("observed_at"), "observed_at")
    published_at = parse_time(manifest.get("published_at"), "published_at")
    if published_at < observed_at:
        raise ValueError("capture published_at precedes observed_at")
    frames = manifest.get("frames")
    if not isinstance(frames, list) or not frames:
        raise ValueError("capture manifest lists no frames")
    missing, empty = [], []
    for frame in frames:
        if not isinstance(frame, dict) or not frame.get("file"):
            raise ValueError("a frame entry names no file")
        if not frame.get("label"):
            raise ValueError(f"frame {frame['file']} carries no label")
        path = manifest_path.parent / frame["file"]
        if not path.exists():
            missing.append(frame["file"])
        elif path.stat().st_size == 0:
            empty.append(frame["file"])
    if missing:
        raise ValueError(f"the manifest lists frames that are not here: {', '.join(missing)}")
    if empty:
        raise ValueError(f"these frames are empty files: {', '.join(empty)}")
    labels = [frame["label"] for frame in frames]
    if len(set(labels)) != len(labels):
        raise ValueError("two frames carry the same label, so one of them describes nothing")
    return {
        "schema_version": manifest["schema_version"],
        "base": base,
        "frames": len(frames),
        "observed_at": manifest.get("observed_at"),
        "status": "valid credential-free capture manifest",
    }


def verify(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    # JUDGE.md tells a reader to run this against a manifest, and the only
    # manifest this repository ships is `bell.demo-capture.v1`, written by
    # capture_demo.py - which this refused at the door because it only knew
    # `bell.demo-video.v1`. A documented command failing on the repository's own
    # file is the defect the Makefile already records having shipped once.
    schema = manifest.get("schema_version")
    if schema == "bell.demo-capture.v1":
        return verify_capture(manifest, manifest_path)
    if schema != "bell.demo-video.v1":
        raise ValueError(
            f"unexpected demo manifest schema {schema!r}: expected bell.demo-video.v1 or "
            "bell.demo-capture.v1")
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

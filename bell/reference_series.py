#!/usr/bin/env python3
"""A per-reference series, stored as deltas so it can grow daily.

A reviewer named the largest usefulness gap: "a product sold to someone
tracking tokenised assets needs to answer 'what did this reference do over the
last month', and today it cannot". The change view compares against exactly one
baseline; the 14-observation history is population-level.

The honest limit first: this repository holds full per-reference detail for one
dated observation and the live receipt. It cannot manufacture the days in
between, and it does not. What it can do is stop throwing the detail away, so
the series grows by one point every time an observation is published, and says
how many points it has rather than implying a month.

Stored as deltas against the base snapshot, because references mostly do not
move: between 21 and 26 September, 33 of 792 changed, which is 4.2 KB raw and
0.5 KB on the wire. A year of daily observations is about 1.5 MB raw, against
1.2 GB if each day shipped a full snapshot. That ratio is the whole design.

    PYTHONPATH=bell python3 bell/reference_series.py --receipt <receipt.json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROOF = HERE / "site" / "proof"
BASE = PROOF / "reference-snapshot-2026-09-21.json"
DELTAS = PROOF / "reference-deltas.json"
SCHEMA = "bell.reference_deltas.v1"

FIELDS = ("state", "representations", "comparison_published", "signal_codes")


def snapshot_of(receipt: dict) -> dict:
    """The four fields a change needs, keyed by stable reference ID."""
    out: dict = {}
    for item in receipt.get("alert_index") or []:
        key = str(item.get("rwa_id") or "").strip()
        if not key:
            continue
        out[key] = {
            "state": item.get("state"),
            "representations": int(item.get("token_count") or 0),
            "comparison_published": bool(item.get("comparison")),
            "signal_codes": sorted(item.get("signal_codes") or []),
        }
    return out


def delta(previous: dict, current: dict) -> dict:
    """What moved. Absent is recorded as a removal, never as an empty value."""
    changed = {key: value for key, value in current.items() if previous.get(key) != value}
    removed = sorted(set(previous) - set(current))
    return {"changed": changed, "removed": removed}


def apply(base: dict, deltas: list) -> dict:
    """Replay the deltas in order onto the base snapshot."""
    state = {key: dict(value) for key, value in base.items()}
    for step in deltas:
        for key, value in (step.get("changed") or {}).items():
            state[key] = dict(value)
        for key in step.get("removed") or []:
            state.pop(key, None)
    return state


def series_for(reference_id: str, base: dict, base_at: str, deltas: list) -> list:
    """Every observation at which this reference is recorded as having moved.

    The base is point one. After that a reference appears only on the
    observations where something about it changed, which is what makes the
    file small and is also the more readable answer: a list of the days it
    moved, not a list of every day it did not.
    """
    key = str(reference_id)
    points = []
    if key in base:
        points.append({"observed_at": base_at, "baseline": True, **base[key]})
    for step in deltas:
        if key in (step.get("changed") or {}):
            points.append({"observed_at": step["observed_at"], "baseline": False,
                           **step["changed"][key]})
        elif key in (step.get("removed") or []):
            points.append({"observed_at": step["observed_at"], "baseline": False,
                           "removed": True})
    return points


def load() -> tuple:
    base_doc = json.loads(BASE.read_text(encoding="utf-8"))
    if DELTAS.exists():
        deltas_doc = json.loads(DELTAS.read_text(encoding="utf-8"))
    else:
        deltas_doc = {"schema_version": SCHEMA, "base": BASE.name,
                      "rules_version": base_doc.get("rules_version"), "observations": []}
    return base_doc, deltas_doc


def record(receipt: dict) -> tuple:
    """Add one observation to the series. Returns (document, message)."""
    base_doc, deltas_doc = load()
    observed_at = receipt.get("observed_at")
    if not observed_at:
        raise SystemExit("the receipt carries no observed_at")
    rules = (receipt.get("universe") or {}).get("rules_version")
    if rules != deltas_doc.get("rules_version"):
        # The series is a market series. Replaying a state computed under one
        # rule set onto states computed under another would report the rule
        # change as movement, which is the error this product exists to refuse.
        raise SystemExit(
            f"refusing to extend the series: it is recorded under "
            f"{deltas_doc.get('rules_version')!r} and this receipt declares {rules!r}. A series "
            "that spans a rule change reports the rule change as market movement.")
    existing = [step["observed_at"] for step in deltas_doc["observations"]]
    if observed_at in existing or observed_at == base_doc.get("observed_at"):
        return deltas_doc, f"no new point: {observed_at} is already in the series"
    if existing and observed_at < max(existing):
        raise SystemExit(
            f"refusing to extend the series: {observed_at} is older than {max(existing)}")
    previous = apply(base_doc["references"], deltas_doc["observations"])
    step = delta(previous, snapshot_of(receipt))
    step["observed_at"] = observed_at
    moved = len(step["changed"]) + len(step["removed"])
    deltas_doc["observations"].append(step)
    return deltas_doc, (f"recorded {observed_at}: {moved} references moved, "
                        f"series is now {len(deltas_doc['observations']) + 1} points")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    document, message = record(receipt)
    print(message)
    if not args.dry_run:
        DELTAS.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
                          encoding="utf-8")
        print(f"{DELTAS.name}: {DELTAS.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

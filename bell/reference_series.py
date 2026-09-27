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
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROOF = HERE / "site" / "proof"
BASE = PROOF / "reference-snapshot-2026-09-21.json"
DELTAS = PROOF / "reference-deltas.json"
SCHEMA = "bell.reference_deltas.v1"

FIELDS = ("state", "representations", "comparison_published", "signal_codes")


def index_digest(receipt: dict) -> str:
    """A fingerprint of the alert_index the delta was derived from.

    The deltas were the one evidence file nothing verified: a reviewer rewrote
    Silver into the 26 September step as clean, with no signals, and the whole
    378-test gate stayed green. Nothing could re-derive it, because the receipt
    that produced it is not shipped - so the fix is not to re-derive it, it is
    to record what it came from and refuse a step whose stated origin is not
    the origin the series claims.
    """
    return digest_of_state(snapshot_of(receipt))


def digest_of_state(state: dict) -> str:
    """Hash a replayed state the same way the receipt's index is hashed.

    The recorder hashes the receipt; the verifier hashes the state the deltas
    replay to. If those were two computations they would drift, and the check
    would quietly become about nothing. One function, both callers.
    """
    rows = sorted(
        (key, str(value.get("state") or ""), int(value.get("representations") or 0),
         bool(value.get("comparison_published")), tuple(value.get("signal_codes") or []))
        for key, value in state.items())
    return hashlib.sha256(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


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


def verify(base_doc: dict, deltas_doc: dict, history: dict) -> list:
    """Refuse a series that does not answer to the published history.

    Checks what CAN be checked without the receipts: that every step names an
    observation the history records, that the fingerprints it claims are the
    ones that observation recorded, that it is in order, and that the rule set
    does not change under it. What it cannot check is the row detail itself,
    because the receipts behind the steps are not shipped, and that limit is
    named on the judge page rather than left to be discovered.
    """
    notes = []
    recorded = {str(item.get("observed_at")): item for item in history.get("observations") or []}
    # Emptying `observations` made this return an empty list and the verifier
    # print "reference series: 1 points", while observation 15 still anchored a
    # digest nothing then checked. A guard that vanishes when the evidence is
    # removed, in the function written to stop exactly that. Every observation
    # that anchors a digest must have the step that digest describes.
    anchored = {stamp for stamp, item in recorded.items() if item.get("reference_digest")}
    present = {str(step.get("observed_at")) for step in deltas_doc.get("observations") or []}
    orphaned = sorted(anchored - present)
    if orphaned:
        raise ValueError(
            f"the history anchors a series digest for {', '.join(orphaned)} and the series has no "
            "step for it. A removed step is not an absent feature: the observation still claims "
            "the digest.")
    if deltas_doc.get("base") != BASE.name:
        raise ValueError(f"the series is built on {deltas_doc.get('base')!r}, not {BASE.name}")
    if deltas_doc.get("rules_version") != base_doc.get("rules_version"):
        raise ValueError("the series and its base answer to different rule sets")
    previous_at = base_doc.get("observed_at")
    for index, step in enumerate(deltas_doc.get("observations") or [], start=1):
        label = f"series step {index} ({step.get('observed_at')})"
        observed_at = str(step.get("observed_at") or "")
        if observed_at <= str(previous_at):
            raise ValueError(f"{label} is not after {previous_at}")
        previous_at = observed_at
        observation = recorded.get(observed_at)
        if observation is None:
            raise ValueError(
                f"{label} describes an observation the published history does not record. A "
                "series point with no observation behind it is a day nobody observed.")
        if observation.get("rules_version") != deltas_doc.get("rules_version"):
            raise ValueError(f"{label} was recorded under {observation.get('rules_version')!r}")
        claimed = step.get("source_hashes")
        if not claimed:
            raise ValueError(
                f"{label} records no source fingerprints, so nothing says which scan it came from")
        if claimed != observation.get("source_hashes"):
            raise ValueError(
                f"{label} claims source fingerprints the history does not record for that "
                "observation")
        digest = step.get("alert_index_sha256")
        if not digest:
            raise ValueError(f"{label} records no alert_index digest")
        # Recomputed, not merely present. The previous version tested that the
        # field existed and this docstring said the check refused a rewritten
        # step - a docstring describing a fix that had not been made, which is
        # the pattern this repository has now recorded ten times. A reviewer
        # wrote a reference into a step as clean, with no signals, and the gate
        # returned 0 while printing that the step was matched to its digests.
        #
        # What this can do: the state after replaying every step up to and
        # including this one must hash to the digest the step recorded. So a
        # step cannot be edited without also editing its own digest, and it
        # cannot be edited to agree with a digest the history does not carry.
        replayed = apply(base_doc["references"], (deltas_doc.get("observations") or [])[:index])
        recomputed = digest_of_state(replayed)
        if recomputed != digest:
            raise ValueError(
                f"{label} records alert_index digest {digest[:16]} and the state it produces "
                f"hashes to {recomputed[:16]}: the step was edited after it was written")
        # And the digest itself lives in the file it protects, so repairing
        # both together would pass. The history is chained and anchored outside
        # itself, so the observation carries the digest the series must
        # reproduce. Where it does, it is compared; where it does not - every
        # observation older than this mechanism - that is said rather than
        # skipped silently.
        anchored = observation.get("reference_digest")
        if anchored is None:
            notes.append(f"{label}: digest not anchored in the history (recorded before the "
                         "history carried the field)")
        elif anchored != digest:
            raise ValueError(
                f"{label} records digest {digest[:16]} and the chained history anchors "
                f"{anchored[:16]}: the series and the history disagree about that observation")
        notes.append(f"{label}: {len(step.get('changed') or {})} moved, "
                     f"{len(step.get('removed') or [])} removed")
    return notes


def load() -> tuple:
    base_doc = json.loads(BASE.read_text(encoding="utf-8"))
    if DELTAS.exists():
        deltas_doc = json.loads(DELTAS.read_text(encoding="utf-8"))
    else:
        deltas_doc = {"schema_version": SCHEMA, "base": BASE.name,
                      "rules_version": base_doc.get("rules_version"), "observations": []}
    return base_doc, deltas_doc


def record(receipt: dict, history: dict | None = None) -> tuple:
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
    # A series point must describe an observation the published history records.
    # The first version stamped a point at 23:43:43 while the history's newest
    # was 23:28:21, and nothing reconciled them - a reviewer found two surfaces
    # describing the same day and disagreeing, which is the defect this whole
    # product is named after.
    history_path = PROOF / "rwa-surface-integrity-history.json"
    if history is None and history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
    if history is not None:
        recorded = {str(item.get("observed_at")) for item in history.get("observations") or []}
        if observed_at not in recorded:
            raise SystemExit(
                f"refusing to extend the series: {observed_at} is not in the published history. "
                "Append the observation first, so the series and the history describe the same "
                "days.")
    existing = [step["observed_at"] for step in deltas_doc["observations"]]
    if observed_at in existing or observed_at == base_doc.get("observed_at"):
        return deltas_doc, f"no new point: {observed_at} is already in the series"
    if existing and observed_at < max(existing):
        raise SystemExit(
            f"refusing to extend the series: {observed_at} is older than {max(existing)}")
    previous = apply(base_doc["references"], deltas_doc["observations"])
    step = delta(previous, snapshot_of(receipt))
    step["observed_at"] = observed_at
    # What this step was derived from, so `make verify` can refuse a step whose
    # origin is not the origin it claims, and so a reader can tell a recorded
    # observation from an edited one.
    step["source_hashes"] = receipt.get("source_hashes") or {}
    step["alert_index_sha256"] = index_digest(receipt)
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

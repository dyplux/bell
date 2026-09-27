#!/usr/bin/env python3
"""Lift a per-reference snapshot out of a dated receipt, so change is visible.

A reviewer put it plainly: "for a product sold as tracking, there is still no
per-reference change-over-time view". The history answers "how did the
POPULATION move"; nothing answered "did THIS reference change since the dated
observation", which is the question a reader holding one reference actually
has.

The data was already there and unreachable. The dated replay receipt is 3.42
MiB, far too much for a page to load beside the live receipt it is comparing
against. This extracts the four fields a change view needs - state, how many
representations, whether a comparison was published, and which rules fired -
into 95 KB, 4.2 KB on the wire, fetched once per page and cached. The hero
opens a case on load, so that is first paint rather than an interaction.

The snapshot records its own `rules_version`. A state is a function of the
rules, so a diff across a rule boundary would state a market change nobody
observed; the page refuses that comparison the same way the publication history
already refuses a delta between two receipts written under different rules.

Run it after a new dated receipt is published:

    PYTHONPATH=bell python3 bell/extract_reference_snapshot.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RECEIPT = HERE / "site" / "proof" / "rwa-surface-integrity-latest-replay-2026-09-21.json"
OUTPUT = HERE / "site" / "proof" / "reference-snapshot-2026-09-21.json"
SCHEMA = "bell.reference_snapshot.v1"


def snapshot(receipt: dict) -> dict:
    index = receipt.get("alert_index")
    if not isinstance(index, list) or not index:
        raise SystemExit("the receipt carries no alert_index to snapshot")
    universe = receipt.get("universe")
    if not isinstance(universe, dict):
        raise SystemExit("the receipt carries no universe block")
    references = {}
    for item in index:
        key = str(item.get("rwa_id") or "").strip()
        if not key:
            continue
        references[key] = {
            # No name: the live receipt already carries it for any reference the
            # page can render a change view for, and 791 names were 40% of this
            # file. A field that is only ever read beside its own duplicate is
            # weight.
            "state": item.get("state"),
            "representations": int(item.get("token_count") or 0),
            # Whether a comparison was PUBLISHED, not the comparison itself:
            # the numbers inside it belong to that observation and would invite
            # a price delta this monitor does not make.
            "comparison_published": bool(item.get("comparison")),
            "signal_codes": sorted(item.get("signal_codes") or []),
        }
    if not references:
        raise SystemExit("no reference in the receipt carries a stable rwa_id")
    return {
        "schema_version": SCHEMA,
        "observed_at": receipt.get("observed_at"),
        # Without this the page cannot tell a rule change from a market change,
        # which is the error this project spent five days publishing.
        "rules_version": universe.get("rules_version"),
        "extracted_from": RECEIPT.name,
        "note": ("Per-reference state at one dated observation, lifted from the dated replay "
                 "receipt so a change view does not have to load 3.42 MiB. It records whether a "
                 "comparison was published, never the compared prices: those belong to the "
                 "observation that produced them. A diff against a receipt written under a "
                 "different rules_version states a rule change as if it were a market change, "
                 "so the page refuses it."),
        "references": references,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--receipt", default=str(RECEIPT))
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args(argv)
    built = snapshot(json.loads(Path(args.receipt).read_text(encoding="utf-8")))
    out = Path(args.output)
    out.write_text(json.dumps(built, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(f"reference snapshot: {len(built['references']):,} references under "
          f"{built['rules_version'] or 'an unrecorded rule set'}, "
          f"{out.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

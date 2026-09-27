#!/usr/bin/env python3
"""One-time: make "this record predates rule versioning" something it SAYS.

`verify_observation` skipped the state comparison whenever the recorded and
current rule versions differed, and read a MISSING `rules_version` as "a
different version". So deleting the key from a history record switched the
comparison off. A reviewer rewrote observation 11's distribution to 791 blocked,
re-linked the chain, updated the anchor, and the whole gate returned ok. That is
the third place in this repository where a check took its scope from the thing
it was checking.

Absence must not grant the skip. So the skip now requires the record to declare
`rules_version_recorded: false`, and eleven records really do predate the field:
they were written before `RULES_VERSION` existed. Recording that is not
inventing a rule set. It is the opposite: it refuses to name one.

This adds that field, and only that field, and only where `rules_version` is
absent. It changes no recorded count, verifies the chain before and after, and
re-links because a new field changes every digest from that record on. That
re-linking is exactly what `append_history` refuses to do, which is why this is
a separate script a person runs once and names in a commit, rather than
something the daily job can do.

    PYTHONPATH=bell python3 bell/declare_unversioned_observations.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from history_chain import CHAIN_VERSION, rebuild, verify

HERE = Path(__file__).resolve().parent
HISTORY = HERE / "site" / "proof" / "rwa-surface-integrity-history.json"
ANCHOR = HERE / "history-chain-head.txt"
FIELD = "rules_version_recorded"


def declare(observations: list) -> list:
    touched = []
    for index, observation in enumerate(observations):
        if FIELD in observation:
            continue
        if "rules_version" in observation and observation["rules_version"]:
            # It names its rule set, so there is nothing to declare and nothing
            # here may touch it.
            observation[FIELD] = True
            touched.append((index + 1, observation.get("observed_at"), True))
            continue
        observation[FIELD] = False
        touched.append((index + 1, observation.get("observed_at"), False))
    return touched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--history", default=str(HISTORY))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.history)
    history = json.loads(path.read_text(encoding="utf-8"))
    observations = history["observations"]

    before = verify(observations)
    if history.get("chain_head") != before:
        raise SystemExit(
            f"refusing to migrate: the history verifies to {before} and declares "
            f"{history.get('chain_head')!r}. Resolve that first.")
    recorded = [
        {key: value for key, value in item.items()
         if key not in ("sha256", "prev_sha256", "chain_version")}
        for item in observations
    ]

    touched = declare(recorded)
    if not touched:
        print("every observation already declares whether it recorded a rule set")
        return 0

    relinked = rebuild(recorded)
    # Nothing but the new field may change. Checked rather than asserted,
    # because rewriting published records is the operation this repository
    # exists to make visible.
    for old, new in zip(observations, relinked):
        for key, value in old.items():
            if key in ("sha256", "prev_sha256", "chain_version"):
                continue
            if new.get(key) != value:
                raise SystemExit(f"refusing to migrate: {key} changed on {old.get('observed_at')}")
    head = verify(relinked)

    for index, observed_at, declared in touched:
        print(f"  observation {index} ({observed_at}): {FIELD} = {str(declared).lower()}")
    print(f"chain head {before[:16]} -> {head[:16]}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    history["observations"] = relinked
    history["chain_version"] = CHAIN_VERSION
    history["chain_head"] = head
    path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ANCHOR.write_text(head + "\n", encoding="utf-8")
    print(f"wrote {path.name} and {ANCHOR.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

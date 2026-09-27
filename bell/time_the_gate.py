#!/usr/bin/env python3
"""Time the offline gate and write the number the documents publish.

judge.html says the runtime band is "measured and pinned by a test rather than
quoted from one run", and earlier it said "a bound nobody can observe is not a
measurement". Neither was true of the band itself: no test ever started a
clock. A reviewer changed the band to "6.0 and 11.0 seconds" with a `<11s`
tile, on a gate that takes twelve, and the whole suite stayed green. Then their
own cold run measured 14.007 seconds, outside the band the page advertised.

Two sentences about measurement, both unmeasured, in the repository whose
subject is surfaces that quietly disagree.

This runs the gate and records what it observed, with the machine and the test
count beside it, so the band in the documents answers to a file that answers to
a clock. It is not part of `make check-offline` for the obvious reason: a gate
cannot time itself without running itself.

    make time-gate
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RECEIPT = HERE / "site" / "proof" / "gate-runtime.json"
SCHEMA = "bell.gate_runtime.v1"


def run_once() -> float:
    start = time.perf_counter()
    result = subprocess.run(["make", "check-offline"], cwd=str(ROOT),
                            capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        raise SystemExit(
            f"the gate failed, so its runtime is not a measurement of anything:\n"
            f"{result.stdout[-600:]}\n{result.stderr[-600:]}")
    return elapsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=3,
                        help="how many times to run it; the first is the cold one")
    parser.add_argument("--output", default=str(RECEIPT))
    args = parser.parse_args(argv)

    timings = [round(run_once(), 2) for _ in range(max(args.runs, 1))]
    existing = {}
    out = Path(args.output)
    if out.exists():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    # Every machine this has run on, kept, because a band is a claim about the
    # range a reader might see and one machine cannot establish a range.
    machines = {entry["machine"]: entry for entry in existing.get("runs", [])}
    machines[platform.platform()] = {
        "machine": platform.platform(),
        "python": platform.python_version(),
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cold": timings[0],
        "warm": timings[1:],
    }
    runs = sorted(machines.values(), key=lambda entry: entry["machine"])
    every = [value for entry in runs for value in [entry["cold"]] + list(entry["warm"])]
    receipt = {
        "schema_version": SCHEMA,
        "fastest": min(every),
        "slowest": max(every),
        "runs": runs,
        "note": ("Wall time of `make check-offline`, measured by bell/time_the_gate.py. The band "
                 "the documents publish must contain every figure here, and a test compares them. "
                 "A band is a claim about what a reader will see, so it keeps one entry per "
                 "machine rather than only the latest."),
    }
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"gate runtime: {', '.join(f'{value}s' for value in timings)} on "
          f"{platform.platform()}")
    print(f"observed range across {len(runs)} machine(s): {receipt['fastest']}s to "
          f"{receipt['slowest']}s")
    print(f"written to {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

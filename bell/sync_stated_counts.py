#!/usr/bin/env python3
"""Rewrite the counts the documents state, from a real measurement.

judge.html and README.md quote four numbers about the gate: how many tests it
runs, how many are Python, how many are JavaScript, and how many tracked files
the submission gate inspects. Each one has a test asserting the documents agree
with reality, which is why they get caught. They were still being corrected by
hand, and a hand-corrected number drifts: a commit that adds two files ships
with the old count, the gate goes red on the very commit a judge clones, and
the project's most quoted figure fails when run. That happened.

Counting tracked files is the part that bit. `git ls-files` lists what is
already staged or committed, so running this before `git add` measures the
repository as it was and the count is wrong the moment the commit lands. The
first fix counted untracked-not-ignored files too, and that made the number
depend on the machine: a clone that has run `npm install` carries an untracked
package-lock.json, so a judge's gate went red while this one stayed green.

So it counts tracked files, and you run it after staging:

    git add -A && make sync-counts && make check-offline

It changes only the four numbers. If a sentence stops carrying one, that is
reported rather than silently skipped.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
JUDGE = HERE / "site" / "judge.html"
RUNTIME = HERE / "site" / "proof" / "gate-runtime.json"
README = ROOT / "README.md"

JS_COUNTER = """
const fs = require("fs"), path = require("path");
const count = (dir, pattern) => fs.readdirSync(dir).filter(name => pattern.test(name))
  .reduce((total, name) => total +
    ((fs.readFileSync(path.join(dir, name), "utf8").match(/^test\\(/gm) || []).length), 0);
console.log(count("bell/tests", /^test_.*\\.cjs$/) + count("cloudflare/tests", /\\.mjs$/));
"""


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, **kwargs)


def measure() -> dict:
    # Tracked files only. Counting untracked-not-ignored as well seemed to
    # solve "run this before git add", and it made the number depend on the
    # machine: a fresh clone that has run `npm install` carries an untracked
    # package-lock.json, so the gate failed for a judge and passed here. A
    # figure a document states about the repository has to be a figure of the
    # repository. Run this after staging instead, which is what the failure
    # message says.
    listing = run(["git", "ls-files"], check=True)
    files = len(listing.stdout.split())

    python = run(["python3", "-m", "unittest", "discover", "-s", "bell/tests", "-p", "test_*.py"],
                 env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
    found = re.search(r"^Ran (\d+)", python.stderr, re.M)
    if not found:
        raise SystemExit(f"could not read a test count from the Python suite:\n{python.stderr[-400:]}")

    javascript = run(["node", "-e", JS_COUNTER], check=True)
    return {"files": files, "python": int(found.group(1)),
            "javascript": int(javascript.stdout.strip())}


def runtime_band() -> dict:
    """What the runtime receipt actually observed, and on how many machines.

    The page said the gate "runs between 11.0 and 15.1 seconds across the
    machines it has been measured on". The receipt held one machine and
    12.48 to 12.61. So the band was neither the measurement nor plural, and the
    test that guarded it only asked whether the published band CONTAINED every
    figure, which any wide enough invention satisfies. A reviewer's own machine
    then measured 16.01, 16.01 and 18.31 and the sentence was simply wrong.

    The sentence is generated from the receipt now, the same way the test
    counts are, so it cannot be written by hand and cannot be wider than what
    was seen.
    """
    receipt = json.loads(RUNTIME.read_text(encoding="utf-8"))
    machines = len(receipt.get("runs") or [])
    if not machines:
        raise SystemExit("gate-runtime.json records no run; `make time-gate` writes it")
    return {"fastest": receipt["fastest"], "slowest": receipt["slowest"], "machines": machines}


def rewrite(counts: dict, dry_run: bool) -> list[str]:
    total = counts["python"] + counts["javascript"]
    band = runtime_band()
    # "on 1 machine" rather than "across the machines it has been measured on",
    # which read as several and was one.
    where = ("on 1 machine" if band["machines"] == 1
             else f"across {band['machines']} machines")
    edits = (
        (JUDGE, r"(?<=Tests in the offline gate</small>)<strong>\d+</strong>",
         f"<strong>{total}</strong>"),
        (JUDGE, r"\d+ tests, \d+ Python and \d+ JavaScript",
         f"{total} tests, {counts['python']} Python and {counts['javascript']} JavaScript"),
        (JUDGE, r"a submission gate over \d+ tracked files",
         f"a submission gate over {counts['files']} tracked files"),
        (README, r"`make check-offline` - \d+ tests", f"`make check-offline` - {total} tests"),
        (JUDGE, r"The gate runs between [\d.]+ and [\d.]+ seconds (?:on \d+ machine|across \d+ machines)",
         f"The gate runs between {band['fastest']} and {band['slowest']} seconds {where}"),
        (JUDGE, r"(?<=<small>Gate runtime</small>)<strong>[^<]*</strong>",
         f"<strong>&lt;{math.ceil(band['slowest'])}s</strong>"),
        (README, r"measured between [\d.]+ and [\d.]+ seconds (?:on \d+ machine|across \d+ machines|across machines)",
         f"measured between {band['fastest']} and {band['slowest']} seconds {where}"),
    )
    changed: list[str] = []
    pending: dict[Path, str] = {}
    for path, pattern, replacement in edits:
        text = pending.get(path, path.read_text(encoding="utf-8"))
        updated, hits = re.subn(pattern, replacement, text, count=1)
        if not hits:
            print(f"warning: {path.name} no longer carries /{pattern}/", file=sys.stderr)
        elif updated != text:
            changed.append(f"{path.name}: {replacement}")
        pending[path] = updated
    if not dry_run:
        for path, text in pending.items():
            path.write_text(text, encoding="utf-8")
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args(argv)
    counts = measure()
    total = counts["python"] + counts["javascript"]
    changed = rewrite(counts, args.dry_run)
    print(f"measured: {total} tests ({counts['python']} Python, {counts['javascript']} JavaScript), "
          f"{counts['files']} tracked files")
    for line in changed:
        print(f"  updated {line}")
    if not changed:
        print("  the documents already state these numbers")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Fail when the deployed site is not the site in this repository.

A reviewer scored this project down for a gap nobody was measuring: the
artefact judges are pointed at was not the artefact in the repository. The
deployed page had no link to /judge, /judge itself answered 404, its outcome
key omitted a state the repository publishes, and one example chip stated the
wrong verdict for a reference the page invites you to click. All of that was
fixed in the repository, none of it was deployed, and every gate was green
because no gate compared the two.

The browser audit does drive the deployed site, but it only runs on a schedule,
on the stated reasoning that a site outage must not redden a commit that is
fine. That reasoning is right about an outage and wrong about drift. So this
separates them:

  unreachable  -> reported and skipped, exit 0. Not the commit's fault.
  different    -> named and failed, exit 1. Exactly the commit's business.

It compares bytes, not behaviour, so it is cheap enough to run on every push
and needs no browser. `verify_public_browser.py` still owns behaviour.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
DEFAULT_BASE = "https://bell.dyplux.com"

# The files a judge actually reads, and the routes they are served at. A route
# whose repository file is missing is a bug in this list, not a pass.
SURFACES = (
    ("/", "index.html"),
    ("/judge", "judge.html"),
    ("/integrity.js", "integrity.js"),
    ("/explorer.js", "explorer.js"),
    ("/integrity.css", "integrity.css"),
)


def fetch(url: str, timeout: int) -> tuple[int, bytes]:
    request = urllib.request.Request(
        url, headers={"Accept": "*/*", "User-Agent": "Dyplux-Bell-DriftCheck/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def compare(base: str, timeout: int) -> tuple:
    drifted: list[str] = []
    unreachable: list[str] = []
    matched = 0

    for route, filename in SURFACES:
        local = SITE / filename
        if not local.exists():
            print(f"deployment drift check: {filename} is not in this repository", file=sys.stderr)
            return 1
        try:
            status, body = fetch(base + route, timeout)
        except Exception as error:
            unreachable.append(f"{route}: {type(error).__name__}: {error}")
            continue
        if status >= 500:
            unreachable.append(f"{route}: HTTP {status}")
            continue
        if status != 200:
            drifted.append(f"{route} answers HTTP {status}; this repository publishes {filename}")
            continue
        want = hashlib.sha256(local.read_bytes()).hexdigest()
        got = hashlib.sha256(body).hexdigest()
        if want != got:
            drifted.append(
                f"{route} serves {got[:12]} but {filename} in this commit is {want[:12]} "
                f"({len(body):,} bytes deployed against {local.stat().st_size:,} here)")
        else:
            matched += 1
    return drifted, unreachable, matched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument(
        "--wait", type=int, default=0, metavar="SECONDS",
        help=("keep re-checking for this long before reporting drift. A push and its deploy "
              "are two events, and CI runs between them, so a commit that is about to be "
              "correct was failing on the clock rather than on its contents. Drift that is "
              "real survives the wait; a propagation window does not."))
    args = parser.parse_args(argv)
    base = args.base.rstrip("/")

    deadline = time.monotonic() + max(args.wait, 0)
    attempts = 0
    while True:
        attempts += 1
        drifted, unreachable, matched = compare(base, args.timeout)
        if not drifted or time.monotonic() >= deadline:
            break
        remaining = deadline - time.monotonic()
        print(f"deployment drift check: {len(drifted)} surface(s) differ, {remaining:.0f}s of "
              f"the wait left; re-checking")
        time.sleep(min(10, max(1, remaining)))

    if attempts > 1 and not drifted:
        print(f"deployment drift check: matched after {attempts} attempts within the "
              f"{args.wait}s wait")

    if unreachable:
        # An outage is not a failing commit. Say so out loud rather than
        # returning a quiet zero, because a check that cannot be seen to have
        # skipped is indistinguishable from one that passed.
        print(f"deployment drift check: SKIPPED, {base} did not answer")
        for line in unreachable:
            print(f"  {line}")
        return 0

    if drifted:
        print(f"deployment drift check: {base} is not serving this commit", file=sys.stderr)
        for line in drifted:
            print(f"  {line}", file=sys.stderr)
        print("  Deploy this commit, or point --base at the origin that serves it.", file=sys.stderr)
        return 1

    print(f"deployment drift check: ok ({matched} surfaces byte-identical to this commit)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

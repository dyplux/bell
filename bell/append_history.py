#!/usr/bin/env python3
"""Append the published receipt's summary to the dated history, once per observation.

The history was eleven observations, nine of them on 21 September and eight of
those within six hours, because it was appended by hand from a Mac mini that had
to be awake. A series with that shape cannot answer "did this reference change
last week", which is the question a dated receipt exists to answer.

This runs from the scheduled workflow instead. It needs no CMC credential: the
receipt Bell publishes is credential-free by construction, so the series can be
built from the same bytes any reader can fetch.

It appends only when the observation is new. If the publisher has not run, the
live receipt still carries its previous `observed_at`, and writing that again
would manufacture a data point nobody observed - the same failure this product
exists to catch. In that case it prints what it saw and changes nothing.

Every appended observation records `rules_version`. Without it the page cannot
tell a rule change from a market change, and it spent five days reporting one as
the other.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

from history_chain import CHAIN_VERSION, link, verify

HERE = Path(__file__).resolve().parent
HISTORY = HERE / "site" / "proof" / "rwa-surface-integrity-history.json"
LIVE = "https://bell.dyplux.com/api/integrity"
SUMMARY_FIELDS = ("tokenised_references_scanned", "tokens_scanned", "states", "signals")


def load_receipt(source: str) -> dict:
    if source.startswith("http://") or source.startswith("https://"):
        request = Request(source, headers={"Accept": "application/json",
                                           "User-Agent": "Dyplux-Bell-History/1.0"})
        with urlopen(request, timeout=60) as response:
            if response.status != 200:
                raise SystemExit(f"receipt endpoint returned HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def summarise(receipt: dict) -> dict:
    observed_at = receipt.get("observed_at")
    universe = receipt.get("universe")
    if not observed_at or not isinstance(universe, dict):
        raise SystemExit("receipt carries no observed_at or no universe block")
    summary: dict = {"observed_at": observed_at}
    for field in SUMMARY_FIELDS:
        if field in universe:
            summary[field] = universe[field]
    # Recorded even when absent, as null rather than omitted: a reader must be
    # able to see that this observation did not declare its rule set, instead of
    # having to infer it from a missing key.
    summary["rules_version"] = universe.get("rules_version")
    summary["source_hashes"] = receipt.get("source_hashes", {})
    return summary


def append(history: dict, summary: dict) -> tuple[bool, str]:
    observations = history.setdefault("observations", [])
    seen = {str(item.get("observed_at")) for item in observations}
    if summary["observed_at"] in seen:
        return False, (f"no new observation: the published receipt still reads "
                       f"{summary['observed_at']}, which is already in the series")
    observations.append(summary)
    observations.sort(key=lambda item: str(item.get("observed_at") or ""))
    # Extending the chain, not appending beside it: a record added without a
    # link is a record nothing depends on, which is the state that let a
    # forged observation verify.
    previous = None
    for index, item in enumerate(observations):
        observations[index] = link(item, previous)
        previous = observations[index]["sha256"]
    history["chain_version"] = CHAIN_VERSION
    history["chain_head"] = verify(observations)
    return True, (f"appended {summary['observed_at']} under "
                  f"{summary['rules_version'] or 'an unrecorded rule set'}; "
                  f"chain head {history['chain_head'][:16]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--receipt", default=LIVE,
                        help="URL or path of the published receipt (default: the live endpoint)")
    parser.add_argument("--history", default=str(HISTORY), help="history file to update")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    args = parser.parse_args(argv)

    history_path = Path(args.history)
    history = json.loads(history_path.read_text(encoding="utf-8"))
    before = len(history.get("observations") or [])
    changed, message = append(history, summarise(load_receipt(args.receipt)))
    print(message)
    if changed and not args.dry_run:
        history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
        print(f"history: {before} -> {len(history['observations'])} observations")
    elif changed:
        print(f"dry run: would take the series to {len(history['observations'])} observations")
    return 0


if __name__ == "__main__":
    sys.exit(main())

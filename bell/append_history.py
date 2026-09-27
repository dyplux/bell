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
import re
import sys
from urllib.request import Request, urlopen

from history_chain import CHAIN_VERSION, link, verify

HERE = Path(__file__).resolve().parent
HISTORY = HERE / "site" / "proof" / "rwa-surface-integrity-history.json"
ANCHOR = HERE / "history-chain-head.txt"
# Two prose sentences state the length of the series. Appending the fourteenth
# observation left both reading thirteen, and the gate went red - correctly, but
# the fix belongs here rather than in the two files, because a count that is
# restated by hand drifts again on the next append.
RESTATE = (HERE / "site" / "judge.html", HERE.parent / "README.md")
COUNT_PHRASES = (
    (re.compile(r"Of the \d+ dated observations"), "Of the {n} dated observations"),
    (re.compile(r"every one of the \d+ is chained"), "every one of the {n} is chained"),
)
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
    """Extend the chain. Never rebuild it, and never write over a broken one.

    This rebuilt every record and then called `verify` on the list it had just
    built, so the verification could not fail and the pre-existing chain was
    never checked at all. A reviewer edited one record, ran this, and watched a
    detected forgery become a verified fifteen-record chain with a freshly
    written anchor - performed automatically, daily, by the CI job that commits
    and pushes both files. The one defence the judge page names, that a forger
    must also edit the anchor, was being carried out by the project itself, and
    the evidence of the original edit was destroyed.

    So: verify what is on disk first and refuse to touch it if it does not
    verify, then link only the new record to the existing head. An existing
    record is never re-linked, which means this can no longer rewrite history
    even by accident.
    """
    observations = history.setdefault("observations", [])
    seen = {str(item.get("observed_at")) for item in observations}
    if summary["observed_at"] in seen:
        return False, (f"no new observation: the published receipt still reads "
                       f"{summary['observed_at']}, which is already in the series")

    head = None
    if observations:
        # Refusing rather than repairing. A history that does not verify is a
        # question for a person, and appending to it would answer that question
        # with a clean chain.
        try:
            head = verify(observations)
        except ValueError as error:
            raise SystemExit(
                f"refusing to append: the history on disk does not verify. {error}\n"
                "Appending would rebuild the chain over this and write a new anchor, "
                "which would replace the evidence of the edit with a valid-looking series.")
        declared = history.get("chain_head")
        if declared != head:
            raise SystemExit(
                f"refusing to append: the history verifies to {head} but declares {declared!r}. "
                "Resolve that before extending the series.")
        # The anchor, which is the whole point. The previous fix checked the
        # head declared INSIDE the file it protects and then overwrote the
        # external anchor without ever reading it - so a forger who rebuilt the
        # chain and left the anchor stale had `make verify` fail, waited for the
        # 06:17 cron, and this job repaired the anchor and pushed it. The one
        # defence the judge page names, that a forger must edit a second tracked
        # file, was being carried out by the project on a schedule. Closing the
        # in-file case and leaving this one is the same half-fix this repository
        # has now recorded nine times.
        if ANCHOR.exists():
            anchored = ANCHOR.read_text(encoding="utf-8").strip()
            if anchored != head:
                raise SystemExit(
                    f"refusing to append: the history verifies to {head} and {ANCHOR.name} anchors "
                    f"{anchored}. They disagree, so either the series was rewritten or the anchor "
                    "was not updated with it. Appending would resolve that disagreement by "
                    "overwriting the anchor, which is the forgery this job must not perform.")
        else:
            raise SystemExit(
                f"refusing to append: {ANCHOR.name} is missing, so the chain has no anchor outside "
                "the file it protects and appending would create one over whatever is there.")
        newest = max(str(item.get("observed_at") or "") for item in observations)
        if summary["observed_at"] < newest:
            raise SystemExit(
                f"refusing to append: {summary['observed_at']} is older than {newest}, which is "
                "already the newest observation. A series that accepts backdated records cannot "
                "be read as a series.")

    observations.append(link(summary, head))
    history["chain_version"] = CHAIN_VERSION
    history["chain_head"] = observations[-1]["sha256"]
    # Verified after the write, over the whole series, not over a list this
    # function just rebuilt: every record before the new one is untouched, so
    # this is a real check of real data.
    if verify(observations) != history["chain_head"]:
        raise SystemExit("the extended chain does not verify; nothing was written")
    return True, (f"appended {summary['observed_at']} under "
                  f"{summary['rules_version'] or 'an unrecorded rule set'}; "
                  f"chain head {history['chain_head'][:16]}")


def restate_counts(total: int) -> list[str]:
    """Update the prose that states how long the series is.

    Only the two phrases that carry the count are touched, and a file that does
    not carry them is reported rather than silently skipped: a sentence that
    stopped matching is a sentence that will drift.
    """
    touched: list[str] = []
    for path in RESTATE:
        if not path.exists():
            continue
        text = original = path.read_text(encoding="utf-8")
        matched = 0
        for pattern, template in COUNT_PHRASES:
            text, hits = pattern.subn(template.format(n=total), text)
            matched += hits
        if not matched:
            print(f"warning: {path.name} no longer carries the observation count", file=sys.stderr)
        if text != original:
            path.write_text(text, encoding="utf-8")
            touched.append(path.name)
    return touched


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
    receipt = load_receipt(args.receipt)
    changed, message = append(history, summarise(receipt))
    print(message)
    if changed and not args.dry_run:
        history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
        # The head is anchored outside the file it protects, so it has to be
        # written with it. Leaving them apart would fail verification on the
        # next run, which is the correct failure but a needless one.
        ANCHOR.write_text(history["chain_head"] + "\n", encoding="utf-8")
        print(f"history: {before} -> {len(history['observations'])} observations")
        print(f"anchor: {ANCHOR.name} updated to {history['chain_head'][:16]}")
        restated = restate_counts(len(history["observations"]))
        if restated:
            print(f"restated the series length in {', '.join(restated)}")
        # The per-reference series grows by one point per observation, or it
        # never answers "what did THIS reference do". Stored as a delta against
        # the base snapshot: between 21 and 26 September 33 of 792 references
        # moved, which is 4.2 KB. A full snapshot per day would be 95 KB.
        try:
            from reference_series import DELTAS, record as record_series
            document, note = record_series(receipt)
            DELTAS.write_text(
                json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n",
                encoding="utf-8")
            print(f"reference series: {note}")
        except SystemExit as refusal:
            # A refusal here is a real finding, not a reason to lose the
            # observation that was just appended and written.
            print(f"reference series not extended: {refusal}", file=sys.stderr)
    elif changed:
        print(f"dry run: would take the series to {len(history['observations'])} observations")
    return 0


if __name__ == "__main__":
    sys.exit(main())

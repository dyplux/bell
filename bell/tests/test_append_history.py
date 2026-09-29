"""The dated series must grow by observation, never by schedule.

The history was eleven observations, nine of them on 21 September and eight of
those inside six hours, because appending was manual. Automating it introduces
the opposite risk: a job that runs daily will happily write a row every day even
when nothing new was published, turning a cron schedule into what looks like a
measurement series. That is the failure this product exists to catch, so it is
tested rather than trusted.
"""

from __future__ import annotations

import json
import gzip
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from history_chain import rebuild, verify as verify_chain  # noqa: E402
import append_history  # noqa: E402

REAL_ANCHOR = append_history.ANCHOR
from append_history import append, archive_receipt, restate_counts, summarise  # noqa: E402


class ReceiptArchiving(unittest.TestCase):
    def test_full_receipts_are_canonicalized_and_compressed_deterministically(self):
        receipt = {"observed_at": "2026-09-30T00:00:00Z", "universe": {"states": {}},
                   "source_hashes": {"map": "abc"}}
        path, digest, compressed = archive_receipt(receipt)
        expected = json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode("utf-8") + b"\n"
        self.assertEqual(path, "rwa-surface-integrity-receipts/2026-09-30T00-00-00Z.json.gz")
        self.assertEqual(digest, hashlib.sha256(expected).hexdigest())
        self.assertEqual(gzip.decompress(compressed), expected)
        self.assertEqual(archive_receipt(receipt)[2], compressed)

    def test_receipt_archive_refuses_noncanonical_or_backdated_labels(self):
        with self.assertRaises(SystemExit):
            archive_receipt({"observed_at": "not-a-timestamp"})


def history_of(*stamps: str) -> dict:
    """A real chained history, because append now refuses anything else.

    These fixtures were bare `{"observed_at": ...}` dicts with no chain fields.
    append used to re-link every record, so an unlinked history was silently
    converted into a linked one - the same operation that let the daily job
    launder a tampered record into a verified series. It refuses now, so the
    fixture has to be a chain.
    """
    observations = rebuild([{"observed_at": stamp} for stamp in stamps])
    head = observations[-1]["sha256"]
    # append() reads the external anchor before writing it now, because the
    # daily job was repairing a stale anchor over a forged chain. A synthetic
    # history needs a synthetic anchor, pointed at the repository's real one
    # only when a test means to use it.
    anchor = Path(tempfile.mkdtemp()) / "history-chain-head.txt"
    anchor.write_text(head + "\n", encoding="utf-8")
    append_history.ANCHOR = anchor
    return {"observations": observations, "chain_head": head}


def receipt(observed_at: str, rules: str | None = "bell.rules.v2") -> dict:
    universe = {
        "tokenised_references_scanned": 792,
        "tokens_scanned": 1442,
        "states": {"do_not_compare": 30, "investigate": 98, "no_flags": 664},
        "signals": {"PRICE_DENOMINATION_BREAK": 4},
    }
    if rules is not None:
        universe["rules_version"] = rules
    return {"observed_at": observed_at, "universe": universe,
            "source_hashes": {"map": "abc"}}


class AppendHistory(unittest.TestCase):
    def tearDown(self):
        # history_of points the module's ANCHOR at a temporary file. Left set,
        # it leaked into another test file and broke three tests there - a
        # fixture with a side effect nobody restored.
        append_history.ANCHOR = REAL_ANCHOR

    def test_a_new_observation_is_appended_with_its_rule_set(self):
        history = history_of("2026-09-21T21:25:01Z")
        changed, message = append(history, summarise(receipt("2026-09-26T20:08:35Z")))
        self.assertTrue(changed)
        self.assertIn("bell.rules.v2", message)
        self.assertEqual(len(history["observations"]), 2)
        self.assertEqual(history["observations"][-1]["rules_version"], "bell.rules.v2")
        self.assertIs(history["observations"][-1]["rules_version_recorded"], True)

    def test_an_unchanged_receipt_is_never_written_twice(self):
        # The publisher not having run is not an observation. Writing the same
        # timestamp again would manufacture a data point nobody made.
        history = history_of("2026-09-26T20:08:35Z")
        changed, message = append(history, summarise(receipt("2026-09-26T20:08:35Z")))
        self.assertFalse(changed)
        self.assertIn("already in the series", message)
        self.assertEqual(len(history["observations"]), 1)

    def test_a_receipt_without_a_rule_set_records_null_rather_than_omitting_it(self):
        # A reader must be able to see that the observation did not declare its
        # rules, instead of inferring it from a missing key.
        summary = summarise(receipt("2026-09-27T06:00:00Z", rules=None))
        self.assertIn("rules_version", summary)
        self.assertIsNone(summary["rules_version"])
        self.assertIs(summary["rules_version_recorded"], False)

    def test_a_backdated_observation_is_refused_rather_than_sorted_in(self):
        # This used to assert that a backdated record was sorted into place.
        # Sorting it in means re-linking every record after it, which is the
        # rebuild that let a tampered history be laundered into a verified one.
        # A series that accepts backdated records is also not a series. So it
        # refuses, and the order is preserved by never inserting.
        history = history_of("2026-09-26T20:08:35Z")
        with self.assertRaises(SystemExit) as raised:
            append(history, summarise(receipt("2026-09-22T06:00:00Z")))
        self.assertIn("older than", str(raised.exception))
        self.assertEqual(len(history["observations"]), 1)

    def test_appending_leaves_the_series_in_observation_order_and_verifying(self):
        history = history_of("2026-09-21T21:25:01Z", "2026-09-22T06:00:00Z")
        append(history, summarise(receipt("2026-09-26T20:08:35Z")))
        stamps = [item["observed_at"] for item in history["observations"]]
        self.assertEqual(stamps, sorted(stamps))
        self.assertEqual(verify_chain(history["observations"]), history["chain_head"])

    def test_a_receipt_missing_its_universe_is_refused(self):
        with self.assertRaises(SystemExit):
            summarise({"observed_at": "2026-09-27T06:00:00Z"})
        with self.assertRaises(SystemExit):
            summarise({"universe": {"states": {}}})

    def test_the_shipped_history_carries_a_rule_set_on_its_newest_observation(self):
        # Item one of this work made the page refuse a delta across a rule
        # boundary. That refusal is only informative if new observations declare
        # which side of the boundary they are on.
        path = HERE.parent / "site" / "proof" / "rwa-surface-integrity-history.json"
        observations = json.loads(path.read_text(encoding="utf-8"))["observations"]
        self.assertIn("rules_version", observations[-1])
        self.assertEqual(observations[-1]["rules_version"], "bell.rules.v2")

    def test_appending_restates_the_series_length_in_the_prose_that_claims_it(self):
        # Appending the fourteenth observation left judge.html and README.md
        # reading thirteen. The gate caught it, which is the gate working, and
        # then the fix was applied to the two sentences rather than to the thing
        # that writes them - which is how the same drift comes back on the
        # fifteenth. So the appender restates them, and this checks it does.
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "judge.html"
            page.write_text("<p>Of the 13 dated observations, 2 ship their full payload, "
                            "and every one of the 13 is chained to the one before it.</p>",
                            encoding="utf-8")
            readme = Path(tmp) / "README.md"
            readme.write_text("| Of the 13 dated observations, 2 ship |\n", encoding="utf-8")
            original = append_history.RESTATE
            append_history.RESTATE = (page, readme)
            try:
                touched = restate_counts(14)
            finally:
                append_history.RESTATE = original
            rewritten = page.read_text(encoding="utf-8")
            self.assertEqual(sorted(touched), ["README.md", "judge.html"])
            self.assertIn("Of the 14 dated observations", rewritten)
            self.assertIn("every one of the 14 is chained", rewritten)
            self.assertIn("Of the 14 dated observations", readme.read_text(encoding="utf-8"))
            # Both counts move, not just the first: they are two separate
            # phrases and the drift that started this updated neither.
            self.assertNotIn("13", rewritten)

    def test_the_shipped_prose_states_the_length_the_shipped_series_actually_has(self):
        # The check above proves the mechanism; this one proves it was run. A
        # rewriter nobody invoked leaves exactly the red gate it exists to stop.
        history = json.loads((HERE.parent / "site" / "proof"
                              / "rwa-surface-integrity-history.json").read_text(encoding="utf-8"))
        total = len(history["observations"])
        for path in (HERE.parent / "site" / "judge.html", HERE.parent.parent / "README.md"):
            self.assertIn(f"Of the {total} dated observations", path.read_text(encoding="utf-8"),
                          f"{path.name} states a series length the history does not have")

    def test_the_scheduled_job_only_commits_when_the_file_changed(self):
        workflow = (HERE.parent.parent / ".github" / "workflows" / "bell-quality.yml").read_text()
        self.assertIn("bell/append_history.py", workflow)
        self.assertRegex(workflow, r"if git diff --quiet(?!\s+--\s)",
                         "the job decides whether to commit by looking at a hand-written list "
                         "of files instead of at the tree it just changed")
        # It must never run on a push: a commit is not an observation either.
        self.assertIn("if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",
                      workflow)

    def test_the_scheduled_job_stages_everything_the_script_wrote(self):
        """A list of filenames beside a script that chooses filenames drifts.

        It drifted twice. First reference-deltas.json was written by
        append_history and never staged, so the per-reference series could not
        grow by the automatic path the documents describe. Then, with that
        fixed, the job's first real commit left out judge.html, README.md and
        bell/README.md, which this script restates the series length into: it
        landed a history of 16 observations beside prose saying 15, and
        `make check-offline` went red on main on a commit no human wrote.

        The script already decides what it writes, and it prints the list. The
        job must not keep a second copy of that decision.
        """
        workflow = (HERE.parent.parent / ".github" / "workflows" / "bell-quality.yml").read_text()
        step = workflow[workflow.index("Commit only when the series actually grew"):]
        step = step[:step.index("git push") + len("git push")]
        self.assertIn("git add -A", step)
        named = [line.strip() for line in step.splitlines()
                 if line.strip().startswith("git add ") and "-A" not in line]
        self.assertEqual(named, [],
                         "the commit step names files by hand; append_history decides which "
                         "files it writes and the list has been wrong twice")
        # Every file the script restates into has to be reachable by that add.
        for target in append_history.RESTATE:
            self.assertTrue(target.exists(), f"{target} no longer exists to be restated")


if __name__ == "__main__":
    unittest.main()

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
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from append_history import append, summarise  # noqa: E402


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
    def test_a_new_observation_is_appended_with_its_rule_set(self):
        history = {"observations": [{"observed_at": "2026-09-21T21:25:01Z"}]}
        changed, message = append(history, summarise(receipt("2026-09-26T20:08:35Z")))
        self.assertTrue(changed)
        self.assertIn("bell.rules.v2", message)
        self.assertEqual(len(history["observations"]), 2)
        self.assertEqual(history["observations"][-1]["rules_version"], "bell.rules.v2")

    def test_an_unchanged_receipt_is_never_written_twice(self):
        # The publisher not having run is not an observation. Writing the same
        # timestamp again would manufacture a data point nobody made.
        history = {"observations": [{"observed_at": "2026-09-26T20:08:35Z"}]}
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

    def test_observations_stay_in_observation_order(self):
        history = {"observations": [{"observed_at": "2026-09-26T20:08:35Z"}]}
        append(history, summarise(receipt("2026-09-22T06:00:00Z")))
        stamps = [item["observed_at"] for item in history["observations"]]
        self.assertEqual(stamps, sorted(stamps))

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

    def test_the_scheduled_job_only_commits_when_the_file_changed(self):
        workflow = (HERE.parent.parent / ".github" / "workflows" / "bell-quality.yml").read_text()
        self.assertIn("bell/append_history.py", workflow)
        self.assertIn("git diff --quiet -- bell/site/proof/rwa-surface-integrity-history.json",
                      workflow)
        # It must never run on a push: a commit is not an observation either.
        self.assertIn("if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'",
                      workflow)


if __name__ == "__main__":
    unittest.main()

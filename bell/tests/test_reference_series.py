"""The per-reference series must grow honestly, or not at all.

A reviewer named this the largest usefulness gap: "a product sold to someone
tracking tokenised assets needs to answer 'what did this reference do over the
last month', and today it cannot". The repository holds full per-reference
detail for one dated observation and the live receipt; it cannot manufacture
the days between, and the point of this file is that it does not try.

What it does is stop discarding the detail, so the series gains a point per
published observation, stored as a delta because references mostly do not move.
The tests that matter here are the refusals: a series that spans a rule change
would report the rule change as market movement, and a series that accepts a
backdated point is not a series.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from reference_series import (  # noqa: E402
    BASE, DELTAS, apply, delta, record, series_for, snapshot_of)

BASE_DOC = json.loads(BASE.read_text(encoding="utf-8"))
REPLAY = json.loads((HERE.parent / "site" / "proof"
                     / "rwa-surface-integrity-latest-replay-2026-09-21.json")
                    .read_text(encoding="utf-8"))


def receipt_with(observed_at: str, rules: str | None = "bell.rules.v2", **changes) -> dict:
    payload = {"observed_at": observed_at,
               "universe": {"rules_version": rules} if rules else {},
               "alert_index": copy.deepcopy(REPLAY["alert_index"])}
    for rwa_id, fields in changes.items():
        for row in payload["alert_index"]:
            if str(row.get("rwa_id")) == rwa_id:
                row.update(fields)
    return payload


class DeltasReplayExactly(unittest.TestCase):
    def test_a_delta_applied_to_the_base_reproduces_the_current_state(self):
        current = snapshot_of(receipt_with("2026-09-30T00:00:00Z"))
        step = delta(BASE_DOC["references"], current)
        self.assertEqual(apply(BASE_DOC["references"], [step]), current,
                         "replaying the delta does not reproduce the observation it came from")

    def test_a_delta_records_only_what_moved(self):
        base = {"1": {"state": "no_flags"}, "2": {"state": "investigate"}}
        step = delta(base, {"1": {"state": "no_flags"}, "2": {"state": "do_not_compare"}})
        self.assertEqual(list(step["changed"]), ["2"],
                         "the delta carries references that did not move, which is the whole cost")
        self.assertEqual(step["removed"], [])

    def test_a_reference_that_disappears_is_a_removal_not_an_empty_value(self):
        step = delta({"1": {"state": "no_flags"}}, {})
        self.assertEqual(step["removed"], ["1"])
        self.assertEqual(apply({"1": {"state": "no_flags"}}, [step]), {})


class TheSeriesRefusesWhatItCannotMean(unittest.TestCase):
    def test_it_refuses_to_span_a_rule_change(self):
        # A state is a function of the rules. Replaying a v3 observation onto a
        # v2 series would print the rule change as movement, which is the error
        # this whole product exists to refuse.
        with self.assertRaises(SystemExit) as raised:
            record(receipt_with("2026-09-30T00:00:00Z", rules="bell.rules.v3"))
        self.assertIn("reports the rule change as market movement", str(raised.exception))

    def test_it_refuses_an_unversioned_receipt(self):
        with self.assertRaises(SystemExit):
            record(receipt_with("2026-09-30T00:00:00Z", rules=None))

    def test_it_refuses_a_backdated_point(self):
        with self.assertRaises(SystemExit) as raised:
            record(receipt_with("2020-01-01T00:00:00Z"))
        self.assertIn("older than", str(raised.exception))

    def test_it_does_not_write_the_same_observation_twice(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        newest = shipped["observations"][-1]["observed_at"]
        _, message = record(receipt_with(newest))
        self.assertIn("already in the series", message)

    def test_a_new_observation_extends_the_series_by_one(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        document, message = record(receipt_with("2026-09-30T00:00:00Z"))
        self.assertEqual(len(document["observations"]), len(shipped["observations"]) + 1)
        self.assertIn("series is now", message)


class TheShippedSeriesIsWhatTheCodeDerives(unittest.TestCase):
    def test_the_deltas_file_replays_onto_a_state_every_reference_can_be_read_from(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        self.assertEqual(shipped["base"], BASE.name)
        self.assertEqual(shipped["rules_version"], BASE_DOC["rules_version"],
                         "the series and its base answer to different rule sets")
        replayed = apply(BASE_DOC["references"], shipped["observations"])
        self.assertGreaterEqual(len(replayed), len(BASE_DOC["references"]) - 1)
        for value in replayed.values():
            self.assertEqual(sorted(value), ["comparison_published", "representations",
                                             "signal_codes", "state"])

    def test_the_series_is_in_observation_order(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        stamps = [step["observed_at"] for step in shipped["observations"]]
        self.assertEqual(stamps, sorted(stamps))
        for stamp in stamps:
            self.assertGreater(stamp, BASE_DOC["observed_at"],
                               "a delta predates the base it is applied to")

    def test_a_reference_that_moved_shows_more_than_one_point(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        moved = {key for step in shipped["observations"] for key in (step.get("changed") or {})}
        self.assertTrue(moved, "no reference moved in the whole series, so nothing is exercised")
        key = sorted(moved)[0]
        points = series_for(key, BASE_DOC["references"], BASE_DOC["observed_at"],
                            shipped["observations"])
        self.assertGreater(len(points), 1)
        self.assertTrue(points[0]["baseline"])
        self.assertFalse(points[-1]["baseline"])

    def test_a_reference_that_did_not_move_shows_only_its_baseline(self):
        shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        moved = {key for step in shipped["observations"] for key in (step.get("changed") or {})}
        still = sorted(set(BASE_DOC["references"]) - moved)
        self.assertTrue(still, "every reference moved, so this proves nothing")
        points = series_for(still[0], BASE_DOC["references"], BASE_DOC["observed_at"],
                            shipped["observations"])
        self.assertEqual(len(points), 1)

    def test_the_series_stays_small_enough_to_ship_daily(self):
        # The design claim: a delta per observation rather than a snapshot per
        # observation. If this stops holding, the series has become the thing
        # it was built to avoid.
        per_observation = DELTAS.stat().st_size / max(
            len(json.loads(DELTAS.read_text(encoding="utf-8"))["observations"]), 1)
        self.assertLess(per_observation, BASE.stat().st_size / 4,
                        f"a point costs {per_observation:,.0f} bytes against a "
                        f"{BASE.stat().st_size:,}-byte snapshot; the delta is not paying for itself")


if __name__ == "__main__":
    unittest.main()

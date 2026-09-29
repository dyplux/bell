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
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def history_with(*stamps: str) -> dict:
    """A history that records these observations, so a test can place a point.

    `record` refuses an observation the published history does not carry, which
    is the fix for a series point that named a day the history did not. A test
    that wants to place a point therefore has to say which history it means.
    """
    return {"observations": [{"observed_at": stamp, "rules_version": "bell.rules.v2"}
                             for stamp in stamps]}

import reference_series  # noqa: E402
from reference_series import (  # noqa: E402
    BASE, DELTAS, apply, build_versioned_series, delta, digest_of_state, index_digest,
    record, record_versioned_series, series_for, snapshot_of, verify_versioned_series,
    verify_versioned_series_document)

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


class TheSeriesRefusesMalformedOrBackdatedPoints(unittest.TestCase):
    def setUp(self):
        self.shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        self.newest = self.shipped["observations"][-1]["observed_at"]

    def test_it_refuses_to_span_a_rule_change(self):
        # A state is a function of the rules. Replaying a v3 observation onto a
        # v2 series would print the rule change as movement, which is the error
        # this whole product exists to refuse.
        with self.assertRaises(SystemExit) as raised:
            record(receipt_with("2026-09-30T00:00:00Z", rules="bell.rules.v3"),
                   history_with(self.newest, "2026-09-30T00:00:00Z"))
        self.assertIn("reports the rule change as market movement", str(raised.exception))


class RetainedReceiptsVerifySeriesRows(unittest.TestCase):
    def _fixture(self, proof: Path):
        base = {"1": {"state": "no_flags", "representations": 1,
                       "comparison_published": False, "signal_codes": []}}
        stamp = "2026-09-30T00:00:00Z"
        receipt = {
            "observed_at": stamp,
            "source_hashes": {"map": "source-map"},
            "universe": {"rules_version": "bell.rules.v2"},
            "alert_index": [{"rwa_id": "1", "state": "do_not_compare", "token_count": 2,
                             "comparison": None, "signal_codes": ["PRICE_DISPERSION"]}],
        }
        current = snapshot_of(receipt)
        canonical = json.dumps(receipt, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8") + b"\n"
        relative = "rwa-surface-integrity-receipts/2026-09-30T00-00-00Z.json.gz"
        archive = proof / relative
        archive.parent.mkdir(parents=True)
        archive.write_bytes(gzip.compress(canonical, compresslevel=9, mtime=0))
        step = delta(base, current)
        step.update({"observed_at": stamp, "source_hashes": receipt["source_hashes"],
                     "alert_index_sha256": index_digest(receipt)})
        digest = digest_of_state(current)
        history = {"observations": [{
            "observed_at": stamp, "rules_version": "bell.rules.v2",
            "source_hashes": receipt["source_hashes"], "reference_digest": digest,
            "receipt_path": relative, "receipt_sha256": hashlib.sha256(canonical).hexdigest(),
        }]}
        base_doc = {"observed_at": "2026-09-29T00:00:00Z", "references": base,
                    "rules_version": "bell.rules.v2"}
        deltas_doc = {"base": BASE.name, "rules_version": "bell.rules.v2",
                      "observations": [step]}
        return base_doc, deltas_doc, history

    def test_receipt_archive_is_compared_row_for_row_with_the_replayed_series(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp)
            base_doc, deltas_doc, history = self._fixture(proof)
            original = reference_series.PROOF
            reference_series.PROOF = proof
            try:
                notes = reference_series.verify(base_doc, deltas_doc, history)
            finally:
                reference_series.PROOF = original
        self.assertIn("receipt rows verified", notes[0])

    def test_a_rewritten_series_step_is_refused_even_with_updated_self_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            proof = Path(tmp)
            base_doc, deltas_doc, history = self._fixture(proof)
            deltas_doc["observations"][0]["changed"]["1"]["state"] = "no_flags"
            forged_state = apply(base_doc["references"], deltas_doc["observations"])
            forged_digest = digest_of_state(forged_state)
            deltas_doc["observations"][0]["alert_index_sha256"] = forged_digest
            history["observations"][0]["reference_digest"] = forged_digest
            original = reference_series.PROOF
            reference_series.PROOF = proof
            try:
                with self.assertRaisesRegex(ValueError, "reference rows do not match"):
                    reference_series.verify(base_doc, deltas_doc, history)
            finally:
                reference_series.PROOF = original

class TheSeriesRefusesWhatItCannotMean(unittest.TestCase):
    def setUp(self):
        self.shipped = json.loads(DELTAS.read_text(encoding="utf-8"))
        self.newest = self.shipped["observations"][-1]["observed_at"]

    def test_it_refuses_an_unversioned_receipt(self):
        with self.assertRaises(SystemExit):
            record(receipt_with("2026-09-30T00:00:00Z", rules=None),
                   history_with(self.newest, "2026-09-30T00:00:00Z"))

    def test_it_refuses_a_backdated_point(self):
        # Recorded by the history, so the membership check passes and the
        # ordering check is the one being tested.
        with self.assertRaises(SystemExit) as raised:
            record(receipt_with("2020-01-01T00:00:00Z"),
                   history_with("2020-01-01T00:00:00Z", self.newest))
        self.assertIn("older than", str(raised.exception))

    def test_it_does_not_write_the_same_observation_twice(self):
        _, message = record(receipt_with(self.newest), history_with(self.newest))
        self.assertIn("already in the series", message)

    def test_a_new_observation_extends_the_series_by_one(self):
        document, message = record(receipt_with("2026-09-30T00:00:00Z"),
                                   history_with(self.newest, "2026-09-30T00:00:00Z"))
        self.assertEqual(len(document["observations"]), len(self.shipped["observations"]) + 1)
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


class RetainedRuleVersionSeries(unittest.TestCase):
    def setUp(self):
        self.history = json.loads((HERE.parent / "site" / "proof"
                                   / "rwa-surface-integrity-history.json")
                                  .read_text(encoding="utf-8"))

    def test_v3_segment_is_derived_only_from_the_two_retained_v3_receipts(self):
        document = build_versioned_series(self.history, "bell.rules.v3")
        self.assertEqual(document["schema_version"], "bell.reference_deltas_by_rules.v1")
        self.assertEqual(document["base"]["observed_at"], "2026-09-29T23:08:10Z")
        self.assertEqual(len(document["observations"]), 1)
        step = document["observations"][0]
        self.assertEqual(step["observed_at"], "2026-09-29T23:23:34Z")
        self.assertEqual(len(step["changed"]), 2)
        self.assertEqual(step["removed"], [])
        self.assertEqual(step["changed"]["140"]["state"], "investigate")
        self.assertNotIn("ZERO_MCAP_POSITIVE_VOLUME", step["changed"]["140"]["signal_codes"])

    def test_shipped_v3_segment_replays_from_retained_receipts(self):
        notes = verify_versioned_series(self.history)
        self.assertEqual(len(notes), 1)
        self.assertIn("2 reference changes verified", notes[0])

    def test_append_path_rebuilds_the_versioned_file_from_retained_history(self):
        with tempfile.TemporaryDirectory() as temp:
            proof = Path(temp)
            receipts = [item for item in self.history["observations"]
                        if item.get("rules_version") == "bell.rules.v3" and item.get("receipt_path")]
            for item in receipts:
                source = reference_series.PROOF / item["receipt_path"]
                destination = proof / item["receipt_path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            original = reference_series.PROOF
            reference_series.PROOF = proof
            try:
                notes = record_versioned_series(self.history)
                self.assertEqual(len(notes), 1)
                self.assertEqual(len(verify_versioned_series(self.history)), 1)
            finally:
                reference_series.PROOF = original

    def test_v3_segment_cannot_claim_a_different_row_change(self):
        path = HERE.parent / "site" / "proof" / "reference-deltas-v3.json"
        shipped = json.loads(path.read_text(encoding="utf-8"))
        shipped["observations"][0]["changed"]["140"]["state"] = "no_flags"
        with self.assertRaisesRegex(ValueError, "differs from the series derived"):
            verify_versioned_series_document(shipped, self.history, "bell.rules.v3")


class TheSeriesAnswersToThePublishedHistory(unittest.TestCase):
    """A step that names a day nobody published is a day nobody observed.

    The first version stamped a point at 23:43:43 while the history's newest
    observation was 23:28:21, and nothing reconciled them - two surfaces
    describing one day and disagreeing, in the product named after that defect.
    """

    def setUp(self):
        from reference_series import verify as verify_series
        self.verify = verify_series
        self.history = json.loads((HERE.parent / "site" / "proof"
                                   / "rwa-surface-integrity-history.json")
                                  .read_text(encoding="utf-8"))
        self.deltas = json.loads(DELTAS.read_text(encoding="utf-8"))

    def test_the_shipped_series_answers_to_the_shipped_history(self):
        notes = self.verify(BASE_DOC, self.deltas, self.history)
        self.assertEqual(len(notes), len(self.deltas["observations"]))

    def test_a_step_the_history_does_not_record_is_refused(self):
        # Appended rather than renamed: renaming leaves the observation that
        # anchored its digest orphaned, and the orphan check refuses first.
        # Both refusals are correct and they are the same forgery seen from
        # two sides; this one exercises the step check.
        forged = copy.deepcopy(self.deltas)
        invented = copy.deepcopy(forged["observations"][-1])
        invented["observed_at"] = "2099-01-01T00:00:00Z"
        forged["observations"].append(invented)
        with self.assertRaisesRegex(ValueError, "the published history does not record"):
            self.verify(BASE_DOC, forged, self.history)

    def test_an_observation_whose_step_was_removed_is_refused(self):
        # The other side: the history still anchors a digest for a step that is
        # no longer there. Emptying the series used to return an empty list and
        # print "1 points" while an observation claimed a digest nothing checked.
        forged = copy.deepcopy(self.deltas)
        forged["observations"] = []
        with self.assertRaisesRegex(ValueError, "the series has no step for it"):
            self.verify(BASE_DOC, forged, self.history)

    def test_a_step_claiming_the_wrong_source_digests_is_refused(self):
        forged = copy.deepcopy(self.deltas)
        forged["observations"][0]["source_hashes"] = {"map": "0" * 64}
        with self.assertRaisesRegex(ValueError, "source fingerprints"):
            self.verify(BASE_DOC, forged, self.history)

    def test_a_step_with_no_origin_recorded_is_refused(self):
        for field in ("source_hashes", "alert_index_sha256"):
            forged = copy.deepcopy(self.deltas)
            forged["observations"][0].pop(field, None)
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.verify(BASE_DOC, forged, self.history)

    def test_record_refuses_a_receipt_the_history_does_not_carry(self):
        with self.assertRaises(SystemExit) as raised:
            record(receipt_with("2030-01-01T00:00:00Z"))
        self.assertIn("not in the published history", str(raised.exception))

    def test_every_step_records_the_digest_of_the_index_it_came_from(self):
        from reference_series import index_digest
        for step in self.deltas["observations"]:
            self.assertRegex(step["alert_index_sha256"], r"^[0-9a-f]{64}$")
        # And the digest is a function of the rows, not of the file's byte order.
        one = {"alert_index": [{"rwa_id": "2", "state": "no_flags", "token_count": 1},
                               {"rwa_id": "1", "state": "investigate", "token_count": 2}]}
        other = {"alert_index": list(reversed(one["alert_index"]))}
        self.assertEqual(index_digest(one), index_digest(other))
        moved = {"alert_index": [{"rwa_id": "1", "state": "do_not_compare", "token_count": 2},
                                 {"rwa_id": "2", "state": "no_flags", "token_count": 1}]}
        self.assertNotEqual(index_digest(one), index_digest(moved))


class EverySeriesRefusalIsDefended(unittest.TestCase):
    """Seven refusals in reference_series.py were defended by nothing.

    `make mutate` found them: it rewrites each guard's condition so the body
    cannot run and asks whether the gate notices. Three reviewers did that by
    hand before it existed, and every one of these is a refusal I wrote and
    never tested.
    """

    def setUp(self):
        from reference_series import verify as verify_series
        self.verify = verify_series
        self.history = json.loads((HERE.parent / "site" / "proof"
                                   / "rwa-surface-integrity-history.json")
                                  .read_text(encoding="utf-8"))
        self.deltas = json.loads(DELTAS.read_text(encoding="utf-8"))

    def test_a_series_built_on_another_base_is_refused(self):
        forged = copy.deepcopy(self.deltas)
        forged["base"] = "some-other-snapshot.json"
        with self.assertRaisesRegex(ValueError, "is built on"):
            self.verify(BASE_DOC, forged, self.history)

    def test_a_series_under_another_rule_set_than_its_base_is_refused(self):
        forged = copy.deepcopy(self.deltas)
        forged["rules_version"] = "bell.rules.v9"
        with self.assertRaisesRegex(ValueError, "different rule sets"):
            self.verify(BASE_DOC, forged, self.history)

    def test_a_step_that_does_not_advance_the_clock_is_refused(self):
        # Backdated by appending rather than renaming: renaming orphans the
        # observation that anchors the step's digest, and that refusal fires
        # first. Both are correct; this one exercises the clock.
        forged = copy.deepcopy(self.deltas)
        stale = copy.deepcopy(forged["observations"][-1])
        stale["observed_at"] = BASE_DOC["observed_at"]
        forged["observations"].append(stale)
        with self.assertRaisesRegex(ValueError, "is not after"):
            self.verify(BASE_DOC, forged, self.history)

    def test_a_step_whose_observation_answers_to_another_rule_set_is_refused(self):
        forged_history = copy.deepcopy(self.history)
        stamp = self.deltas["observations"][0]["observed_at"]
        for item in forged_history["observations"]:
            if item["observed_at"] == stamp:
                item["rules_version"] = "bell.rules.v9"
        with self.assertRaisesRegex(ValueError, "was recorded under"):
            self.verify(BASE_DOC, self.deltas, forged_history)

    def test_a_step_with_no_source_fingerprints_is_refused(self):
        forged = copy.deepcopy(self.deltas)
        forged["observations"][0]["source_hashes"] = {}
        with self.assertRaisesRegex(ValueError, "records no source fingerprints"):
            self.verify(BASE_DOC, forged, self.history)

    def test_an_observation_that_predates_the_anchor_field_is_reported_not_failed(self):
        # The branch that says "this observation was written before the history
        # carried the digest". It must report rather than refuse, or every
        # series older than the mechanism becomes unverifiable.
        forged_history = copy.deepcopy(self.history)
        for item in forged_history["observations"]:
            item.pop("reference_digest", None)
        notes = self.verify(BASE_DOC, self.deltas, forged_history)
        self.assertTrue(any("not anchored" in note for note in notes),
                        f"the unanchored case is not reported: {notes}")

    def test_a_receipt_with_no_observed_at_is_refused_by_record(self):
        with self.assertRaises(SystemExit) as raised:
            record({"universe": {"rules_version": "bell.rules.v2"}, "alert_index": []})
        self.assertIn("observed_at", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

"""Forge the evidence four ways and require the verifier to say so.

A reviewer found three places where the central verifier could be made to pass
over a forged file, all of the same shape: a conditional the forger controls.
Remove the evidence and the check that guards it disappears with it.

  1. Rewrite the cross-checked receipt's whole state distribution, then add
     `rules_version: "bell.rules.v3"`. The state comparison is skipped when the
     versions differ, and the version is read from the file being audited, so
     the attacker declares the comparison inapplicable. Exit 0.
  2. Delete `request_count`, `successful_response_count`, `response_sha256` and
     `status_codes` from all six surfaces. The provenance block was guarded by
     "if any of these four is present". Exit 0, over a package 5.9 MB lighter.
  3. Set every response fingerprint to sixty-four zeroes. They were checked for
     length and compared to nothing, while the page renders them as transport
     evidence. Exit 0, whole suite green.
  4. Edit a history record, then run the daily append job. It rebuilt every
     link and called verify on the list it had just built, so a detected
     forgery became a verified chain with a fresh anchor - committed and pushed
     by CI.

This project's thesis is that a check nobody sees fail is not a check. These
are the four, each run against a real copy of the shipped evidence.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
BELL = HERE.parent
sys.path.insert(0, str(BELL))

PROOF = BELL / "site" / "proof"
DATED = "rwa-surface-integrity-2026-09-15.json"
INPUTS = "rwa-surface-integrity-inputs-2026-09-21.json"
LATEST = "rwa-surface-integrity-latest-replay-2026-09-21.json"
HISTORY = "rwa-surface-integrity-history.json"


class Forgery(unittest.TestCase):
    """Forge the shipped evidence and require the verifier to name it.

    The surfaces are parsed once for the whole class: re-reading 16.5 MB per
    forgery put three seconds into a gate whose runtime this repository
    publishes. Only the manifest, a few kilobytes, is copied per test, and the
    forgeries all live there or in the dated receipt.
    """

    @classmethod
    def setUpClass(cls):
        from verify_integrity_receipt import (
            verify_collection_manifest, verify_observation, load)
        cls.verify_collection_manifest = staticmethod(verify_collection_manifest)
        cls.verify_observation = staticmethod(verify_observation)
        package = load(PROOF / INPUTS)
        cls.surfaces = package["surfaces"]
        cls.manifest = package["collection_manifest"]
        cls.names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
        cls.history = load(PROOF / HISTORY)
        cls.dated = load(PROOF / DATED)

    def manifest_copy(self) -> dict:
        return copy.deepcopy(self.manifest)

    def dated_observation(self) -> dict:
        observed = self.dated["observed_at"]
        for item in self.history["observations"]:
            if item["observed_at"] == observed:
                return copy.deepcopy(item)
        self.fail(f"{DATED} is not in the shipped history, so nothing cross-checks it")

    def test_no_declared_rule_set_can_excuse_a_rewritten_distribution(self):
        # The first version of this test only tried "bell.rules.v3", a version
        # this repository never published, and the fix only refused unpublished
        # ones. A reviewer then used "bell.rules.v1" - real, published, and
        # never stamped by any publisher in this tree - and rewrote the whole
        # distribution through a green 306-test gate. One value of a field is
        # not the field, so every value that is not the current one is tried.
        for declared in ("bell.rules.v1", "bell.rules.v2.1", "bell.rules.v3", ""):
            receipt = copy.deepcopy(self.dated)
            receipt["universe"]["states"] = {"do_not_compare": 0, "investigate": 0,
                                             "no_flags": 790}
            if declared:
                receipt["universe"]["rules_version"] = declared
            else:
                receipt["universe"].pop("rules_version", None)
            with self.subTest(declared=declared or "absent"), \
                    self.assertRaises(ValueError, msg=f"{declared!r} switched the check off"):
                self.verify_observation(self.dated_observation(), receipt, "forged")

    def test_the_current_rule_set_is_accepted_and_still_compared(self):
        # The control: refusing every version would also refuse every forgery.
        # A receipt stamped by this tree's publisher must be accepted, and its
        # states must actually be compared rather than waved through.
        from rwa_integrity import RULES_VERSION
        observation = self.dated_observation()
        receipt = copy.deepcopy(self.dated)
        receipt["universe"]["rules_version"] = RULES_VERSION
        observation["rules_version"] = RULES_VERSION
        observation["rules_version_recorded"] = True
        self.assertTrue(self.verify_observation(observation, receipt, "current"))
        receipt["universe"]["states"] = {"do_not_compare": 0, "investigate": 0, "no_flags": 790}
        with self.assertRaises(ValueError):
            self.verify_observation(observation, receipt, "current but rewritten")


    def test_emptying_the_claimed_signals_does_not_empty_the_comparison(self):
        # A reviewer emptied the history record's signals, zeroed every signal
        # in the receipt, rebuilt the chain and the anchor, and the gate went
        # green while printing that signals WERE compared - because the
        # comparison projected the receipt onto the keys the record claimed.
        # Every contradiction the product exists to find, erased by a check the
        # forger scoped.
        observation = self.dated_observation()
        receipt = copy.deepcopy(self.dated)
        receipt["universe"]["signals"] = {key: 0 for key in receipt["universe"]["signals"]}
        observation["signals"] = {}
        with self.assertRaises(ValueError) as raised:
            self.verify_observation(observation, receipt, "signals deleted")
        self.assertIn("signals", str(raised.exception))

    def test_a_shortened_signal_claim_does_not_shorten_the_comparison(self):
        # The same shape one step subtler: keep one signal so the dict is not
        # empty, and the projection still ignores everything else.
        observation = self.dated_observation()
        receipt = copy.deepcopy(self.dated)
        keep = sorted(observation["signals"])[0]
        observation["signals"] = {keep: observation["signals"][keep]}
        with self.assertRaises(ValueError):
            self.verify_observation(observation, receipt, "signals shortened")

    def test_two_bundled_receipts_cannot_claim_one_observation(self):
        # Relabelling the dated receipt to the latest receipt's timestamp made
        # one overwrite the other in a dict literal, so it was compared to
        # nothing. This lived inside main(), which the rest of this file never
        # exercised; it is a function now so it can be.
        from verify_integrity_receipt import bundle
        first = {"observed_at": "2026-09-21T21:25:01Z"}
        second = {"observed_at": "2026-09-21T21:25:01Z"}
        with self.assertRaises(ValueError) as raised:
            bundle([(first, "dated receipt"), (second, "latest receipt")])
        self.assertIn("same observation", str(raised.exception))
        # The control: two real observations index cleanly.
        indexed = bundle([(first, "dated receipt"),
                          ({"observed_at": "2026-09-26T23:28:21Z"}, "latest receipt")])
        self.assertEqual(len(indexed), 2)

    def test_a_reordered_series_is_refused_even_after_the_chain_is_rebuilt(self):
        # history_chain.verify's own error message promises it detects a record
        # "inserted, removed or reordered". It detected none of those once the
        # forger re-linked, because the links agreed with the new order. A claim
        # in an error message is still a claim.
        from history_chain import rebuild, verify as verify_chain
        series = rebuild([{"observed_at": "2026-09-15T22:22:00Z"},
                          {"observed_at": "2026-09-21T21:25:01Z"},
                          {"observed_at": "2026-09-26T23:28:21Z"}])
        self.assertTrue(verify_chain(series), "an ordered series no longer verifies")
        swapped = rebuild([series[1], series[0], series[2]])
        with self.assertRaises(ValueError) as raised:
            verify_chain(swapped)
        self.assertIn("observation order", str(raised.exception))

    def test_deleting_the_provenance_does_not_delete_the_check(self):
        manifest = self.manifest_copy()
        for surface in manifest["surfaces"].values():
            for field in ("request_count", "successful_response_count",
                          "response_sha256", "status_codes"):
                surface.pop(field, None)
        with self.assertRaises(ValueError,
                               msg="removing the evidence removed the check that guards it"):
            self.verify_collection_manifest(self.surfaces, manifest, self.names)

    def test_placeholder_response_fingerprints_are_refused(self):
        manifest = self.manifest_copy()
        for surface in manifest["surfaces"].values():
            if isinstance(surface.get("response_sha256"), list):
                surface["response_sha256"] = ["0" * 64 for _ in surface["response_sha256"]]
        with self.assertRaises(ValueError) as raised:
            self.verify_collection_manifest(self.surfaces, manifest, self.names)
        self.assertIn("placeholder", str(raised.exception))

    def test_the_untouched_manifest_passes_the_same_function(self):
        # The control, at the level the forgeries actually run. There was also
        # a control that ran the whole CLI over the untouched evidence, which
        # is exactly what `make verify` already does in this same gate: half a
        # second spent twice for one answer, in a gate whose runtime this
        # repository publishes.
        # This passed by not raising, so it executed no assertion and the
        # assertion audit counted it as a test that checked nothing. "It did not
        # throw" is a real guarantee; it just has to be stated as one.
        try:
            self.verify_collection_manifest(self.surfaces, self.manifest_copy(), self.names)
        except ValueError as refusal:
            self.fail(f"the untouched manifest was refused: {refusal}")
        self.assertTrue(True, "the untouched manifest passes the function the forgeries use")


class TheDailyJobDoesNotLaunderATamperedHistory(unittest.TestCase):
    def setUp(self):
        import append_history
        from append_history import append
        # Another test file points this at a temporary anchor. Reading a global
        # another module may have moved is how three tests here went red, so
        # this states which anchor it means.
        append_history.ANCHOR = Path(__file__).resolve().parent.parent / "history-chain-head.txt"
        self.append = append
        self.history = json.loads((PROOF / HISTORY).read_text(encoding="utf-8"))

    def summary(self, observed_at: str) -> dict:
        newest = copy.deepcopy(self.history["observations"][-1])
        return {"observed_at": observed_at,
                "tokenised_references_scanned": newest["tokenised_references_scanned"],
                "tokens_scanned": newest["tokens_scanned"],
                "states": dict(newest["states"]), "signals": dict(newest["signals"]),
                "rules_version": newest.get("rules_version"),
                "source_hashes": dict(newest["source_hashes"])}

    def test_a_clean_history_still_appends(self):
        before = len(self.history["observations"])
        changed, message = self.append(self.history, self.summary("2099-01-01T00:00:00Z"))
        self.assertTrue(changed, message)
        self.assertEqual(len(self.history["observations"]), before + 1)

    def test_it_refuses_to_append_to_a_tampered_history(self):
        # The forgery the reviewer performed: edit a record, then let the daily
        # job rebuild the chain over it and write a valid anchor.
        self.history["observations"][4]["states"] = {"do_not_compare": 0, "investigate": 0,
                                                     "no_flags": 791}
        with self.assertRaises(SystemExit) as raised:
            self.append(self.history, self.summary("2099-01-01T00:00:00Z"))
        self.assertIn("refusing to append", str(raised.exception))

    def test_it_never_relinks_an_existing_record(self):
        # Rebuilding is what made the chain rewritable by its own maintenance
        # job, so the guarantee is that every earlier digest survives untouched.
        before = [item["sha256"] for item in self.history["observations"]]
        self.append(self.history, self.summary("2099-01-01T00:00:00Z"))
        self.assertEqual([item["sha256"] for item in self.history["observations"][:len(before)]],
                         before, "appending rewrote digests that were already published")


    def test_it_refuses_to_repair_a_stale_anchor(self):
        # The guard the judge page names as the one defence a forger must also
        # defeat, and no test exercised it: the fixture pointed ANCHOR at a
        # temporary file written with the CORRECT head, so the refusal could
        # never fire. A reviewer replaced the guard with `pass` and the whole
        # gate stayed green.
        import append_history
        import tempfile
        summary = self.summary("2099-01-01T00:00:00Z")
        stale = Path(tempfile.mkdtemp()) / "history-chain-head.txt"
        stale.write_text("0" * 64 + "\n", encoding="utf-8")
        original = append_history.ANCHOR
        append_history.ANCHOR = stale
        try:
            with self.assertRaises(SystemExit) as raised:
                self.append(self.history, summary)
            self.assertIn("anchors", str(raised.exception))
        finally:
            append_history.ANCHOR = original

    def test_it_refuses_when_the_anchor_is_missing(self):
        import append_history
        import tempfile
        summary = self.summary("2099-01-01T00:00:00Z")
        absent = Path(tempfile.mkdtemp()) / "history-chain-head.txt"
        original = append_history.ANCHOR
        append_history.ANCHOR = absent
        try:
            with self.assertRaises(SystemExit) as raised:
                self.append(self.history, summary)
            self.assertIn("missing", str(raised.exception))
        finally:
            append_history.ANCHOR = original

    def test_it_refuses_a_history_that_does_not_verify(self):
        import append_history
        summary = self.summary("2099-01-01T00:00:00Z")
        self.history["observations"][3]["tokens_scanned"] = 999999
        with self.assertRaises(SystemExit) as raised:
            self.append(self.history, summary)
        self.assertIn("does not verify", str(raised.exception))

    def test_it_refuses_an_emptied_observation_list(self):
        # Every refusal in append() lived inside `if observations:`, so setting
        # the list to [] removed all of them and the daily job wrote a fresh
        # anchor over the one protecting fifteen records. The guard was added
        # and shipped without a test - the pattern this repository has now
        # recorded ten times - and a reviewer then found that deleting the
        # anchor as well got past it anyway.
        summary = self.summary("2099-01-01T00:00:00Z")
        self.history["observations"] = []
        with self.assertRaises(SystemExit) as raised:
            self.append(self.history, summary)
        self.assertIn("carries no observations", str(raised.exception))

    def test_an_emptied_list_is_refused_even_with_the_anchor_deleted(self):
        # The reviewer's escalation: `if not observations and ANCHOR.exists()`
        # still let the job through once the anchor was gone too, which is the
        # same guard vanishing with a different piece of the evidence.
        import append_history
        import tempfile
        summary = self.summary("2099-01-01T00:00:00Z")
        original = append_history.ANCHOR
        append_history.ANCHOR = Path(tempfile.mkdtemp()) / "history-chain-head.txt"
        try:
            self.history["observations"] = []
            with self.assertRaises(SystemExit) as raised:
                self.append(self.history, summary)
            self.assertIn("carries no observations", str(raised.exception))
        finally:
            append_history.ANCHOR = original

    def test_it_refuses_a_backdated_observation(self):
        with self.assertRaises(SystemExit) as raised:
            self.append(self.history, self.summary("2020-01-01T00:00:00Z"))
        self.assertIn("older than", str(raised.exception))


class GuardsThatNothingCovered(unittest.TestCase):
    """Neuter each guard and require a test to notice.

    A reviewer disabled twenty guards one at a time and ran the full gate.
    Seven stayed green, five of them added in response to earlier attacks: the
    fix shipped without the test. The worst was `if recomputed != receipt`, the
    re-derivation judge.html calls the thing a single changed count fails on -
    delete it and all 352 tests pass.

    Each test here drives the guard directly with evidence that should trip it.
    """

    @classmethod
    def setUpClass(cls):
        from verify_integrity_receipt import load, verify_public_inputs
        cls.load = staticmethod(load)
        cls.verify_public_inputs = staticmethod(verify_public_inputs)
        cls.proof = PROOF
        cls.history = load(PROOF / HISTORY)
        cls.dated = load(PROOF / DATED)

    def observation_for(self, receipt):
        for item in self.history["observations"]:
            if item["observed_at"] == receipt["observed_at"]:
                return copy.deepcopy(item)
        self.fail("the shipped history does not describe this receipt")

    def test_the_re_derivation_refuses_a_receipt_the_inputs_do_not_produce(self):
        # The headline claim, and the guard nothing covered. Written to a
        # temporary file so the shipped receipt is never touched.
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            inputs = Path(directory) / "inputs.json"
            receipt_path = Path(directory) / "receipt.json"
            shutil.copy2(self.proof / INPUTS, inputs)
            receipt = self.load(self.proof / LATEST)
            receipt["universe"]["tokens_scanned"] += 1
            receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                self.verify_public_inputs(inputs, receipt_path)
            self.assertIn("does not recompute", str(raised.exception))

    def test_the_re_derivation_accepts_the_shipped_pair(self):
        # The control. A guard that refuses everything proves nothing. Written
        # as "does not raise", which executed no assertion, and `make
        # audit-tests` caught it ten minutes after I added the audit - which is
        # the whole argument for measuring instead of reading.
        try:
            self.verify_public_inputs(self.proof / INPUTS, self.proof / LATEST)
        except ValueError as refusal:
            self.fail(f"the shipped inputs no longer recompute the shipped receipt: {refusal}")
        self.assertTrue(True, "the shipped pair recomputes, so the refusal above means something")

    def test_a_shortened_source_hash_claim_is_refused_on_both_sides(self):
        from verify_integrity_receipt import verify_observation
        observation = self.observation_for(self.dated)
        receipt = copy.deepcopy(self.dated)
        kept = {"map": observation["source_hashes"]["map"]}
        observation["source_hashes"] = dict(kept)
        receipt["source_hashes"] = dict(kept)
        with self.assertRaises(ValueError) as raised:
            verify_observation(observation, receipt, "shortened")
        self.assertIn("missing", str(raised.exception))

    def test_a_source_hash_the_code_does_not_read_is_refused(self):
        from verify_integrity_receipt import verify_observation
        observation = self.observation_for(self.dated)
        receipt = copy.deepcopy(self.dated)
        digest = observation["source_hashes"]["map"]
        observation["source_hashes"]["invented_surface"] = digest
        receipt["source_hashes"]["invented_surface"] = digest
        with self.assertRaisesRegex(ValueError, "does not read"):
            verify_observation(observation, receipt, "invented surface")

    def test_a_placeholder_source_digest_is_refused(self):
        from verify_integrity_receipt import verify_observation_shape
        observation = self.observation_for(self.dated)
        observation["source_hashes"]["map"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "placeholder"):
            verify_observation_shape(observation, "placeholder digest")

    def test_an_empty_signals_claim_is_refused(self):
        from verify_integrity_receipt import verify_observation_shape
        observation = self.observation_for(self.dated)
        observation["signals"] = {}
        with self.assertRaisesRegex(ValueError, "signals is empty"):
            verify_observation_shape(observation, "emptied signals")

    def test_the_case_verifier_refuses_rows_whose_fingerprints_are_not_the_published_ones(self):
        from verify_case_receipt import bind
        published = self.load(self.proof / LATEST)
        alert = next(item for item in published["alerts"] if item.get("tokens"))
        payload = {
            "observed_at": published["observed_at"],
            "reference": {
                "rwa_id": alert["rwa_id"], "name": alert["name"], "symbol": alert["symbol"],
                "asset_type": alert.get("asset_type"), "token_count": len(alert["tokens"]),
                "issuer_count": alert.get("issuer_count"),
                "tradfi_market_count": alert.get("tradfi_market_count"),
            },
            "tokens": copy.deepcopy(alert["tokens"]),
            "source_hashes": {key: "b" * 64 for key in published["source_hashes"]},
        }
        with self.assertRaisesRegex(ValueError, "source fingerprints"):
            bind(payload, published, "receipt")
        # Control: the published digests bind.
        payload["source_hashes"] = copy.deepcopy(published["source_hashes"])
        try:
            bind(payload, published, "receipt")
        except ValueError as refusal:
            self.fail(f"a receipt carrying the published digests was refused: {refusal}")


class EveryGuardFailsWhenNeutered(unittest.TestCase):
    """Delete each guard and require a test to notice.

    A reviewer neutered every guard in the evidence path one at a time and ran
    the full gate after each. Eight survived with 395 tests green, including the
    subject and row bindings on the artefact a judge downloads - the two whose
    own docstrings say a receipt about the wrong subject is worse than no
    receipt, and that removing a row changes the answer to a question nobody
    asked. The code was fixed and the test was not written, ten times over.

    These drive each guard with evidence that must trip it. Every one was run
    against its own neutered guard before being accepted.
    """

    @classmethod
    def setUpClass(cls):
        from verify_integrity_receipt import load
        cls.replay = load(PROOF / LATEST)
        cls.dated = load(PROOF / DATED)
        cls.history = load(PROOF / HISTORY)

    def case_for(self, alert, **overrides):
        import copy as _copy
        payload = {
            "schema_version": "bell.case-receipt.v1",
            "observed_at": self.replay["observed_at"],
            "published_at": self.replay["observed_at"],
            "source": "/api/integrity", "credential_free": True,
            "question": "Can these representations be compared?",
            "reference": {"rwa_id": alert["rwa_id"], "name": alert["name"],
                          "symbol": alert["symbol"], "asset_type": alert.get("asset_type"),
                          "token_count": len(alert["tokens"]),
                          "issuer_count": alert.get("issuer_count") or 1,
                          "tradfi_market_count": alert.get("tradfi_market_count") or 0},
            "decision": _copy.deepcopy(alert["decision"]),
            "next_action": alert.get("next_action"),
            "signals": _copy.deepcopy(alert["signals"]),
            "tokens": _copy.deepcopy(alert["tokens"]),
            "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
            "source_hashes": _copy.deepcopy(self.replay["source_hashes"]),
            "limits": ["Observed fields do not prove liquidity"],
        }
        payload.update(overrides)
        return payload

    def alert(self):
        return next(item for item in self.replay["alerts"] if item.get("tokens"))

    def test_the_subject_binding_refuses_a_relabelled_reference(self):
        from verify_case_receipt import verify
        payload = self.case_for(self.alert())
        payload["reference"]["name"] = "Something Else Entirely"
        with self.assertRaisesRegex(ValueError, "wrong subject"):
            verify(payload)

    def test_the_row_binding_refuses_a_row_set_the_scan_did_not_publish(self):
        from verify_case_receipt import bind
        alert = self.alert()
        payload = self.case_for(alert)
        payload["tokens"] = payload["tokens"][:-1]
        with self.assertRaises(ValueError) as raised:
            bind(payload, self.replay, "receipt")
        self.assertRegex(str(raised.exception), "representations|token_count")

    def test_the_next_action_rederivation_refuses_an_invented_sentence(self):
        from verify_case_receipt import verify
        payload = self.case_for(self.alert())
        payload["next_action"] = "Proceed to shortlist."
        with self.assertRaisesRegex(ValueError, "next action"):
            verify(payload)

    def test_the_source_allowlist_refuses_an_arbitrary_origin(self):
        from verify_case_receipt import verify
        payload = self.case_for(self.alert(), source="https://example.invalid/whatever")
        with self.assertRaisesRegex(ValueError, "source must be"):
            verify(payload)

    def test_the_history_to_receipt_source_hash_comparison_refuses_a_mismatch(self):
        from verify_integrity_receipt import verify_observation
        observation = next(item for item in self.history["observations"]
                           if item["observed_at"] == self.dated["observed_at"])
        forged = copy.deepcopy(self.dated)
        key = sorted(forged["source_hashes"])[0]
        forged["source_hashes"][key] = "1234567890abcdef" * 4
        with self.assertRaisesRegex(ValueError, "source_hashes"):
            verify_observation(copy.deepcopy(observation), forged, "mismatched digests")

    def test_the_series_step_digest_is_recomputed(self):
        from reference_series import BASE, DELTAS, verify as verify_series
        base_doc = json.loads(BASE.read_text(encoding="utf-8"))
        deltas = json.loads(DELTAS.read_text(encoding="utf-8"))
        forged = copy.deepcopy(deltas)
        key = sorted(forged["observations"][0]["changed"])[0]
        forged["observations"][0]["changed"][key] = {
            "state": "no_flags", "representations": 1,
            "comparison_published": False, "signal_codes": []}
        with self.assertRaisesRegex(ValueError, "the state it produces"):
            verify_series(base_doc, forged, self.history)

    def test_the_series_digest_is_compared_to_the_one_the_history_anchors(self):
        from reference_series import BASE, DELTAS, verify as verify_series
        base_doc = json.loads(BASE.read_text(encoding="utf-8"))
        deltas = json.loads(DELTAS.read_text(encoding="utf-8"))
        anchored = [item for item in self.history["observations"]
                    if item.get("reference_digest")]
        if not anchored:
            self.skipTest("no observation anchors a series digest yet")
        history = copy.deepcopy(self.history)
        for item in history["observations"]:
            if item.get("reference_digest"):
                item["reference_digest"] = "fedcba9876543210" * 4
        with self.assertRaisesRegex(ValueError, "the chained history anchors"):
            verify_series(base_doc, deltas, history)

    def test_appending_refuses_a_history_whose_declared_head_disagrees(self):
        from append_history import append
        import append_history
        history = copy.deepcopy(self.history)
        newest = copy.deepcopy(history["observations"][-1])
        summary = {key: value for key, value in newest.items()
                   if key not in ("sha256", "prev_sha256", "chain_version",
                                  "reference_digest", "rules_version_recorded")}
        summary["observed_at"] = "2099-01-01T00:00:00Z"
        summary["rules_version"] = newest.get("rules_version")
        history["chain_head"] = "0000000011111111" * 4
        original = append_history.ANCHOR
        try:
            with self.assertRaisesRegex(ValueError, "declares") if False else \
                    self.assertRaises(SystemExit) as raised:
                append(history, summary)
            self.assertIn("declares", str(raised.exception))
        finally:
            append_history.ANCHOR = original


if __name__ == "__main__":
    unittest.main()

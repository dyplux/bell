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

    def test_a_bumped_rule_version_cannot_excuse_a_rewritten_distribution(self):
        receipt = copy.deepcopy(self.dated)
        receipt["universe"]["states"] = {"do_not_compare": 0, "investigate": 0, "no_flags": 791}
        receipt["universe"]["rules_version"] = "bell.rules.v3"
        with self.assertRaises(ValueError) as raised:
            self.verify_observation(self.dated_observation(), receipt, "forged")
        self.assertIn("bell.rules.v3", str(raised.exception))

    def test_a_known_rule_version_is_still_reported_rather_than_refused(self):
        # The fix must not turn the rule boundary into a wall. v1 is a rule set
        # this repository really published, and a receipt carrying it must stay
        # readable, with its counts reported instead of compared.
        receipt = copy.deepcopy(self.dated)
        receipt["universe"]["rules_version"] = "bell.rules.v1"
        compared = self.verify_observation(self.dated_observation(), receipt, "older rules")
        self.assertFalse(compared, "a receipt from another rule set was compared on state counts")

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
        self.verify_collection_manifest(self.surfaces, self.manifest_copy(), self.names)


class TheDailyJobDoesNotLaunderATamperedHistory(unittest.TestCase):
    def setUp(self):
        from append_history import append
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

    def test_it_refuses_a_backdated_observation(self):
        with self.assertRaises(SystemExit) as raised:
            self.append(self.history, self.summary("2020-01-01T00:00:00Z"))
        self.assertIn("older than", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

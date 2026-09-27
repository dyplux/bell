"""A state is a function of the rules, so a receipt is only comparable with
another receipt computed under the same rules.

When the rules changed, the published distribution changed without the
catalogue moving, and the integrity check failed - correctly, because a receipt
disagreed with its own recorded history. The wrong fix is to overwrite the
history so the numbers line up: that erases the fact that it was the rules and
not the market. The right fix is to record which rules produced a distribution
and refuse to compare across versions.
"""
import unittest

from rwa_integrity import RULES_VERSION, scan
from verify_integrity_receipt import verify_observation


def receipt(states, rules_version=RULES_VERSION, refs=10, rows=20):
    universe = {
        "tokenised_references_scanned": refs,
        "tokens_scanned": rows,
        "states": states,
        "signals": {"PRICE_DENOMINATION_BREAK": 1},
    }
    if rules_version is not None:
        universe["rules_version"] = rules_version
    return {"observed_at": "2026-09-21T21:25:01Z", "universe": universe,
            "source_hashes": {name: MAP_DIGEST for name in
                          ("map", "asset_list", "quotes", "info", "issuers")}}


def observation(states, rules_version=None, refs=10, rows=20):
    entry = {
        "observed_at": "2026-09-21T21:25:01Z",
        "tokenised_references_scanned": refs,
        "tokens_scanned": rows,
        "states": states,
        "signals": {"PRICE_DENOMINATION_BREAK": 1},
        "source_hashes": {name: MAP_DIGEST for name in
                          ("map", "asset_list", "quotes", "info", "issuers")},
    }
    if rules_version is not None:
        entry["rules_version"] = rules_version
    # A record must SAY whether it recorded a rule set. Absence used to be read
    # as "a different version", so deleting the key switched the state
    # comparison off; the skip requires a positive declaration now.
    entry["rules_version_recorded"] = rules_version is not None
    return entry


# A real digest, not a placeholder. These fixtures used sixty-four zeroes, which
# `verify_observation_shape` now rejects: a single repeated character is not the
# fingerprint of any payload, and accepting it let a forged summary-only
# observation pass shape validation.
MAP_DIGEST = "26140aa20c466e68a059462fc53906a983c129bdf10dcf5a720e8fe0fed1de83"


class RulesVersionIsPublished(unittest.TestCase):
    def test_the_engine_publishes_the_version_that_produced_the_states(self):
        self.assertTrue(RULES_VERSION.startswith("bell.rules."))

    def test_a_scan_carries_the_version_in_its_universe(self):
        result = scan({"data": {"rwa_assets": []}}, {"data": {"rwa_assets": []}},
                      {"data": {"rwa_assets": []}}, {"data": {"rwa_assets": []}},
                      observed_at="2026-09-21T21:25:01Z")
        self.assertEqual(result["universe"]["rules_version"], RULES_VERSION)


class ComparisonRespectsTheVersion(unittest.TestCase):
    def test_same_version_still_compares_states_strictly(self):
        # Had no assertion at all: it called the function and discarded the
        # answer, so it passed whatever the function did. A reviewer counted
        # three tests in this file in that shape. What it means to "compare" is
        # that the function reports having compared, so that is asserted.
        states = {"do_not_compare": 1, "investigate": 2, "no_flags": 7}
        self.assertTrue(
            verify_observation(observation(states, RULES_VERSION), receipt(states), "same"),
            "a matching pair under one rule set was not compared on state counts")

    def test_same_version_still_fails_on_a_real_mismatch(self):
        # Version awareness must not become a blanket excuse: within one version
        # a disagreement is still a disagreement.
        with self.assertRaises(ValueError):
            verify_observation(
                observation({"do_not_compare": 1, "investigate": 2, "no_flags": 7}, RULES_VERSION),
                receipt({"do_not_compare": 9, "investigate": 0, "no_flags": 1}),
                "same-version-mismatch")

    def test_a_version_change_is_reported_not_failed(self):
        # Also had no assertion. The guarantee is that the counts are reported
        # rather than compared, so the return value says so.
        compared = verify_observation(
            observation({"do_not_compare": 1, "investigate": 8, "no_flags": 1}, "bell.rules.v1"),
            receipt({"do_not_compare": 1, "investigate": 2, "no_flags": 7}, RULES_VERSION),
            "changed")
        self.assertFalse(compared, "counts from two rule sets were compared as if comparable")

    def test_an_unversioned_history_entry_counts_as_a_different_version(self):
        # Everything recorded before versioning existed predates these rules.
        compared = verify_observation(
            observation({"do_not_compare": 1, "investigate": 8, "no_flags": 1}),
            receipt({"do_not_compare": 1, "investigate": 2, "no_flags": 7}, RULES_VERSION),
            "unversioned")
        self.assertFalse(compared)

    def test_a_receipt_cannot_declare_a_rule_set_the_publisher_never_stamps(self):
        # The attack this file previously helped hide. A receipt that declares
        # any version other than the current one switched the state comparison
        # off, so two lines of JSON rewrote a whole distribution through a green
        # gate. The publisher stamps RULES_VERSION or nothing; anything else is
        # an edit.
        for declared in ("bell.rules.v1", "bell.rules.v3", "anything"):
            with self.subTest(declared=declared), self.assertRaises(ValueError) as raised:
                verify_observation(
                    observation({"do_not_compare": 1, "investigate": 2, "no_flags": 7}),
                    receipt({"do_not_compare": 0, "investigate": 0, "no_flags": 10}, declared),
                    "forged")
            self.assertIn(declared, str(raised.exception))

    def test_an_unversioned_pair_is_compared_rather_than_excused(self):
        # Both sides carry no version, which means one unversioned rule set,
        # which means they are comparable. Treating "absent" as "different" was
        # what let a declared version escape the comparison.
        states = {"do_not_compare": 1, "investigate": 2, "no_flags": 7}
        self.assertTrue(
            verify_observation(observation(states), receipt(states, None), "both unversioned"))
        with self.assertRaises(ValueError):
            verify_observation(observation(states),
                               receipt({"do_not_compare": 0, "investigate": 0, "no_flags": 10}, None),
                               "both unversioned, mismatched")



class TheSkipRequiresADeclaration(unittest.TestCase):
    """Absence of a rule version may not switch the state comparison off.

    A reviewer deleted `rules_version` from the history record, which made the
    versions "differ", skipped the comparison, and let a rewritten distribution
    through a green gate. The record has to state which case it is in.
    """

    def test_a_record_that_does_not_say_is_refused(self):
        entry = observation({"do_not_compare": 1, "investigate": 2, "no_flags": 7})
        entry.pop("rules_version_recorded")
        with self.assertRaises(ValueError) as raised:
            verify_observation(entry, receipt({"do_not_compare": 0, "investigate": 0, "no_flags": 10}),
                               "undeclared")
        self.assertIn("does not say whether it recorded a rule set", str(raised.exception))

    def test_a_declaration_that_contradicts_the_record_is_refused(self):
        states = {"do_not_compare": 1, "investigate": 2, "no_flags": 7}
        entry = observation(states)
        entry["rules_version_recorded"] = True
        with self.assertRaisesRegex(ValueError, "declares it recorded a rule set and carries none"):
            verify_observation(entry, receipt(states), "lying declaration")
        entry = observation(states, RULES_VERSION)
        entry["rules_version_recorded"] = False
        with self.assertRaisesRegex(ValueError, "declares it recorded no rule set"):
            verify_observation(entry, receipt(states), "lying the other way")

    def test_a_declared_boundary_is_still_reported_rather_than_failed(self):
        # The fix must not turn a real rule boundary into a wall.
        compared = verify_observation(
            observation({"do_not_compare": 1, "investigate": 8, "no_flags": 1}),
            receipt({"do_not_compare": 1, "investigate": 2, "no_flags": 7}, RULES_VERSION),
            "declared boundary")
        self.assertFalse(compared)


if __name__ == "__main__":
    unittest.main()

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
            "source_hashes": {"map": "0" * 64}}


def observation(states, rules_version=None, refs=10, rows=20):
    entry = {
        "observed_at": "2026-09-21T21:25:01Z",
        "tokenised_references_scanned": refs,
        "tokens_scanned": rows,
        "states": states,
        "signals": {"PRICE_DENOMINATION_BREAK": 1},
        "source_hashes": {"map": "0" * 64},
    }
    if rules_version is not None:
        entry["rules_version"] = rules_version
    return entry


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
        states = {"do_not_compare": 1, "investigate": 2, "no_flags": 7}
        verify_observation(observation(states, RULES_VERSION), receipt(states), "same")

    def test_same_version_still_fails_on_a_real_mismatch(self):
        # Version awareness must not become a blanket excuse: within one version
        # a disagreement is still a disagreement.
        with self.assertRaises(ValueError):
            verify_observation(
                observation({"do_not_compare": 1, "investigate": 2, "no_flags": 7}, RULES_VERSION),
                receipt({"do_not_compare": 9, "investigate": 0, "no_flags": 1}),
                "same-version-mismatch")

    def test_a_version_change_is_reported_not_failed(self):
        verify_observation(
            observation({"do_not_compare": 1, "investigate": 8, "no_flags": 1}, "bell.rules.v1"),
            receipt({"do_not_compare": 1, "investigate": 2, "no_flags": 7}),
            "changed")

    def test_an_unversioned_history_entry_counts_as_a_different_version(self):
        # Everything recorded before versioning existed predates these rules.
        verify_observation(
            observation({"do_not_compare": 1, "investigate": 8, "no_flags": 1}),
            receipt({"do_not_compare": 1, "investigate": 2, "no_flags": 7}),
            "unversioned")


if __name__ == "__main__":
    unittest.main()

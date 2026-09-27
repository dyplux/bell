"""Feed the verifiers malformed evidence and require a refusal for each shape.

`make mutate` neuters every guard in the evidence path and reports the ones no
test notices. On the first full sweep, 68 of 123 survived - and most of them
were shape checks: `if not isinstance(states, dict)`, `if field not in
observation`, `if not SHA256.fullmatch(digest)`. Real refusals, each one
written deliberately, none of them exercised, because every test in the suite
fed the verifiers well-formed evidence.

Three reviewers found the shape of this problem by hand before the tool
existed. Writing fifty-seven tests by hand is how it stays unwritten, so this
is a table: one row per malformation, driven at the function that refuses it.

A row here is not decoration. Each was confirmed to fail when its guard is
neutered, by running `make mutate` before and after.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

PROOF = HERE.parent / "site" / "proof"
HISTORY = json.loads((PROOF / "rwa-surface-integrity-history.json").read_text(encoding="utf-8"))
DATED = json.loads(
    (PROOF / "rwa-surface-integrity-2026-09-15.json").read_text(encoding="utf-8"))
REPLAY = json.loads(
    (PROOF / "rwa-surface-integrity-latest-replay-2026-09-21.json").read_text(encoding="utf-8"))


def observation_for(receipt: dict) -> dict:
    for item in HISTORY["observations"]:
        if item["observed_at"] == receipt["observed_at"]:
            return copy.deepcopy(item)
    raise AssertionError("the shipped history does not describe that receipt")


def case_for(alert: dict) -> dict:
    return {
        "schema_version": "bell.case-receipt.v1",
        "observed_at": REPLAY["observed_at"], "published_at": REPLAY["observed_at"],
        "source": "/api/integrity", "credential_free": True,
        "question": "Can these representations be compared?",
        "reference": {"rwa_id": alert["rwa_id"], "name": alert["name"],
                      "symbol": alert["symbol"], "asset_type": alert.get("asset_type"),
                      "token_count": len(alert["tokens"]),
                      "issuer_count": alert.get("issuer_count") or 1,
                      "tradfi_market_count": alert.get("tradfi_market_count") or 0},
        "decision": copy.deepcopy(alert["decision"]),
        "next_action": alert.get("next_action"),
        "signals": copy.deepcopy(alert["signals"]),
        "tokens": copy.deepcopy(alert["tokens"]),
        "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
        "source_hashes": copy.deepcopy(REPLAY["source_hashes"]),
        "limits": ["Observed fields do not prove liquidity"],
    }


class TheIntegrityVerifierRefusesMalformedEvidence(unittest.TestCase):
    """One row per shape the observation verifier refuses."""

    def setUp(self):
        from verify_integrity_receipt import verify_observation, verify_observation_shape
        self.verify_observation = verify_observation
        self.verify_shape = verify_observation_shape

    def test_a_receipt_of_the_wrong_shape_is_refused(self):
        cases = {
            "universe missing": lambda r: r.pop("universe"),
            "universe not an object": lambda r: r.__setitem__("universe", []),
            "states not an object": lambda r: r["universe"].__setitem__("states", []),
            "signals not an object": lambda r: r["universe"].__setitem__("signals", []),
            "receipt carries no source_hashes": lambda r: r.__setitem__("source_hashes", {}),
        }
        for label, break_it in cases.items():
            receipt = copy.deepcopy(DATED)
            break_it(receipt)
            with self.subTest(case=label), self.assertRaises((ValueError, KeyError)):
                self.verify_observation(observation_for(DATED), receipt, label)

    def test_an_observation_of_the_wrong_shape_is_refused(self):
        required = ("observed_at", "tokenised_references_scanned", "tokens_scanned",
                    "states", "signals")
        for field in required:
            observation = observation_for(DATED)
            observation.pop(field, None)
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.verify_shape(observation, f"missing {field}")

    def test_a_state_total_that_does_not_equal_the_population_is_refused(self):
        observation = observation_for(DATED)
        key = sorted(observation["states"])[0]
        observation["states"][key] += 1
        with self.assertRaisesRegex(ValueError, "state total"):
            self.verify_shape(observation, "wrong total")

    def test_a_fingerprint_that_is_not_a_fingerprint_is_refused(self):
        for bad in ("", "abc", "z" * 64, "0123456789abcdef" * 3):
            observation = observation_for(DATED)
            observation["source_hashes"][sorted(observation["source_hashes"])[0]] = bad
            with self.subTest(digest=bad[:12]), self.assertRaises(ValueError):
                self.verify_shape(observation, "bad digest")

    def test_source_hashes_that_are_not_an_object_are_refused(self):
        for value in ([], "", 0, None):
            observation = observation_for(DATED)
            observation["source_hashes"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.verify_shape(observation, "bad source_hashes")


class TheCaseVerifierRefusesMalformedEvidence(unittest.TestCase):
    """One row per shape the case receipt verifier refuses."""

    def setUp(self):
        from verify_case_receipt import verify
        self.verify = verify
        self.alert = next(item for item in REPLAY["alerts"] if item.get("tokens"))

    def test_a_payload_of_the_wrong_type_is_refused(self):
        for value in ([], "receipt", 7, None):
            with self.subTest(value=repr(value)), self.assertRaisesRegex(ValueError, "JSON object"):
                self.verify(value)

    def test_a_missing_top_level_field_is_named(self):
        from verify_case_receipt import REQUIRED_TOP_LEVEL
        for field in sorted(REQUIRED_TOP_LEVEL):
            payload = case_for(self.alert)
            payload.pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception),
                          f"removing {field} was refused without naming it")

    def test_a_wrong_schema_version_is_refused(self):
        payload = case_for(self.alert)
        payload["schema_version"] = "bell.case-receipt.v99"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            self.verify(payload)

    def test_a_missing_reference_field_is_named(self):
        from verify_case_receipt import REQUIRED_REFERENCE
        for field in sorted(REQUIRED_REFERENCE):
            payload = case_for(self.alert)
            payload["reference"].pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception))

    def test_a_missing_method_field_is_named(self):
        from verify_case_receipt import REQUIRED_METHOD
        for field in sorted(REQUIRED_METHOD):
            payload = case_for(self.alert)
            payload["method"].pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception))

    def test_a_join_key_the_product_does_not_use_is_refused(self):
        for field, value in (("join_key", "symbol"), ("token_join_key", "ticker")):
            payload = case_for(self.alert)
            payload["method"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                self.verify(payload)

    def test_the_collection_of_wrong_types_is_refused(self):
        cases = {
            "tokens not an array": ("tokens", {}),
            "signals not an array": ("signals", {}),
            "source_hashes not an object": ("source_hashes", []),
            "limits empty": ("limits", []),
            "limits not an array": ("limits", "none"),
            "method not an object": ("method", []),
            "reference not an object": ("reference", []),
            "question empty": ("question", "   "),
            "question not a string": ("question", 7),
        }
        # The first version accepted (ValueError, TypeError, AttributeError),
        # so removing the guard still blew up further along and the test still
        # passed: `make mutate` reported nine of these as undefended. Accepting
        # a crash as a check is the same defect in different clothes. A guard's
        # value is the NAMED refusal, so the message has to carry the field.
        for label, (field, value) in cases.items():
            payload = case_for(self.alert)
            payload[field] = value
            with self.subTest(case=label), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field.split("_")[0], str(raised.exception).lower(),
                          f"{label} was refused without naming {field}")

    def test_a_token_count_that_is_not_a_positive_integer_is_refused(self):
        for value in (0, -1, True, "5", None):
            payload = case_for(self.alert)
            payload["reference"]["token_count"] = value
            with self.subTest(value=repr(value)), self.assertRaisesRegex(ValueError, "token_count"):
                self.verify(payload)
        # And a count that is a valid positive integer and still wrong, which
        # is a different guard from the type check above.
        payload = case_for(self.alert)
        payload["reference"]["token_count"] = len(payload["tokens"]) + 3
        with self.assertRaisesRegex(ValueError, "token_count"):
            self.verify(payload)

    def test_a_decision_that_is_not_an_object_is_refused(self):
        for value in ("comparable", [], None, {}):
            payload = case_for(self.alert)
            payload["decision"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.verify(payload)

    def test_a_receipt_this_repository_does_not_ship_is_refused(self):
        payload = case_for(self.alert)
        payload["source"] = "proof/rwa-surface-integrity-1999-01-01.json"
        with self.assertRaisesRegex(ValueError, "does not ship"):
            self.verify(payload)


class ReadingAReceiptToBindAgainstRefusesWhatItCannotRead(unittest.TestCase):
    """`--against` takes a URL or a path, and both branches were undefended."""

    def test_a_path_that_does_not_exist_is_refused_by_name(self):
        from verify_case_receipt import fetch_receipt
        with self.assertRaisesRegex(ValueError, "not a URL and not a file"):
            fetch_receipt("/tmp/a-receipt-that-is-not-here-1234.json")

    def test_a_path_that_exists_is_read_and_named(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(REPLAY), encoding="utf-8")
            document, name = fetch_receipt_local(str(path))
            self.assertEqual(name, "receipt.json")
            self.assertEqual(document["observed_at"], REPLAY["observed_at"])


def fetch_receipt_local(source: str):
    from verify_case_receipt import fetch_receipt
    return fetch_receipt(source)


class BindingRefusesWhatItCannotMatch(unittest.TestCase):
    def setUp(self):
        from verify_case_receipt import bind
        self.bind = bind
        self.alert = next(item for item in REPLAY["alerts"] if item.get("tokens"))

    def test_a_reference_the_published_receipt_does_not_carry_in_full_is_named(self):
        payload = case_for(self.alert)
        payload["reference"]["rwa_id"] = "9999999"
        with self.assertRaises(LookupError) as raised:
            self.bind(payload, REPLAY, "receipt")
        self.assertIn("not carried in full", str(raised.exception))

    def test_a_receipt_describing_another_observation_is_named(self):
        payload = case_for(self.alert)
        other = dict(REPLAY, observed_at="2099-01-01T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "moves on"):
            self.bind(payload, other, "receipt")


if __name__ == "__main__":
    unittest.main()

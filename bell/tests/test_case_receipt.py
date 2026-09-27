"""The receipt a judge downloads must be checked for its verdict, not its shape.

A reviewer took a real Silver case receipt from the running site, flipped
`decision.state` from `blocked` to `comparable`, relabelled it `COMPARABLE, NOT
ENDORSED`, emptied all six signals, wrote "Proceed to shortlist" as the next
action and set every source fingerprint to sixty-four `f`s. The verifier
printed "valid public case receipt" and exited 0, with the five Silver rows and
their 31.24x quote range still in the file.

The fixture here was a hand-written stub: one token with no price, a
`source_hashes` of `{"map": "abc"}`, and a `decision` that was a bare string.
Nothing in it could have exercised a verdict check, which is part of why there
was not one. It is built from the shipped replay receipt now, so these tests
run against evidence the product actually produced.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from verify_case_receipt import ROW_DERIVED_SIGNALS, verify  # noqa: E402

REPLAY = json.loads((HERE.parent / "site" / "proof"
                     / "rwa-surface-integrity-latest-replay-2026-09-21.json")
                    .read_text(encoding="utf-8"))
DIGEST = hashlib.sha256(b"bell case receipt fixture").hexdigest()


def receipt_for(alert: dict) -> dict:
    """The exported case shape, built from a real alert in the shipped receipt."""
    return {
        "schema_version": "bell.case-receipt.v1",
        "observed_at": REPLAY["observed_at"],
        "published_at": REPLAY["observed_at"],
        "source": "/api/integrity",
        "credential_free": True,
        "question": "Can these representations be compared?",
        "reference": {
            "rwa_id": alert["rwa_id"], "name": alert["name"], "symbol": alert["symbol"],
            "asset_type": alert.get("asset_type"), "token_count": len(alert["tokens"]),
            "issuer_count": alert.get("issuer_count") or 1,
            "tradfi_market_count": alert.get("tradfi_market_count") or 0,
        },
        "decision": copy.deepcopy(alert["decision"]),
        "next_action": alert.get("next_action") or "continue external diligence",
        "signals": copy.deepcopy(alert["signals"]),
        "tokens": copy.deepcopy(alert["tokens"]),
        "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
        "source_hashes": {"map": DIGEST},
        "limits": ["Observed fields do not prove liquidity"],
    }


def blocked_alert() -> dict:
    for alert in REPLAY["alerts"]:
        if alert.get("state") == "do_not_compare" and alert.get("tokens"):
            return alert
    raise AssertionError("the shipped receipt carries no blocked case to test with")


class CaseReceiptTests(unittest.TestCase):
    def setUp(self):
        self.alert = blocked_alert()

    def test_valid_receipt(self):
        result = verify(receipt_for(self.alert))
        self.assertEqual(result["status"], "valid public case receipt")
        self.assertEqual(result["token_rows"], len(self.alert["tokens"]))
        self.assertEqual(result["verdict_rederived_from_rows"], self.alert["decision"]["state"])

    def test_every_shipped_case_verifies(self):
        # Without this the refusals below prove nothing: a verifier that refuses
        # everything also refuses every forgery. All 50 published cases, not a
        # sample, because the re-derivation is the new claim.
        checked = 0
        for alert in REPLAY["alerts"]:
            if not alert.get("tokens"):
                continue
            verify(receipt_for(alert))
            checked += 1
        self.assertGreaterEqual(checked, 40,
                                f"only {checked} shipped cases were exercised")

    def test_token_count_must_match_rows(self):
        payload = receipt_for(self.alert)
        payload["reference"]["token_count"] = len(payload["tokens"]) + 1
        with self.assertRaisesRegex(ValueError, "token_count"):
            verify(payload)

    def test_credentials_are_not_accepted(self):
        payload = receipt_for(self.alert)
        payload["credential_free"] = False
        with self.assertRaisesRegex(ValueError, "credential_free"):
            verify(payload)

    def test_a_verdict_that_does_not_follow_from_the_rows_is_refused(self):
        payload = receipt_for(self.alert)
        payload["decision"] = {"state": "comparable", "label": "COMPARABLE, NOT ENDORSED",
                               "consequence": "Prices can be set side by side.",
                               "allocation_effect": "Wrapper selection permitted."}
        with self.assertRaisesRegex(ValueError, "does not follow from the evidence"):
            verify(payload)

    def test_relabelling_the_verdict_is_refused_too(self):
        # The state is only half the verdict; the label is what a reader sees.
        payload = receipt_for(self.alert)
        payload["decision"]["label"] = "COMPARABLE, NOT ENDORSED"
        with self.assertRaisesRegex(ValueError, "decision.label"):
            verify(payload)

    def test_deleting_the_findings_does_not_delete_them_from_the_rows(self):
        payload = receipt_for(self.alert)
        payload["signals"] = []
        with self.assertRaisesRegex(ValueError, "rows produce"):
            verify(payload)

    def test_an_invented_finding_is_refused(self):
        payload = receipt_for(self.alert)
        payload["signals"].append({"code": "TOTALLY_MADE_UP", "severity": "critical",
                                   "message": "x", "evidence": {}})
        with self.assertRaisesRegex(ValueError, "TOTALLY_MADE_UP"):
            verify(payload)

    def test_a_placeholder_fingerprint_is_refused(self):
        # The integrity verifier has refused this since a reviewer found it
        # there. This file accepted sixty-four f's six times over.
        payload = receipt_for(self.alert)
        payload["source_hashes"] = {"map": "f" * 64}
        with self.assertRaisesRegex(ValueError, "placeholder"):
            verify(payload)

    def test_the_two_context_signals_are_named_rather_than_silently_skipped(self):
        # They answer to the whole catalogue and cannot be recomputed from one
        # case. Saying so is the difference between a limit and a hole.
        result = verify(receipt_for(self.alert))
        self.assertEqual(result["signals_not_rederived"],
                         ["NO_TRADFI_MARKET", "TOKEN_INFO_MISSING"])
        self.assertTrue(set(result["signals_rederived"]) <= ROW_DERIVED_SIGNALS)
        self.assertNotIn("NO_TRADFI_MARKET", ROW_DERIVED_SIGNALS)


if __name__ == "__main__":
    unittest.main()

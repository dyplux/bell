import unittest

from verify_case_receipt import verify


def valid_receipt():
    return {
        "schema_version": "bell.case-receipt.v1",
        "observed_at": "2026-09-22T00:00:00Z",
        "published_at": "2026-09-22T00:01:00Z",
        "source": "/api/integrity",
        "credential_free": True,
        "question": "Can these representations be compared?",
        "reference": {"rwa_id": "1", "name": "Example", "symbol": "EX", "asset_type": "stock", "token_count": 1, "issuer_count": 1, "tradfi_market_count": 0},
        "decision": "facts_open",
        "next_action": "continue external diligence",
        "signals": [],
        "tokens": [{"crypto_id": "2"}],
        "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
        "source_hashes": {"map": "abc"},
        "limits": ["Observed fields do not prove liquidity"],
    }


class CaseReceiptTests(unittest.TestCase):
    def test_valid_receipt(self):
        result = verify(valid_receipt())
        self.assertEqual(result["status"], "valid public case receipt")
        self.assertEqual(result["token_rows"], 1)

    def test_token_count_must_match_rows(self):
        payload = valid_receipt()
        payload["reference"]["token_count"] = 2
        with self.assertRaisesRegex(ValueError, "token_count"):
            verify(payload)

    def test_credentials_are_not_accepted(self):
        payload = valid_receipt()
        payload["credential_free"] = False
        with self.assertRaisesRegex(ValueError, "credential_free"):
            verify(payload)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal import build_terminal_summary
import unittest


class TheTerminal(unittest.TestCase):
    def test_terminal_marks_no_token_asset_as_underlying_only(self):
        result = build_terminal_summary({"asset": {"name": "Royal Bank", "has_tokens": False}})
        self.assertTrue(result["state"] == "underlying_only")
        self.assertTrue(result["output"] == "MONITOR")
        self.assertTrue(result["metrics"]["token_count"] == 0)


    def test_terminal_does_not_turn_missing_token_rows_into_underlying_only(self):
        result = build_terminal_summary({"asset": {"name": "Gold", "has_tokens": True}})
        self.assertTrue(result["state"] == "coverage_pending")
        self.assertTrue(result["output"] == "LOAD")


    def test_terminal_marks_one_token_asset_as_dossier(self):
        result = build_terminal_summary({
            "asset": {"name": "SPY", "has_tokens": True},
            "tokens": [{"symbol": "SPYx", "issuer_name": "bStocks", "price": 762.94}],
            "issuers": [{"name": "bStocks"}],
            "market_pairs": [{"category": "spot"}],
        })
        self.assertTrue(result["state"] == "single_token")
        self.assertTrue(result["output"] == "DOSSIER")
        self.assertTrue(result["metrics"]["issuer_count"] == 1)
        self.assertTrue(result["metrics"]["spot_pair_count"] == 1)


    def test_terminal_exposes_multi_token_market_and_data_quality_evidence(self):
        result = build_terminal_summary({
            "asset": {"name": "Tesla", "has_tokens": True, "tokenized_market_cap": 100},
            "tokens": [
                {"symbol": "TSLAX", "issuer_name": "Backed", "price": 362, "market_cap": 90},
                {"symbol": "TSLA", "issuer_name": "Hyperliquid", "price": 235, "market_cap": None},
            ],
            "issuers": [{"name": "Backed"}, {"name": "Hyperliquid"}],
            "crypto_info": [{"platform": {"name": "Ethereum"}}, {"platform": {"name": "Hyperliquid"}}],
            "market_pairs": [{"category": "spot"}, {"category": "perpetual"}],
            "findings": [{"code": "symbol_collision"}],
        })
        self.assertTrue(result["state"] == "multi_token")
        self.assertTrue(result["output"] == "COMPARE")
        self.assertTrue(result["metrics"]["derivative_pair_count"] == 1)
        self.assertTrue(result["metrics"]["network_count"] == 2)
        self.assertTrue(any("TSLA" in point for point in result["points"]))
        self.assertTrue(result["points"][-1] == "1 deterministic finding(s) require review")


    def test_terminal_exposes_dex_coverage_as_a_separate_evidence_layer(self):
        result = build_terminal_summary({
            "asset": {"name": "Gold", "has_tokens": True},
            "tokens": [{"symbol": "PAXG", "issuer_name": "Paxos", "price": 4300}],
            "issuers": [{"name": "Paxos"}],
            "crypto_info": [{"platform": {"name": "Ethereum"}}],
            "market_pairs": [],
            "market_pairs_error": "CMC request failed for market pairs: HTTP 403",
            "dex_evidence": {
                "covered_token_count": 1,
                "contract_token_count": 1,
                "surface_counts": {"detail": 1, "pools": 1, "security": 1, "holders": 1, "holder_tags": 1},
            },
        })
        self.assertTrue(result["metrics"]["dex_covered_token_count"] == 1)
        self.assertTrue(result["metrics"]["dex_holder_tag_count"] == 1)
        self.assertTrue(any("DEX evidence" in point for point in result["points"]))
        self.assertTrue(any("DEX evidence is shown separately" in point for point in result["points"]))


if __name__ == "__main__":
    unittest.main()

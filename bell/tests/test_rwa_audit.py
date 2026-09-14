import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rwa_audit import audit_rwa_evidence, collect_rwa_evidence


class FakeCMC:
    def __init__(self):
        self.calls = []

    def get(self, endpoint, params):
        self.calls.append({"endpoint": endpoint, "params": params, "status": 200})
        if endpoint.endswith("quotes/latest") and "real-world-assets" in endpoint:
            return {
                "data": {
                    "rwa_assets": [{
                        "rwa_id": 14,
                        "name": "Tesla, Inc.",
                        "symbol": "TSLA",
                        "slug": "tesla",
                        "asset_type": "stock",
                        "rwa_rank": 12,
                        "has_tokens": True,
                        "average_tokenized_price": 362.5,
                        "tokenized_market_cap": 1000000,
                        "tokenized_volume_24h": 100000,
                        "last_updated": "2026-09-13T10:00:00Z",
                        "tokens": [
                            {"crypto_id": 37004, "name": "Tesla tokenized stock (xStock)", "symbol": "TSLAX", "issuer_id": "issuer-backed", "issuer_name": "Backed Assets", "price": 362, "market_cap": 70000000, "volume_24h": 5000000},
                            {"crypto_id": 39618, "name": "Tesla Tokenized Stock (Hyperliquid)", "symbol": "TSLA", "issuer_id": "issuer-hyper", "issuer_name": "Hyperliquid Assets", "price": 235, "market_cap": 4748, "volume_24h": 0},
                            {"crypto_id": 38152, "name": "Tesla (Derivatives)", "symbol": "TSLA", "issuer_id": "issuer-derivative", "issuer_name": "NA (Derivatives)", "price": 362, "market_cap": 0, "volume_24h": 294827},
                        ],
                    }],
                }
            }
        if endpoint.endswith("cryptocurrency/info"):
            return {"data": {"37004": {"id": 37004, "name": "Tesla tokenized stock (xStock)", "symbol": "TSLAX", "slug": "tesla-tokenized-stock-xstock", "description": "tracker certificate", "platform": {"id": 1027, "name": "Ethereum", "slug": "ethereum", "token_address": "0xabc"}, "urls": {"website": ["https://example.test"]}}, "39618": {"id": 39618, "name": "Tesla Tokenized Stock (Hyperliquid)", "symbol": "TSLA", "slug": "tesla-tokenized-stock-hyperliquid", "description": "", "urls": {}}}}
        if endpoint.endswith("/info"):
            return {"data": {"rwa_assets": [{"rwa_id": 14, "name": "Tesla, Inc.", "symbol": "TSLA", "slug": "tesla", "asset_type": "stock", "primary_exchange": "Nasdaq"}]}}
        if endpoint.endswith("market-pairs/list"):
            return {"data": {"rwa_id": 14, "market_pairs": [{"market_id": 1, "market_pair": "TSLA/USDT", "category": "spot", "fee_type": "percentage", "exchange": {"exchange_id": 270, "name": "Binance"}}, {"market_id": 2, "market_pair": "TSLA-PERP", "category": "perpetual", "fee_type": "percentage", "exchange": {"exchange_id": 999, "name": "Example"}}]}}
        if endpoint.endswith("/issuers"):
            issuer_id = params["issuer_id"]
            return {"data": {"issuer_id": issuer_id, "name": issuer_id, "website": None, "num_tokens": 1, "tokens": []}}
        if endpoint.endswith("/v1/dex/token"):
            return {"data": {"n": "Tesla tokenized stock", "sym": "TSLAX", "addr": params["address"], "plt": params["platform"], "p": "362", "liqUsd": "100000", "nps": 1}}
        if endpoint.endswith("/v1/dex/token/price"):
            return {"data": {"p": "362", "pc24h": "1.2", "v24h": "5000", "mc": "70000000"}}
        if endpoint.endswith("/v1/dex/token/pools"):
            return {"data": [{"addr": "0xpool", "exn": "Example DEX", "liqUsd": "100000", "v24": "5000", "t0": {"addr": params["address"], "sym": "TSLAX"}, "t1": {"addr": "0xusdc", "sym": "USDC"}}]}
        if endpoint.endswith("/v1/dex/security/detail"):
            return {"data": [{"platformName": "Ethereum", "tokenContractAddress": params["address"], "securityLevel": "safe", "securityItems": [], "extra": {}}]}
        if endpoint.endswith("/v1/dex/holders/count"):
            return {"data": {"count": 42, "tokenAddress": params["tokenAddress"]}}
        if endpoint.endswith("/v1/dex/holders/tag_count"):
            return {"data": {"platformId": 1, "tokenAddress": params["tokenAddress"], "holders": [{"tag": "tag_whale", "hc": "3", "tb": "10", "hr": "0.4"}]}}
        raise AssertionError(f"unexpected endpoint: {endpoint}")


class LimitedMarketPairsCMC(FakeCMC):
    def get(self, endpoint, params):
        if endpoint.endswith("market-pairs/list"):
            self.calls.append({"endpoint": endpoint, "params": params, "status": 403})
            from engine import BellDataError
            raise BellDataError("CMC returned HTTP 403 for market pairs")
        return super().get(endpoint, params)


class RwaAuditTests(unittest.TestCase):
    def test_collects_rwa_quotes_metadata_pairs_issuers_and_crypto_info(self):
        client = FakeCMC()
        evidence = collect_rwa_evidence(client, "tesla")
        self.assertEqual(evidence["asset"]["slug"], "tesla")
        self.assertEqual(len(evidence["tokens"]), 3)
        self.assertEqual(len(evidence["market_pairs"]), 2)
        self.assertEqual(len(evidence["issuers"]), 3)
        self.assertEqual(len(evidence["crypto_info"]), 2)
        self.assertEqual(evidence["crypto_info"][0]["platform"]["name"], "Ethereum")
        self.assertEqual(evidence["crypto_info"][0]["contract_address"], "0xabc")
        self.assertEqual(evidence["dex_evidence"]["covered_token_count"], 1)
        self.assertEqual(evidence["dex_evidence"]["no_contract_token_count"], 2)
        self.assertEqual(evidence["dex_evidence"]["surface_counts"]["holders"], 1)
        self.assertEqual(evidence["dex_evidence"]["surface_counts"]["holder_tags"], 1)
        self.assertEqual(evidence["provenance"]["raw_responses_included"], False)
        self.assertEqual(client.calls[0]["params"], {"rwa_slug": "tesla", "convert": "USD"})

    def test_flags_collisions_derivatives_volume_without_mcap_and_outlier(self):
        result = audit_rwa_evidence(collect_rwa_evidence(FakeCMC(), "tesla"))
        codes = {finding["code"] for finding in result["findings"]}
        self.assertEqual(result["conclusion"], "investigate")
        self.assertIn("symbol_collision", codes)
        self.assertIn("derivative_markets_present", codes)
        self.assertIn("volume_without_mcap", codes)

    def test_gold_like_price_spread_is_do_not_compare(self):
        evidence = {
            "asset": {"slug": "gold", "name": "Gold"},
            "tokens": [
                {"name": "Tether Gold", "symbol": "XAUt", "issuer_name": "Tether", "issuer_id": "a", "price": 4330, "market_cap": 10, "volume_24h": 1},
                {"name": "VNX Gold", "symbol": "VNXAU", "issuer_name": "VNX", "issuer_id": "b", "price": 140, "market_cap": 10, "volume_24h": 1},
            ],
            "market_pairs": [],
        }
        result = audit_rwa_evidence(evidence)
        self.assertEqual(result["conclusion"], "do_not_compare")
        self.assertIn("denomination_unresolved", {finding["code"] for finding in result["findings"]})

    def test_optional_market_pairs_failure_keeps_terminal_evidence_usable(self):
        evidence = collect_rwa_evidence(LimitedMarketPairsCMC(), "tesla")
        self.assertEqual(evidence["market_pairs"], [])
        self.assertIn("HTTP 403", evidence["market_pairs_error"])
        self.assertEqual(evidence["provenance"]["optional_errors"][0]["surface"], "market_pairs")
        result = audit_rwa_evidence(evidence)
        codes = {finding["code"] for finding in result["findings"]}
        self.assertIn("market_pairs_unavailable", codes)
        self.assertNotIn("no_market_pairs", codes)

    def test_missing_prices_are_insufficient_evidence(self):
        result = audit_rwa_evidence({"asset": {"slug": "unknown"}, "tokens": [{"symbol": "X", "price": None}], "market_pairs": []})
        self.assertEqual(result["conclusion"], "insufficient_evidence")
        self.assertIn("no_token_prices", {finding["code"] for finding in result["findings"]})

    def test_clean_single_unit_fixture_is_provisionally_comparable(self):
        result = audit_rwa_evidence({
            "asset": {"slug": "spy", "name": "SPDR S&P 500 ETF Trust"},
            "tokens": [{
                "symbol": "SPYx",
                "price": 762.94,
                "market_cap": 143570000,
                "volume_24h": 53150000,
                "issuer_id": "bstocks",
                "issuer_name": "bStocks",
            }],
            "market_pairs": [{"market_pair": "SPYx/USDC", "category": "spot"}],
        })
        self.assertEqual(result["conclusion"], "provisionally_comparable")


if __name__ == "__main__":
    unittest.main()

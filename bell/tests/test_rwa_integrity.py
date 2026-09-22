import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from rwa_integrity import api_get, scan


class _JsonResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class RwaIntegrityTests(unittest.TestCase):
    def test_surface_drift_and_critical_breaks_are_explicit(self):
        map_payload = {"data": {"rwa_assets": [{"rwa_id": 1, "name": "Gold", "has_tokens": True}]}}
        list_payload = {"data": {"rwa_assets": [{"name": "Unaddressable", "symbol": "X"}, {"rwa_id": 1}]}}
        quotes_payload = {"data": {"rwa_assets": [{
            "rwa_id": 1,
            "name": "Gold",
            "symbol": "GOLD",
            "tokens": [
                {"crypto_id": 10, "symbol": "A", "name": "A", "issuer_id": "issuer-a", "price": 10, "market_cap": 100, "volume_24h": 5},
                {"crypto_id": 11, "symbol": "B", "name": "B", "issuer_id": "issuer-b", "price": 1000, "market_cap": 0, "volume_24h": 5},
            ],
            "tradfi_markets": [],
        }]}}
        result = scan(map_payload, list_payload, quotes_payload, observed_at="2026-09-15T20:00:00Z")
        self.assertEqual(result["catalogue_integrity"]["asset_list_rows_without_rwa_id"], 1)
        self.assertEqual(result["universe"]["states"]["do_not_compare"], 1)
        self.assertEqual(result["universe"]["signals"]["PRICE_DENOMINATION_BREAK"], 1)
        self.assertEqual(result["universe"]["signals"]["ZERO_MCAP_POSITIVE_VOLUME"], 1)
        self.assertEqual(result["method"]["join_key"], "rwa_id")
        self.assertEqual(result["method"]["refresh_profiles"]["map"], "30 seconds")
        self.assertIn("Resolve", result["alerts"][0]["next_action"])
        self.assertEqual(result["alerts"][0]["decision"]["state"], "blocked")
        self.assertEqual(len(result["alert_index"]), 1)
        self.assertEqual(result["alert_index"][0]["rwa_id"], 1)
        self.assertIn("PRICE_DENOMINATION_BREAK", result["alert_index"][0]["signal_codes"])
        self.assertEqual(result["alert_index"][0]["signal_evidence"]["PRICE_DENOMINATION_BREAK"]["max_min_ratio"], 100.0)
        self.assertEqual([row["crypto_id"] for row in result["alert_index"][0]["representations"]], [10, 11])
        self.assertEqual(result["alert_index"][0]["representations"][0]["issuer_id"], "issuer-a")

    def test_identity_surfaces_are_cross_checked_when_available(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 7, "has_tokens": True}]}}
        info = {"data": {"rwa_assets": [{"rwa_id": 7}]}}
        quotes = {"data": {"rwa_assets": [{"rwa_id": 7, "name": "Gold", "tokens": [{"crypto_id": 12, "symbol": "GOLD", "issuer_id": "issuer-a", "price": 1, "market_cap": 1, "volume_24h": 1}], "tradfi_markets": []}]}}
        issuers = {"data": {"issuers": [{"issuer_id": "issuer-a", "name": "Issuer A", "website": "https://issuer.example", "num_tokens": 1}]}}
        crypto_info = {"data": {"12": {"id": 12, "slug": "gold-wrapper", "urls": {"website": ["https://token.example"]}, "contract_address": [{"contract_address": "0xabc", "platform": {"name": "Ethereum", "coin": {"slug": "ethereum"}}}]}}}
        result = scan(base, base, quotes, info, issuers, crypto_info_payload=crypto_info)
        self.assertEqual(result["identity_integrity"]["info_unique_ids"], 1)
        self.assertEqual(result["identity_integrity"]["quote_issuer_ids_missing_from_catalogue"], [])
        self.assertEqual(result["identity_integrity"]["quote_crypto_ids_missing_from_info"], [])
        self.assertEqual(result["alerts"][0]["tokens"][0]["issuer_website"], "https://issuer.example")
        self.assertEqual(result["alerts"][0]["tokens"][0]["cmc_url"], "https://coinmarketcap.com/currencies/gold-wrapper/")
        self.assertEqual(result["alerts"][0]["tokens"][0]["platforms"][0]["contract_address"], "0xabc")
        self.assertEqual(result["issuer_catalogue"][0]["name"], "Issuer A")

    def test_decision_output_exposes_the_operational_capital_gate(self):
        payload = {"data": {"rwa_assets": [{"rwa_id": 9, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 9,
            "name": "Silver",
            "tokens": [
                {"crypto_id": 90, "symbol": "S1", "name": "Silver wrapper", "issuer_id": "issuer-a", "price": 1, "market_cap": 100, "volume_24h": 1},
                {"crypto_id": 91, "symbol": "S2", "name": "Silver wrapper", "issuer_id": "issuer-b", "price": 20, "market_cap": 100, "volume_24h": 1},
            ],
            "tradfi_markets": [],
        }]}}
        result = scan(payload, payload, quotes)
        decision = result["alerts"][0]["decision"]
        self.assertEqual(decision["label"], "DO NOT SELECT A WRAPPER")
        self.assertIn("NO WRAPPER SELECTED", decision["allocation_effect"])

    def test_population_attribution_reconciles_rows_and_keeps_missing_values_visible(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 1, "has_tokens": True}]}}
        list_payload = {"data": {"rwa_assets": [{"rwa_id": 1, "tokenized_market_cap": 100.0}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 1,
            "name": "Gold",
            "asset_type": "commodity",
            "tokens": [
                {"crypto_id": 1, "issuer_id": "issuer-a", "issuer_name": "Issuer A", "market_cap": 60.0},
                {"crypto_id": 2, "issuer_id": "issuer-b", "issuer_name": "Issuer B", "market_cap": 40.0},
                {"crypto_id": 3, "issuer_id": "issuer-c", "issuer_name": "Issuer C", "market_cap": None},
                {"crypto_id": 4, "issuer_id": "issuer-c", "issuer_name": "Issuer C", "market_cap": 0.0},
            ],
            "tradfi_markets": [],
        }]}}
        result = scan(base, list_payload, quotes)
        population = result["population_attribution"]
        self.assertEqual(population["token_rows"], 4)
        self.assertEqual(population["positive_market_cap_rows"], 2)
        self.assertEqual(population["missing_market_cap_rows"], 1)
        self.assertEqual(population["zero_or_non_positive_market_cap_rows"], 1)
        self.assertEqual(population["asset_level_reconciliation"]["exact_within_usd_cent"], 1)
        self.assertEqual(population["asset_level_reconciliation"]["token_to_asset_value_ratio"], 1.0)
        self.assertEqual(population["concentration"]["hhi"], 5200.0)
        self.assertEqual(population["concentration"]["effective_issuer_count"], 1.923076923076923)
        self.assertEqual(population["top_issuers"][0]["declared_num_tokens"], None)

    def test_rule_boundaries_are_inclusive_and_missing_values_stay_missing(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 1, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 1,
            "name": "Boundary",
            "tokens": [
                {"crypto_id": 1, "symbol": "A", "name": "A", "issuer_id": "i", "price": 1, "market_cap": 10, "volume_24h": 1},
                {"crypto_id": 2, "symbol": "B", "name": "B", "issuer_id": "j", "price": 2, "market_cap": None, "volume_24h": 1},
            ],
            "tradfi_markets": [{}],
        }]}}
        result = scan(base, base, quotes)
        codes = {signal["code"] for signal in result["alerts"][0]["signals"]}
        self.assertIn("PRICE_DISPERSION", codes)
        self.assertNotIn("PRICE_DENOMINATION_BREAK", codes)
        self.assertIn("MARKET_FIELDS_MISSING", codes)
        self.assertEqual(result["alerts"][0]["decision"]["state"], "hold")

    def test_rule_calibration_publishes_observed_threshold_bands(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 1, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 1,
            "name": "Calibration",
            "tokens": [
                {"crypto_id": 1, "price": 1, "market_cap": 10, "volume_24h": 1},
                {"crypto_id": 2, "price": 2, "market_cap": 10, "volume_24h": 1},
                {"crypto_id": 3, "price": 10, "market_cap": 10, "volume_24h": 1},
            ],
            "tradfi_markets": [],
        }]}}
        result = scan(base, base, quotes)
        calibration = result["rule_calibration"]
        self.assertEqual(calibration["schema_version"], "bell.rule_calibration.v1")
        self.assertEqual(calibration["reference_count"], 1)
        self.assertEqual(calibration["references_with_two_positive_prices"], 1)
        self.assertEqual(calibration["observed_ratio_bands"]["10x_or_more"], 1)
        self.assertTrue(calibration["thresholds"]["price_denomination_break"]["inclusive"])

    def test_malformed_numeric_fields_are_missing_not_zero(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 4, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 4,
            "name": "Malformed fields",
            "tokens": [{"crypto_id": 40, "symbol": "BAD", "issuer_id": "issuer-a", "price": "n/a", "market_cap": "0", "volume_24h": "n/a"}],
            "tradfi_markets": [],
        }]}}
        result = scan(base, base, quotes)
        signals = {signal["code"]: signal for signal in result["alerts"][0]["signals"]}
        self.assertIn("MARKET_FIELDS_MISSING", signals)
        self.assertNotIn("ZERO_MCAP_POSITIVE_VOLUME", signals)
        self.assertEqual(signals["MARKET_FIELDS_MISSING"]["evidence"]["count"], 1)

    def test_non_finite_numeric_fields_are_missing_without_crashing(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 5, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 5,
            "name": "Non finite fields",
            "tokens": [{"crypto_id": 50, "symbol": "NAN", "issuer_id": "issuer-a", "price": "NaN", "market_cap": "Infinity", "volume_24h": "-Infinity"}],
            "tradfi_markets": [],
        }]}}
        result = scan(base, base, quotes)
        codes = {signal["code"] for signal in result["alerts"][0]["signals"]}
        self.assertIn("MARKET_FIELDS_MISSING", codes)
        self.assertNotIn("ZERO_MCAP_POSITIVE_VOLUME", codes)

    def test_clean_reference_is_not_called_safe(self):
        base = {"data": {"rwa_assets": [{"rwa_id": 1, "has_tokens": True}]}}
        quotes = {"data": {"rwa_assets": [{
            "rwa_id": 1,
            "name": "Clean",
            "tokens": [{"crypto_id": 1, "symbol": "A", "name": "A", "issuer_id": "i", "price": 1, "market_cap": 10, "volume_24h": 1}],
            "tradfi_markets": [{}],
        }]}}
        result = scan(base, base, quotes)
        self.assertEqual(result["universe"]["states"]["no_flags"], 1)
        self.assertEqual(result["alerts"][0]["decision"]["label"], "NO RULE HIT, NOT APPROVED")

    def test_malformed_required_surface_is_incomplete_not_clean(self):
        valid = {"data": {"rwa_assets": []}}
        result = scan(valid, {"data": {"wrong_key": []}}, valid)
        self.assertEqual(result["method"]["scan_status"], "incomplete")
        self.assertEqual(result["method"]["input_integrity"]["invalid_or_missing_surfaces"], ["asset_list"])
        self.assertIn("Incomplete input", result["method"]["input_integrity"]["decision_note"])

    def test_transient_cmc_failure_retries_with_backoff(self):
        transient = HTTPError("https://example.test", 429, "rate limited", {}, None)
        response = _JsonResponse(b'{"data": {"rwa_assets": []}}')
        with patch("rwa_integrity.urlopen", side_effect=[transient, response]) as mocked, patch("rwa_integrity.time.sleep") as sleeper:
            result = api_get("/v5/real-world-assets/map", {"start": 1}, "key-not-stored")
        self.assertEqual(result["data"]["rwa_assets"], [])
        self.assertEqual(mocked.call_count, 2)
        sleeper.assert_called_once_with(1)

    def test_permanent_cmc_failure_is_not_hidden_as_empty_data(self):
        failure = HTTPError("https://example.test", 403, "forbidden", {}, None)
        with patch("rwa_integrity.urlopen", side_effect=failure) as mocked:
            with self.assertRaises(HTTPError):
                api_get("/v5/real-world-assets/market-pairs/list", {"rwa_id": 5}, "key-not-stored")
        self.assertEqual(mocked.call_count, 1)


if __name__ == "__main__":
    unittest.main()

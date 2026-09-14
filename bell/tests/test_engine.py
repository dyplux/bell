import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bell import fetch_live_asset, fetch_live_catalog, fetch_live_dataset
from engine import BellDataError, analyse_dataset, analyse_wrapper, classify_session, normalise_bar


def bar(timestamp, opened=100, high=101, low=99):
    return {"time_open": timestamp, "open": opened, "high": high, "low": low, "close": opened}


class SessionEngineTests(unittest.TestCase):
    def test_session_boundaries_and_dst(self):
        self.assertEqual(classify_session("2026-01-06T14:30:00Z"), "cash")
        self.assertEqual(classify_session("2026-01-06T21:00:00Z"), "after_hours")
        self.assertEqual(classify_session("2026-01-10T15:00:00Z"), "weekend")
        self.assertEqual(classify_session("2026-07-06T13:30:00Z"), "cash")
        self.assertEqual(classify_session("2026-11-02T14:30:00Z"), "cash")

    def test_range_formula_and_normalisation(self):
        result = normalise_bar(bar("2026-01-06T14:30:00Z", high=102, low=99))
        self.assertEqual(result["range_pct"], 3.0)
        self.assertEqual(result["time_open"], "2026-01-06T14:30:00Z")

    def test_zero_open_and_incomplete_schema_are_rejected(self):
        with self.assertRaises(BellDataError):
            normalise_bar(bar("2026-01-06T14:30:00Z", opened=0))
        result = analyse_dataset({
            "window_start": "2026-01-06T14:30:00Z",
            "window_end": "2026-01-06T15:30:00Z",
            "wrappers": [{"symbol": "BAD", "bars": [{"time_open": "2026-01-06T14:30:00Z", "open": 100}]}],
        })
        self.assertEqual(result["state"], "insufficient-data")
        self.assertEqual(result["wrappers"][0]["bars_valid"], 0)

    def test_duplicates_gaps_and_unknown_venue_are_visible(self):
        wrapper = {
            "symbol": "TEST",
            "issuer": "Issuer",
            "bars": [
                bar("2026-01-06T14:30:00Z"),
                bar("2026-01-06T14:30:00Z"),
                bar("2026-01-06T21:00:00Z"),
                bar("2026-01-10T15:00:00Z"),
            ],
        }
        result = analyse_wrapper(
            wrapper,
            normalise_bar(bar("2026-01-06T14:30:00Z"))["time_open"],
            normalise_bar(bar("2026-01-10T15:00:00Z"))["time_open"],
        )
        self.assertEqual(result["venue"]["status"], "unavailable")
        self.assertTrue(any("duplicate" in warning for warning in result["warnings"]))
        self.assertTrue(any("gap" in warning for warning in result["warnings"]))

    def test_fixture_has_explicit_partial_state_and_venue_math(self):
        payload = {
            "window_start": "2026-01-06T14:30:00Z",
            "window_end": "2026-01-10T16:00:00Z",
            "wrappers": [{
                "symbol": "A",
                "bars": [
                    bar("2026-01-06T14:30:00Z"),
                    bar("2026-01-06T21:00:00Z"),
                    bar("2026-01-10T15:00:00Z"),
                ],
                "venue": {"cex_volume_24h": 80, "dex_volume_24h": 20},
            }],
        }
        result = analyse_dataset(payload)
        self.assertEqual(result["state"], "partial")
        self.assertEqual(result["wrappers"][0]["venue"]["cex_share_pct"], 80.0)
        self.assertIsNotNone(result["wrappers"][0]["sessions"]["weekend"]["median_range_pct"])

    def test_live_adapter_reads_cmc_object_shapes_without_network(self):
        class FakeCMC:
            calls = []

            def get(self, endpoint, params):
                self.calls.append({"endpoint": endpoint, "params": params, "status": 200})
                if "real-world-assets/quotes/latest" in endpoint:
                    return {"data": {"rwa_assets": [{"name": "Tesla", "slug": "tesla", "rwa_id": 14, "tokens": [{"symbol": "FIX", "crypto_id": 1, "issuer_name": "Issuer"}]}]}}
                if endpoint.endswith("ohlcv/historical"):
                    return {"data": {"quotes": [{"time_open": "2026-01-06T14:30:00Z", "quote": {"USD": {"open": 100, "high": 101, "low": 99, "close": 100}}}]}}
                return {"data": {"1": {"quote": {"USD": {"cex_volume_24h": 80, "dex_volume_24h": 20}}}}}

        payload = fetch_live_dataset(FakeCMC(), "tesla", 1)
        self.assertEqual(payload["asset"]["name"], "Tesla")
        self.assertEqual(payload["wrappers"][0]["bars"][0]["open"], 100)
        self.assertEqual(payload["wrappers"][0]["venue"]["cex_volume_24h"], 80)
        ohlcv_call = next(call for call in FakeCMC.calls if call["endpoint"].endswith("ohlcv/historical"))
        self.assertEqual(ohlcv_call["params"]["time_period"], "hourly")
        self.assertEqual(ohlcv_call["params"]["interval"], "hourly")
        self.assertEqual(ohlcv_call["params"]["count"], 25)

    def test_catalog_adapter_paginates_and_keeps_search_fields(self):
        class FakeCMC:
            calls = []

            def get(self, endpoint, params):
                self.calls.append({"endpoint": endpoint, "params": params, "status": 200})
                start = params["start"]
                if start == 1:
                    return {"data": {"rwa_assets": [{"rwa_id": 14, "name": "Tesla, Inc.", "symbol": "TSLA", "slug": "tesla", "asset_type": "stock", "rwa_rank": 3, "has_tokens": True}], "total_size": 2, "has_more": True}}
                return {"data": {"rwa_assets": [{"rwa_id": 15, "name": "Gold", "symbol": "GOLD", "slug": "gold", "asset_type": "commodity", "rwa_rank": 1, "has_tokens": True}], "total_size": 2, "has_more": False}}

        catalog = fetch_live_catalog(FakeCMC(), page_size=1)
        self.assertEqual(catalog["schema_version"], "bell.catalog.v1")
        self.assertEqual(catalog["total_size"], 2)
        self.assertEqual([asset["slug"] for asset in catalog["assets"]], ["tesla", "gold"])
        self.assertEqual(len(catalog["provenance"]["calls"]), 2)

    def test_asset_dossier_keeps_token_identity_and_quotes(self):
        class FakeCMC:
            calls = []

            def get(self, endpoint, params):
                self.calls.append({"endpoint": endpoint, "params": params, "status": 200})
                return {"data": {"rwa_assets": [{"rwa_id": 14, "name": "Tesla", "symbol": "TSLA", "slug": "tesla", "asset_type": "stock", "has_tokens": True, "last_updated": "2026-09-13T09:00:00Z", "tokens": [{"name": "Tesla xStock", "symbol": "TSLAX", "price": 100, "crypto_id": 123, "issuer_name": "Backed Assets", "market_cap": 1000, "volume_24h": 50}], "tradfi_markets": []}]}}

        dossier = fetch_live_asset(FakeCMC(), "tesla")
        self.assertEqual(dossier["schema_version"], "bell.asset.v1")
        self.assertEqual(dossier["tokens"][0]["issuer_name"], "Backed Assets")
        self.assertEqual(dossier["tokens"][0]["price"], 100)
        self.assertEqual(dossier["provenance"]["raw_responses_included"], False)


if __name__ == "__main__":
    unittest.main()

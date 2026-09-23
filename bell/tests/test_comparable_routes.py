"""Contract for the affirmative half of the monitor.

Every rule in this scanner answers "can these representations be compared?".
Until now a reference that cleared every rule produced nothing but the absence
of a complaint, so a reader who asked "then which one do I buy?" got no answer.
These tests pin the answer, and pin the cases where refusing to answer is
still correct.
"""
import unittest

from rwa_integrity import MAX_PUBLISHABLE_SPREAD_BPS, asset_scan, comparable_routes


def token(symbol, price, volume, *, derivative=False, issuer="Issuer", crypto_id=None):
    return {
        "crypto_id": crypto_id or symbol,
        "symbol": symbol,
        "name": f"{symbol} wrapper",
        "issuer_id": issuer,
        "issuer_name": issuer,
        "price": price,
        "market_cap": (price or 0) * 1000,
        "volume_24h": volume,
        "is_derivative": derivative,
    }


def crypto_lookup_for(tokens):
    """Resolve every crypto_id, so TOKEN_INFO_MISSING does not fire.

    `crypto_info_resolved` is derived inside token_summary from this lookup, not
    accepted from the token, so a test that wants a clear reference has to
    supply the lookup rather than assert the flag.
    """
    return {str(t["crypto_id"]): {"id": t["crypto_id"], "platform": {"name": "Ethereum"}} for t in tokens}


class ComparableRoutes(unittest.TestCase):
    def test_two_tradable_routes_are_ranked_cheapest_first(self):
        result = comparable_routes([
            token("AAA", 100.0, 50_000),
            token("BBB", 102.0, 10_000),
        ])
        self.assertIsNotNone(result)
        self.assertEqual(result["route_count"], 2)
        self.assertEqual(result["cheapest"]["symbol"], "AAA")
        # 102/100 - 1 = 2%, which is 200 basis points.
        self.assertAlmostEqual(result["spread_bps"], 200.0, places=1)
        self.assertAlmostEqual(result["routes"][1]["premium_to_cheapest_bps"], 200.0, places=1)

    def test_deepest_route_is_reported_separately_from_cheapest(self):
        # The cheapest print is not always the one you can actually fill.
        result = comparable_routes([
            token("THIN", 100.0, 1_000),
            token("DEEP", 101.0, 900_000),
        ])
        self.assertEqual(result["cheapest"]["symbol"], "THIN")
        self.assertEqual(result["deepest"]["symbol"], "DEEP")
        self.assertFalse(result["cheapest_is_deepest"])

    def test_volume_shares_sum_to_one(self):
        result = comparable_routes([
            token("AAA", 10.0, 250_000),
            token("BBB", 11.0, 750_000),
        ])
        self.assertAlmostEqual(sum(route["volume_share"] for route in result["routes"]), 1.0, places=9)

    def test_untraded_row_is_not_a_route(self):
        # A quote nobody traded cannot be bought at the price it prints.
        self.assertIsNone(comparable_routes([
            token("AAA", 100.0, 50_000),
            token("DEAD", 90.0, 0),
        ]))

    def test_unpriced_row_is_not_a_route(self):
        self.assertIsNone(comparable_routes([
            token("AAA", 100.0, 50_000),
            token("NOPRICE", None, 50_000),
        ]))

    def test_derivative_is_excluded_from_the_comparison(self):
        # A derivative is not another way into the same spot exposure.
        self.assertIsNone(comparable_routes([
            token("SPOT", 100.0, 50_000),
            token("PERP", 100.5, 900_000, derivative=True),
        ]))

    def test_single_representation_produces_no_comparison(self):
        self.assertIsNone(comparable_routes([token("ONLY", 100.0, 50_000)]))


class ComparisonIsGatedByTheRules(unittest.TestCase):
    def _scan(self, tokens):
        asset = {"rwa_id": "1", "name": "Ref", "symbol": "REF", "asset_type": "commodity", "tokens": tokens}
        return asset_scan(asset, None, crypto_lookup_for(tokens), crypto_info_checked=True)

    def test_clear_reference_publishes_a_comparison(self):
        scan = self._scan([token("AAA", 100.0, 50_000), token("BBB", 101.0, 40_000)])
        self.assertEqual(scan["state"], "no_flags")
        self.assertIsNotNone(scan["comparison"])
        self.assertEqual(scan["comparison"]["cheapest"]["symbol"], "AAA")

    def test_blocked_reference_publishes_no_comparison(self):
        # A 10x price span is a denomination break: comparing these numbers is
        # exactly the mistake the monitor exists to prevent.
        scan = self._scan([token("GRAM", 100.0, 50_000), token("OUNCE", 3_110.0, 40_000)])
        self.assertEqual(scan["state"], "do_not_compare")
        self.assertIsNone(scan["comparison"])

    def test_investigate_reference_still_publishes_when_the_warning_is_neutralised(self):
        # Requiring a spotless reference made the answer unreachable: across a
        # 50-reference live receipt, nothing ever reached no_flags, so the
        # monitor refused 35 cases and affirmed none. A warning the route filter
        # already handles must not also withhold the answer.
        scan = self._scan([
            token("AAA", 100.0, 50_000),
            token("BBB", 101.0, 40_000),
            token("NOVOL", 99.0, 0),          # excluded: nobody traded it
            token("PERP", 100.5, 900_000, derivative=True),  # excluded: not the same exposure
        ])
        self.assertEqual(scan["state"], "investigate")
        self.assertIsNotNone(scan["comparison"])
        self.assertEqual(scan["comparison"]["route_count"], 2)
        self.assertEqual(scan["comparison"]["published_under"], "investigate")
        # Published WITH what is still open, never as a clean bill of health.
        # The derivative was dropped from the routes, but the warning that a
        # derivative is present stays visible to the reader.
        self.assertIn("DERIVATIVE_MIX", scan["comparison"]["unresolved"])

    def test_price_dispersion_withholds_the_comparison(self):
        # When the prices themselves disagree beyond any plausible wrapper
        # spread, the disagreement is the finding. Do not rank through it.
        scan = self._scan([token("AAA", 100.0, 50_000), token("WIDE", 260.0, 40_000)])
        codes = [s["code"] for s in scan["signals"]]
        self.assertIn("PRICE_DISPERSION", codes)
        self.assertIsNone(scan["comparison"])

    def test_spread_above_the_publishable_ceiling_is_withheld(self):
        # 20% is not a dislocation anyone trades; it is an unmodelled unit or
        # claim difference the coded rules did not catch.
        routes = comparable_routes([
            token("AAA", 100.0, 50_000),
            token("FAR", 100.0 * (1 + (MAX_PUBLISHABLE_SPREAD_BPS + 1) / 10_000), 40_000),
        ])
        self.assertIsNone(routes)

    def test_spread_just_inside_the_ceiling_is_published(self):
        routes = comparable_routes([
            token("AAA", 100.0, 50_000),
            token("NEAR", 100.0 * (1 + (MAX_PUBLISHABLE_SPREAD_BPS - 100) / 10_000), 40_000),
        ])
        self.assertIsNotNone(routes)



class CoverageIsReportedNotRestated(unittest.TestCase):
    """Demoting a rule must not hide what it was telling you.

    MARKET_FIELDS_MISSING fired on 646 of 791 references and drove 84% of the
    catalogue to INVESTIGATE, so the state distribution restated one API
    coverage fact 646 times instead of describing any reference. It no longer
    decides a state - but the fact itself must stay visible, or demoting it
    would be concealment rather than correction.
    """

    def _scan(self, tokens):
        asset = {"rwa_id": "1", "name": "Ref", "symbol": "REF", "asset_type": "commodity", "tokens": tokens}
        return asset_scan(asset, None, crypto_lookup_for(tokens), crypto_info_checked=True)

    def test_missing_market_fields_no_longer_holds_a_reference_open(self):
        scan = self._scan([
            token("AAA", 100.0, 50_000),
            token("BBB", 101.0, 40_000),
            token("NOCAP", 99.0, 30_000),
        ])
        scan["tokens"][2]["market_cap"] = None
        rescan = asset_scan(
            {"rwa_id": "1", "name": "Ref", "symbol": "REF", "asset_type": "commodity",
             "tokens": [dict(t) for t in scan["tokens"]]},
            None, crypto_lookup_for(scan["tokens"]), crypto_info_checked=True)
        codes = [s["code"] for s in rescan["signals"]]
        self.assertIn("MARKET_FIELDS_MISSING", codes, "the fact must still be reported")
        severity = next(s["severity"] for s in rescan["signals"] if s["code"] == "MARKET_FIELDS_MISSING")
        self.assertEqual(severity, "info", "it must not carry warning severity any more")
        self.assertNotEqual(rescan["state"], "investigate",
                            "a coverage gap must not by itself hold a reference open")

    def test_the_fact_still_names_which_rows_are_missing(self):
        reps = [token("AAA", 100.0, 50_000), token("NOCAP", 99.0, 30_000)]
        reps[1]["market_cap"] = None
        scan = self._scan(reps)
        signal = next(s for s in scan["signals"] if s["code"] == "MARKET_FIELDS_MISSING")
        self.assertIn("tokens", signal["evidence"])
        self.assertGreaterEqual(signal["evidence"]["count"], 1)
        self.assertIn("NOCAP", signal["evidence"]["tokens"])

    def test_a_real_contradiction_still_holds_the_reference_open(self):
        # Demoting one rule must not soften the ones that discriminate.
        scan = self._scan([
            token("SPOT", 100.0, 50_000),
            token("PERP", 100.5, 40_000, derivative=True),
            token("ALSO", 101.0, 30_000),
        ])
        self.assertEqual(scan["state"], "investigate")
        self.assertIn("DERIVATIVE_MIX", [s["code"] for s in scan["signals"]])
if __name__ == "__main__":
    unittest.main()


class TheDecisionMatchesWhatTheReaderHolds(unittest.TestCase):
    """A reader handed the cheapest route, the spread and the depth was told in
    the same block that nothing had been produced: the decision still read
    "NO RULE HIT, NOT APPROVED". The refusal was right about diligence and
    wrong about what the reader was holding.
    """

    def _scan(self, tokens):
        asset = {"rwa_id": "1", "name": "Ref", "symbol": "REF", "asset_type": "commodity", "tokens": tokens}
        return asset_scan(asset, None, crypto_lookup_for(tokens), crypto_info_checked=True)

    def test_a_published_comparison_is_named_in_the_decision(self):
        scan = self._scan([token("AAA", 100.0, 50_000), token("BBB", 101.0, 40_000)])
        self.assertIsNotNone(scan["comparison"])
        self.assertEqual(scan["decision"]["label"], "COMPARABLE, NOT ENDORSED")
        self.assertIn("bps", scan["decision"]["consequence"])
        self.assertIn("AAA", scan["decision"]["consequence"])

    def test_the_decision_still_refuses_to_endorse(self):
        # Naming the comparison must not turn into an allocation claim.
        scan = self._scan([token("AAA", 100.0, 50_000), token("BBB", 101.0, 40_000)])
        effect = scan["decision"]["allocation_effect"].lower()
        for absent in ("backing", "redemption", "eligibility", "custody"):
            self.assertIn(absent, effect)
        self.assertIn("not an allocation", effect)

    def test_a_blocked_reference_keeps_its_refusal(self):
        scan = self._scan([token("GRAM", 100.0, 50_000), token("OUNCE", 3_110.0, 40_000)])
        self.assertIsNone(scan["comparison"])
        self.assertEqual(scan["decision"]["label"], "DO NOT SELECT A WRAPPER")

    def test_a_reference_with_no_comparison_keeps_the_unresolved_label(self):
        scan = self._scan([token("ONLY", 100.0, 50_000)])
        self.assertIsNone(scan["comparison"])
        self.assertNotEqual(scan["decision"]["label"], "COMPARABLE, NOT ENDORSED")

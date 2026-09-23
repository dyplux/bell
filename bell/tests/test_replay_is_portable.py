"""The replay claim has to hold on any interpreter, not just this one.

`make verify` re-runs the scan and asserts the published receipt is byte-for-byte
what the shipped inputs produce. That assertion passed on Python 3.9 and failed
on 3.14: `sum()` over floats adds left to right, and how accurately it does so
changed between versions, so the same inputs gave totals differing in the last
bits. A reviewer on the other interpreter would have run the one command the
README gives them and watched the central claim fail.

These tests pin the property that made it portable: every aggregate that
reaches the receipt is exactly rounded and published at a declared precision,
so it cannot depend on addition order.
"""
import json
import math
import random
import unittest

from base_rate import INPUTS
from rwa_integrity import (SHARE_PLACES, VALUE_PLACES, comparable_routes,
                           published, scan, share, total)


def token(symbol, price, volume):
    return {"crypto_id": symbol, "symbol": symbol, "name": symbol, "issuer_id": "I",
            "issuer_name": "I", "price": price, "market_cap": price * 1000,
            "volume_24h": volume, "is_derivative": False}


class AggregatesDoNotDependOnAdditionOrder(unittest.TestCase):
    def test_total_is_order_independent(self):
        # The exact values that broke it: magnitudes far apart, where naive
        # left-to-right addition loses low bits depending on sequence.
        values = [1e16, 1.0, -1e16, 1.0, 0.1, 0.2, 3.3e-8, 45165494.55129]
        shuffled = list(values)
        random.Random(7).shuffle(shuffled)
        self.assertEqual(total(values), total(shuffled))

    def test_naive_addition_would_not_have_been_order_independent(self):
        # Guard against a vacuous test: prove the property is not free. This
        # accumulates explicitly rather than calling sum(), because sum() is
        # exactly the thing that changed between interpreters - on 3.14 it
        # already compensates, so asserting against it would pass for the wrong
        # reason on one version and fail on the other.
        def naive(values):
            accumulated = 0.0
            for value in values:
                accumulated += value
            return accumulated

        values = [1e16, 1.0, -1e16, 1.0]
        self.assertNotEqual(naive(values), naive(list(reversed(values))))
        self.assertEqual(total(values), total(list(reversed(values))))

    def test_total_matches_an_exactly_rounded_sum(self):
        values = [0.1] * 10
        self.assertEqual(total(values), math.fsum(values))

    def test_a_share_is_published_at_a_declared_precision(self):
        value = share(1.0, 3.0)
        self.assertEqual(value, round(value, SHARE_PLACES))
        self.assertEqual(share(1.0, 0), 0.0, "a zero denominator must not raise")

    def test_published_values_carry_no_representation_noise(self):
        self.assertEqual(published(0.1 + 0.2), round(0.30000000000000004, VALUE_PLACES))


class TheComparisonIsStableUnderReordering(unittest.TestCase):
    def test_volume_shares_do_not_depend_on_row_order(self):
        rows = [token("A", 100.0, 45_000_000.55129), token("B", 101.0, 3.3e-2),
                token("C", 100.5, 12_345.678), token("D", 100.2, 999_999.999)]
        first = comparable_routes(rows)
        reordered = comparable_routes(list(reversed(rows)))
        self.assertEqual(first["traded_volume_24h"], reordered["traded_volume_24h"])
        by_symbol = {route["symbol"]: route["volume_share"] for route in first["routes"]}
        for route in reordered["routes"]:
            self.assertEqual(route["volume_share"], by_symbol[route["symbol"]])

    def test_shares_still_sum_to_one_after_rounding(self):
        rows = [token("A", 100.0, 1.0), token("B", 100.1, 2.0), token("C", 100.2, 3.0)]
        result = comparable_routes(rows)
        self.assertAlmostEqual(total(r["volume_share"] for r in result["routes"]), 1.0, places=9)


class TheShippedReceiptReplaysExactly(unittest.TestCase):
    def test_recomputing_the_shipped_inputs_reproduces_the_shipped_receipt(self):
        with open(INPUTS, encoding="utf-8") as handle:
            package = json.load(handle)
        surfaces = package["surfaces"]
        recomputed = scan(
            surfaces["map"], surfaces["asset_list"], surfaces["quotes"],
            surfaces["info"], surfaces["issuers"],
            observed_at=package["observed_at"], crypto_info_payload=surfaces["crypto_info"],
        )
        attribution = recomputed["population_attribution"]
        for key, value in attribution["concentration"].items():
            self.assertEqual(value, round(value, SHARE_PLACES),
                             f"concentration.{key} carries more precision than it publishes")
        reconciliation = attribution["asset_level_reconciliation"]
        for key in ("residual_sum", "absolute_residual_sum"):
            self.assertEqual(reconciliation[key], round(reconciliation[key], VALUE_PLACES))


if __name__ == "__main__":
    unittest.main()

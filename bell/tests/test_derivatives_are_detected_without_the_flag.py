"""CoinMarketCap does not send `is_derivative`, and the code read it alone.

The key appears zero times in the 16.5 MB credential-free input package this
repository ships, and it is null on all 312 token rows of the live receipt,
including the 42 whose name ends in "(Derivatives)". So
`if token.get("is_derivative"): continue` never excluded anything, and the
published comparison carried a basis string reading "Observed CMC quotes for
the non-derivative representations of this reference".

The signal path had the working detector the whole time - reading the words in
name, asset_type, token_type and category - which is how DERIVATIVE_MIX finds
121 groups. Two answers to one question in one file, and the affirmative output
read the wrong one.

The existing test for this passed on fiction: its fixtures set
`"is_derivative": True`, a key the source never sends. Mutation testing could
not help either, because neutering the filter DOES break that test, so the
guard reported as defended while never firing on real data. This file feeds the
shape CoinMarketCap actually returns.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from rwa_integrity import asset_scan, comparable_routes, is_derivative_row  # noqa: E402

PROOF = HERE.parent / "site" / "proof"


def cmc_row(crypto_id: int, symbol: str, name: str, price: float, **extra) -> dict:
    """A row shaped the way the source really returns one: no is_derivative."""
    row = {"crypto_id": crypto_id, "symbol": symbol, "name": name, "price": price,
           "market_cap": price * 1000, "volume_24h": 50_000.0,
           "issuer_id": 1, "issuer_name": "Acme", "crypto_info_resolved": True}
    row.update(extra)
    assert "is_derivative" not in row, "the fixture reintroduced the key CMC never sends"
    return row


class TheSourceNeverSendsTheFlag(unittest.TestCase):
    def test_the_shipped_inputs_do_not_carry_is_derivative(self):
        # If this ever fails, CoinMarketCap started sending the field and the
        # fallback below stops being the only way to know.
        inputs = (PROOF / "rwa-surface-integrity-inputs-2026-09-21.json").read_text(encoding="utf-8")
        self.assertNotIn('"is_derivative"', inputs,
                         "the input package now carries is_derivative; re-read the docstring")

    def test_the_shipped_receipt_has_derivative_rows_and_no_flag(self):
        receipt = json.loads((PROOF / "rwa-surface-integrity-latest-replay-2026-09-21.json")
                             .read_text(encoding="utf-8"))
        rows = [token for alert in receipt.get("alerts", [])
                for token in (alert.get("tokens") or [])]
        named = [row for row in rows if "derivative" in str(row.get("name", "")).lower()]
        self.assertTrue(named, "the shipped receipt carries no derivative-named rows to check")
        self.assertTrue(all(row.get("is_derivative") in (None, False) for row in named),
                        "a derivative-named row now carries the flag")
        for row in named:
            self.assertTrue(is_derivative_row(row),
                            f"{row.get('name')!r} is not detected as a derivative")


class ADerivativeIsNeverNamedAsARoute(unittest.TestCase):
    def test_a_derivative_named_row_is_excluded_from_the_comparison(self):
        tokens = [
            cmc_row(1, "ACME", "Acme Inc (Derivatives)", 90.0),
            cmc_row(2, "ACMEa", "Acme Tokenized Stock", 100.0),
            cmc_row(3, "ACMEb", "Acme Wrapped Share", 101.0),
        ]
        routes = comparable_routes(tokens)
        self.assertIsNotNone(routes, "a two-route comparison was refused outright")
        symbols = [route["symbol"] for route in routes["routes"]]
        self.assertNotIn("ACME", symbols,
                         "a row named (Derivatives) was published as a comparable route")
        self.assertEqual(sorted(symbols), ["ACMEa", "ACMEb"])
        self.assertEqual(routes["cheapest"]["symbol"], "ACMEa",
                         "the derivative was named the cheapest route")

    def test_every_field_the_detector_reads_excludes_the_row(self):
        # "name" is covered by the test above, which is also the field the
        # real rows use; these are the three the source might use instead.
        for field in ("asset_type", "token_type", "category"):
            tokens = [
                cmc_row(1, "ACME", "Acme Inc", 90.0, **{field: "Derivative"}),
                cmc_row(2, "ACMEa", "Acme Tokenized Stock", 100.0),
                cmc_row(3, "ACMEb", "Acme Wrapped Share", 101.0),
            ]
            routes = comparable_routes(tokens)
            with self.subTest(field=field):
                self.assertNotIn("ACME", [route["symbol"] for route in routes["routes"]],
                                 f"a derivative declared through {field} was published as a route")

    def test_the_basis_string_is_true_of_the_rows_it_describes(self):
        # The sentence the comparison publishes about itself.
        tokens = [
            cmc_row(1, "ACME", "Acme Inc (Derivatives)", 90.0),
            cmc_row(2, "ACMEa", "Acme Tokenized Stock", 100.0),
            cmc_row(3, "ACMEb", "Acme Wrapped Share", 101.0),
        ]
        routes = comparable_routes(tokens)
        self.assertIn("non-derivative", routes["basis"])
        for route in routes["routes"]:
            row = next(token for token in tokens if token["symbol"] == route["symbol"])
            self.assertFalse(is_derivative_row(row),
                             "the basis says non-derivative and a route is one")

    def test_the_flag_is_still_honoured_when_the_source_sends_it(self):
        # The fallback must not replace the field, only cover for its absence.
        row = {"crypto_id": 9, "symbol": "X", "name": "Plain Wrapper", "is_derivative": True}
        self.assertTrue(is_derivative_row(row))
        self.assertFalse(is_derivative_row({"crypto_id": 9, "symbol": "X", "name": "Plain Wrapper"}))

    def test_the_scan_reports_the_mix_and_still_refuses_to_rank_the_derivative(self):
        asset = {"rwa_id": 1, "name": "Acme", "symbol": "ACME", "tokens": [
            cmc_row(1, "ACME", "Acme Inc (Derivatives)", 90.0),
            cmc_row(2, "ACMEa", "Acme Tokenized Stock", 100.0),
            cmc_row(3, "ACMEb", "Acme Wrapped Share", 101.0),
        ]}
        result = asset_scan(asset)
        self.assertIn("DERIVATIVE_MIX", [signal["code"] for signal in result["signals"]])
        published = result.get("comparison")
        if published:
            self.assertNotIn("ACME", [route["symbol"] for route in published["routes"]],
                             "the published comparison names the derivative it just flagged")


if __name__ == "__main__":
    unittest.main()

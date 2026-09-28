"""The engine and the measurement had no mutation coverage at all.

`make mutate` reported "122 guards, 0 survive" while `rwa_integrity.py` and
`base_rate.py` were outside its guarded set. That number was a statement about
the evidence chain and not about the two files that produce every published
figure, which is how a route filter that had never excluded anything survived
four reviews.

Bringing them into scope took the sweep to 140 guards and reported six nobody
notices. These are the five that can be driven directly: the refusals that stop
a broken input being published as a measurement of the catalogue.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import base_rate  # noqa: E402
from rwa_integrity import number  # noqa: E402


class NumberRefusesWhatIsNotANumber(unittest.TestCase):
    def test_a_boolean_is_not_a_quantity(self):
        # isinstance(True, int) is True and Decimal(str(True)) raises, but
        # `number` is the only path every price, market cap and volume takes,
        # so the refusal is stated rather than left to an exception further on.
        for value in (True, False):
            self.assertIsNone(number(value), f"{value!r} was read as a quantity")

    def test_absence_is_not_zero(self):
        self.assertIsNone(number(None))
        self.assertIsNone(number("not a price"))
        self.assertIsNone(number(float("nan")))
        self.assertIsNone(number(float("inf")))

    def test_a_real_quantity_still_parses(self):
        self.assertEqual(number("4259.34"), number(4259.34))
        self.assertEqual(float(number(0)), 0.0)


class TheMeasurementRefusesADegenerateInput(unittest.TestCase):
    """A number computed from a broken input is not a measurement of anything.

    Each of these is a step that is individually correct and produces a
    published sentence that is false: an empty index is not a 100% refusal
    rate, and a catalogue where nothing carries two prices is not a catalogue
    where every comparison was refused.
    """

    def test_a_receipt_with_no_index_is_not_a_hundred_percent_refusal_rate(self):
        for receipt in ({}, {"alert_index": []}, {"alert_index": None}):
            with self.subTest(receipt=receipt), self.assertRaises(SystemExit) as raised:
                base_rate.measure(receipt)
            self.assertIn("no population to measure", str(raised.exception))

    def test_a_catalogue_where_nothing_is_priced_is_a_degenerate_input(self):
        # Every price non-numeric: each refusal is correct and "Refusal rate
        # 100.0%" is a measurement of the input, not of the market.
        index = [{"rwa_id": n, "name": f"R{n}", "symbol": f"R{n}", "state": "no_flags",
                  "representations": [{"crypto_id": n * 10, "price": float("nan")},
                                      {"crypto_id": n * 10 + 1, "price": None}]}
                 for n in range(1, 6)]
        with self.assertRaises(SystemExit) as raised:
            base_rate.measure({"alert_index": index})
        self.assertIn("degenerate input", str(raised.exception))
        self.assertIn("not a refusal", str(raised.exception))

    def test_a_lens_that_does_not_account_for_every_reference_is_refused(self):
        # The partition has to be a partition. A new signal code added without
        # deciding which part it belongs to leaves references in none of them,
        # and the first version of this printed two figures that summed to 541
        # of 547 without saying so.
        lens = base_rate._single_representation_lens
        # Four parts, and every reference in exactly one of them.
        singles = [
            {"rwa_id": 1, "signal_codes": ["MARKET_FIELDS_MISSING"]},
            {"rwa_id": 2, "signal_codes": ["ZERO_MCAP_POSITIVE_VOLUME"]},
            {"rwa_id": 3, "signal_codes": ["NO_TRADFI_MARKET"]},
            {"rwa_id": 4, "signal_codes": []},
        ]
        PARTS = ("review_trigger_rows", "incomplete_source_fields", "context_only",
                 "fully_reported")
        counted = lens(singles)
        self.assertEqual(counted["references"], len(singles))
        self.assertEqual(sum(counted[name] for name in PARTS), len(singles),
                         f"the lens accounts for {sum(counted[name] for name in PARTS)} "
                         f"of {len(singles)}")

        # And a code the partition has never seen must not fall through all
        # four branches into nothing. If it ever does, the sum check is what
        # says so rather than a quietly short total.
        with_unknown = singles + [{"rwa_id": 5, "signal_codes": ["A_CODE_NOBODY_CLASSIFIED"]}]
        recounted = lens(with_unknown)
        self.assertEqual(sum(recounted[name] for name in PARTS), len(with_unknown),
                         "a signal code the partition does not know leaves a reference "
                         "in no part")

    def test_a_file_that_is_not_a_json_object_is_refused_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "thing.json"
            for value in ([], "text", 3, True, None):
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.subTest(value=repr(value)), self.assertRaises(SystemExit) as raised:
                    base_rate.read_json(str(path))
                self.assertIn("is not a JSON object", str(raised.exception))
                self.assertIn(path.name, str(raised.exception))


if __name__ == "__main__":
    unittest.main()

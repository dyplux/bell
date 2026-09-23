"""The README's numbers have to be the numbers the code produces.

A README is the one document every judge reads and no test checks. This one
carried "observed on 22 September 2026 ... as observed on 23 September 2026" in
a single sentence for days, because prose drifts silently while code is
verified. The base rate is the most load-bearing number Bell publishes, so it
is recomputed here from the shipped credential-free inputs and compared against
what the README claims, character for character where it matters.
"""
import json
import os
import re
import unittest

from base_rate import INPUTS, measure
from rwa_integrity import scan

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
README = os.path.join(ROOT, 'README.md')


def measured():
    with open(INPUTS, encoding='utf-8') as handle:
        package = json.load(handle)
    surfaces = package['surfaces']
    receipt = scan(
        surfaces['map'], surfaces['asset_list'], surfaces['quotes'],
        surfaces['info'], surfaces['issuers'],
        observed_at=package['observed_at'], crypto_info_payload=surfaces['crypto_info'],
    )
    return measure(receipt)


class ReadmeMatchesTheMeasurement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = measured()
        with open(README, encoding='utf-8') as handle:
            cls.text = handle.read()

    def numbers_in_the_block(self):
        block = re.search(r'```\n(.*?Refusal rate.*?)\n```', self.text, re.S)
        self.assertIsNotNone(block, 'the README no longer shows the base-rate block')
        return block.group(1)

    def test_the_population_and_denominator_are_the_measured_ones(self):
        block = self.numbers_in_the_block()
        self.assertIn(f"{self.result['population']:,}".replace(',', ','), block)
        self.assertIn(str(self.result['excluded_single_representation']), block)
        self.assertIn(str(self.result['denominator_two_or_more_representations']), block)

    def test_the_refused_and_comparable_counts_are_the_measured_ones(self):
        block = self.numbers_in_the_block()
        self.assertIn(str(self.result['refused']), block)
        self.assertIn(str(self.result['comparable']), block)

    def test_the_rate_and_interval_are_the_measured_ones(self):
        block = self.numbers_in_the_block()
        lo, hi = self.result['refusal_rate_ci95']
        self.assertIn(f"{self.result['refusal_rate'] * 100:.1f}%", block)
        self.assertIn(f"{lo * 100:.1f}%", block)
        self.assertIn(f"{hi * 100:.1f}%", block)
        self.assertIn(f"n = {self.result['denominator_two_or_more_representations']}", block)

    def test_the_refused_and_comparable_counts_add_up_to_the_denominator(self):
        # An arithmetic identity the README would otherwise be free to break.
        self.assertEqual(
            self.result['refused'] + self.result['comparable'],
            self.result['denominator_two_or_more_representations'])

    def test_a_wrong_number_would_be_caught(self):
        # Guard against a check that passes on anything: a count that is not in
        # the block must not be found in it.
        block = self.numbers_in_the_block()
        impossible = str(self.result['population'] * 7 + 13)
        self.assertNotIn(impossible, block)

    def test_the_readme_states_the_affirmative_decision(self):
        # The monitor can say yes. If that disappears from the front page, the
        # product reads as a gate with no door again.
        self.assertIn('COMPARABLE, NOT ENDORSED', self.text)


if __name__ == '__main__':
    unittest.main()

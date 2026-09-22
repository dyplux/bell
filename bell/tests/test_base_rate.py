"""Contract for the population claim.

A base rate is only worth publishing if the denominator is honest. These tests
pin the two decisions that decide the number - what leaves the denominator, and
what counts as a refusal - so neither can drift quietly afterwards.
"""
import unittest

from base_rate import MIN_REPRESENTATIONS, _no_route_reason, measure, wilson


def rep(symbol, price, volume, *, derivative=False):
    return {
        'crypto_id': symbol, 'symbol': symbol, 'name': symbol,
        'issuer_id': 'I', 'issuer_name': 'I',
        'price': price, 'market_cap': (price or 0) * 1000,
        'volume_24h': volume, 'is_derivative': derivative,
    }


def row(reps, codes=(), severities=()):
    return {
        'rwa_id': 'x', 'name': 'Ref', 'symbol': 'REF',
        'representations': reps,
        'signal_codes': list(codes),
        'signal_severities': list(severities),
    }


class WilsonInterval(unittest.TestCase):
    def test_interval_brackets_the_point_estimate(self):
        lo, hi = wilson(50, 100)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)

    def test_interval_narrows_as_the_sample_grows(self):
        narrow = wilson(500, 1000)
        wide = wilson(5, 10)
        self.assertLess(narrow[1] - narrow[0], wide[1] - wide[0])

    def test_interval_stays_inside_zero_and_one_at_the_extremes(self):
        # The normal approximation escapes [0,1] here, which is why Wilson.
        lo, hi = wilson(0, 30)
        self.assertGreaterEqual(lo, 0.0)
        lo, hi = wilson(30, 30)
        self.assertLessEqual(hi, 1.0)

    def test_empty_sample_does_not_divide_by_zero(self):
        self.assertEqual(wilson(0, 0), (0.0, 0.0))


class DenominatorIsHonest(unittest.TestCase):
    def test_single_representation_is_excluded_not_counted_against_the_rate(self):
        # There is nothing to compare, so the question does not arise. Counting
        # it as a refusal would inflate the headline with cases that were never
        # a comparison in the first place.
        receipt = {'observed_at': 'T', 'alert_index': [
            row([rep('ONLY', 100.0, 5_000)]),
            row([rep('A', 100.0, 5_000), rep('B', 101.0, 4_000)]),
        ]}
        result = measure(receipt)
        self.assertEqual(result['population'], 2)
        self.assertEqual(result['excluded_single_representation'], 1)
        self.assertEqual(result['denominator_two_or_more_representations'], 1)

    def test_minimum_representations_is_two(self):
        self.assertEqual(MIN_REPRESENTATIONS, 2)

    def test_a_critical_signal_counts_as_a_refusal(self):
        receipt = {'observed_at': 'T', 'alert_index': [
            row([rep('A', 100.0, 5_000), rep('B', 101.0, 4_000)],
                codes=['PRICE_DENOMINATION_BREAK'], severities=['critical']),
        ]}
        result = measure(receipt)
        self.assertEqual(result['refused'], 1)
        self.assertEqual(result['comparable'], 0)
        self.assertEqual(result['refusal_reasons']['PRICE_DENOMINATION_BREAK'], 1)

    def test_a_clean_reference_counts_as_comparable(self):
        receipt = {'observed_at': 'T', 'alert_index': [
            row([rep('A', 100.0, 5_000), rep('B', 101.0, 4_000)]),
        ]}
        result = measure(receipt)
        self.assertEqual(result['comparable'], 1)
        self.assertEqual(result['refused'], 0)
        self.assertEqual(result['refusal_rate'], 0.0)

    def test_rate_and_counts_agree(self):
        receipt = {'observed_at': 'T', 'alert_index': [
            row([rep('A', 100.0, 5_000), rep('B', 101.0, 4_000)]),
            row([rep('C', 100.0, 5_000), rep('D', 101.0, 4_000)],
                codes=['ZERO_MCAP_POSITIVE_VOLUME'], severities=['critical']),
        ]}
        result = measure(receipt)
        self.assertEqual(result['refused'] + result['comparable'],
                         result['denominator_two_or_more_representations'])
        self.assertAlmostEqual(result['refusal_rate'], 0.5)


class RefusalReasonsAreDecomposed(unittest.TestCase):
    def test_unpriced_representations_are_named_as_such(self):
        self.assertEqual(
            _no_route_reason([rep('A', None, 5_000), rep('B', None, 4_000)]),
            'REPRESENTATIONS_WITHOUT_A_PRICE')

    def test_untraded_representations_are_named_as_such(self):
        self.assertEqual(
            _no_route_reason([rep('A', 100.0, 0), rep('B', 101.0, 0)]),
            'REPRESENTATIONS_QUOTED_BUT_UNTRADED')

    def test_a_spread_above_the_ceiling_is_named_separately(self):
        # Distinguishing this from "nobody trades these" matters: one is a gap
        # in the catalogue, the other is a price that cannot be the same
        # instrument.
        self.assertEqual(
            _no_route_reason([rep('A', 100.0, 5_000), rep('B', 100_000.0, 4_000)]),
            'SPREAD_ABOVE_PUBLISHABLE_CEILING')

    def test_derivative_only_pair_is_not_a_spot_comparison(self):
        self.assertEqual(
            _no_route_reason([rep('A', 100.0, 5_000),
                              rep('PERP', 101.0, 9_000, derivative=True)]),
            'FEWER_THAN_TWO_SPOT_REPRESENTATIONS')


if __name__ == '__main__':
    unittest.main()

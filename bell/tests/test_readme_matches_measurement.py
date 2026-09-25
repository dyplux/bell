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
API_FEEDBACK = os.path.join(ROOT, 'bell', 'API-FEEDBACK.md')


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


class ApiFeedbackMatchesTheReceipt(unittest.TestCase):
    """The CMC feedback note cites counts. Counts in prose rot.

    Every figure in API-FEEDBACK.md is a count of references carrying a signal
    in the shipped receipt, so it can be checked rather than trusted.
    """

    @classmethod
    def setUpClass(cls):
        from collections import Counter
        with open(INPUTS, encoding='utf-8') as handle:
            package = json.load(handle)
        surfaces = package['surfaces']
        receipt = scan(
            surfaces['map'], surfaces['asset_list'], surfaces['quotes'],
            surfaces['info'], surfaces['issuers'],
            observed_at=package['observed_at'], crypto_info_payload=surfaces['crypto_info'],
        )
        counts = Counter()
        for row in receipt['alert_index']:
            for code in row['signal_codes']:
                counts[code] += 1
        cls.counts = counts
        cls.references = len(receipt['alert_index'])
        with open(API_FEEDBACK, encoding='utf-8') as handle:
            cls.text = handle.read()

    def test_every_cited_signal_count_is_the_measured_one(self):
        cited = {
            'MARKET_FIELDS_MISSING': 646,
            'DERIVATIVE_MIX': 119,
            'SYMBOL_COLLISION': 60,
            'ZERO_MCAP_POSITIVE_VOLUME': 32,
            'NO_TRADFI_MARKET': 13,
            'PRICE_DENOMINATION_BREAK': 4,
            'TOKEN_INFO_MISSING': 4,
            'PRICE_DISPERSION': 4,
        }
        for code, claimed in cited.items():
            self.assertEqual(self.counts[code], claimed,
                             f'API-FEEDBACK.md cites {claimed} for {code}; the receipt says {self.counts[code]}')
            self.assertIn(str(claimed), self.text, f'{code} count is no longer stated in the note')

    def test_the_population_is_the_measured_one(self):
        self.assertIn(f'{self.references}', self.text)

    def test_the_named_example_is_really_in_the_capture(self):
        # A worked example is the part a reader checks first, so it must be a
        # row that exists rather than an illustration.
        with open(INPUTS, encoding='utf-8') as handle:
            package = json.load(handle)
        quotes = json.dumps(package['surfaces']['quotes'])
        self.assertIn('24439', quotes, 'the cited crypto_id is not in the shipped capture')
        self.assertIn('Kinesis Silver', self.text)

    def test_the_first_finding_is_the_one_that_cost_the_most(self):
        # Ordering is the whole point of this note: a reader who stops after the
        # first section should have the finding four teams hit independently.
        head = self.text.split('## 2.')[0]
        self.assertIn('error_code', head)
        self.assertIn('string', head)


if __name__ == '__main__':
    unittest.main()


class TheReadmeDoesNotOversellTheGate(unittest.TestCase):
    """`make check` was advertised as offline. Half of it is not.

    It drives the deployed site with a real browser when one is present, which
    is the point of it - but the word "offline" sat directly above the command,
    so a reader in a hermetic environment would have run it expecting no
    network and been surprised. The credential-free claim is true of every
    variant; the offline claim is only true of one.
    """

    @classmethod
    def setUpClass(cls):
        with open(README, encoding='utf-8') as handle:
            cls.text = handle.read()

    def test_the_offline_promise_is_attached_to_the_offline_target(self):
        block = self.text.split('## Verify the release')[1].split('###')[0]
        headline = block.split('```')[0]
        self.assertNotIn('offline', headline.lower(),
                         'the one-line promise above `make check` still says offline')
        self.assertIn('make check-offline', block,
                      'the hermetic variant is not offered where the promise is made')

    def test_the_credential_free_promise_is_still_made(self):
        block = self.text.split('## Verify the release')[1].split('###')[0]
        self.assertTrue('no API key' in block or 'credential' in block,
                        'the credential-free guarantee, which IS true of every variant, is gone')


class EveryPublishedCountIsPinnedToAnArtefact(unittest.TestCase):
    """Two figures were stated as facts with nothing checking them, and one was
    wrong.

    The documents said the receipt of 21 September contained "1,440
    representation rows". That receipt contains 1,435. The 1,440 came from a
    later, different observation and was copied across three files. The
    base-rate block had a test and stayed correct for days; these two numbers
    had none and drifted. A reviewer spotted it before any of this project's
    own machinery did.
    """

    @classmethod
    def setUpClass(cls):
        import glob
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cls.root = root
        proof = os.path.join(root, 'bell', 'site', 'proof')
        with open(os.path.join(proof, 'rwa-surface-integrity-latest-replay-2026-09-21.json'),
                  encoding='utf-8') as handle:
            cls.receipt = json.load(handle)
        with open(os.path.join(root, 'bell', 'site', 'catalog.json'), encoding='utf-8') as handle:
            catalogue = json.load(handle)
        rows = catalogue if isinstance(catalogue, list) else (
            catalogue.get('assets') or catalogue.get('rwa_assets') or catalogue.get('entries') or [])
        cls.catalogue_entries = len(rows)
        cls.documents = {}
        for name in ('README.md', 'bell/README.md', 'bell/API-FEEDBACK.md'):
            with open(os.path.join(root, *name.split('/')), encoding='utf-8') as handle:
                cls.documents[name] = handle.read()

    def test_the_representation_row_count_is_the_one_in_the_receipt(self):
        stated = f"{self.receipt['universe']['tokens_scanned']:,}"
        for name, text in self.documents.items():
            if 'representation' not in text:
                continue
            for wrong in re.findall(r'([\d,]+) representation(?:s| rows)', text):
                self.assertEqual(wrong, stated,
                                 f'{name} states {wrong} representation rows; the receipt says {stated}')

    def test_the_catalogue_size_is_the_one_in_the_shipped_snapshot(self):
        stated = f'{self.catalogue_entries:,}'
        for name, text in self.documents.items():
            for claimed in re.findall(r'([\d,]{4,}) ?(?:-entry|RWAs|records|references, including)', text):
                if claimed.replace(',', '').isdigit() and len(claimed.replace(',', '')) == 4:
                    self.assertEqual(claimed, stated,
                                     f'{name} states a catalogue size of {claimed}; the snapshot has {stated}')

    def test_a_wrong_row_count_would_be_caught(self):
        # Guard against a check that passes on anything.
        stated = f"{self.receipt['universe']['tokens_scanned']:,}"
        self.assertNotEqual(stated, '1,440',
                            'the receipt now reports the figure the documents used to claim, '
                            'so this test no longer proves anything')


class TheRefusalSplitIsPublishedAndAddsUp(unittest.TestCase):
    """64.3% read as a verdict on the market. Most of it is a verdict on the
    catalogue, and the product had the breakdown all along without printing it.
    """

    @classmethod
    def setUpClass(cls):
        cls.result = measured()
        with open(README, encoding='utf-8') as handle:
            cls.text = handle.read()

    def test_the_split_separates_coverage_from_contradiction(self):
        split = self.result['refusal_split']
        self.assertGreater(split['source_coverage'], 0)
        self.assertGreater(split['data_contradiction'], 0)
        self.assertEqual(
            split['source_coverage'] + split['data_contradiction'],
            sum(self.result['refusal_reasons'].values()),
            'the split drops or double-counts a reason')

    def test_the_readme_states_the_measured_split(self):
        split = self.result['refusal_split']
        self.assertIn(str(split['source_coverage']), self.text)
        self.assertIn(str(split['data_contradiction']), self.text)

    def test_the_readme_admits_reasons_outnumber_references(self):
        # Reasons sum past the reference count because a reference can fail more
        # than one rule. Printing both without saying so would be exactly the
        # unreconciled arithmetic this project corrects elsewhere.
        reasons = sum(self.result['refusal_reasons'].values())
        if reasons != self.result['refused']:
            self.assertIn(str(reasons), self.text)
            self.assertIn('more than one rule', self.text)

    def test_an_unknown_code_counts_as_a_contradiction_not_coverage(self):
        # A rule added later must not be quietly filed under "not our problem".
        from collections import Counter
        from base_rate import _split_refusals
        split = _split_refusals(Counter({'A_BRAND_NEW_RULE': 5}))
        self.assertEqual(split['data_contradiction'], 5)
        self.assertEqual(split['source_coverage'], 0)

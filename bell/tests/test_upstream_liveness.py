"""The shipped liveness receipt has to be evidence, and has to be safe to ship.

Every other contract check here reads payloads captured on 13, 17 and 21
September, so it catches a regression against those captures and cannot notice
that the API changed afterwards. The liveness probe closes that gap by actually
calling CMC - which means the artefact it leaves behind is the one file in this
repository written from an authenticated session, and it must therefore carry
no credential, no payload and no row of data.
"""
import glob
import json
import os
import re
import unittest

PROOF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'site', 'proof')
SHA256 = re.compile(r'^[0-9a-f]{64}$')


def receipts():
    return sorted(glob.glob(os.path.join(PROOF, 'upstream-liveness-*.json')))


class ALivenessReceiptIsShipped(unittest.TestCase):
    def setUp(self):
        found = receipts()
        if not found:
            self.skipTest('no liveness receipt shipped yet')
        self.path = found[-1]
        with open(self.path, encoding='utf-8') as handle:
            self.receipt = json.load(handle)

    def test_it_declares_what_it_is(self):
        self.assertEqual(self.receipt['schema_version'], 'bell.upstream_liveness.v1')
        self.assertIs(self.receipt['credential_free'], True)
        self.assertIn('question', self.receipt)
        self.assertIn('limits', self.receipt)

    def test_it_records_a_result_for_every_surface_it_probed(self):
        surfaces = self.receipt['surfaces']
        self.assertTrue(surfaces, 'the receipt probed nothing')
        for name, entry in surfaces.items():
            self.assertIn('endpoint', entry, f'{name} does not say which endpoint it called')
            self.assertIn('reachable', entry, f'{name} does not say whether it answered')
            if entry['reachable']:
                self.assertTrue(SHA256.match(entry['response_sha256'] or ''),
                                f'{name} has no response fingerprint')
                self.assertTrue(entry['properties'], f'{name} checked no property')

    def test_the_verdict_matches_the_recorded_properties(self):
        # A receipt that says "intact" while carrying a failed property would be
        # exactly the contradiction this product exists to catch elsewhere.
        failed = [f'{name}.{prop}'
                  for name, entry in self.receipt['surfaces'].items()
                  for prop, result in (entry.get('properties') or {}).items()
                  if not result['holds']]
        unreachable = [name for name, entry in self.receipt['surfaces'].items()
                       if not entry.get('reachable')]
        self.assertEqual(self.receipt['contract_intact'], not (failed or unreachable),
                         f'verdict disagrees with the record: failed={failed} unreachable={unreachable}')
        if failed or unreachable:
            self.assertTrue(self.receipt['failures'], 'failures are not named')

    def test_it_carries_no_payload_and_no_credential(self):
        raw = open(self.path, encoding='utf-8').read()
        # Small by construction: status, a fingerprint and a sentence per
        # property. Anything large means a payload got in.
        self.assertLess(len(raw), 64_000,
                        'the liveness receipt is large enough to contain returned data')
        declared = {entry.get('response_sha256') for entry in self.receipt['surfaces'].values()}
        stray = set(re.findall(r'\b[0-9a-f]{64}\b', raw)) - declared
        self.assertEqual(stray, set(), f'unexplained 64-hex values in the receipt: {sorted(stray)}')
        for forbidden in ('X-CMC_PRO_API_KEY', 'CMC_API_KEY', 'Authorization'):
            self.assertNotIn(forbidden, raw, f'{forbidden} appears in a committed receipt')

    def test_the_probe_never_writes_a_payload(self):
        # Assert the property at the source too, so a future change to the probe
        # cannot start recording data and pass because today's receipt is clean.
        probe = os.path.join(os.path.dirname(PROOF), '..', 'live_contract_probe.py')
        source = open(os.path.normpath(probe), encoding='utf-8').read()
        self.assertNotIn('"payload": payload', source)
        self.assertIn('response_sha256', source)


if __name__ == '__main__':
    unittest.main()

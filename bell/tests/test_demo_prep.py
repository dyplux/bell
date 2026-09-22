import unittest

from prepare_demo import demo_snapshot


class DemoPrepTests(unittest.TestCase):
    def test_snapshot_uses_live_rows_and_signal_evidence(self):
        receipt = {
            'observed_at': '2026-09-22T03:47:44Z',
            '_publication': {'published_at': '2026-09-22T03:48:06Z'},
            'alerts': [{
                'rwa_id': 5,
                'name': 'Silver',
                'symbol': 'SILVER',
                'state': 'do_not_compare',
                'token_count': 2,
                'issuer_count': 2,
                'signals': [
                    {'code': 'PRICE_DENOMINATION_BREAK', 'severity': 'critical', 'evidence': {'max_min_ratio': 31.019}},
                    {'code': 'ZERO_MCAP_POSITIVE_VOLUME', 'severity': 'critical', 'evidence': {}},
                ],
                'tokens': [
                    {'symbol': 'LOW', 'issuer_name': 'Issuer A', 'price': 2.0},
                    {'symbol': 'HIGH', 'issuer_name': 'Issuer B', 'price': 62.0},
                ],
            }],
        }
        snapshot = demo_snapshot(receipt, 'Silver')
        self.assertEqual(snapshot['reference']['state'], 'do_not_compare')
        self.assertEqual(snapshot['reference']['critical_signal_count'], 2)
        self.assertEqual(snapshot['reference']['low']['symbol'], 'LOW')
        self.assertEqual(snapshot['reference']['high']['price'], 62.0)
        self.assertEqual(snapshot['reference']['observed_ratio'], 31.019)

    def test_reference_matching_accepts_rwa_id(self):
        receipt = {'alerts': [{'rwa_id': 14, 'name': 'Tesla', 'symbol': 'TSLA', 'tokens': []}]}
        self.assertEqual(demo_snapshot(receipt, '14')['reference']['name'], 'Tesla')


if __name__ == '__main__':
    unittest.main()

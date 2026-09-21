import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from receipt_compare import compare


class ReceiptCompareTests(unittest.TestCase):
    def test_comparison_preserves_delta_and_flat_bar_diagnostic(self):
        before = {"asset": {"slug": "gold"}, "window": {"start_utc": "a"}, "wrappers": [{"symbol": "A", "issuer": "I", "state": "ready", "sessions": {"cash": {"median_range_pct": 1}, "after_hours": {"median_range_pct": 2}, "weekend": {"median_range_pct": 3}}}]}
        after = {"asset": {"slug": "gold"}, "window": {"start_utc": "b"}, "wrappers": [{"symbol": "A", "issuer": "I", "state": "ready", "sessions": {"cash": {"median_range_pct": 2}, "after_hours": {"median_range_pct": 2.5}, "weekend": {"median_range_pct": 4}}}]}
        before_payload = {"wrappers": [{"bars": [{"high": 1, "low": 1}, {"high": 2, "low": 1}]}]}
        after_payload = {"wrappers": [{"bars": [{"high": 2, "low": 1}, {"high": 3, "low": 1}]}]}
        result = compare(before, after, before_payload, after_payload)
        self.assertEqual(result["wrappers"][0]["sessions"]["cash"]["delta"], 1)
        self.assertEqual(result["flat_bar_diagnostics"]["before"]["flat_pct"], 50.0)
        self.assertEqual(result["flat_bar_diagnostics"]["after"]["flat_pct"], 0.0)

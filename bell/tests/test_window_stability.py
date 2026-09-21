import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from window_stability import assess_persistence


class WindowStabilityTests(unittest.TestCase):
    def receipt(self, start, value):
        return {
            "window": {"start_utc": start, "end_utc": f"{start}-end"},
            "wrappers": [{"symbol": "PAXG", "sessions": {
                "cash": {"median_range_pct": value},
                "after_hours": {"median_range_pct": value / 2},
                "weekend": {"median_range_pct": value / 4},
            }}],
        }

    def test_two_windows_cannot_be_called_persistent(self):
        result = assess_persistence([self.receipt("a", 1), self.receipt("b", 2)])
        self.assertFalse(result["eligible_for_persistence_claim"])
        self.assertFalse(result["summaries"][0]["persistent_claim_allowed"])

    def test_four_distinct_windows_unlock_gate_and_show_spread(self):
        result = assess_persistence([self.receipt(str(i), i) for i in range(1, 5)])
        self.assertTrue(result["eligible_for_persistence_claim"])
        self.assertEqual(result["summaries"][0]["observations"], 4)
        self.assertEqual(result["summaries"][0]["spread"], 3.0)


import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from quick_review import load_review, render


class QuickReviewTests(unittest.TestCase):
    def test_gold_path_is_a_refusal_with_a_next_action(self):
        result = load_review("gold", False)
        output = render(result)
        self.assertEqual(result["conclusion"], "do_not_compare")
        self.assertIn("DENOMINATION_UNRESOLVED", output)
        self.assertIn("Next action", output)

"""The pair-specific finding must stay attached to its exact dated CMC rows."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import verify_pair_review  # noqa: E402


class PairReviewTests(unittest.TestCase):
    def test_dated_pair_review_verifies_against_shipped_capture(self):
        result = verify_pair_review.verify()
        self.assertEqual(result["route_ids_verified"], [37013, 38001])
        self.assertEqual(result["decision"], "do_not_compare_as_like_for_like")

    def test_modified_capture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory) / "site"
            proof = site / "proof"
            proof.mkdir(parents=True)
            shutil.copy2(verify_pair_review.REVIEW_PATH, proof / verify_pair_review.REVIEW_PATH.name)
            review = json.loads((proof / verify_pair_review.REVIEW_PATH.name).read_text())
            original_capture = verify_pair_review.SITE / "proof" / review["cmc_observation"]["source"]
            changed = json.loads(original_capture.read_text())
            changed["alert_index"][0]["name"] = "tampered capture"
            (proof / original_capture.name).write_text(json.dumps(changed))
            with patch.object(verify_pair_review, "SITE", site), patch.object(
                    verify_pair_review, "REVIEW_PATH", proof / verify_pair_review.REVIEW_PATH.name):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    verify_pair_review.verify()

    def test_modified_issuer_page_capture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory) / "site"
            proof = site / "proof"
            proof.mkdir(parents=True)
            shutil.copy2(verify_pair_review.REVIEW_PATH, proof / verify_pair_review.REVIEW_PATH.name)
            review = json.loads((proof / verify_pair_review.REVIEW_PATH.name).read_text())
            cmc_capture = verify_pair_review.SITE / "proof" / review["cmc_observation"]["source"]
            shutil.copy2(cmc_capture, proof / cmc_capture.name)
            archives = review["issuer_source_archives"]
            originals = []
            for archive in archives:
                original = verify_pair_review.SITE / "proof" / archive["capture"]
                shutil.copy2(original, proof / original.name)
                originals.append(proof / original.name)
            originals[0].write_text(originals[0].read_text() + "tampered\n")
            with patch.object(verify_pair_review, "SITE", site), patch.object(
                    verify_pair_review, "REVIEW_PATH", proof / verify_pair_review.REVIEW_PATH.name):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    verify_pair_review.verify()


if __name__ == "__main__":
    unittest.main()

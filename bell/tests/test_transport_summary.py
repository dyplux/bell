"""The transport record has to reach the artefact a judge downloads.

Reviewers marked the exported case receipt down three times for carrying no
HTTP status and no request counts. They were right about the artefact and wrong
about the data: all of it already sat in the replay package's collection
manifest, which is 16.5 MB, so the page could never load it to build a receipt.

Extracted once into 3 KB. Nothing here is computed; it is the manifest.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from extract_transport import SCHEMA, build  # noqa: E402

INPUTS = HERE.parent / "site" / "proof" / "rwa-surface-integrity-inputs-2026-09-21.json"
SUMMARY = HERE.parent / "site" / "proof" / "transport-2026-09-21.json"


class TheTransportSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shipped = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.manifest = json.loads(INPUTS.read_text(encoding="utf-8"))["collection_manifest"]

    def test_the_shipped_summary_is_what_the_extractor_produces(self):
        # Regenerating must be a no-op, or the file drifted from its source.
        self.assertEqual(self.shipped, build(INPUTS))
        self.assertEqual(self.shipped["schema_version"], SCHEMA)

    def test_every_figure_traces_to_the_manifest(self):
        for name, surface in self.shipped["surfaces"].items():
            source = self.manifest["surfaces"][name]
            self.assertEqual(surface["endpoint"], source["endpoint"])
            self.assertEqual(surface["payload_sha256"], source["payload_sha256"])
            self.assertEqual(surface["request_count"], source["request_count"])
            self.assertEqual(sum(surface["status_codes"].values()),
                             len(source["status_codes"]),
                             f"{name} lost or invented a status code")
            for code, count in surface["status_codes"].items():
                self.assertEqual(count, source["status_codes"].count(int(code)))

    def test_it_stays_small_enough_for_the_page_to_fetch(self):
        # The whole point is that the 16.5 MB manifest never reached the
        # artefact. A summary that grows back into megabytes defeats it.
        self.assertLess(SUMMARY.stat().st_size, 32_000)

    def test_no_credential_or_transport_header_is_carried(self):
        text = SUMMARY.read_text(encoding="utf-8").lower()
        for forbidden in ("authorization", "x-cmc_pro_api_key", "api_key", "bearer", "cookie"):
            self.assertNotIn(forbidden, text)
        self.assertIs(self.shipped["transport_headers_published"], False)

    def test_the_case_receipt_carries_it_and_says_which_observation_it_describes(self):
        integrity = (HERE.parent / "site" / "integrity.js").read_text(encoding="utf-8")
        self.assertIn("proof/transport-2026-09-21.json", integrity)
        self.assertIn("status_codes: transport.status_codes", integrity)
        self.assertIn("transport_observed_at: transportRecord.observed_at", integrity)
        # Transport belongs to the dated package, not necessarily to the
        # observation above it, so the artefact must not imply it measured
        # whatever scan happens to be loaded.
        self.assertIn("transport_note", integrity)


if __name__ == "__main__":
    unittest.main()

"""Opt-in live CMC smoke tests.

The key is supplied by the process environment. It is intentionally never stored
in this test, a fixture, a receipt or the repository.
"""

import os
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bell import CMCClient, fetch_live_asset


@unittest.skipUnless(
    os.environ.get("BELL_LIVE_TEST") == "1" and os.environ.get("CMC_API_KEY"),
    "set BELL_LIVE_TEST=1 and CMC_API_KEY to run the live smoke test",
)
class LiveCmcSmokeTests(unittest.TestCase):
    def test_rwa_asset_response_has_a_safe_shape(self):
        client = CMCClient(os.environ["CMC_API_KEY"])
        dossier = fetch_live_asset(client, "gold")
        self.assertEqual(dossier["schema_version"], "bell.asset.v1")
        self.assertIn("provenance", dossier)
        self.assertFalse(dossier["provenance"].get("raw_responses_included", True))
        self.assertIsInstance(dossier.get("tokens", []), list)

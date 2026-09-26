"""These tests never ran.

They were written as pytest-style module functions and the gate collects with
unittest, which ignores them. Nine tests across three files existed, passed
nobody's eye, and protected nothing. Converted to run.
"""

import json
from pathlib import Path
import tempfile
import unittest

from live_store import LiveStore


class TheLiveStore(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._dir.name)
        self.addCleanup(self._dir.cleanup)

    def test_live_store_writes_credential_free_atomic_record(self):
        store = LiveStore(self.tmp_path)
        record = store.write("terminal", "gold", {"observed_at": "2026-09-14T12:00:00Z",
                                                  "audit": {"conclusion": "investigate"}})
        self.assertIs(record["credential_free"], True)
        self.assertEqual(record["slug"], "gold")
        self.assertEqual(store.read("terminal", "gold")["payload"]["audit"]["conclusion"],
                         "investigate")
        written = json.loads((self.tmp_path / "terminal/gold.json").read_text())
        self.assertEqual(written["schema_version"], "bell.live.store.v1")

    def test_live_store_rejects_path_traversal(self):
        store = LiveStore(self.tmp_path)
        with self.assertRaises(ValueError) as caught:
            store.read("terminal", "../secret")
        self.assertIn("invalid", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

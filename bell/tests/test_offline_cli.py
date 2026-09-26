"""The offline CLI the README leads with had no test at all.

A reviewer reported `bell/tests/fixtures/offline.json` as a dead file: deleting
it left the gate green. It is not dead - `bell.py` uses it as the default input
for `--offline`, which is the first command the README documents - it was
untested, which looks identical from outside and is worse, because the fixture
could rot without anything saying so.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FIXTURE = HERE / "fixtures" / "offline.json"
ENV = {"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"}


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", "bell/bell.py", *args], cwd=REPO,
                          capture_output=True, text=True, env=ENV)


class TheOfflineCli(unittest.TestCase):
    def test_the_default_run_produces_a_receipt_from_the_shipped_fixture(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr[:400])
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["schema_version"], "bell.receipt.v1")
        self.assertEqual(receipt["mode"], "offline_fixture")
        # It must not quietly claim a live observation while reading a file.
        self.assertNotIn("live", receipt["mode"])

    def test_it_needs_no_credential(self):
        # The claim the whole product rests on: nothing here reads a key.
        result = subprocess.run(["python3", "bell/bell.py"], cwd=REPO,
                                capture_output=True, text=True,
                                env={"PYTHONPATH": "bell", "PATH": ENV["PATH"]})
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("CMC_API_KEY", result.stderr)

    def test_the_fixture_is_the_shape_the_cli_reads(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertIsInstance(payload, dict)
        self.assertTrue(payload, "the offline fixture is empty")

    def test_a_missing_input_is_explained_rather_than_traced(self):
        result = run("--input", "bell/nope.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Traceback", result.stderr)

    def test_a_corrupt_input_is_explained_rather_than_traced(self):
        broken = REPO / "bell" / "tests" / "fixtures" / "_broken.json"
        try:
            broken.write_text('{"asset": ', encoding="utf-8")
            result = run("--input", str(broken.relative_to(REPO)))
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            broken.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

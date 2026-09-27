import json
import re
import tempfile
import unittest
from pathlib import Path

from verify_demo_manifest import verify

HERE = Path(__file__).resolve().parent


class DemoManifestTests(unittest.TestCase):
    def test_long_manifest_binds_receipt_steps_and_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "demo.webm"
            video.write_bytes(b"video")
            steps = [
                {"id": step, "route": "/", "selector": "#step"}
                for step in (
                    "hero",
                    "silver-search",
                    "silver-evidence",
                    "population-shape",
                    "population-concentration",
                    "facts-open",
                    "gold-repeat-window",
                    "map-only",
                    "receipt",
                )
            ]
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "bell.demo-video.v1",
                "mode": "long",
                "base": "https://bell.dyplux.com",
                "captured_at": "2026-09-22T07:50:17Z",
                "receipt": {
                    "status": "fresh",
                    "observed_at": "2026-09-22T07:39:11Z",
                    "published_at": "2026-09-22T07:39:32Z",
                    "tokenised_references": 791,
                    "representations": 1435,
                },
                "steps": steps,
                "console_errors": [],
                "video": video.name,
            }), encoding="utf-8")
            result = verify(manifest)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["steps"], 9)


class DemoNamesItsDenominator(unittest.TestCase):
    """The demo may not print a count that reads as a rate.

    `Of 50 references in this receipt: 35 refused` invited a reader to divide
    and get 70%. The 50 are `alerts[:50]`, a priority-sorted truncation of a
    list that never contained the 666 references carrying no signal at all.
    Quoting a rate off a list selected for flags is the exact error
    `base_rate.py` exists to correct, and the demo that introduces the product
    was making it.
    """

    def setUp(self):
        import subprocess
        self.output = subprocess.run(
            ["python3", str(HERE.parent / "demo.py")],
            capture_output=True, text=True, timeout=120, cwd=str(HERE.parent.parent),
            env={"PATH": "/usr/bin:/bin", "NO_COLOR": "1", "PYTHONPATH": str(HERE.parent)},
        ).stdout
        self.plain = re.sub(r"\x1b\[[0-9;]*m", "", self.output)

    def test_the_headline_count_says_what_it_is_counting(self):
        self.assertNotIn("references in this receipt:", self.plain,
                         "the demo went back to presenting a truncated flagged list as the receipt")
        self.assertIn("highest-priority flagged references", self.plain,
                      "the demo no longer says the 50 are a priority-sorted slice")

    def test_it_names_the_population_and_refuses_to_be_read_as_a_rate(self):
        self.assertRegex(self.plain, r"of the [\d,]+ scanned",
                         "the demo states no population behind its 50")
        self.assertIn("not a rate", self.plain,
                      "nothing stops a reader dividing 35 by 50")
        self.assertIn("make base-rate", self.plain,
                      "the demo does not point at the command that does measure the rate")


if __name__ == "__main__":
    unittest.main()

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

    # setUpClass, not setUp: demo.py is a subprocess, and running it once per
    # test put 1.4 seconds into a gate whose published runtime band this
    # repository then has to keep widening. Its output does not depend on which
    # assertion reads it.
    @classmethod
    def setUpClass(cls):
        import subprocess
        cls.output = subprocess.run(
            ["python3", str(HERE.parent / "demo.py")],
            capture_output=True, text=True, timeout=120, cwd=str(HERE.parent.parent),
            env={"PATH": "/usr/bin:/bin", "NO_COLOR": "1", "PYTHONPATH": str(HERE.parent)},
        ).stdout
        cls.plain = re.sub(r"\x1b\[[0-9;]*m", "", cls.output)

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

    def test_the_judge_page_states_the_counts_the_demo_prints(self):
        # judge.html says `make demo` "prints 35 refused, 10 comparable, 5 held
        # for investigation". A reviewer changed it to "3 refused, 44
        # comparable, 3 held" and the gate stayed green, on the page whose
        # first sentence promises every number came from a command. This is
        # that command's output.
        import re
        numbers = re.search(r"(\d+) refused[^0-9]+(\d+) comparable[^0-9]+(\d+) held", self.plain)
        self.assertIsNotNone(numbers, f"the demo stopped printing its three counts: {self.plain[-300:]!r}")
        judge = " ".join((HERE.parent / "site" / "judge.html").read_text(encoding="utf-8").split())
        stated = (f"prints {numbers.group(1)} refused, {numbers.group(2)} comparable, "
                  f"{numbers.group(3)} held for investigation")
        self.assertIn(stated, judge,
                      f"the judge page does not state what `make demo` prints: {stated!r}")


class TheShippedManifestVerifies(unittest.TestCase):
    """JUDGE.md's command must work on the file this repository ships.

    It told a reader to run the verifier against a manifest, and the only
    manifest here is a capture manifest, which the verifier rejected at the
    door because it knew one schema. The Makefile already records shipping a
    command that failed for anyone who ran it; this was a second.
    """

    MANIFEST = HERE.parent / "site" / "demo" / "manifest.json"

    def test_the_shipped_capture_manifest_verifies(self):
        result = verify(self.MANIFEST)
        self.assertEqual(result["status"], "valid credential-free capture manifest")
        self.assertGreater(result["frames"], 0)

    def test_a_frame_the_manifest_lists_and_the_repository_lacks_is_refused(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest = json.loads(self.MANIFEST.read_text(encoding="utf-8"))
            for frame in manifest["frames"][1:]:
                shutil.copy2(self.MANIFEST.parent / frame["file"], folder / frame["file"])
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not here"):
                verify(folder / "manifest.json")

    def test_a_console_error_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            manifest = json.loads(self.MANIFEST.read_text(encoding="utf-8"))
            manifest["console_errors"] = ["TypeError: x is not a function"]
            manifest["frames"] = []
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "console errors"):
                verify(folder / "manifest.json")

    def test_an_unknown_schema_is_still_refused_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "manifest.json").write_text(
                json.dumps({"schema_version": "bell.something-else.v9"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "bell.something-else.v9"):
                verify(folder / "manifest.json")


if __name__ == "__main__":
    unittest.main()

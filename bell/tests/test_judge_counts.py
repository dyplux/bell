"""The judge page's test count must be the one the gate actually collects.

Counting `def test_` finds 147; unittest collects 138. Nine are helpers on
classes the runner never picks up. A judge told "147 tests" who runs the suite
and sees 138 has caught the page overstating itself, on a product whose subject
is numbers that do not reconcile. So ask the runner.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest

HERE = Path(__file__).resolve().parent
JUDGE = HERE.parent / "site" / "judge.html"
README = HERE.parent.parent / "README.md"


def collected() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(HERE), pattern="test_*.py")

    def flatten(item):
        if isinstance(item, unittest.TestSuite):
            for child in item:
                yield from flatten(child)
        else:
            yield item

    assert not loader.errors, f"test discovery failed: {loader.errors}"
    return len(list(flatten(suite)))


class JudgeCounts(unittest.TestCase):
    def test_the_page_states_the_python_count_the_runner_collects(self):
        stated = re.search(r"(\d+) tests, (\d+) Python and (\d+) JavaScript",
                           JUDGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(stated, "the judge page stopped stating its test breakdown")
        self.assertEqual(int(stated.group(2)), collected(),
                         "the judge page Python count is not what unittest collects")
        self.assertEqual(int(stated.group(1)),
                         int(stated.group(2)) + int(stated.group(3)),
                         "the judge page total does not equal its own breakdown")

    def test_the_readme_states_the_same_count_as_the_judge_page(self):
        # The README is the first thing a judge reads on GitHub, and it now
        # opens with the same figure. One number, two places, both checked.
        judged = re.search(r"(\d+) tests, \d+ Python and \d+ JavaScript",
                           JUDGE.read_text(encoding="utf-8"))
        readme = re.search(r"`make check-offline` - (\d+) tests in",
                           README.read_text(encoding="utf-8"))
        self.assertIsNotNone(readme, "the README stopped stating its test count")
        self.assertEqual(readme.group(1), judged.group(1),
                         "the README and the judge page disagree about the test count")

    def test_the_readme_opens_with_a_path_a_judge_can_run(self):
        text = README.read_text(encoding="utf-8")
        opening = text[:text.index("## What the product does")]
        self.assertIn("make base-rate", opening,
                      "the README no longer offers a runnable command before the prose")
        self.assertIn("no API key", opening)
        self.assertIn("/judge", opening)

    def test_the_page_states_the_tracked_file_count_the_gate_inspects(self):
        # The page claimed 132 while the gate reported 136. The test count next
        # to it was pinned and this one was not, so it drifted unnoticed.
        repo = HERE.parent.parent
        tracked = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True,
                                 text=True, check=True).stdout.split()
        stated = re.search(r"a submission gate over (\d+) tracked files",
                           JUDGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(stated, "the judge page stopped stating the gate's scope")
        self.assertEqual(int(stated.group(1)), len(tracked),
                         "the judge page tracked-file count no longer matches git")

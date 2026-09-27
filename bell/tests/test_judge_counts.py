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


# The verifier is a subprocess that loads 16.5 MB and recomputes the scan, so it
# costs about half a second. Two tests below run it against the unmodified
# repository and only differ in which document they hold its output against, so
# they ran it twice for the same answer. Cached once, per process.
_VERIFIER_OUTPUT = None


def verifier_output():
    global _VERIFIER_OUTPUT
    if _VERIFIER_OUTPUT is None:
        import subprocess
        _VERIFIER_OUTPUT = subprocess.run(
            ["python3", "bell/verify_integrity_receipt.py"], cwd=HERE.parent.parent,
            capture_output=True, text=True,
            env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
    return _VERIFIER_OUTPUT


class JudgeCounts(unittest.TestCase):
    def test_the_page_states_the_python_count_the_runner_collects(self):
        stated = re.search(r"(\d+) tests, (\d+) Python and (\d+) JavaScript",
                           JUDGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(stated, "the judge page stopped stating its test breakdown")
        self.assertEqual(int(stated.group(2)), collected(),
                         "the judge page Python count is not what unittest collects. Run `make sync-counts`.")
        self.assertEqual(int(stated.group(1)),
                         int(stated.group(2)) + int(stated.group(3)),
                         "the judge page total does not equal its own breakdown")

    def test_the_readme_states_the_same_count_as_the_judge_page(self):
        # The README is the first thing a judge reads on GitHub, and it now
        # opens with the same figure. One number, two places, both checked.
        judged = re.search(r"(\d+) tests, \d+ Python and \d+ JavaScript",
                           JUDGE.read_text(encoding="utf-8"))
        readme = re.search(r"`make check-offline` - (\d+) tests",
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
        # Tracked files, nothing else. Counting untracked-not-ignored files as
        # well made this pass here and fail in a fresh clone that had run
        # `npm install`, because of one untracked package-lock.json. A count a
        # document states about the repository cannot depend on the machine
        # reading it.
        tracked = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True,
                                 text=True, check=True).stdout.split()
        stated = re.search(r"a submission gate over (\d+)\s+tracked files",
                           JUDGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(stated, "the judge page stopped stating the gate's scope")
        self.assertEqual(int(stated.group(1)), len(tracked),
                         "the judge page tracked-file count no longer matches git. Run `make sync-counts`, and run it AFTER staging: the count is of what the commit will contain.")

    def test_the_pages_state_the_number_of_boundary_checks_that_exist(self):
        # The page said "six checks" where the verifier publishes eight, on a
        # page that opens "Every number on this page was produced by a command
        # you can run yourself". The test count and the file count beside it
        # were pinned; this one was not, so it was wrong in both files.
        # This read the committed receipt, so deleting two checks from that
        # file and restating both pages to "6" kept the gate green while the
        # verifier still printed 8. Adding the verifier to `make verify` made
        # the gate RUN it; it did not make anything COMPARE its output. Ask the
        # verifier.
        import json
        import subprocess
        run = subprocess.run(
            ["python3", "bell/verify_rule_boundaries.py"], cwd=HERE.parent.parent,
            capture_output=True, text=True,
            env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
        self.assertEqual(run.returncode, 0, run.stderr[-400:])
        produced = json.loads(run.stdout)
        self.assertEqual(produced.get("status"), "pass", run.stdout[-300:])
        checks = len(produced["checks"])
        self.assertGreater(checks, 0, "the boundary verifier ran no checks")
        # And the committed receipt must agree with the code that wrote it,
        # rather than being the only thing anyone reads.
        receipt = json.loads((HERE.parent / "site" / "proof"
                              / "rule-boundary-verifier-2026-09-22.json").read_text(encoding="utf-8"))
        self.assertEqual(len(receipt["checks"]), checks,
                         "the committed rule-boundary receipt does not match what the verifier runs")
        self.assertIn(f"All {checks} checks pass", JUDGE.read_text(encoding="utf-8"))
        self.assertIn(f"{checks} boundary checks", README.read_text(encoding="utf-8"))

    def test_the_two_pages_do_not_disagree_about_the_gate(self):
        # judge.html said 2.9s and README said 2.8s, and a reviewer measured
        # 3.39s on their machine. Runtime is not a property of this repository,
        # so both files describe it the same way and neither invents precision.
        judge = JUDGE.read_text(encoding="utf-8").lower()
        readme = README.read_text(encoding="utf-8").lower()
        # "About 3 seconds" was the fastest run on one machine. Reviewers
        # measured 3.67, 4.51 and 5.33 on theirs. A range is the honest shape of
        # a figure that depends on who is running it.
        # This used to assert only that both files contained the same string,
        # which is a check that cannot fail: when the gate slowed past the
        # stated band, the two documents agreed with each other and disagreed
        # with reality. Read the numbers and require the headline bound to
        # cover the stated range with margin.
        band = re.search(r"between (\d+\.\d+) and (\d+\.\d+) seconds", judge)
        self.assertIsNotNone(band, "the judge page stopped stating a measured range")
        self.assertIn(f"between {band.group(1)} and {band.group(2)} seconds", readme,
                      "the README and the judge page disagree about the gate runtime")
        tile = re.search(r"<strong>&lt;(\d+)s</strong>", judge)
        self.assertIsNotNone(tile, "the gate runtime tile went missing")
        self.assertGreaterEqual(float(tile.group(1)), float(band.group(2)),
                                "the headline bound is below the range the page itself states")
        # The individual command timings stay precise - they are single
        # commands and they were measured. It is the gate, which varies with
        # the machine running it, that must not be quoted to a tenth.
        for text, name in ((judge, "judge.html"), (readme, "README.md")):
            self.assertIsNone(re.search(r"check-offline[^.]{0,40}?\d\.\ds", text),
                              f"{name} quotes the gate runtime to a tenth again")

    def test_the_page_describes_the_verification_the_verifier_performs(self):
        # "A recomputation of the published receipt" promised more than it
        # delivers: two of the twelve observations ship their payload and are
        # cross-checked, the rest are summaries, and counts either side of a
        # rule change are reported rather than compared. On this product, a
        # claim about evidence has to be the claim the evidence supports.
        out = verifier_output()
        self.assertEqual(out.returncode, 0, out.stderr[:400])
        observations = re.search(r"ok \((\d+) observations\)", out.stdout)
        bundled = re.search(r"bundled cross-checks: (\d+)", out.stdout)
        self.assertIsNotNone(observations, out.stdout[:300])
        self.assertIsNotNone(bundled, out.stdout[:300])
        judge = JUDGE.read_text(encoding="utf-8")
        self.assertIn(f"Of the {observations.group(1)} dated observations, {bundled.group(1)} ship", judge,
                      "the judge page no longer states the verification the verifier performs")

    def test_the_readme_does_not_overstate_what_the_readme_verifies(self):
        # The judge page was made precise about what make verify proves and the
        # README kept the broad version, so the two documents disagreed about
        # the same command. Whatever the verifier reports, both must say it.
        out = verifier_output()
        bundled = re.search(r"bundled cross-checks: (\d+)", out.stdout)
        observations = re.search(r"ok \((\d+) observations\)", out.stdout)
        phrase = (f"Of the {observations.group(1)} dated observations, "
                  f"{bundled.group(1)} ship their full payload and are cross-checked")
        chained = f"every one of the {observations.group(1)} is chained to the one before it"
        for text, name in ((JUDGE.read_text(encoding="utf-8"), "judge.html"),
                           (README.read_text(encoding="utf-8"), "README.md")):
            self.assertIn(phrase, text, f"{name} no longer states what the verifier verifies")
        # The chain is the answer to the forgery that got through, so the page
        # that describes the verification has to describe it.
        self.assertIn(chained, JUDGE.read_text(encoding="utf-8"),
                      "the judge page no longer states that the observations are chained")

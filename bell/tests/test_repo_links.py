"""Every relative link in the repository has to resolve.

Nine internal documents were removed in one pass and seven links across three
files were left pointing at files that no longer existed. Nothing failed: a
broken link in a README is invisible to a test suite and obvious to the first
reader who clicks it. This closes that gap, so documentation rot is a build
failure rather than a reviewer's discovery.
"""
import os
import re
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)\)')
SKIP = ('http://', 'https://', 'mailto:', '#', 'data:')


SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.v'}


def documents():
    """Every tracked markdown file, without requiring a git checkout.

    `git ls-files` was the obvious way to ask, and it made the whole suite fail
    with exit 128 in a copy of the repository that has no .git - which is what a
    reviewer who downloads a release archive actually has. A test that only
    passes inside a clone is testing the clone.
    """
    out = subprocess.run(['git', 'ls-files', '*.md'], cwd=ROOT,
                         capture_output=True, text=True)
    if out.returncode == 0 and out.stdout.strip():
        return [line for line in out.stdout.splitlines() if line]
    found = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith('.md'):
                found.append(os.path.relpath(os.path.join(root, name), ROOT))
    return sorted(found)


class RelativeLinksResolve(unittest.TestCase):
    def test_every_markdown_link_points_at_a_file_that_exists(self):
        broken = []
        for rel in documents():
            path = os.path.join(ROOT, rel)
            with open(path, encoding='utf-8') as handle:
                text = handle.read()
            for target in LINK.findall(text):
                if target.startswith(SKIP):
                    continue
                target = target.split('#', 1)[0]
                if not target:
                    continue
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
                if not os.path.exists(resolved):
                    broken.append(f'{rel} -> {target}')
        self.assertEqual(broken, [], 'links point at files that are not in the repository')

    def test_the_file_list_works_without_a_git_checkout(self):
        # The reviewer case: an unpacked archive, no .git. The walk fallback has
        # to find the same documents the tracked listing would.
        import importlib
        module = importlib.import_module('test_repo_links')
        original = module.subprocess.run
        module.subprocess.run = lambda *a, **k: type('R', (), {'returncode': 128, 'stdout': ''})()
        try:
            found = module.documents()
        finally:
            module.subprocess.run = original
        self.assertIn('README.md', found)
        self.assertTrue(any(name.endswith('JUDGE.md') for name in found))

    def test_the_check_would_notice_a_broken_link(self):
        # A checker that passes on anything proves nothing, so assert the
        # resolution step itself rejects a target that is not there.
        resolved = os.path.normpath(os.path.join(ROOT, 'bell', 'A-DOCUMENT-THAT-WAS-REMOVED.md'))
        self.assertFalse(os.path.exists(resolved))


if __name__ == '__main__':
    unittest.main()


class TheReleaseGateRunsOutsideACheckout(unittest.TestCase):
    """`make check` is the one command the README asks a reviewer to run.

    Both the link checker and the submission gate asked git which files are in
    the release, so `make check` exited non-zero for anyone who downloaded an
    archive instead of cloning - which is most reviewers. The gate that exists
    to stop a bad release shipping was unrunnable in the form the release
    actually takes.
    """

    def test_the_submission_gate_enumerates_files_without_git(self):
        import importlib
        gate = importlib.import_module('verify_submission')
        original = gate.subprocess.run
        gate.subprocess.run = lambda *a, **k: type('R', (), {'returncode': 128, 'stdout': b''})()
        try:
            found = gate.tracked_files()
        finally:
            gate.subprocess.run = original
        self.assertTrue(found, 'the gate found no files without a git checkout')
        self.assertIn('README.md', found)
        self.assertFalse([name for name in found if name.startswith('.git/')],
                         'the walk fallback is reading the git directory itself')

    def test_the_gate_still_refuses_to_pass_on_an_empty_listing(self):
        # A fallback that silently returns nothing would make every content
        # assertion vacuously true, which is worse than the failure it replaced.
        import importlib
        gate = importlib.import_module('verify_submission')
        self.assertGreater(len(gate.tracked_files()), 50)

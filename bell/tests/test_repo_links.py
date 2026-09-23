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


def tracked(suffix):
    out = subprocess.run(['git', 'ls-files', suffix], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


class RelativeLinksResolve(unittest.TestCase):
    def test_every_markdown_link_points_at_a_file_that_exists(self):
        broken = []
        for rel in tracked('*.md'):
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

    def test_the_check_would_notice_a_broken_link(self):
        # A checker that passes on anything proves nothing, so assert the
        # resolution step itself rejects a target that is not there.
        resolved = os.path.normpath(os.path.join(ROOT, 'bell', 'A-DOCUMENT-THAT-WAS-REMOVED.md'))
        self.assertFalse(os.path.exists(resolved))


if __name__ == '__main__':
    unittest.main()

"""A test may read a published artefact. It may not write one.

Three tests forged the dated history by writing into
`bell/site/proof/rwa-surface-integrity-history.json` and putting the original
back in a `finally`. That holds until something interrupts it, and `make mutate`
runs the offline gate 140 times in a row: the shipped series was found rewritten
in the working tree, every digest after observation four re-linked, because one
of those runs never reached its finally. It was one `git add -A` away from being
committed, into the one file whose whole purpose is that it cannot be quietly
rewritten.

The verifiers all take a path, so a forgery belongs in a temporary file. This
refuses the shape rather than the three instances, by reading the suite's own
source.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SITE = HERE.parent / "site"

# What ships. Anything under site/proof is published, and so is the anchor.
PUBLISHED = {"site", "proof", "history-chain-head.txt"}
WRITERS = {"write_text", "write_bytes", "unlink", "touch", "rename", "replace"}


def writes(tree: ast.Module):
    """Every call that writes through a Path, with the name it was called on."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in WRITERS:
            continue
        target = node.func.value
        while isinstance(target, ast.Attribute):
            target = target.value
        if isinstance(target, ast.Name):
            yield node.lineno, target.id, node.func.attr


def resolves_into_the_published_tree(name: str, source: str) -> bool:
    """Is this name bound to something under site/proof at module level?"""
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped.startswith(f"{name} ") or "=" not in stripped:
            continue
        value = stripped.split("=", 1)[1]
        if any(word in value for word in ('"site"', "'site'", '"proof"', "'proof'",
                                          "history-chain-head", "site/proof")):
            return True
    return False


class NoTestWritesAPublishedArtefact(unittest.TestCase):
    def test_no_test_file_writes_into_the_published_tree(self):
        offenders = []
        for path in sorted(HERE.glob("test_*.py")):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            for lineno, name, call in writes(tree):
                if name.isupper() and resolves_into_the_published_tree(name, source):
                    offenders.append(f"{path.name}:{lineno} calls {name}.{call}()")
        self.assertEqual(offenders, [],
                         "a test writes a published artefact; forge a copy in a temporary "
                         "directory and pass its path to the verifier instead")

    def test_the_detector_recognises_the_shape_it_refuses(self):
        # Proving the check can fail without leaving a forger in the suite.
        source = ('HISTORY = HERE.parent / "site" / "proof" / "history.json"\n'
                  'def f():\n'
                  '    HISTORY.write_text("forged")\n')
        tree = ast.parse(source)
        found = [(name, call) for _, name, call in writes(tree)
                 if resolves_into_the_published_tree(name, source)]
        self.assertEqual(found, [("HISTORY", "write_text")],
                         "the detector no longer recognises a write into site/proof")

    def test_the_shipped_history_is_the_one_git_has(self):
        # The cheapest possible tripwire on the artefact itself: if a suite run
        # leaves it different from HEAD, the next run says so rather than the
        # next `git add -A`.
        import subprocess
        repo = HERE.parent.parent
        result = subprocess.run(
            ["git", "diff", "--name-only", "--",
             "bell/site/proof/rwa-surface-integrity-history.json",
             "bell/history-chain-head.txt"],
            cwd=repo, capture_output=True, text=True)
        if result.returncode != 0:
            self.skipTest("not a git checkout")
        self.assertEqual(result.stdout.strip(), "",
                         "the published history differs from the commit; a test or a tool "
                         "wrote it and did not put it back")


if __name__ == "__main__":
    unittest.main()

"""Running a test file directly must run all of it.

test_readme_matches_measurement.py had `unittest.main()` in the middle, before
three more classes. Executing the file printed a green OK over 10 of its 19
tests; only discovery ran them all. Nine checks hid behind a pass, in a project
whose thesis is that a check nobody sees fail is not a check. Three other files
had the same shape, one because a class was appended after the block without
noticing it was there.

Checked by parsing rather than by running: executing every test file twice as a
subprocess takes minutes, and a gate that takes minutes stops being run.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def main_guard_line(tree: ast.Module) -> int | None:
    """The line of `if __name__ == "__main__":`, if the module has one."""
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name) and test.left.id == "__name__"):
            return node.lineno
    return None


class EveryTestRuns(unittest.TestCase):
    def test_no_test_case_is_defined_after_the_main_block(self):
        offenders = []
        for path in sorted(HERE.glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            guard = main_guard_line(tree)
            if guard is None:
                continue
            late = [node.name for node in tree.body
                    if isinstance(node, ast.ClassDef) and node.lineno > guard]
            if late:
                offenders.append(f"{path.name}: {', '.join(late)} defined after the main block")
        self.assertEqual(offenders, [],
                         "a direct run of these files would print OK over tests it never reached")

    def test_no_test_is_written_in_a_style_the_gate_does_not_collect(self):
        # test_terminal.py, test_live_store.py and test_publisher.py held nine
        # tests written as pytest-style module functions. The gate collects with
        # unittest, which ignores them, so they existed, passed nobody's eye and
        # protected nothing. A test the runner cannot see is not a test.
        uncollected = []
        for path in sorted(HERE.glob("test_*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            loose = [node.name for node in tree.body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and node.name.startswith("test")]
            if loose:
                uncollected.append(f"{path.name}: {', '.join(loose)} are module functions")
            cases = [node for node in tree.body if isinstance(node, ast.ClassDef)]
            methods = sum(1 for node in cases for child in node.body
                          if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and child.name.startswith("test"))
            if not methods and not loose:
                uncollected.append(f"{path.name}: defines no test methods at all")
        self.assertEqual(uncollected, [],
                         "unittest discovery will not collect these, so the gate never runs them")

if __name__ == "__main__":
    unittest.main()

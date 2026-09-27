"""A check may not take its scope from the thing it is checking.

Three separate reviewers found three instances of one shape in the verifier,
and each time the instance was fixed and the shape was left alone:

  1. `if request_count is not None or status_codes is not None: ...` - delete
     the four provenance fields and the block that guards them disappears.
  2. `rules_differ = ...` read from the receipt being audited - declare a
     different rule version and the state comparison switches itself off.
  3. `{key: signals.get(key) for key in observation["signals"]}` - empty the
     claimed keys and the comparison compares nothing, while the gate prints
     that signals were compared.

All three are the same sentence: the forger supplies the scope. This file
refuses the shape rather than the instances, by reading the verifier's source.
A pattern test is blunt, and blunt is the point: the next instance of this cost
three review rounds to find by hand.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
BELL = HERE.parent

# The verifiers whose job is to refuse forged evidence. A helper that formats a
# receipt for display is not in scope; these decide whether it is believed.
GUARDED = (
    "verify_integrity_receipt.py",
    "history_chain.py",
    "append_history.py",
)


def comparisons(tree: ast.Module):
    """Every call that compares two values for equality in a verifier."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "assert_equal":
            yield node


class NoCheckTakesItsScopeFromItsInput(unittest.TestCase):
    def test_no_equality_check_projects_one_side_onto_the_other_s_keys(self):
        offenders = []
        for name in GUARDED:
            path = BELL / name
            if not path.exists():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for call in comparisons(tree):
                for argument in call.args:
                    # {k: a.get(k) for k in b} - the comparison's scope is b,
                    # which in every instance found so far is the claim, not
                    # the evidence.
                    if isinstance(argument, ast.DictComp):
                        offenders.append(
                            f"{name}:{argument.lineno} compares a projection instead of the "
                            "whole value, so an empty or shortened claim compares nothing")
        self.assertEqual(offenders, [],
                         "a check is taking its scope from the thing it is checking")

    def test_the_pattern_test_can_see_the_pattern(self):
        # Proving the check above can fail, without leaving a forged file in the
        # repository: parse the exact expression the reviewer exploited and
        # require the detector to flag it.
        source = ('def f():\n'
                  '    assert_equal("x", {key: a.get(key) for key in b["signals"]}, b["signals"])\n')
        tree = ast.parse(source)
        found = [argument for call in comparisons(tree) for argument in call.args
                 if isinstance(argument, ast.DictComp)]
        self.assertEqual(len(found), 1,
                         "the detector no longer recognises the shape it exists to refuse")

    def test_no_guard_in_a_verifier_is_satisfied_by_deleting_the_evidence(self):
        # The provenance block was `if any of these four fields is present`,
        # so removing all four removed the check. The repaired form is a bare
        # `if True:` kept for indentation, which reads oddly and is deliberate.
        # What this refuses is a condition built out of `is not None` tests on
        # the very fields the body then validates.
        offenders = []
        for name in GUARDED:
            path = BELL / name
            if not path.exists():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.If) or not isinstance(node.test, ast.BoolOp):
                    continue
                if not isinstance(node.test.op, ast.Or):
                    continue
                presence = [value for value in node.test.values
                            if isinstance(value, ast.Compare)
                            and any(isinstance(op, (ast.IsNot, ast.Is)) for op in value.ops)
                            and any(isinstance(c, ast.Constant) and c.value is None
                                    for c in value.comparators)]
                if len(presence) >= 2:
                    offenders.append(
                        f"{name}:{node.lineno} runs its checks only when the fields it checks "
                        "are present, so deleting them deletes the check")
        self.assertEqual(offenders, [], "a verifier guard can be satisfied by removing evidence")


if __name__ == "__main__":
    unittest.main()

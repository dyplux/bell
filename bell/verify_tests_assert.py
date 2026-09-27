#!/usr/bin/env python3
"""Run the suite and refuse any test that executed no assertion.

Be exact about the claim, because a reviewer was right to press on it: this
measures that an assertion RAN, not that it CAN FAIL. It catches a test with no
assertion, a loop over an empty list, and a bare `assert` that -O removes. It
does not catch `self.assertTrue(True)` or `assertEqual(x, x)`, and saying it
did would be the overclaim this repository exists to refuse. It also covers the
Python suite only: the 98 JavaScript and worker tests are outside it, which is
named in the output rather than left to be assumed.

Six review rounds found the same thing six times: a test that cannot fail. A
loop over zero items. `assertGreaterEqual(compared, 0)`. A class named after a
re-derivation it never performed. A guard keyed on a phrase the regression
removes. Nineteen bare `assert`s that vanish under `python3 -O`. Every one was
found by a person reading the file.

Static analysis is the wrong instrument: parsing for "all assertions are inside
a loop" flags twelve tests here and ten of them iterate over real data and are
fine. What matters is not where an assertion is written, it is whether it RAN.

So this wraps every `TestCase.assert*` with a counter, runs the suite once, and
fails on any test that reached the end having checked nothing. A skipped test
is not a failure and is listed separately, because a skip that nobody sees is
the same defect wearing a different hat.

It is a separate target rather than part of `make check-offline`: it runs the
whole suite a second time, and a gate that doubles in length stops being run.
CI runs it on every push.

    make audit-tests
"""

from __future__ import annotations

import argparse
from collections import Counter
import io
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent

# A control whose assertion is "this call does not raise" has no assert* to
# count. Naming them here is the price of that shape, and the list is meant to
# stay short: each entry is a test whose passing condition is the absence of an
# exception, which must be obvious from its name and its body.
ALLOWED_WITHOUT_ASSERTIONS: frozenset = frozenset()


def counted_suite(pattern: str) -> tuple:
    counts: Counter = Counter()
    current = [""]
    original = {name: getattr(unittest.TestCase, name)
                for name in dir(unittest.TestCase)
                if name.startswith("assert") and callable(getattr(unittest.TestCase, name))}

    def wrap(function):
        def wrapper(self, *args, **kwargs):
            counts[current[0]] += 1
            return function(self, *args, **kwargs)
        return wrapper

    for name, function in original.items():
        setattr(unittest.TestCase, name, wrap(function))

    loader = unittest.TestLoader()
    suite = loader.discover(str(HERE / "tests"), pattern=pattern, top_level_dir=str(HERE / "tests"))

    def flatten(item):
        for child in item:
            if isinstance(child, unittest.TestSuite):
                yield from flatten(child)
            else:
                yield child

    tests = list(flatten(suite))
    skipped = []
    runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
    for test in tests:
        key = f"{test.__class__.__module__}.{test.__class__.__name__}.{test._testMethodName}"
        current[0] = key
        counts.setdefault(key, 0)
        result = runner.run(unittest.TestSuite([test]))
        if result.skipped:
            skipped.append(key)
    for name, function in original.items():
        setattr(unittest.TestCase, name, function)
    return counts, skipped, len(tests)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pattern", default="test_*.py")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(HERE))
    counts, skipped, total = counted_suite(args.pattern)
    silent = sorted(name for name, count in counts.items()
                    if count == 0 and name not in skipped
                    and name not in ALLOWED_WITHOUT_ASSERTIONS)

    print(f"assertion audit: {total} Python tests, "
          f"{sum(counts.values()):,} assertions executed, {len(skipped)} skipped")
    print("  scope: an assertion RAN. Not that it can fail - assertTrue(True) passes this. "
          "The JavaScript and worker suites are not covered.")
    for name in skipped:
        print(f"  skipped: {name}")
    if silent:
        print("these tests ran to the end and checked nothing:", file=sys.stderr)
        for name in silent:
            print(f"  {name}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

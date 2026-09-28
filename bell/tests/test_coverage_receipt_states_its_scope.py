"""A coverage receipt may not publish one file's numbers as the repository's.

`make mutate ONLY=verify_case_receipt.py` wrote the whole receipt from that one
file and left in place a note describing a sweep. The version this repository
published said:

    "guards_mutated": 41, "survivors": [ ...17 entries... ]

Every one of those seventeen was in `verify_case_receipt.py`. The other four
guarded files were not in the run. The real figure at the last full sweep was
123 mutated and 38 survivors, so the published receipt overstated the coverage
of the evidence path by a factor of three, in the directory a judge downloads
from, in a repository whose subject is surfaces that quietly disagree.

Nothing read the file, so nothing disagreed with it. That is the whole defect:
the scope of the measurement came from a command-line flag and was never
written down, so every reader supplied the widest scope themselves.

What this file refuses is the misdescription, not the partial run. A one-file
run is the useful run - four minutes against twenty - and stays allowed. It
must merge into what is already known, carry the digest of the source it
measured, and refuse to call itself complete while a guarded file is missing or
was measured against a source that has since changed.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
BELL = HERE.parent
sys.path.insert(0, str(BELL))

import mutate_the_guards as mutate  # noqa: E402

RECEIPT = BELL / "site" / "proof" / "guard-coverage.json"


class TheCoverageReceiptStatesItsScope(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        # Named, rather than left to fail as a KeyError three assertions later:
        # the shipped receipt had no per-file records at all, and a reader of a
        # red suite should learn that from the first line of it.
        self.assertEqual(
            self.receipt.get("schema_version"), mutate.SCHEMA,
            "this receipt predates the per-file records, so it cannot say which files its "
            "numbers cover; re-run `make mutate`")
        for key in ("complete", "scope", "files", "files_not_measured"):
            self.assertIn(key, self.receipt, f"the receipt does not state its {key}")

    def test_the_totals_are_the_sum_of_the_files_measured(self):
        files = self.receipt["files"]
        self.assertEqual(
            self.receipt["guards_mutated"],
            sum(record["guards_mutated"] for record in files.values()),
            "the headline count does not add up from the per-file records, so it is a "
            "number about some other set of files")
        expected = sorted(({"file": name, "line": line}
                           for name, record in files.items() for line in record["survivors"]),
                          key=lambda entry: (entry["file"], entry["line"]))
        self.assertEqual(self.receipt["survivors"], expected)

    def test_every_file_it_names_is_a_guarded_file_that_exists(self):
        for name in self.receipt["files"]:
            self.assertIn(name, mutate.GUARDED)
            self.assertTrue((BELL / name).exists(), f"{name} no longer exists")

    def test_it_calls_itself_complete_only_when_it_is(self):
        missing = [name for name in mutate.GUARDED
                   if (BELL / name).exists() and name not in self.receipt["files"]]
        self.assertEqual(self.receipt["files_not_measured"], missing)
        self.assertEqual(self.receipt["complete"], not missing,
                         "the receipt's own claim about its coverage disagrees with what it "
                         "contains")

    def test_a_record_measured_against_another_tree_is_reported_as_outdated(self):
        # Currency is reported, not gated. A sweep takes twenty minutes and
        # cannot be the price of editing a test, and gating on it deadlocks the
        # repository: the receipt only becomes current by running `make
        # mutate`, which refuses to start on a red gate, which is red because
        # the receipt is not current. So what is under test here is the
        # function that decides currency, driven on records built for it, and
        # `make mutate` prints its answer on every run.
        #
        # A record with no digests at all is reported outdated by the same
        # rule, which is why their presence is not asserted separately:
        # stripping the fields does not hide the record, it condemns it.
        current = {name: {"guards_mutated": 1, "survivors": [],
                          "source_digest": mutate.digest_of(BELL / name),
                          "suite_digest": mutate.suite_digest(),
                          "measured_at": "2026-09-27T00:00:00Z"}
                   for name in sorted(self.receipt["files"])}
        self.assertEqual(mutate.outdated(current), [],
                         "records measured against this tree are being called outdated")
        for field in ("source_digest", "suite_digest"):
            name = sorted(current)[0]
            moved = copy.deepcopy(current)
            moved[name][field] = "0" * 64
            with self.subTest(changed=field):
                self.assertEqual(mutate.outdated(moved), [name],
                                 f"a record whose {field} no longer describes this tree is "
                                 "being passed off as current coverage")

    def test_the_scope_line_names_what_the_numbers_leave_out(self):
        # Deliberately not a skip when the receipt is complete: a test that
        # stands down as soon as the thing is healthy is how the earlier
        # version of this measurement went three files unwatched.
        if self.receipt["complete"]:
            self.assertEqual(self.receipt["files_not_measured"], [])
            self.assertIn("every guarded file", self.receipt["scope"])
            return
        for name in self.receipt["files_not_measured"]:
            self.assertIn(name, self.receipt["scope"],
                          "a reader cannot tell which files this number leaves out")

    def test_one_file_alone_is_never_called_a_sweep(self):
        # The exact shape that shipped: the guarded set has five files and the
        # receipt was written from one of them.
        one = sorted(mutate.GUARDED)[0]
        forged = mutate.assemble({one: {"guards_mutated": 41, "survivors": [12],
                                        "source_digest": mutate.digest_of(BELL / one),
                                        "suite_digest": mutate.suite_digest(),
                                        "measured_at": "2026-09-27T00:00:00Z"}})
        self.assertFalse(forged["complete"])
        self.assertEqual(forged["guards_mutated"], 41,
                         "the total must be the total of what was measured, not of what a "
                         "reader assumes was measured")
        for name in mutate.GUARDED:
            if name != one and (BELL / name).exists():
                self.assertIn(name, forged["files_not_measured"])



class AStatedExceptionCarriesItsReason(unittest.TestCase):
    """A guard excused from the sweep has to say why, in the receipt.

    Two guards change no behaviour when neutered: `number()` rejects None and
    bool before a parse that would have refused them anyway, and the
    single-representation lens sorts every row through an if/elif/elif/else so
    its parts cannot fail to sum. No behaviour test can catch either, and
    leaving them in the survivor list makes that number mean two things at
    once - "nobody tested this" and "nothing could".

    So they are counted apart and the argument ships with them. The failure
    mode this guards against is the obvious one: an inconvenient guard quietly
    joining the list to make a number look better.
    """

    def setUp(self):
        self.receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    def test_every_stated_exception_names_a_real_guard(self):
        for (name, line) in mutate.STATED_EXCEPTIONS:
            path = BELL / name
            self.assertTrue(path.exists(), f"{name} does not exist")
            self.assertIn(name, mutate.GUARDED,
                          f"{name} is excused from a sweep that never covers it")
            self.assertIn(line, [found for found, _, _ in mutate.guards(path)],
                          f"{name}:{line} is not a guard, so excusing it means nothing")

    def test_every_stated_exception_carries_an_argument(self):
        for key, reason in mutate.STATED_EXCEPTIONS.items():
            self.assertGreater(len(reason), 80,
                               f"{key} is excused without saying why in any detail")
            self.assertNotIn("TODO", reason)

    def test_the_receipt_ships_the_reasons_and_does_not_hide_them_in_the_total(self):
        stated = [(name, entry["line"], entry["reason"])
                  for name, record in self.receipt["files"].items()
                  for entry in record.get("stated_exceptions", [])]
        survivors = {(entry["file"], entry["line"]) for entry in self.receipt["survivors"]}
        for name, line, reason in stated:
            self.assertEqual(reason, mutate.STATED_EXCEPTIONS[(name, line)],
                             f"{name}:{line} ships a different reason than the code states")
            self.assertNotIn((name, line), survivors,
                             f"{name}:{line} is both excused and counted as a survivor")
if __name__ == "__main__":
    unittest.main()

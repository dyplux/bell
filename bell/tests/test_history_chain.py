"""A forged observation must not verify.

A reviewer rewrote one summary-only observation into an invented but internally
consistent day - 791 references, every one no_flags, every signal zero - and the
verifier returned ok. Replacing a source hash with sixty-four zeros passed too.
Two of the observations ship their payload and are cross-checked against it; the
other eleven were checked only for shape, so a coherent forgery was
indistinguishable from a record.

These tests are that reviewer's attacks, kept.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from history_chain import CHAIN_VERSION, link, rebuild, verify  # noqa: E402

HISTORY = HERE.parent / "site" / "proof" / "rwa-surface-integrity-history.json"


def observation(stamp: str, clear: int = 94) -> dict:
    return {
        "observed_at": stamp,
        "tokenised_references_scanned": 791,
        "tokens_scanned": 1435,
        "states": {"do_not_compare": 35, "investigate": 662, "no_flags": clear},
        "signals": {"PRICE_DENOMINATION_BREAK": 4},
        "source_hashes": {"map": "a" * 64},
    }


class TheChain(unittest.TestCase):
    def test_a_clean_series_verifies_and_returns_its_head(self):
        chained = rebuild([observation("2026-09-21T21:25:01Z"), observation("2026-09-26T20:08:35Z")])
        self.assertEqual(verify(chained), chained[-1]["sha256"])
        self.assertIsNone(chained[0]["prev_sha256"])
        self.assertEqual(chained[1]["prev_sha256"], chained[0]["sha256"])

    def test_editing_a_summary_only_observation_is_caught(self):
        # The attack that succeeded: an invented day, internally consistent.
        chained = rebuild([observation("2026-09-21T17:01:00Z"), observation("2026-09-26T20:08:35Z")])
        forged = copy.deepcopy(chained)
        forged[0]["states"] = {"do_not_compare": 0, "investigate": 0, "no_flags": 791}
        forged[0]["signals"] = {"PRICE_DENOMINATION_BREAK": 0}
        with self.assertRaises(ValueError) as caught:
            verify(forged)
        self.assertIn("2026-09-21T17:01:00Z", str(caught.exception))
        self.assertIn("contents were edited", str(caught.exception))

    def test_replacing_a_source_hash_with_zeroes_is_caught(self):
        chained = rebuild([observation("2026-09-21T21:25:01Z"), observation("2026-09-26T20:08:35Z")])
        forged = copy.deepcopy(chained)
        forged[0]["source_hashes"]["map"] = "0" * 64
        with self.assertRaises(ValueError):
            verify(forged)

    def test_relinking_the_forgery_still_breaks_everything_after_it(self):
        # A forger who recomputes the edited record's own digest still has to
        # rewrite every record after it, which is the point of the chain.
        chained = rebuild([observation("2026-09-21T21:25:01Z"),
                           observation("2026-09-26T20:08:35Z"),
                           observation("2026-09-26T21:25:28Z")])
        forged = copy.deepcopy(chained)
        forged[0]["states"]["no_flags"] = 999
        forged[0] = link(forged[0], None)
        with self.assertRaises(ValueError) as caught:
            verify(forged)
        self.assertIn("an observation was inserted, removed or reordered", str(caught.exception))

    def test_removing_or_reordering_an_observation_is_caught(self):
        chained = rebuild([observation("2026-09-15T22:22:00Z"),
                           observation("2026-09-21T21:25:01Z"),
                           observation("2026-09-26T20:08:35Z")])
        with self.assertRaises(ValueError):
            verify([chained[0], chained[2]])
        with self.assertRaises(ValueError):
            verify([chained[1], chained[0], chained[2]])

    def test_an_unlinked_observation_is_refused_rather_than_ignored(self):
        chained = rebuild([observation("2026-09-21T21:25:01Z")])
        chained.append(observation("2026-09-26T20:08:35Z"))
        with self.assertRaises(ValueError) as caught:
            verify(chained)
        self.assertIn(CHAIN_VERSION, str(caught.exception))

    def test_the_shipped_history_is_chained_and_declares_its_own_head(self):
        history = json.loads(HISTORY.read_text(encoding="utf-8"))
        self.assertEqual(history.get("chain_version"), CHAIN_VERSION)
        self.assertEqual(history.get("chain_head"), verify(history["observations"]))

    def test_the_verifier_exits_non_zero_on_a_forged_history(self):
        # End to end, not just the library: the command a judge runs has to fail.
        repo = HERE.parent.parent
        history = json.loads(HISTORY.read_text(encoding="utf-8"))
        original = HISTORY.read_bytes()
        # Internally consistent, exactly as the reviewer's forgery was: the
        # states still sum to the population, so the shape check passes and the
        # chain is what has to catch it.
        target = history["observations"][3]
        total = target["tokenised_references_scanned"]
        target["states"] = {"do_not_compare": 0, "investigate": 0, "no_flags": total}
        target["signals"] = {key: 0 for key in target["signals"]}
        try:
            HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
            result = subprocess.run(["python3", "bell/verify_integrity_receipt.py"], cwd=repo,
                                    capture_output=True, text=True,
                                    env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
            self.assertNotEqual(result.returncode, 0,
                                "the verifier accepted an edited observation")
            self.assertIn("does not match its own digest", result.stderr)
        finally:
            HISTORY.write_bytes(original)

    def test_a_truncated_file_is_explained_rather_than_traced(self):
        # A half-written file raised JSONDecodeError and printed a raw stack. A
        # verifier exists to say what is wrong with the evidence; the exit code
        # was already right, the message was not.
        repo = HERE.parent.parent
        original = HISTORY.read_bytes()
        try:
            HISTORY.write_bytes(original[:900])
            result = subprocess.run(["python3", "bell/verify_integrity_receipt.py"], cwd=repo,
                                    capture_output=True, text=True,
                                    env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
            self.assertEqual(result.returncode, 1)
            self.assertIn("is not readable JSON", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            HISTORY.write_bytes(original)

    def test_a_missing_file_says_which_one(self):
        repo = HERE.parent.parent
        result = subprocess.run(
            ["python3", "bell/verify_integrity_receipt.py", "--history", "bell/nope.json"],
            cwd=repo, capture_output=True, text=True,
            env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("nope.json is missing", result.stderr)
        self.assertNotIn("Traceback", result.stderr)



class TheAnchor(unittest.TestCase):
    """Rebuilding the whole chain and updating the declared head used to pass.

    The head lived inside the file it protects, so a forger who re-linked every
    record and rewrote that one field verified clean. A reviewer did exactly
    that and reported exit 0. The head is anchored in a second tracked file now:
    the forgery has to edit both, which is a separate line in the diff, and a
    reader verifying a fixed commit compares against a value the history cannot
    rewrite for itself.
    """

    ANCHOR = HERE.parent / "history-chain-head.txt"

    def test_the_anchor_matches_the_shipped_chain(self):
        history = json.loads(HISTORY.read_text(encoding="utf-8"))
        self.assertEqual(self.ANCHOR.read_text(encoding="utf-8").strip(),
                         verify(history["observations"]))

    def test_a_fully_rebuilt_chain_no_longer_verifies(self):
        repo = HERE.parent.parent
        original = HISTORY.read_bytes()
        history = json.loads(original)
        target = history["observations"][5]
        target["states"] = {"do_not_compare": 0, "investigate": 0,
                            "no_flags": target["tokenised_references_scanned"]}
        target["signals"] = {key: 0 for key in target["signals"]}
        history["observations"] = rebuild(history["observations"])
        history["chain_head"] = verify(history["observations"])
        try:
            HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
            result = subprocess.run(["python3", "bell/verify_integrity_receipt.py"], cwd=repo,
                                    capture_output=True, text=True,
                                    env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
            self.assertEqual(result.returncode, 1,
                             "a fully rebuilt chain with a matching head still verified")
            self.assertIn("history-chain-head.txt anchors", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
        finally:
            HISTORY.write_bytes(original)

    def test_a_missing_anchor_is_refused_rather_than_skipped(self):
        repo = HERE.parent.parent
        original = self.ANCHOR.read_bytes()
        try:
            self.ANCHOR.unlink()
            result = subprocess.run(["python3", "bell/verify_integrity_receipt.py"], cwd=repo,
                                    capture_output=True, text=True,
                                    env={"PYTHONPATH": "bell", "PATH": "/usr/bin:/bin:/usr/local/bin"})
            self.assertEqual(result.returncode, 1)
            self.assertIn("has no anchor outside the history", result.stderr)
        finally:
            self.ANCHOR.write_bytes(original)



class TheSurfaceGuards(unittest.TestCase):
    """A wrong-typed surface used to raise a bare AttributeError.

    An empty surface was already refused by name and reported in the receipt.
    A string where a payload belongs reached .get() and raised
    "'str' object has no attribute 'get'", which names nothing a reader could
    act on, in the one place that exists to say what is wrong with the input.
    """

    def test_a_mistyped_surface_is_refused_by_name(self):
        import rwa_integrity
        good = {"data": {"rwa_assets": []}}
        for payloads, expected in (
            (("not a dict", good, good, good), "map"),
            ((good, [], good, good), "asset_list"),
            ((good, good, 7, good), "quotes"),
            ((good, good, good, "x"), "info"),
        ):
            with self.assertRaises(ValueError) as caught:
                rwa_integrity.scan(*payloads)
            self.assertIn(expected, str(caught.exception))
            self.assertIn("is not an object", str(caught.exception))

    def test_an_absent_optional_surface_is_still_allowed(self):
        # None means "not collected", which is different from "handed the wrong
        # thing", and the scan has always tolerated it.
        import rwa_integrity
        good = {"data": {"rwa_assets": []}}
        receipt = rwa_integrity.scan(good, good, good, None, None, "2026-09-27T00:00:00Z", None)
        self.assertEqual(receipt["schema_version"], "rwa_surface_integrity.v1")


class AnEmptyChainIsNotAVerifiedChain(unittest.TestCase):
    def test_verifying_no_observations_is_refused(self):
        # `make mutate` found this refusal undefended: verify([]) returning a
        # head would mean an empty file verifies, which is the strongest
        # possible forgery and the cheapest to make.
        with self.assertRaisesRegex(ValueError, "carries no observations"):
            verify([])


if __name__ == "__main__":
    unittest.main()

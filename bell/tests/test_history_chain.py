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


if __name__ == "__main__":
    unittest.main()

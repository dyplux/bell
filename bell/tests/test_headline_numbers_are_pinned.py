"""Every number the judge page prints must come from a shipped measurement.

judge.html opens with "Every number on this page was produced by a command you
can run yourself". A reviewer tested that sentence and it was false for the
four figures the page puts first: the two headline tiles and the two counts in
the opening paragraph could each be changed to anything - 87 to 870, 157 to 9,
244 to 2444 - and the whole gate stayed green. The machinery to catch it
existed and stopped at the README's fenced code block, so the numbers inside
the fence were pinned and the ones a reader sees first were not.

The comparison figures come from the base-rate receipt, which `make base-rate`
reproduces. The catalogue-reconciliation figures come from the shipped replay
receipt's own `catalogue_integrity` block. Nothing here is written down twice:
each expected value is read out of the evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
BELL = HERE.parent
JUDGE = BELL / "site" / "judge.html"
README = BELL.parent / "README.md"
PROOF = BELL / "site" / "proof"

BASE_RATE = json.loads((PROOF / "base-rate-2026-09-21.json").read_text(encoding="utf-8"))
REPLAY = json.loads(
    (PROOF / "rwa-surface-integrity-latest-replay-2026-09-21.json").read_text(encoding="utf-8"))
CATALOGUE = REPLAY["catalogue_integrity"]


def judge_text() -> str:
    return JUDGE.read_text(encoding="utf-8")


def readme_text() -> str:
    return README.read_text(encoding="utf-8")


def flowed(text: str) -> str:
    """Collapse the line wrapping, so a reflow is not read as a changed number."""
    return re.sub(r"\s+", " ", text)


class HeadlineNumbersArePinned(unittest.TestCase):
    def test_the_two_tiles_state_the_measured_comparison_counts(self):
        page = judge_text()
        published = BASE_RATE["comparable"]
        refused = BASE_RATE["refused"]
        self.assertIn(f"<small>Comparisons published</small><strong>{published}</strong>", page,
                      f"the published-comparisons tile is not the measured {published}")
        self.assertIn(f"<small>Refusals, by named rule</small><strong>{refused}</strong>", page,
                      f"the refusals tile is not the measured {refused}")

    def test_the_opening_paragraph_states_the_measured_denominator_and_counts(self):
        page = judge_text()
        denominator = BASE_RATE["denominator_two_or_more_representations"]
        flow = flowed(page)
        self.assertIn(f"Of the {denominator} references carrying more than one representation",
                      flow, "the opening paragraph's denominator is not the measured one")
        self.assertIn(f"<strong>{BASE_RATE['comparable']} have a cheapest route worth naming",
                      flow, "the opening paragraph's affirmative count is not measured")
        self.assertIn(f"and {BASE_RATE['refused']} are refused by a coded rule", flow,
                      "the opening paragraph's refusal count is not measured")

    def test_the_readme_body_states_the_same_measured_counts(self):
        # Outside the fenced block, which is the only part the older test read.
        body = readme_text()
        body = flowed(body)
        self.assertIn(f"**{BASE_RATE['comparable']} have a cheapest route worth naming**", body)
        self.assertIn(f"{BASE_RATE['refused']} are refused by a coded rule", body)
        self.assertIn(f"Of the {BASE_RATE['denominator_two_or_more_representations']} references",
                      body)

    def test_the_catalogue_reconciliation_states_the_receipt_s_own_figures(self):
        page = judge_text()
        flow = flowed(page)
        self.assertIn(f"{CATALOGUE['map_rows']:,}-entry", flowed(readme_text()),
                      "the README map-row count is not the receipt's")
        self.assertIn(f"the {CATALOGUE['map_rows']:,} rows the map returns against "
                      f"the {CATALOGUE['asset_list_rows']:,} the asset list returns", flow,
                      "the reconciliation sentence is not the receipt's own figures")
        self.assertIn(f"exposes {CATALOGUE['asset_list_rows_without_rwa_id']} rows with no stable",
                      flow)

    def test_the_base_rate_receipt_is_internally_consistent(self):
        # Without this the assertions above are pinned to a file that could
        # itself say anything. `make base-rate` recomputes this receipt from the
        # shipped catalogue, and test_readme_matches_measurement checks the
        # printed block against it; this checks the arithmetic holds.
        self.assertEqual(
            BASE_RATE["refused"] + BASE_RATE["comparable"],
            BASE_RATE["denominator_two_or_more_representations"],
            "the base-rate receipt's own counts do not add up to its denominator")
        self.assertEqual(
            BASE_RATE["denominator_two_or_more_representations"]
            + BASE_RATE["excluded_single_representation"],
            BASE_RATE["population"],
            "the base-rate receipt's denominator and exclusions do not sum to its population")

    def test_no_bare_headline_number_survives_unpinned(self):
        # The rule, not the four instances. Every number inside a judge-page
        # tile must be one this suite has pinned, so adding a fifth tile with an
        # invented figure fails here rather than shipping.
        pinned = {
            str(BASE_RATE["comparable"]), str(BASE_RATE["refused"]),
            str(BASE_RATE["denominator_two_or_more_representations"]),
        }
        page = judge_text()
        tiles = re.findall(r"<small>([^<]+)</small><strong>([^<]+)</strong>", page)
        self.assertTrue(tiles, "the judge page tiles went missing")
        unpinned = []
        for label, value in tiles:
            bare = value.replace(",", "")
            if not bare.isdigit():
                # "&lt;8s" is a duration, pinned against the stated band by
                # test_judge_counts. Only bare counts are this test's business.
                continue
            if bare not in pinned and label != "Tests in the offline gate":
                unpinned.append(f"{label}: {value}")
        self.assertEqual(unpinned, [],
                         "these judge-page tiles state a number no measurement pins")


if __name__ == "__main__":
    unittest.main()

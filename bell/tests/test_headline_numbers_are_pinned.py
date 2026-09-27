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
        # itself say anything. This comment used to claim that
        # test_readme_matches_measurement compared this file to
        # measure(scan(inputs)); it did not - it compared the README's fenced
        # block - and a reviewer got an internally consistent forgery through
        # the whole Python suite on the strength of that gap. The comparison
        # exists now, in TheBaseRateReceiptIsTheMeasurement. This still checks
        # the arithmetic, which is a different question from provenance.
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


    def test_the_thirty_second_path_states_the_measured_base_rate(self):
        # A reviewer mutated all of these and the gate stayed green, on the page
        # whose first sentence promises every number came from a command.
        flow = flowed(judge_text())
        rate = f"{BASE_RATE['refusal_rate'] * 100:.1f}%"
        self.assertIn(f"Refusal rate {rate}", flow, "the stated refusal rate is not the measured one")
        self.assertIn(f"{BASE_RATE['population']} references, "
                      f"{BASE_RATE['excluded_single_representation']} with a single", flow,
                      "the 30-second block's population or exclusions are not measured")
        self.assertIn(f"{BASE_RATE['denominator_two_or_more_representations']} where a comparison "
                      f"could be attempted, {BASE_RATE['refused']}", flow)
        low, high = BASE_RATE["refusal_rate_ci95"]
        self.assertIn(f"Wilson 95% interval {low * 100:.1f} to {high * 100:.1f}%", flow,
                      "the stated confidence interval is not the measured one")

    def test_the_refusal_split_is_the_measured_split(self):
        split = BASE_RATE["refusal_split"]
        reasons = sum(BASE_RATE["refusal_reasons"].values()) \
            if isinstance(BASE_RATE.get("refusal_reasons"), dict) else BASE_RATE["refusal_reasons"]
        flow = flowed(judge_text())
        self.assertIn(f"<strong>{split['source_coverage']} of the {reasons} reasons", flow,
                      "the coverage half of the refusal split is not measured")
        # `assertIn("38 are rows")` is satisfied by "1138 are rows". A pin a
        # forger beats by prepending a digit is not a pin; the siblings here
        # survived only because they happen to have a non-digit before the
        # number. Word boundary, everywhere.
        self.assertRegex(flow, rf"\b{split['data_contradiction']} are rows",
                         "the contradiction half of the refusal split is not measured")

    def test_the_demo_line_states_the_slice_the_receipt_actually_carries(self):
        alerts = len(REPLAY.get("alerts") or [])
        self.assertIn(f"the {alerts} highest-priority flagged references", flowed(judge_text()),
                      f"the judge page describes a slice of a different size; the receipt ships {alerts}")

    def test_the_input_package_size_is_the_size_on_disk(self):
        megabytes = (PROOF / "rwa-surface-integrity-inputs-2026-09-21.json").stat().st_size / 1_000_000
        stated = f"{megabytes:.1f} MB of shipped inputs"
        self.assertIn(stated, flowed(judge_text()),
                      f"the judge page states an input package size that is not {stated}")

    def test_the_readme_states_the_receipt_s_own_reference_count(self):
        references = REPLAY["universe"]["tokenised_references_scanned"]
        self.assertIn(f"contained {references} tokenised references", flowed(readme_text()),
                      "the README states a reference count the replay receipt does not")

    def test_the_named_contradiction_counts_come_from_their_own_denominator(self):
        # The first version of this pinned the sentence to the receipt's
        # whole-population signal counts and would have "corrected" a number
        # that was already right. The sentence is inside the breakdown of the
        # 157 refusals, so its denominator is the 244 comparable-attemptable
        # references, and the source is base_rate's refusal_reasons: 30 there
        # against 32 over the whole population. Two right numbers answering two
        # questions is exactly what this product exists to keep apart, so the
        # test has to read the one the sentence is about.
        reasons = BASE_RATE["refusal_reasons"]
        flow = flowed(readme_text())
        self.assertIn(f"including {reasons['PRICE_DENOMINATION_BREAK']} references quoted in "
                      "different units", flow,
                      "the README's unit-mismatch count is not the measured one")
        self.assertRegex(flow, rf"\b{reasons['ZERO_MCAP_POSITIVE_VOLUME']} reporting traded "
                               r"volume against a zero market cap",
                         "the README's zero-market-cap count is not the measured one")

    def test_the_runtime_tile_cannot_drift_out_of_its_own_stated_band(self):
        # The `<12s` tile sat beside a pinned "2.8 and 12.0 seconds" band and
        # was free to say anything. A headline that contradicts the sentence
        # under it is the defect this page is about.
        page = flowed(judge_text())
        band = re.search(r"between (\d+\.\d+) and (\d+\.\d+) seconds", page)
        self.assertIsNotNone(band, "the judge page stopped stating a measured band")
        tile = re.search(r"<small>Gate runtime</small><strong>&lt;(\d+)s</strong>", judge_text())
        self.assertIsNotNone(tile, "the gate runtime tile went missing")
        self.assertGreaterEqual(float(tile.group(1)), float(band.group(2)),
                                "the runtime tile is below the band stated beside it")

    def test_every_statement_of_the_published_count_agrees(self):
        # "157 refused, 87 published" had 157 pinned and 87 free in the same
        # sentence, so the page could print arithmetic that does not close. Both
        # figures, everywhere they appear in that role, come from the receipt.
        published = str(BASE_RATE["comparable"])
        refused = str(BASE_RATE["refused"])
        for label, text in (("judge.html", flowed(judge_text())),
                            ("README.md", flowed(readme_text()))):
            for found_refused, found_published in re.findall(
                    r"(\d+)\s+refused,\s+(\d+)\s+published", text):
                self.assertEqual((found_refused, found_published), (refused, published),
                                 f"{label} states {found_refused} refused and {found_published} "
                                 f"published; the measurement is {refused} and {published}")
            for found in re.findall(r"Refusal rate ([\d.]+)%", text):
                self.assertEqual(found, f"{BASE_RATE['refusal_rate'] * 100:.1f}",
                                 f"{label} states a refusal rate the measurement does not produce")

    def test_the_readme_states_one_runtime_band_not_two(self):
        # README.md stated the band twice and pinned one of them, so the
        # duplicate could drift away from its own pinned twin.
        bands = set(re.findall(r"between (\d+\.\d+) and (\d+\.\d+) seconds",
                               flowed(readme_text())))
        bands |= set(re.findall(r"same (\d+\.\d+) to (\d+\.\d+)\s*\n?\s*seconds",
                                readme_text()))
        self.assertLessEqual(len(bands), 1,
                             f"the README states more than one runtime band: {sorted(bands)}")

    def test_the_change_panel_baseline_field_is_the_one_the_page_branches_on(self):
        # renderReferenceChange branches on snapshot.baseline === 'recomputed'.
        # Changing that string to anything else flips the panel to the claim a
        # reviewer caught it making, and nothing read it.
        snapshot = json.loads((PROOF / "reference-snapshot-2026-09-21.json")
                              .read_text(encoding="utf-8"))
        self.assertEqual(snapshot.get("baseline"), "recomputed",
                         "the snapshot no longer declares that its states are a recomputation, so "
                         "the page will call them the receipt published that day")
        note = snapshot.get("baseline_note") or ""
        self.assertIn("not the receipt published", note,
                      "the snapshot's own note no longer states what it is a recomputation of")
        source = (BELL / "site" / "integrity.js").read_text(encoding="utf-8")
        self.assertIn("snapshot.baseline === 'recomputed'", source,
                      "the page stopped branching on the field this test pins")

    def test_the_boundary_check_count_is_the_same_in_both_documents(self):
        # judge.html's "All 8 checks pass" is pinned to the verifier's output;
        # README's "8 boundary checks" was free. Same figure, two files, one
        # pinned - this repository's named signature defect.
        page = flowed(judge_text())
        stated = re.search(r"All (\d+) checks pass", page)
        self.assertIsNotNone(stated, "the judge page stopped stating the boundary check count")
        self.assertRegex(flowed(readme_text()), rf"\b{stated.group(1)} boundary checks",
                         "the README states a different number of boundary checks")

    def test_the_cold_run_figure_sits_inside_the_stated_band(self):
        # "a first run on a cold machine was measured at 10.3 seconds" could
        # say 1.3 and stay green, beside a band it is supposed to justify.
        page = flowed(judge_text())
        band = re.search(r"between (\d+\.\d+) and (\d+\.\d+) seconds", page)
        cold = re.search(r"cold machine was measured at (\d+\.\d+) seconds", page)
        self.assertIsNotNone(cold, "the judge page stopped naming the cold run it widened for")
        self.assertTrue(float(band.group(1)) <= float(cold.group(1)) <= float(band.group(2)),
                        f"the cold run figure {cold.group(1)} is outside the band it justifies")

    def test_the_excluded_majority_is_measured_and_stated(self):
        # 547 references - 69% of the catalogue - were excluded from the rate,
        # correctly, and that exclusion was everything the product said about
        # them. The measurement is published now, so it is pinned like every
        # other number on that page.
        lens = BASE_RATE.get("single_representation_lens")
        self.assertIsNotNone(lens, "base_rate no longer measures the excluded majority")
        self.assertEqual(lens["references"], BASE_RATE["excluded_single_representation"],
                         "the lens and the exclusion count describe different populations")
        self.assertEqual(lens["incomplete_market_fields"] + 0, lens["reasons"].get(
            "MARKET_FIELDS_MISSING", 0))
        self.assertEqual(lens["fully_reported"],
                         lens["references"] - lens["with_a_named_gap_or_finding"])
        flow = flowed(judge_text())
        self.assertRegex(
            flow, rf"\b{lens['incomplete_market_fields']} of the {lens['references']} carry at "
                  r"least one field",
            "the judge page states a different count for the excluded majority")
        self.assertRegex(flow, rf"\b{lens['fully_reported']} report price, market cap and volume")

if __name__ == "__main__":
    unittest.main()

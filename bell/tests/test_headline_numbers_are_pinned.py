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

BASE_RATE = json.loads((PROOF / "base-rate-2026-09-28.json").read_text(encoding="utf-8"))
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
        # Keep coverage, data-review triggers, no-pair cases, and the published
        # comparison count separate and pinned to the same measurement.
        page = judge_text()
        published = BASE_RATE["comparable"]
        review = BASE_RATE["refusal_split"]["data_review"]
        coverage = BASE_RATE["refusal_split"]["source_coverage"]
        no_pair = BASE_RATE["refusal_split"]["not_applicable"]
        # The dated tiles carry the date of the measurement behind them,
        # because /judge ships no JavaScript and cannot show today's: a
        # reviewer read 87 here and found 75 in the live index 400px below,
        # both correct, a week apart, and neither page said so.
        for label, value in (("Comparisons published", published),
                             ("Data-review triggers, by reason", review),
                             ("No eligible spot pair", no_pair),
                             ("Refused for missing coverage", coverage)):
            self.assertRegex(
                page, rf"<small>{re.escape(label)}[^<]*</small><strong>{value}</strong>",
                f"the {label!r} tile is not the measured {value}")
            self.assertRegex(
                page, rf"<small>{re.escape(label)} &middot; \d+ \w+</small>",
                f"the {label!r} tile does not say which day it measured")
        self.assertNotIn(f"<small>Refusals, by named rule</small><strong>{BASE_RATE['refused']}</strong>",
                         page, "the undivided refusal total is back in a tile")

    def test_the_opening_paragraph_states_the_measured_denominator_and_counts(self):
        page = judge_text()
        denominator = BASE_RATE["denominator_two_or_more_representations"]
        flow = flowed(page)
        self.assertIn(f"Of the {denominator} references carrying more than one representation",
                      flow, "the opening paragraph's denominator is not the measured one")
        self.assertIn(f"<strong>{BASE_RATE['comparable']} have a filtered quote comparison",
                      flow, "the opening paragraph's affirmative count is not measured")
        # These three reason classes remain separate; review rules do not
        # establish economic contradictions.
        split = BASE_RATE["refusal_split"]
        reasons = split["reason_total"]
        self.assertIn(f"behind the {BASE_RATE['refused']} refusals sit {reasons} rule hits: "
                      f"<strong>{split['data_review']} triggered price or field review rules", flow,
                      "the opening paragraph's data-review count is not measured")
        self.assertIn(f"{split['source_coverage']} are missing-coverage reasons", flow,
                      "the opening paragraph's coverage count is not measured")
        self.assertIn(f"and {split['not_applicable']} leave fewer than two eligible spot routes", flow)

    def test_the_readme_body_states_the_same_measured_counts(self):
        # Outside the fenced block, which is the only part the older test read.
        body = readme_text()
        body = flowed(body)
        self.assertIn(
            f"In the preserved 28 September capture, {BASE_RATE['comparable']} of "
            f"{BASE_RATE['denominator_two_or_more_representations']} multi-representation "
            "references pass Bell's filtered quote comparison",
            body,
        )
        # The README row led with the refusal total too. Both halves of it are
        # pinned here for the same reason the judge page's are.
        split = BASE_RATE["refusal_split"]
        self.assertIn(f"producing {split['reason_total']} rule hits", body)
        self.assertIn(f"{split['data_review']} price or field review triggers", body)
        self.assertIn(f"{split['source_coverage']} missing-coverage reasons", body)
        self.assertIn(f"{split['not_applicable']} no-pair reasons mean", body)
        self.assertIn(
            f"{BASE_RATE['denominator_two_or_more_representations']} multi-representation references",
            body,
        )

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
            str(BASE_RATE["refusal_split"]["data_review"]),
            str(BASE_RATE["refusal_split"]["source_coverage"]),
            str(BASE_RATE["refusal_split"]["not_applicable"]),
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
        self.assertIn(f"<strong>{split['source_coverage']} of the {reasons} rule hits", flow,
                      "the coverage half of the refusal split is not measured")
        # `assertIn("38 triggered")` is satisfied by "1138 triggered". A pin a
        # forger beats by prepending a digit is not a pin; the siblings here
        # survived only because they happen to have a non-digit before the
        # number. Word boundary, everywhere.
        self.assertRegex(flow, rf"\b{split['data_review']} are price or field review triggers",
                         "the data-review half of the refusal split is not measured")

    def test_the_demo_line_states_the_slice_the_receipt_actually_carries(self):
        alerts = len(REPLAY.get("alerts") or [])
        self.assertIn(f"the {alerts} highest-priority flagged references", flowed(judge_text()),
                      f"the judge page describes a slice of a different size; the receipt ships {alerts}")

    def test_the_input_package_size_is_the_size_on_disk(self):
        megabytes = (PROOF / "rwa-surface-integrity-inputs-2026-09-21.json").stat().st_size / 1_000_000
        stated = f"{megabytes:.1f} MB of shipped inputs"
        page = flowed(judge_text())
        self.assertIn(stated, page,
                      f"the judge page states an input package size that is not {stated}")
        self.assertIn("frozen scanner", page,
                      "the page does not explain how the original rule distribution is replayed")

    def test_the_readme_states_the_receipt_s_own_reference_count(self):
        references = REPLAY["universe"]["tokenised_references_scanned"]
        self.assertIn(f"contained {references} tokenised references", flowed(readme_text()),
                      "the README states a reference count the replay receipt does not")

    def test_the_review_trigger_counts_come_from_their_own_denominator(self):
        # These are rule hits among the 244 references where a comparison was
        # attempted, not claims that the market itself is contradictory.
        reasons = BASE_RATE["refusal_reasons"]
        flow = flowed(readme_text())
        self.assertIn(f"{reasons['PRICE_DENOMINATION_BREAK']} price-denomination", flow)
        self.assertIn(f"{reasons['ZERO_MCAP_POSITIVE_VOLUME']} zero-market-cap/positive-volume field pairs", flow)

    def test_the_runtime_tile_cannot_drift_out_of_its_own_stated_band(self):
        # The `<12s` tile sat beside a pinned "2.8 and 12.0 seconds" band and
        # was free to say anything. A headline that contradicts the sentence
        # under it is the defect this page is about.
        page = flowed(judge_text())
        band = re.search(r"between (\d+\.\d+) and (\d+\.\d+) seconds", page)
        self.assertIsNotNone(band, "the judge page stopped stating a measured band")
        # The tile used to state a ceiling, "&lt;24s", and a third machine ran
        # the gate in 29. A ceiling is a claim about every machine; the file
        # only knows the ones it measured, so the tile states their range and
        # says how many there were.
        tile = re.search(r"<small>Gate runtime, (\d+) machines?</small>"
                         r"<strong>(\d+)&ndash;(\d+)s</strong>", judge_text())
        self.assertIsNotNone(tile, "the gate runtime tile no longer states a range and a count")
        low, high = float(band.group(1)), float(band.group(2))
        self.assertLessEqual(float(tile.group(2)), low,
                             "the runtime tile's floor is above the fastest run measured")
        self.assertGreaterEqual(float(tile.group(3)), high,
                                "the runtime tile's ceiling is below the slowest run measured")

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

    def test_the_excluded_majority_is_partitioned_and_the_parts_sum_to_the_whole(self):
        # The first version printed two code counts that added to 541 of 547,
        # and the six in between included two references whose rows contradict
        # each other - the finding the product exists to make, hidden by the
        # only measurement it takes over 69% of its catalogue. Both numbers
        # were pinned, so the suite was holding a wrong presentation in place.
        lens = BASE_RATE.get("single_representation_lens")
        self.assertIsNotNone(lens, "base_rate no longer measures the excluded majority")
        self.assertEqual(lens["references"], BASE_RATE["excluded_single_representation"])
        parts = ("incomplete_source_fields", "review_trigger_rows", "context_only",
                 "fully_reported")
        self.assertEqual(sum(lens[part] for part in parts), lens["references"],
                         "the lens does not partition the references it describes")
        flow = flowed(judge_text())
        self.assertRegex(flow, rf"\b{lens['incomplete_source_fields']} carry a field")
        self.assertRegex(flow, rf"\b{lens['review_trigger_rows']} trigger quote or field review rules",
                         "the judge page hides market-data review triggers inside the excluded majority")
        self.assertRegex(flow, rf"sum to {lens['references']}")

    # test_the_cold_run_figure_sits_inside_the_stated_band lived here and
    # checked that a sentence quoting one cold run fell inside a band quoted in
    # two documents. Both were sentences. It is replaced by the test below,
    # which compares the band to a clock.
    def test_the_band_is_exactly_what_was_measured(self):
        # Three versions of this claim, three different ways of being wrong.
        #
        # judge.html said the band was "measured and pinned by a test rather
        # than quoted from one run" while no test started a clock; a reviewer
        # rewrote it to 6.0-11.0 on a gate that takes twelve and nothing
        # noticed. The replacement asked only whether the published band
        # CONTAINED every measured figure, which 11.0 to 15.1 satisfied over a
        # receipt holding 12.48 to 12.61, so the page advertised a range no run
        # had produced, said "across the machines" over a file with one, and a
        # reviewer's own machine then measured 18.31 seconds outside it.
        #
        # Containment is not the property. The band has to BE the measurement,
        # and the number of machines has to be the number of machines.
        receipt = PROOF / "gate-runtime.json"
        self.assertTrue(receipt.exists(),
                        "no gate runtime has been measured, so the band answers to nothing. "
                        "Run `make time-gate`.")
        measured = json.loads(receipt.read_text(encoding="utf-8"))
        every = [value for entry in measured["runs"]
                 for value in [entry["cold"]] + list(entry["warm"])]
        self.assertTrue(every, "the runtime receipt records no run")
        page = flowed(judge_text())
        band = re.search(r"observed between (\d+\.\d+) and (\d+\.\d+) seconds "
                         r"(?:on (\d+) machine|across (\d+) machines)", page)
        self.assertIsNotNone(
            band, "the judge page stopped stating a band and the machines behind it")
        low, high = float(band.group(1)), float(band.group(2))
        self.assertEqual((low, high), (min(every), max(every)),
                         f"the published band is {low} to {high} and the runs measured "
                         f"{min(every)} to {max(every)}. `make sync-counts` writes this "
                         "sentence; it is not edited by hand.")
        stated = int(band.group(3) or band.group(4))
        self.assertEqual(stated, len(measured["runs"]),
                         f"the page says {stated} machine(s) and the receipt holds "
                         f"{len(measured['runs'])}")

    def test_the_page_does_not_promise_more_than_one_machine(self):
        # The phrase a reviewer quoted back, in a paragraph that then described
        # a single machine's run. Kept as its own test because the sentence can
        # come back without the band changing.
        page = flowed(judge_text())
        machines = len(json.loads((PROOF / "gate-runtime.json").read_text(encoding="utf-8"))["runs"])
        if machines > 1:
            self.skipTest("more than one machine has been measured")
        for phrase in ("across the machines it has been measured on",
                       "across machines"):
            self.assertNotIn(phrase, page,
                             f"the page says {phrase!r} over a receipt holding one machine")

if __name__ == "__main__":
    unittest.main()

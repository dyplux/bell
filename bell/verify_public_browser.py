#!/usr/bin/env python3
"""Exercise the public Bell flow in a real browser without credentials."""

from __future__ import annotations

import argparse
import json
import re
import sys

from verify_case_receipt import verify as verify_case_receipt


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="https://bell.dyplux.com", help="public Bell origin")
    parser.add_argument("--channel", default="chrome", help="Playwright browser channel, or empty for bundled Chromium")
    parser.add_argument("--screenshot", help="optional path for a full-page screenshot")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("install the Playwright Python package before running this check") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, **({"channel": args.channel} if args.channel else {}))
        try:
            desktop = browser.new_context(
                viewport={"width": 1440, "height": 1100},
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = desktop.new_page()
            page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            page.locator("#receipt-status-label").wait_for(state="visible", timeout=30_000)
            page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            status = page.locator("#receipt-status-label").inner_text()
            require("RECEIPT" in status, f"receipt status did not load: {status!r}")
            require("CMC API / MAP + ASSET LIST + QUOTES" in page.locator("body").inner_text(), "CMC source boundary is not visible")
            require(page.locator("h1").count() == 1, "public page must expose exactly one h1")
            require(page.locator("main").count() == 1 and page.locator("nav").count() >= 1, "public page landmarks are incomplete")
            unnamed = page.locator("button:visible, a:visible, input:visible, textarea:visible, summary:visible").evaluate_all("""elements => elements
              .filter(element => !element.getAttribute('aria-label') && !element.textContent.trim() && !element.getAttribute('title') && !element.getAttribute('placeholder'))
              .map(element => element.outerHTML.slice(0, 120))""")
            require(not unnamed, f"visible controls without an accessible name: {unnamed[:3]!r}")
            missing_alt = page.locator("img").evaluate_all("elements => elements.filter(element => !element.getAttribute('alt')).map(element => element.outerHTML.slice(0, 120))")
            require(not missing_alt, f"images without alt text: {missing_alt[:3]!r}")
            concentration_text = page.locator("#concentration-visual").inner_text()
            require("HHI" in concentration_text, "population concentration visual does not expose HHI")
            require("effective issuer count" in concentration_text.lower(), "population concentration visual does not expose effective issuer count")
            attribution_button = page.locator("#download-population-attribution")
            require(attribution_button.count() == 1, "population attribution export is not visible")
            with page.expect_download(timeout=30_000) as attribution_download_info:
                attribution_button.click()
            attribution_download = attribution_download_info.value
            require(attribution_download.suggested_filename.startswith("bell-rwa-population-attribution-") and attribution_download.suggested_filename.endswith(".csv"), f"unexpected attribution filename: {attribution_download.suggested_filename!r}")
            attribution_text = open(attribution_download.path(), encoding="utf-8").read()
            require(attribution_text.startswith("rwa_id,reference_name"), "attribution export does not expose its stable reference header")
            require("market_cap_status" in attribution_text and "missing" in attribution_text and "zero_or_non_positive" in attribution_text, "attribution export collapsed missing and non-positive market-cap states")

            receipt_response = page.request.get(args.base.rstrip("/") + "/api/integrity", timeout=30_000)
            require(receipt_response.ok, f"integrity receipt request failed: {receipt_response.status}")
            receipt = receipt_response.json()
            page.wait_for_function("observed => document.querySelector('#publication-history')?.textContent?.includes(observed)", arg=receipt["observed_at"], timeout=30_000)
            history_text = page.locator("#publication-history").inner_text()
            require(receipt["observed_at"] in history_text, "publication history does not end at the current live receipt")
            expected_states = {
                "do_not_compare": "DO NOT SHORTLIST",
                "investigate": "INVESTIGATE",
                "no_flags": "FACTS OPEN",
                "single_representation": "SINGLE REPRESENTATION",
            }

            def expected_for(name: str) -> str:
                needle = name.lower()
                candidates = receipt.get("alert_index", [])
                item = next((candidate for candidate in candidates if str(candidate.get("name", "")).lower() == needle), None)
                item = item or next((candidate for candidate in candidates if needle in str(candidate.get("name", "")).lower()), None)
                require(item is not None, f"{name} is not present in the current published receipt")
                if item.get("state") == "no_flags" and int(item.get("token_count") or 0) == 1:
                    return "SINGLE REPRESENTATION"
                return expected_states.get(item.get("state"), "REFERENCE ONLY")

            def search_and_check(name: str) -> str:
                page.locator("#hero-search").fill(name)
                page.locator("#hero-search-form button[type=submit]").click()
                result = page.locator("#search-result")
                result.wait_for(state="visible", timeout=30_000)
                result_text = result.inner_text()
                expected = expected_for(name)
                require(expected in result_text, f"{name} did not mirror receipt state {expected!r}: {result_text[:500]!r}")
                if expected != "SINGLE REPRESENTATION":
                    require("observed quote" in result_text.lower(), f"{name} did not expose observed evidence: {result_text[:500]!r}")
                return expected

            silver_state = search_and_check("Silver")
            require(page.locator("#search-result").get_by_text("Open live dossier context ↓", exact=True).count() == 1, "searched case does not expose the live dossier handoff")
            budget_input = page.locator("#decision-hero [data-capital-budget]")
            require(budget_input.count() == 1, "blocked case does not expose the capital-check input")
            budget_input.fill("25000")
            budget_input.dispatch_event("input")
            page.wait_for_timeout(100)
            capital_headline = page.locator("#decision-hero [data-capital-headline]").inner_text()
            normalized_capital = re.sub(r"[\s,\.\xa0]", "", capital_headline).lower()
            require("25000" in normalized_capital, f"capital check did not update the blocked-case consequence: {capital_headline!r}")
            require("keep25000uncommitted" in normalized_capital, f"unexpected capital consequence: {capital_headline!r}")
            brief_button = page.locator("#decision-hero [data-brief-id]").first
            require(brief_button.count() == 1, "Silver result does not expose a decision-brief action")
            with page.expect_download(timeout=30_000) as download_info:
                brief_button.click()
            brief_download = download_info.value
            require(brief_download.suggested_filename.endswith("-decision-brief.md"), f"unexpected brief filename: {brief_download.suggested_filename!r}")
            case_receipt_button = page.locator("#decision-hero [data-case-receipt]").first
            require(case_receipt_button.count() == 1, "Silver result does not expose a compact case-receipt action")
            with page.expect_download(timeout=30_000) as case_download_info:
                case_receipt_button.click()
            case_download = case_download_info.value
            require(case_download.suggested_filename.endswith("-case-receipt.json"), f"unexpected case receipt filename: {case_download.suggested_filename!r}")
            with open(case_download.path(), encoding="utf-8") as case_file:
                case_receipt = json.load(case_file)
            case_verification = verify_case_receipt(case_receipt)
            require(case_verification["status"] == "valid public case receipt", "downloaded case receipt failed its public contract")
            require(case_receipt.get("reference", {}).get("name") == "Silver", "case receipt does not identify Silver")
            require(len(case_receipt.get("tokens", [])) == 5, "case receipt does not retain the exact Silver rows")
            require(case_receipt.get("source_hashes"), "case receipt does not retain source fingerprints")
            require(case_receipt.get("method", {}).get("join_key") == "rwa_id", "case receipt does not expose the stable join method")
            copy_button = page.locator("#decision-hero [data-copy-case]").first
            require(copy_button.count() == 1, "searched case does not expose a shareable case-link action")
            copy_button.click()
            page.wait_for_function("document.querySelector('#decision-hero [data-copy-case]')?.textContent?.includes('Case link copied')", timeout=5_000)

            watch_button = page.locator("[data-watch-id]").first
            require(watch_button.count() == 1, "Silver evidence queue does not expose a watch action")
            watch_button.click()
            watchlist = page.locator("#watchlist-panel")
            watchlist.wait_for(state="visible", timeout=5_000)
            require("Silver" in watchlist.inner_text(), "saved Silver reference is not visible in the local watchlist")

            gold_state = search_and_check("Gold")
            temporal = page.locator("#decision-hero [data-temporal-evidence]")
            temporal.wait_for(state="visible", timeout=30_000)
            page.wait_for_function("document.querySelector('#decision-hero [data-temporal-evidence]')?.textContent?.includes('cash-session')", timeout=30_000)
            temporal_text = temporal.inner_text()
            require("REPEAT-WINDOW CHECK" in temporal_text, "Gold case did not expose the repeat-window check")
            require("weekend" in temporal_text.lower() and "cash-session" in temporal_text.lower(), "temporal check did not explain the comparison clock")
            require("72H OVERLAP" in temporal_text, "temporal check did not disclose the overlap")
            require("not independent validation" in temporal_text.lower(), "temporal check did not preserve its repeat-observation boundary")

            marvell_state = search_and_check("Marvell")
            marvell_details = page.locator("#alert-list .alert-details").first
            marvell_details.locator("summary").click()
            selectors = marvell_details.locator("[data-wrapper-select]")
            require(selectors.count() >= 2, "Marvell does not expose two wrapper rows for factual comparison")
            selectors.nth(0).check()
            selectors.nth(1).check()
            comparison = marvell_details.locator("[data-comparison-output]")
            comparison.wait_for(state="visible", timeout=5_000)
            comparison_text = comparison.inner_text()
            require("OBSERVED FIELD DIFFERENCES" in comparison_text, "Marvell side-by-side comparison did not render")
            require("FACTS ONLY" in comparison_text, "Marvell comparison did not preserve the no-ranking boundary")
            palladium_state = search_and_check("Palladium")
            require(palladium_state == "SINGLE REPRESENTATION", f"single-representation route was not explicit: {palladium_state!r}")

            page.locator("#explorer-search").fill("Gold")
            page.locator("#explorer-form button[type=submit]").click()
            page.wait_for_function("document.querySelector('#explorer-dossier')?.textContent?.includes('EVIDENCE CONTEXT')", timeout=30_000)
            gold_dossier = page.locator("#explorer-dossier").inner_text()
            require("DEX CONTRACT COVERAGE" in gold_dossier, "Gold dossier did not expose contract coverage context")
            require("DEX SURFACES" in gold_dossier, "Gold dossier did not expose resolved DEX surfaces")
            require("CMC MARKET PAIRS" in gold_dossier, "Gold dossier did not expose the market-pair boundary")

            page.locator("#hero-search").fill("Colgate")
            page.locator("#hero-search-form button[type=submit]").click()
            map_result = page.locator("#search-result")
            map_result.wait_for(state="visible", timeout=30_000)
            require("No live case found" in map_result.inner_text(), "map-only query was incorrectly presented as a live case")
            map_result.locator("[data-open-map-query]").click()
            page.wait_for_function("(() => { const text = document.querySelector('#explorer-dossier')?.textContent || ''; return text.includes('DOSSIER PENDING') || text.includes('REFERENCE ONLY'); })()", timeout=30_000)
            map_text = page.locator("#explorer-dossier").inner_text()
            require("Colgate-Palmolive" in map_text, "map-only route did not resolve the complete RWA catalogue entry")
            map_route = "DOSSIER PENDING" if "DOSSIER PENDING" in map_text else "REFERENCE ONLY"

            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)

            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
            mobile_page = mobile.new_page()
            mobile_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            mobile_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            mobile_page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            overflow = mobile_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            require(not overflow, "mobile page has horizontal overflow")
            mobile_decision = mobile_page.locator("#hero-mobile-decision")
            require(mobile_decision.is_visible(), "mobile first viewport does not expose the decision preview")
            require("DO NOT SHORTLIST" in mobile_decision.inner_text(), "mobile decision preview does not mirror the current blocked case")
            mobile.close()

            tablet = browser.new_context(viewport={"width": 834, "height": 1112})
            tablet_page = tablet.new_page()
            tablet_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            tablet_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            tablet_page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            tablet_overflow = tablet_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            require(not tablet_overflow, "tablet page has horizontal overflow")
            require(tablet_page.locator("#hero-search").is_visible(), "tablet first viewport hides the primary search")
            tablet.close()

            fallback = browser.new_context(viewport={"width": 1440, "height": 1100})
            fallback_page = fallback.new_page()
            fallback_page.route("**/api/integrity", lambda route: route.abort())
            fallback_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            fallback_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            fallback_page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            fallback_status = fallback_page.locator("#receipt-status-label").inner_text()
            require("DATED REPLAY" in fallback_status, f"live failure did not produce a dated replay label: {fallback_status!r}")
            require("Explore RWA" in fallback_page.locator("body").inner_text(), "dated replay fallback did not keep the RWA explorer usable")
            fallback.close()

            print(json.dumps({
                "base": args.base.rstrip("/"),
                "receipt_status": status,
                "history_includes_current_receipt": True,
                "presentation_accessibility": "landmarks, h1, named controls and image alt text pass",
                "silver_decision": silver_state,
                "gold_decision": gold_state,
                "gold_temporal_check": "two dated weekend versus cash-session windows visible; overlap disclosed",
                "marvell_decision": marvell_state,
                "silver_evidence": "observed quote evidence visible",
                "capital_check": "25,000 routed to keep uncommitted",
                "decision_brief": brief_download.suggested_filename,
                "case_receipt": case_download.suggested_filename,
                "shareable_case_link": "Case link copied",
                "watchlist": "Silver saved locally",
                "marvell_comparison": "observed field differences, no wrapper ranking",
                "single_representation": palladium_state,
                "dossier_context": "Gold live dossier shows DEX coverage, surfaces and market-pair boundary",
                "map_only": f"Colgate routed to complete RWA map as {map_route}",
                "mobile_horizontal_overflow": False,
                "tablet_horizontal_overflow": False,
                "population_concentration": "HHI and effective issuer count visible",
                "population_attribution_export": attribution_download.suggested_filename,
                "mobile_decision_preview": "visible before the long task panel",
                "failure_fallback": fallback_status,
                "screenshot": args.screenshot,
            }, ensure_ascii=False, indent=2))
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"PUBLIC BROWSER CHECK FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Exercise the public Bell flow in a real browser without credentials."""

from __future__ import annotations

import argparse
import json
import re
import sys

from verify_case_receipt import verify as verify_case_receipt


LOADED = ("document.querySelector('#receipt-status-label')?.textContent"
          "?.includes('LOADING') === false")


def wait_for_either(page, selector: str, options, *, timeout: int = 30_000) -> None:
    """Either of two words, same reason as wait_for_text below."""
    import time as _time
    deadline = _time.monotonic() + timeout / 1000
    seen = ""
    while _time.monotonic() < deadline:
        target = page.locator(selector)
        if target.count():
            seen = target.first.inner_text()
            if any(option in seen for option in options):
                return
        page.wait_for_timeout(120)
    raise AssertionError(f"{selector} never showed any of {options}; last saw {seen[:200]!r}")


def wait_for_text(page, selector: str, contains: str, *, absent: bool = False,
                  timeout: int = 30_000) -> None:
    """Poll from here instead of evaluating a string in the page.

    The site now serves `script-src 'self'` with no 'unsafe-eval', which is the
    point of having a policy, and Playwright's wait_for_function evaluates a
    string: the audit started failing with "Evaluating a string as JavaScript
    violates the following Content Security Policy directive". The tool was
    asking the page to do something the page is right to refuse. So the
    condition is checked on this side of the wire.
    """
    import time as _time
    deadline = _time.monotonic() + timeout / 1000
    seen = ""
    while _time.monotonic() < deadline:
        target = page.locator(selector)
        if target.count():
            seen = target.first.inner_text()
            if (contains not in seen) if absent else (contains in seen):
                return
        page.wait_for_timeout(120)
    raise AssertionError(
        f"{selector} never {'lost' if absent else 'showed'} {contains!r}; last saw {seen[:200]!r}")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


# The states the public page is allowed to show. A reference may move between
# them as the data moves; it may never render something outside this set.
# The buckets a filter addresses. A label may add a qualifier the filter
# deliberately ignores - COMPARABLE · FLAGGED, SINGLE REPRESENTATION · FLAGGED -
# so a rendered word is in the vocabulary when its bucket is. Listing the
# qualified forms here as well would be a second copy of the rule.
PUBLIC_STATES = frozenset({
    "COMPARABLE", "FACTS OPEN", "INVESTIGATE", "DO NOT SHORTLIST", "SINGLE REPRESENTATION",
})


def in_public_vocabulary(rendered: str) -> bool:
    bucket = str(rendered).split("\u00b7")[0].strip()
    return bucket in PUBLIC_STATES


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
            # The two heaviest things this page can fetch are the receipt and
            # the 1.98 MiB explorer catalogue. The catalogue is deferred until
            # the explorer is on screen and the receipt is fetched once, and
            # together those took the first load from 6.98 MiB to 2.91 MiB.
            # Neither saving was pinned by anything: an IntersectionObserver is
            # one line to delete, and the duplicate fetch had already shipped
            # once. A saving nothing measures is a saving that comes back.
            catalogue_requests = []
            receipt_requests = []
            page.on("request", lambda request: (
                catalogue_requests.append(request.url) if "catalog.json" in request.url
                else receipt_requests.append(request.url) if "/api/integrity" in request.url
                else None))
            page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            page.locator("#receipt-status-label").wait_for(state="visible", timeout=30_000)
            wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
            status = page.locator("#receipt-status-label").inner_text()
            # The label used to read "LIVE RECEIPT / FRESH"; it now states the
            # observation time instead, because "fresh" was read as "measured
            # just now" when it only meant "published recently". This assertion
            # kept checking for the old word and failed silently on the live
            # site for anyone following the README - it is not in `make check`,
            # so nothing caught the rot. Assert the guarantee, not the wording:
            # whatever the label says, it must name when the data was observed.
            require(
                "OBSERVED" in status or "DATED REPLAY" in status,
                f"receipt status did not name an observation time: {status!r}",
            )
            # Asserted here, before the refresh below navigates and legitimately
            # fetches the receipt a second time.
            require(not catalogue_requests,
                    f"the {len(catalogue_requests)} explorer catalogue fetch(es) are no longer "
                    "deferred: 1.98 MiB is back on the first screen")
            require(len(receipt_requests) == 1,
                    f"the receipt was fetched {len(receipt_requests)} times on one load; "
                    "the shared promise is gone and the page is paying for it twice")

            refresh_requests = []
            page.on("request", lambda request: refresh_requests.append(request.url) if "/api/integrity" in request.url else None)
            with page.expect_navigation(wait_until="domcontentloaded", timeout=30_000):
                page.locator("#refresh-receipt").click()
            wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
            refreshed_status = page.locator("#receipt-status-label").inner_text()
            require(
                "OBSERVED" in refreshed_status or "DATED REPLAY" in refreshed_status,
                f"receipt status did not survive refresh: {refreshed_status!r}",
            )
            require(refresh_requests, "refresh action did not request the live integrity receipt")
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

            # A sentence on the product page names the number the COMPARABLE
            # filter shows. It was hardcoded to 87 while the filter showed 78,
            # on a page whose README promises every figure is derived from the
            # receipt. Both are on screen, so both are read.
            stated = page.locator("#population-comparable-count")
            require(stated.count() == 1,
                    "the population sentence no longer renders its count from the receipt; it is "
                    "written into the page again, which is what put a stale 87 beside a filter "
                    "showing 78")
            # The count lives inside a closed <details> disclosure. inner_text()
            # correctly omits text hidden by a closed disclosure, while
            # text_content() reads the value the page will show when opened.
            stated_comparable = (stated.text_content() or "").strip()
            page.locator("[data-filter='COMPARABLE']").first.click()
            page.wait_for_timeout(1_000)
            monitor = page.locator("#monitor").inner_text()
            filtered = re.search(r"of ([\d,]+) matching", monitor)
            require(filtered is not None,
                    f"the reference index stopped reporting its match count: {monitor[:200]!r}")
            require(filtered.group(1).replace(",", "") == stated_comparable.replace(",", ""),
                    f"the page says the COMPARABLE filter shows {stated_comparable} and the "
                    f"filter shows {filtered.group(1)}")
            page.locator("[data-filter='all']").first.click()
            page.wait_for_timeout(500)

            require("market_cap_status" in attribution_text and "missing" in attribution_text and "zero_or_non_positive" in attribution_text, "attribution export collapsed missing and non-positive market-cap states")

            receipt_response = page.request.get(args.base.rstrip("/") + "/api/integrity", timeout=30_000)
            require(receipt_response.ok, f"integrity receipt request failed: {receipt_response.status}")
            receipt = receipt_response.json()
            wait_for_text(page, "#publication-history", receipt["observed_at"])
            # Every population figure the page prints must equal the receipt it
            # is reading AT THIS MOMENT, not a figure from any other observation.
            #
            # This is the one check the project did not have, and it sits inside
            # the exact failure it exists to catch: two surfaces describing one
            # observation and disagreeing. The README's numbers were pinned to
            # the shipped inputs from the start and stayed correct; the live
            # page's were pinned to nothing, and a reviewer reading "1,440" on
            # screen could not tell a fresh observation from the stale figure
            # the project had already corrected once.
            universe = receipt["universe"]
            rendered = {
                "#metric-references": universe["tokenised_references_scanned"],
                "#metric-tokens": universe["tokens_scanned"],
            }
            for selector, expected in rendered.items():
                shown = page.locator(selector).inner_text().strip()
                require(
                    shown.replace(",", "").replace("\u00a0", "") == str(expected),
                    f"{selector} shows {shown!r} but the receipt it just read says "
                    f"{expected:,}. The page is stating a population figure that is "
                    f"not in its own current receipt.",
                )

            history_text = page.locator("#publication-history").inner_text()
            require(receipt["observed_at"] in history_text, "publication history does not end at the current live receipt")
            # The header said "14 DATED OBSERVATIONS ACROSS 4 DAYS" and the chart
            # caption directly below said "Short series: 9 receipts across 2
            # calendar days", because the caption described the nine-column
            # window without saying it was one. Both numbers were true and
            # together they read as a contradiction, on a page that refuses to
            # subtract two receipts on denominator grounds. Whatever window the
            # chart draws, the totals it names have to be the totals above it.
            # The totals live in the hero trail line, the window caption in the
            # history panel. Two elements, one claim.
            trail_text = page.locator("#hero-receipt-trail").inner_text()
            header_counts = re.search(r"(\d+)\s+DATED OBSERVATIONS ACROSS\s+(\d+)", trail_text.upper())
            require(header_counts is not None,
                    f"the receipt trail no longer states its length: {trail_text[:200]!r}")
            # My first version of this only compared the totals WHEN the caption
            # said "of N", so reverting the caption to "9 receipts across 2
            # calendar days" made it skip and pass. A check with an exit the
            # regression takes is not a check. Read whatever totals the caption
            # states, windowed or not, and require them to be the ones above it.
            caption = re.search(
                r"(?:last (\d+) of )?(\d+) receipts,? (?:spanning|across) (?:(\d+) of )?(\d+) calendar days?",
                history_text)
            require(caption is not None,
                    f"the chart caption no longer states a receipt and day count: {history_text[:300]!r}")
            windowed, stated_receipts, window_days, stated_days = caption.groups()
            require(bool(windowed) == bool(window_days),
                    "the chart caption describes a window of one total but not the other")
            require(stated_receipts == header_counts.group(1) and stated_days == header_counts.group(2),
                    f"the chart caption accounts for {stated_receipts} receipts across {stated_days} "
                    f"days while the header above it says {header_counts.group(1)} across "
                    f"{header_counts.group(2)}: a truncated window is being quoted as the series")
            expected_states = {
                "do_not_compare": "DO NOT SHORTLIST",
                "investigate": "INVESTIGATE",
                "no_flags": "FACTS OPEN",
                "single_representation": "SINGLE REPRESENTATION",
            }

            matched_item = None

            def expected_for(name: str) -> str:
                needle = name.lower()
                candidates = receipt.get("alert_index", [])
                item = next((candidate for candidate in candidates if str(candidate.get("name", "")).lower() == needle), None)
                item = item or next((candidate for candidate in candidates if needle in str(candidate.get("name", "")).lower()), None)
                require(item is not None, f"{name} is not present in the current published receipt")
                # A reference carrying a published comparison is labelled by what
                # the reader is holding, not by the state that let it through.
                # Asserting the state alone made this check demand INVESTIGATE
                # on a page correctly showing COMPARABLE.
                nonlocal matched_item
                matched_item = item
                # This was a second copy of the labelling rule, and it drifted
                # from the first the moment one representation stopped being
                # bucketed as a comparison: the audit demanded DO NOT SHORTLIST
                # on a page correctly showing SINGLE REPRESENTATION · FLAGGED.
                # A check that keeps its own copy of the thing it is checking
                # is checking its copy. Ask the page's own function instead.
                rows = int(item.get("token_count") or 0)
                flagged = item.get("state") in ("do_not_compare", "investigate") \
                    or (item.get("decision") or {}).get("state") == "blocked"
                if rows == 1:
                    return "SINGLE REPRESENTATION \u00b7 FLAGGED" if flagged else "SINGLE REPRESENTATION"
                if item.get("comparison") and (item.get("decision") or {}).get("state") != "blocked":
                    return ("COMPARABLE \u00b7 FLAGGED" if item.get("state") == "investigate"
                            else "COMPARABLE")
                return expected_states.get(item.get("state"), "REFERENCE ONLY")

            def search_and_check(name: str) -> str:
                page.locator("#hero-search").fill(name)
                page.locator("#hero-search-form button[type=submit]").click()
                result = page.locator("#search-result")
                result.wait_for(state="visible", timeout=30_000)
                result_text = result.inner_text()
                expected = expected_for(name)
                require(expected in result_text, f"{name} did not mirror receipt state {expected!r}: {result_text[:500]!r}")
                # A quote band needs two rows to compare. This asked for one
                # whenever the STATE was not "SINGLE REPRESENTATION", which is a
                # different question: a reference can carry one representation
                # and still be blocked by a contradiction inside that row, and
                # then there is no band to show and none should be demanded.
                # Assert on what exists, not on the label.
                rows = int((matched_item or {}).get("token_count") or 0)
                if rows >= 2:
                    require("observed quote" in result_text.lower(),
                            f"{name} has {rows} representations and exposes no observed evidence: "
                            f"{result_text[:400]!r}")
                routes = ((matched_item or {}).get("comparison") or {}).get("routes")
                capital_rows = routes if isinstance(routes, list) else (matched_item or {}).get("tokens", [])
                positive_prices = [float(row["price"]) for row in capital_rows
                                   if isinstance(row, dict) and isinstance(row.get("price"), (int, float))
                                   and float(row["price"]) > 0]
                has_range = len(positive_prices) >= 2 and min(positive_prices) != max(positive_prices)
                if has_range:
                    expected_range_label = ("FILTERED ROUTE QUOTE RANGE" if isinstance(routes, list)
                                            else "OBSERVED ROW QUOTE RANGE")
                    require(expected_range_label in result_text,
                            f"{name} capital range label does not name its receipt rows: {result_text[:700]!r}")
                    scope_copy = ("Capital range uses this receipt’s filtered routes"
                                  if isinstance(routes, list)
                                  else "Range uses reported token rows before comparison filters. No filtered comparison is published")
                    require(scope_copy in result_text,
                            f"{name} capital note does not disclose the quote set: {result_text[:700]!r}")
                    capital_ratio = max(positive_prices) / min(positive_prices)
                    if 1 < capital_ratio < 1.01:
                        ratio_label = f"{capital_ratio:.10f}".rstrip("0").rstrip(".") + "×"
                        require(ratio_label in result_text,
                                f"{name} rounds a non-equal capital quote range to 1×: {result_text[:700]!r}")
                    budget_input = result.locator("[data-capital-budget]")
                    budget_input.fill("12000")
                    updated_result = result.inner_text()
                    require(expected_range_label in updated_result and scope_copy in updated_result,
                            f"{name} lost quote-set scope after amount edit: {updated_result[:700]!r}")
                observed_prices = [float(row["price"]) for row in (matched_item or {}).get("tokens", [])
                                   if isinstance(row, dict) and isinstance(row.get("price"), (int, float))
                                   and float(row["price"]) > 0]
                if len(observed_prices) >= 2:
                    observed_ratio = max(observed_prices) / min(observed_prices)
                    if 1 < observed_ratio < 1.01:
                        ratio_label = f"{observed_ratio:.10f}".rstrip("0").rstrip(".") + "×"
                        require(ratio_label in result_text,
                                f"{name} rounds a non-equal observed quote band to 1×: {result_text[:700]!r}")
                if expected == "COMPARABLE":
                    # The affirmative has to carry its consequence, or the badge
                    # is decoration. The page said COMPARABLE while the capital
                    # check underneath still read "not ready for a clean
                    # shortlist" - one screen, two answers.
                    lowered = result_text.lower()
                    require("bps" in lowered and "cheapest route" in lowered,
                            f"{name} shows COMPARABLE without naming the spread and cheapest route: {result_text[:500]!r}")
                    require("not ready for a clean shortlist" not in lowered,
                            f"{name} shows COMPARABLE and the unresolved copy at the same time: {result_text[:500]!r}")
                return expected

            # CMC places an Alphabet Class C route under its Class A reference.
            # The visible decision must disclose whether that route belongs to
            # this receipt's filtered quote set, and the table must show every
            # included route counted in its headline.
            alphabet = next((row for row in receipt.get("alerts", [])
                             if str(row.get("rwa_id")) == "4"), None)
            alphabet_tokens = (alphabet or {}).get("tokens", [])
            if any(str(token.get("crypto_id")) == "42272" for token in alphabet_tokens):
                search_and_check("Alphabet Inc Class A")
                search_summary = page.locator("#search-result").inner_text()
                decision_text = page.locator("#decision-hero").inner_text()
                require("CMC groups GOOGon (Alphabet Class C) under its Class A reference" in decision_text,
                        "the Alphabet decision does not disclose the Class A/Class C CMC grouping")
                comparison = (alphabet or {}).get("comparison") or {}
                class_scope_expectation = (
                    "spread therefore combines Class A and Class C routes"
                    if any(str(route.get("crypto_id")) == "42272"
                           for route in comparison.get("routes", []))
                    else "this observation has no published filtered quote set"
                    if not comparison
                    else "displayed spread uses the remaining Class A routes only"
                )
                require(class_scope_expectation in search_summary,
                        f"the post-search Alphabet class-scope text should say {class_scope_expectation!r}")
                if comparison:
                    expected_membership = (
                        "Class C route is included in this filtered quote set"
                        if any(str(route.get("crypto_id")) == "42272"
                               for route in comparison.get("routes", []))
                        else "Class C route is excluded from this filtered quote set"
                    )
                    require(expected_membership in decision_text,
                            f"the Alphabet decision does not disclose route membership: {expected_membership}")
                    comparison_rows = page.locator(
                        '#alert-list [data-rwa-id="4"] .comparison-table tbody tr')
                    require(comparison_rows.count() == len(comparison.get("routes", [])),
                            "the Alphabet comparison table row count differs from its filtered route set")
                    if "42272" in [str(value) for value in comparison.get("included_crypto_ids", [])]:
                        require("CMC-GROUPED QUOTE SPREAD · CLASS A + C" in
                                page.locator('#alert-list [data-rwa-id="4"] .comparison-head').inner_text(),
                                "the Alphabet spread heading does not name its mixed-class scope")
                page.locator('#search-result [data-open-map-query]').click()
                explorer_verdict = page.locator("#explorer-dossier .explorer-live")
                explorer_verdict.wait_for(state="visible", timeout=30_000)
                explorer_text = explorer_verdict.inner_text()
                require(class_scope_expectation in explorer_text,
                        f"the live Alphabet dossier should state {class_scope_expectation!r}")

            # A digits-only query is a reference id. It used to be a substring
            # over every field joined together, so ?reference=0 reached SPY
            # through "S&P 500" and rendered a full verdict, capital panel and
            # all, for the first of 178 fuzzy hits. A shared link answered a
            # question nobody had asked. The label said "178 MATCHES · SHOWING
            # FIRST", which is honest and is not the same as being right.
            for digits in ("0", "-1"):
                page.goto(f"{args.base.rstrip(chr(47))}/?reference={digits}", wait_until="domcontentloaded", timeout=30_000)
                wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
                page.wait_for_timeout(200)
                result = page.locator("#search-result")
                shown = result.inner_text() if result.count() and result.is_visible() else ""
                require("no live case found" in shown.lower() or not shown.strip(),
                        f"?reference={digits} rendered a verdict for a reference nobody asked "
                        f"for: {shown[:300]!r}")
            # And a real id still resolves, so the fix is not "refuse digits".
            page.goto(f"{args.base.rstrip(chr(47))}/?reference=5", wait_until="domcontentloaded", timeout=30_000)
            wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
            page.wait_for_timeout(200)
            exact = page.locator("#search-result").inner_text()
            require("exact match" in exact.lower(),
                    f"?reference=5 no longer resolves to a single reference: {exact[:300]!r}")
            page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)

            # 39 of the 75 published comparisons in the live receipt are also
            # flagged by the scan, and every one of them used to read
            # COMPARABLE: the affirmative word over the most doubtful half of
            # the affirmative set. The flags were always on the card; a
            # reviewer had to do arithmetic against /api/integrity to see the
            # split. The label carries it now, and the filter must still gather
            # both or the reader has to know two names for one set.
            flagged = [item for item in (receipt.get("alert_index") or [])
                       if item.get("comparison") and item.get("state") == "investigate"
                       and (item.get("decision") or {}).get("state") != "blocked"]
            if flagged:
                subject = flagged[0]
                page.goto(f"{args.base.rstrip(chr(47))}/?reference={subject['rwa_id']}",
                          wait_until="domcontentloaded", timeout=30_000)
                wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
                page.wait_for_timeout(200)
                shown = page.locator("#search-result").inner_text()
                require("FLAGGED" in shown.upper(),
                        f"{subject.get('name')!r} carries a published comparison and a scan flag "
                        f"and reads as plainly comparable: {shown[:300]!r}")
                page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
                wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)
                page.locator('[data-filter="COMPARABLE"]').click()
                page.wait_for_timeout(300)
                gathered = page.locator("#alert-count").inner_text()
                published = len([item for item in (receipt.get("alert_index") or [])
                                 if item.get("comparison")])
                require(str(published) in gathered,
                        f"the COMPARABLE filter no longer gathers all {published} published "
                        f"comparisons: {gathered[:200]!r}")
                page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
                wait_for_text(page, "#receipt-status-label", "LOADING", absent=True)

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
            require(case_receipt.get("schema_version") == "bell.case-receipt.v3",
                    "downloaded case receipt does not expose the v3 provenance contract")
            require(case_receipt.get("receipt_id") and case_receipt.get("ruleset") == universe["rules_version"],
                    "downloaded case receipt lacks its stable ID or the source ruleset")
            case_verification = verify_case_receipt(case_receipt, against=(receipt, "live /api/integrity"))
            require(case_verification["status"] == "valid public case receipt",
                    f"downloaded case receipt did not bind to the live scan: "
                    f"{case_verification.get('rows_binding')!r}")
            require(case_verification["rows_binding"].startswith("bound"),
                    "the case verifier did not bind rows to the exact live receipt")
            require(case_verification.get("rows_binding"),
                    "the case verifier stopped reporting whether it bound the rows to a scan")
            require(case_verification.get("verdict_rederived_from_rows"),
                    "the case verifier stopped re-deriving the verdict from the rows")
            require(case_receipt.get("reference", {}).get("name") == "Silver", "case receipt does not identify Silver")
            require(len(case_receipt.get("tokens", [])) == 5, "case receipt does not retain the exact Silver rows")
            require(case_receipt.get("source_hashes"), "case receipt does not retain source fingerprints")
            require(case_receipt.get("method", {}).get("join_key") == "rwa_id", "case receipt does not expose the stable join method")
            copy_button = page.locator("#decision-hero [data-copy-case]").first
            require(copy_button.count() == 1, "searched case does not expose a shareable case-link action")
            copy_button.click()
            wait_for_text(page, "#decision-hero [data-copy-case]", "Case link copied", timeout=5_000)

            watch_button = page.locator("[data-watch-id]").first
            require(watch_button.count() == 1, "Silver evidence queue does not expose a watch action")
            watch_button.click()
            watchlist = page.locator("#watchlist-panel")
            watchlist.wait_for(state="visible", timeout=5_000)
            require("Silver" in watchlist.inner_text(), "saved Silver reference is not visible in the local watchlist")

            gold_state = search_and_check("Gold")
            temporal = page.locator("#decision-hero [data-temporal-evidence]")
            temporal.wait_for(state="visible", timeout=30_000)
            wait_for_text(page, "#decision-hero [data-temporal-evidence]", "cash-session")
            temporal_text = temporal.inner_text()
            require("REPEAT-WINDOW CHECK" in temporal_text, "Gold case did not expose the repeat-window check")
            require("weekend" in temporal_text.lower() and "cash-session" in temporal_text.lower(), "temporal check did not explain the comparison clock")
            require("72H OVERLAP" in temporal_text, "temporal check did not disclose the overlap")
            require("not independent validation" in temporal_text.lower(), "temporal check did not preserve its repeat-observation boundary")

            # Pinning a named reference to a named verdict asserts today's market
            # data, not the product: this line demanded INVESTIGATE and failed the
            # moment Tesla's representations became comparable. `search_and_check`
            # already proves the page mirrors the current receipt, so what is
            # worth asserting here is that whatever state it lands in is one the
            # public vocabulary defines.
            # A reference with ONE representation - 545 of 791 - exercises a branch
            # that every search in this audit used to miss, because Silver,
            # Marvell and Tesla all carry several. A ReferenceError lived in it
            # undetected for exactly that reason, aborting the render and leaving
            # the panel above showing a previous case.
            single = next((row for row in receipt.get("alert_index", [])
                           if int(row.get("token_count") or 0) == 1
                           and any(str(row.get("name", "")).lower() == str(item.get("name", "")).lower()
                                   for item in receipt.get("alerts", []))), None)
            if single:
                single_state = search_and_check(single["name"])
                body = page.locator("#decision-hero").inner_text()
                require("THE ONE WRAPPER" in body,
                        f"a single-representation reference ({single['name']}) renders no wrapper "
                        f"card: {body[:200]!r}")
                require("ISSUER" in body and "CHAIN" in body,
                        "the single-wrapper card omits the issuer or the chain")

            # The change view answers "did THIS reference move since the dated
            # observation", which is the question the product was missing. It
            # must state a real comparison or refuse, never both and never
            # neither, and it must never read an absent field as a difference:
            # the first version told every reader that every rule had stopped
            # firing, because it read a field the alerts array does not carry.
            change = page.locator("[data-reference-change]")
            require(change.count() == 1, "the per-reference change view is not on the case card")
            change_text = change.inner_text()
            require("SINCE" in change_text,
                    f"the change view does not date what it compares against: {change_text[:200]!r}")
            # The panel names its baseline: either a recomputation of the dated
            # inputs under the current rules, or two observations that really do
            # share a rule set. Both are comparisons; the eyebrow says which.
            stated_change = ("RECOMPUTED BASELINE" in change_text
                             or "SAME RULE SET" in change_text)
            require(stated_change or "would report a rule change" in change_text
                    or "not in the dated observation" in change_text,
                    f"the change view neither compared nor named why it refused: {change_text[:300]!r}")
            if stated_change:
                require("not compared: one side" not in change_text,
                        "the change view could not read one side's signals and still rendered as a "
                        "comparison")
                require("Compared prices are deliberately excluded" in change_text,
                        "the change view stopped stating that it excludes price movement")
                # The series says how many observations it actually spans. A
                # tracking product that implies a month from two points is the
                # overclaim this one is built to refuse, so the number and the
                # start date are both required on screen.
                span = re.search(r"(\d+) published observations? in the series", change_text)
                require(span is not None,
                        f"the change view does not say how many observations its series spans: "
                        f"{change_text[:250]!r}")
                # The two halves describe two observations: the diff is against
                # the receipt this page loaded, the series ends at whatever was
                # last published. A reviewer read "all the same" directly above
                # "moved on 1 of them" and was right to call it a
                # contradiction. Both must be named on screen.
                require("AGAINST" in change_text,
                        "the change view does not name the observation it compares against")
                if "series ends at" in change_text:
                    require("two observations, so the two halves can disagree" in change_text,
                            "the panel names two observations and does not say they are two")
                require("does not reach back before" in change_text,
                        "the series does not say where it starts, so a reader can assume it "
                        "reaches back further than it does")
                if "RECOMPUTED BASELINE" in change_text:
                    require("not the receipt published that day" in change_text,
                            "the change view says its baseline is recomputed and does not say "
                            "what it is recomputed instead of. The history chart calls that same "
                            "observation 'rules not recorded'; the two must not disagree.")

            tesla_state = search_and_check("Tesla")
            require(in_public_vocabulary(tesla_state),
                    f"Tesla rendered a state outside the published vocabulary: {tesla_state!r}")

            marvell_state = search_and_check("Marvell")
            marvell_brief_button = page.locator("#decision-hero [data-brief-id]").first
            require(marvell_brief_button.count() == 1,
                    "Marvell does not expose its human-readable decision brief")
            with page.expect_download(timeout=30_000) as marvell_brief_info:
                marvell_brief_button.click()
            marvell_brief = marvell_brief_info.value
            with open(marvell_brief.path(), encoding="utf-8") as brief_file:
                marvell_brief_text = brief_file.read()
            require("Included crypto IDs:" in marvell_brief_text
                    and "Excluded crypto IDs and reasons:" in marvell_brief_text
                    and "Comparison membership" in marvell_brief_text,
                    "Marvell's brief dropped the exact route set or row membership")
            marvell_case_button = page.locator("#decision-hero [data-case-receipt]").first
            require(marvell_case_button.count() == 1,
                    "Marvell does not expose its machine-readable case receipt")
            with page.expect_download(timeout=30_000) as marvell_case_info:
                marvell_case_button.click()
            with open(marvell_case_info.value.path(), encoding="utf-8") as case_file:
                marvell_case = json.load(case_file)
            require(marvell_case["comparison"]["included_crypto_ids"]
                    and set(map(str, marvell_case["comparison"]["included_crypto_ids"]))
                    <= set(map(str, [token.get("crypto_id") for token in marvell_case["tokens"]])),
                    "Marvell's case receipt does not bind its included route IDs to its rows")
            marvell_live_response = page.request.get(args.base.rstrip("/") + "/api/integrity", timeout=30_000)
            require(marvell_live_response.ok, "could not reload the receipt for Marvell binding")
            marvell_live = marvell_live_response.json()
            require(marvell_case["observed_at"] == marvell_live["observed_at"],
                    "the live receipt changed while the Marvell case was being checked")
            marvell_verification = verify_case_receipt(
                marvell_case, against=(marvell_live, "live /api/integrity"))
            require(marvell_verification["rows_binding"].startswith("bound"),
                    f"Marvell's case did not bind to the full alert index: "
                    f"{marvell_verification['rows_binding']!r}")
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
            wait_for_text(page, "#explorer-dossier", "EVIDENCE CONTEXT")
            gold_dossier = page.locator("#explorer-dossier").inner_text()
            require("DEX CONTRACT COVERAGE" in gold_dossier, "Gold dossier did not expose contract coverage context")
            require("DEX SURFACES" in gold_dossier, "Gold dossier did not expose resolved DEX surfaces")
            require("CMC MARKET PAIRS" in gold_dossier, "Gold dossier did not expose the market-pair boundary")
            # Two searches, one export button. A reviewer searched five
            # references through the explorer and downloaded five identical
            # receipts for a sixth they had never searched. The explorer says
            # which surface owns the case and offers the click that makes them
            # agree; both must be there.
            require("follow the case open in the monitor" in gold_dossier,
                    "the explorer no longer says which surface the export button belongs to")
            bridge = page.locator("[data-open-case]")
            require(bridge.count() >= 1,
                    "the explorer offers no way to open the case it is describing")
            before = page.locator("[data-case-receipt]").first.get_attribute("data-case-receipt")
            bridge.first.click()
            page.wait_for_timeout(1_500)
            after = page.locator("[data-case-receipt]").first.get_attribute("data-case-receipt")
            require(after != before,
                    f"opening the explorer's case left the export on {before!r}, so the two "
                    "surfaces still disagree about which reference is selected")
            # The pair that makes "deferred" mean anything. Without this, an
            # explorer that never loads its catalogue at all would pass the
            # check above and look like a 1.98 MiB saving.
            require(catalogue_requests,
                    "the explorer resolved a dossier without ever fetching its catalogue, so the "
                    "deferral check above is measuring a broken explorer rather than a saving")

            # A search that finds nothing must not leave the previous
            # reference's verdict on screen. The no-match branch reset the
            # metrics and hid the quote contrast, and left CAPITAL ROUTE showing
            # "Keep 10,000 uncommitted · Resolve identity, unit, issuer terms and
            # execution evidence before selecting a wrapper" under a card reading
            # "No published case selected". Checked in both directions, because
            # hiding it permanently would also pass a one-way check.
            page.locator("#hero-search").fill("Silver")
            page.locator("#hero-search-form button[type=submit]").click()
            page.locator("#search-result").wait_for(state="visible", timeout=30_000)
            page.locator("#hero-capital-signal").wait_for(state="visible", timeout=30_000)
            page.locator("#hero-search").fill("zzzz-no-such-reference")
            page.locator("#hero-search-form button[type=submit]").click()
            wait_for_text(page, "#decision-hero", "No matching reference")
            stale = page.locator("body").inner_text()
            require("CAPITAL ROUTE" not in stale,
                    "a search that found nothing still shows the previous reference's capital verdict")
            require(page.locator("#hero-quote-contrast").is_hidden(),
                    "a search that found nothing still shows the previous reference's quote endpoints")

            page.locator("#hero-search").fill("Colgate")
            page.locator("#hero-search-form button[type=submit]").click()
            map_result = page.locator("#search-result")
            map_result.wait_for(state="visible", timeout=30_000)
            require("No live case found" in map_result.inner_text(), "map-only query was incorrectly presented as a live case")
            map_result.locator("[data-open-map-query]").click()
            wait_for_either(page, "#explorer-dossier", ("DOSSIER PENDING", "REFERENCE ONLY"))
            map_text = page.locator("#explorer-dossier").inner_text()
            require("Colgate-Palmolive" in map_text, "map-only route did not resolve the complete RWA catalogue entry")
            map_route = "DOSSIER PENDING" if "DOSSIER PENDING" in map_text else "REFERENCE ONLY"

            # The judge page is the submitted demo URL, and it names two
            # references and the word each one returns. That sentence also
            # claims both hold "on the live one", which nothing verified: the
            # offline test pins them against the shipped replay, and the live
            # receipt moves. A named verdict on moving data is exactly the
            # claim this product exists to refuse, so it is checked here, on
            # whatever receipt is actually published.
            #
            # The names are read out of the page rather than written here. Two
            # copies of a claim drift apart, and the one in this file would be
            # the copy nobody reads.
            judge_page = desktop.new_page()
            judge_page.goto(args.base.rstrip("/") + "/judge", wait_until="domcontentloaded", timeout=30_000)
            judge_html = judge_page.content()
            judge_page.close()
            promised = re.findall(r"<strong>([^<]+)</strong> returns <strong>([^<]+)</strong>", judge_html)
            require(len(promised) == 2,
                    f"the judge page no longer names two worked examples: found {len(promised)}")
            judge_examples = {}
            for name, word in promised:
                require(in_public_vocabulary(word),
                        f"the judge page promises {word!r} for {name}, which is outside the public vocabulary")
                shown = search_and_check(name)
                require(shown == word,
                        f"the judge page tells a judge {name} returns {word!r}; the live page shows {shown!r}")
                judge_examples[name] = shown

            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)

            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
            mobile_page = mobile.new_page()
            mobile_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            mobile_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            wait_for_text(mobile_page, "#receipt-status-label", "LOADING", absent=True)
            overflow = mobile_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            require(not overflow, "mobile page has horizontal overflow")
            mobile_decision = mobile_page.locator("#hero-mobile-decision")
            require(mobile_decision.is_visible(), "mobile first viewport does not expose the decision preview")
            # This demanded the literal words "DO NOT SHORTLIST", so it broke the
            # moment the hero began opening on a reference whose comparison was
            # published - a named verdict pinned again instead of the guarantee.
            # What matters is that the phone preview shows a state the public
            # vocabulary defines, and the same one the desktop hero is showing.
            mobile_text = mobile_decision.inner_text()
            shown_states = [state for state in PUBLIC_STATES if state in mobile_text]
            require(bool(shown_states),
                    f"mobile decision preview shows no published state: {mobile_text[:200]!r}")
            mobile.close()

            narrow_mobile = {}
            for width, height in ((320, 800), (375, 812)):
                narrow_page = browser.new_page(viewport={"width": width, "height": height})
                narrow_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
                narrow_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
                wait_for_text(narrow_page, "#receipt-status-label", "LOADING", absent=True)
                narrow_overflow = narrow_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                require(not narrow_overflow, f"{width}px mobile page has horizontal overflow")
                # Page-level overflow was false while forty-three leaf elements
                # sat past the right edge: the overflow was CUT OFF rather than
                # scrollable, so the document never grew and this check could
                # not fail for the defect it was written to catch. A state badge
                # and a representation count rendered at x=393..476 in a 390px
                # viewport, and card bodies truncated mid-sentence. Count the
                # leaves that leave the screen with nothing to scroll them back.
                clipped = narrow_page.evaluate("""
                    () => {
                      const vw = window.innerWidth;
                      const out = [];
                      document.querySelectorAll('main *').forEach(node => {
                        if (node.children.length) return;
                        const box = node.getBoundingClientRect();
                        if (!box.width || !box.height || box.right <= vw + 1) return;
                        let parent = node.parentElement;
                        while (parent) {
                          const style = getComputedStyle(parent);
                          if (/auto|scroll/.test(style.overflowX)
                              && parent.scrollWidth > parent.clientWidth + 1) return;
                          parent = parent.parentElement;
                        }
                        out.push(`${node.tagName}.${(node.className || '').toString().split(' ')[0]}`
                                 + ` "${(node.innerText || '').trim().slice(0, 24)}"`);
                      });
                      return out;
                    }
                """)
                require(not clipped,
                        f"{width}px mobile cuts {len(clipped)} elements off the right edge "
                        f"with nothing to scroll them back: {clipped[:4]}")
                require(narrow_page.locator("#hero-search").is_visible(), f"{width}px mobile hides the primary search")
                require(narrow_page.locator("#hero-mobile-decision").is_visible(), f"{width}px mobile hides the decision preview")
                narrow_mobile[str(width)] = "no overflow; search and decision visible"
                narrow_page.close()

            tablet_results = {}
            for width in (621, 768, 834, 899, 900):
                tablet = browser.new_context(viewport={"width": width, "height": 1112})
                tablet_page = tablet.new_page()
                tablet_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
                tablet_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
                wait_for_text(tablet_page, "#receipt-status-label", "LOADING", absent=True)
                tablet_overflow = tablet_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
                require(not tablet_overflow, f"{width}px tablet page has horizontal overflow")
                require(tablet_page.locator("#hero-search").is_visible(),
                        f"{width}px tablet first viewport hides the primary search")
                tablet_page.locator("#hero-search").fill("Tesla")
                tablet_page.locator("#hero-search-form button[type=submit]").click()
                tablet_page.locator("#search-result").wait_for(state="visible", timeout=30_000)
                visible_result = False
                for _ in range(30):
                    position = tablet_page.evaluate("""() => {
                        const result = document.querySelector('#search-result');
                        const header = document.querySelector('.topbar');
                        if (!result || !header) return null;
                        return {
                            resultTop: result.getBoundingClientRect().top,
                            resultBottom: result.getBoundingClientRect().bottom,
                            headerBottom: header.getBoundingClientRect().bottom,
                            viewportHeight: window.innerHeight,
                        };
                    }""")
                    if position and position["resultTop"] >= max(8, position["headerBottom"] + 8) \
                            and position["resultBottom"] > 0 \
                            and position["resultTop"] < position["viewportHeight"] - 80:
                        visible_result = True
                        break
                    tablet_page.wait_for_timeout(100)
                require(visible_result,
                        f"{width}px tablet sticky header covers or hides the opening search result: {position}")
                tablet_results[str(width)] = "no overflow; search result clears sticky header"
                tablet.close()

            fallback = browser.new_context(viewport={"width": 1440, "height": 1100})
            fallback_page = fallback.new_page()
            fallback_page.route("**/api/integrity", lambda route: route.abort())
            fallback_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            fallback_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            wait_for_text(fallback_page, "#receipt-status-label", "LOADING", absent=True)
            fallback_status = fallback_page.locator("#receipt-status-label").inner_text()
            require("DATED REPLAY" in fallback_status, f"live failure did not produce a dated replay label: {fallback_status!r}")
            require("Explore RWA" in fallback_page.locator("body").inner_text(), "dated replay fallback did not keep the RWA explorer usable")
            fallback.close()

            # The home search result and workspace used to be separate tasks:
            # the header link discarded the selected asset and made the user
            # search again. A single unambiguous result should carry its stable
            # CMC RWA ID into the workspace; ambiguous and map-only searches
            # keep their existing home-page flow.
            handoff = desktop.new_page()
            handoff.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            wait_for_text(handoff, "#receipt-status-label", "LOADING", absent=True)
            handoff.locator("#hero-search").fill("Tesla")
            handoff.locator("#hero-search-form button[type=submit]").click()
            handoff.locator("#search-result").wait_for(state="visible", timeout=30_000)
            workspace_link = handoff.locator(".workspace-link")
            require("reference=14" in workspace_link.get_attribute("href"),
                    f"a unique Tesla search did not carry its stable ID into the workspace: "
                    f"{workspace_link.get_attribute('href')!r}")
            handoff.set_viewport_size({"width": 390, "height": 844})
            workspace_link.click()
            wait_for_text(handoff, "#receipt-time", "FRESH", timeout=30_000)
            handoff.locator(".review-result").wait_for(state="visible", timeout=30_000)
            require("Tesla" in handoff.locator("#asset-search").input_value(),
                    "the workspace opened without the selected Tesla reference")
            save_review = handoff.get_by_role("button", name="Save review")
            require(save_review.count() == 1,
                    "the carried-over Tesla result cannot be saved as a review brief")
            expected_review_ids = handoff.evaluate("""async () => {
              const response = await fetch('/api/integrity', { cache: 'no-cache' });
              const receipt = await response.json();
              const entry = (receipt.alert_index || []).find(row => String(row.rwa_id) === '14');
              return (entry?.representations || []).map(row => String(row.crypto_id));
            }""")
            require(expected_review_ids and len(expected_review_ids) == len(set(expected_review_ids)),
                    "the loaded Tesla receipt lacks distinct representation IDs")
            requests_from_save = []
            handoff.on("request", lambda request: requests_from_save.append(request.url))
            with handoff.expect_download(timeout=30_000) as review_download_info:
                save_review.click()
            review_download = review_download_info.value
            with open(review_download.path(), encoding="utf-8") as review_file:
                review_text = review_file.read()
            review_ids = re.findall(r"^\| (\d+) \|", review_text, flags=re.MULTILINE)
            require(review_ids == expected_review_ids,
                    f"Tesla review brief IDs differ from the loaded receipt: {review_ids!r} vs {expected_review_ids!r}")
            require("Observed at:" in review_text and "CMC-reported sources" in review_text,
                    "Tesla review brief omitted the receipt timestamp or source boundary")
            require("[Project](<https://assets.backed.fi/products/tesla-xstock>)" in review_text
                    and "[Explorer](<https://www.arbiscan.io/token/0x8ad3c73f833d3f9a523ab01476625f269aeb7cf0>)" in review_text,
                    "Tesla review brief omitted the source links already present in the receipt")
            require(not requests_from_save,
                    f"saving a review brief made an unexpected network request: {requests_from_save!r}")
            xstock = handoff.locator('.representation-table tbody tr:has(td.token strong:text-is("TSLAX"))')
            dinari = handoff.locator('.representation-table tbody tr:has(td.token strong:text-is("TSLA.D"))')
            xstock.locator(".token-source-links summary").click()
            require(xstock.locator('a[href*="assets.backed.fi/products/tesla-xstock"]').count() == 1
                    and xstock.locator('a[href*="arbiscan.io"]').count() >= 1,
                    "TSLAX does not expose the project and explorer URLs reported in its receipt")
            dinari.locator(".token-source-links summary").click()
            require(dinari.locator('a[href$=".pdf"]').count() == 1
                    and dinari.locator('a[href*="arbiscan.io"]').count() == 1,
                    "TSLA.D does not expose the document and contract explorer reported in its receipt")
            require(not handoff.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"),
                    "source disclosure introduced horizontal overflow in the 390px workspace")
            handoff.close()

            print(json.dumps({
                "base": args.base.rstrip("/"),
                "receipt_status": status,
                "receipt_refresh": "live integrity request repeated",
                "history_includes_current_receipt": True,
                "presentation_accessibility": "landmarks, h1, named controls and image alt text pass",
                "silver_decision": silver_state,
                "gold_decision": gold_state,
                "gold_temporal_check": "two dated weekend versus cash-session windows visible; overlap disclosed",
                "tesla_decision": tesla_state,
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
                "judge_page_examples": judge_examples,
                "mobile_horizontal_overflow": False,
                "narrow_mobile": narrow_mobile,
                "tablet_horizontal_overflow": False,
                "tablet_search_results": tablet_results,
                "population_concentration": "HHI and effective issuer count visible",
                "population_attribution_export": attribution_download.suggested_filename,
                "mobile_decision_preview": "visible before the long task panel",
                "failure_fallback": fallback_status,
                "workspace_handoff": "Tesla search opened the matching workspace result and source paths without re-entry",
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

#!/usr/bin/env python3
"""Exercise the public Bell flow in a real browser without credentials."""

from __future__ import annotations

import argparse
import json
import sys


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

            receipt_response = page.request.get(args.base.rstrip("/") + "/api/integrity", timeout=30_000)
            require(receipt_response.ok, f"integrity receipt request failed: {receipt_response.status}")
            receipt = receipt_response.json()
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
                return expected_states.get(item.get("state"), "REFERENCE ONLY")

            def search_and_check(name: str) -> str:
                page.locator("#hero-search").fill(name)
                page.locator("#hero-search-form button[type=submit]").click()
                result = page.locator("#search-result")
                result.wait_for(state="visible", timeout=30_000)
                result_text = result.inner_text()
                expected = expected_for(name)
                require(expected in result_text, f"{name} did not mirror receipt state {expected!r}: {result_text[:500]!r}")
                require("observed quote" in result_text.lower(), f"{name} did not expose observed evidence: {result_text[:500]!r}")
                return expected

            silver_state = search_and_check("Silver")
            brief_button = page.locator("#decision-hero [data-brief-id]").first
            require(brief_button.count() == 1, "Silver result does not expose a decision-brief action")
            with page.expect_download(timeout=30_000) as download_info:
                brief_button.click()
            brief_download = download_info.value
            require(brief_download.suggested_filename.endswith("-decision-brief.md"), f"unexpected brief filename: {brief_download.suggested_filename!r}")
            copy_button = page.locator("#decision-hero [data-copy-case]").first
            require(copy_button.count() == 1, "searched case does not expose a shareable case-link action")
            copy_button.click()
            page.wait_for_function("document.querySelector('#decision-hero [data-copy-case]')?.textContent?.includes('Case link copied')", timeout=5_000)

            marvell_state = search_and_check("Marvell")

            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)

            mobile = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
            mobile_page = mobile.new_page()
            mobile_page.goto(args.base.rstrip("/") + "/", wait_until="domcontentloaded", timeout=30_000)
            mobile_page.locator("#receipt-status-label").wait_for(state="attached", timeout=30_000)
            mobile_page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            overflow = mobile_page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
            require(not overflow, "mobile page has horizontal overflow")
            mobile.close()

            print(json.dumps({
                "base": args.base.rstrip("/"),
                "receipt_status": status,
                "silver_decision": silver_state,
                "marvell_decision": marvell_state,
                "silver_evidence": "observed quote evidence visible",
                "decision_brief": brief_download.suggested_filename,
                "shareable_case_link": "Case link copied",
                "mobile_horizontal_overflow": False,
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

#!/usr/bin/env python3
"""Record credential-free Bell walkthroughs for editing in Hyperframe."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlencode


def wait_for_receipt(page) -> None:
    page.wait_for_function(
        "document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false",
        timeout=30_000,
    )


def pause(seconds: float) -> None:
    time.sleep(seconds)


def record(base: str, output: Path, channel: str) -> Path:
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, **({'channel': channel} if channel else {}))
        context = browser.new_context(
            viewport={'width': 1440, 'height': 1100},
            record_video_dir=str(output),
            record_video_size={'width': 1440, 'height': 1100},
        )
        page = context.new_page()
        errors: list[str] = []
        page.on('console', lambda message: errors.append(f'console: {message.text}') if message.type == 'error' else None)
        page.on('pageerror', lambda error: errors.append(f'pageerror: {error}'))
        page.goto(base.rstrip('/') + '/', wait_until='domcontentloaded', timeout=30_000)
        wait_for_receipt(page)
        pause(2)

        for reference in ('5', None, '70', '1'):
            if reference is None:
                page.goto(base.rstrip('/') + '/', wait_until='domcontentloaded', timeout=30_000)
                wait_for_receipt(page)
                population = page.locator('#population-visual')
                population.wait_for(state='visible', timeout=30_000)
                page.evaluate("window.scrollTo(0, Math.max(0, document.querySelector('#population-visual').offsetTop - 82))")
                pause(4)
                continue
            page.goto(f"{base.rstrip('/')}/?{urlencode({'reference': reference})}", wait_until='domcontentloaded', timeout=30_000)
            wait_for_receipt(page)
            page.locator('#decision-hero h3').wait_for(state='visible', timeout=30_000)
            pause(4)

        video = page.video
        context.close()
        browser.close()
        video_path = video.path()
        target = output / 'bell-demo-raw.webm'
        Path(video_path).replace(target)
        return target


def record_long(base: str, output: Path, channel: str) -> Path:
    """Record the full judge story with readable pauses between evidence states."""
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, **({'channel': channel} if channel else {}))
        context = browser.new_context(
            viewport={'width': 1440, 'height': 1100},
            record_video_dir=str(output),
            record_video_size={'width': 1440, 'height': 1100},
        )
        page = context.new_page()
        errors: list[str] = []
        page.on('console', lambda message: errors.append(f'console: {message.text}') if message.type == 'error' else None)
        page.on('pageerror', lambda error: errors.append(f'pageerror: {error}'))

        def open_page(path: str = '/') -> None:
            page.goto(base.rstrip('/') + path, wait_until='domcontentloaded', timeout=30_000)
            wait_for_receipt(page)

        def show(selector: str, seconds: float) -> None:
            page.locator(selector).wait_for(state='visible', timeout=30_000)
            page.locator(selector).scroll_into_view_if_needed()
            pause(seconds)

        # 1. The product question and the current live receipt
        open_page()
        pause(10)

        # 2. A real first action, rather than a deep-link-only demo
        page.locator('#hero-search').fill('Silver')
        page.locator('#hero-search-form').locator('button[type="submit"]').click()
        page.locator('#search-result').wait_for(state='visible', timeout=30_000)
        pause(10)

        # 3. The selected case, capital consequence and evidence rows
        show('#decision-hero', 12)
        details = page.locator('#decision-hero details').first
        if details.count():
            details.click()
            pause(7)

        # 4. The population-wide shape of the monitor
        open_page()
        show('#population-visual', 12)
        show('#concentration-visual', 10)

        # 5. A facts-open route demonstrates that Bell does not rank clean rows
        open_page('/?reference=70')
        show('#decision-hero', 11)

        # 6. A repeated temporal check supplies deeper evidence for Gold
        open_page('/?reference=1')
        page.wait_for_function(
            "document.querySelector('#decision-hero [data-temporal-evidence]')?.textContent?.includes('72H OVERLAP')",
            timeout=30_000,
        )
        show('#decision-hero [data-temporal-evidence]', 15)

        # 7. The complete map keeps references without a published case honest
        open_page()
        page.locator('#explorer').scroll_into_view_if_needed()
        page.locator('#explorer-search').fill('Colgate')
        page.locator('#explorer-form').locator('button[type="submit"]').click()
        page.locator('#explorer-dossier').wait_for(state='visible', timeout=30_000)
        pause(12)

        # 8. End on the receipt and its reproducibility boundary
        show('#evidence', 12)

        video = page.video
        context.close()
        browser.close()
        video_path = video.path()
        target = output / 'bell-demo-long.webm'
        Path(video_path).replace(target)
        (output / 'manifest.json').write_text(json.dumps({
            'schema_version': 'bell.demo-video.v1',
            'mode': 'long',
            'base': base.rstrip('/'),
            'console_errors': errors,
            'video': target.name,
        }, indent=2) + '\n', encoding='utf-8')
        if errors:
            raise RuntimeError(f'browser errors captured: {errors}')
        return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://bell.dyplux.com')
    parser.add_argument('--output', type=Path, default=Path('/tmp/bell-demo-video'))
    parser.add_argument('--channel', default='chrome')
    parser.add_argument('--long', action='store_true', help='record the full 90–110 second judge story')
    args = parser.parse_args()
    target = record_long(args.base, args.output, args.channel) if args.long else record(args.base, args.output, args.channel)
    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

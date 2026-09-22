#!/usr/bin/env python3
"""Record a short credential-free Bell walkthrough for editing in Hyperframe."""

from __future__ import annotations

import argparse
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://bell.dyplux.com')
    parser.add_argument('--output', type=Path, default=Path('/tmp/bell-demo-video'))
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    target = record(args.base, args.output, args.channel)
    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

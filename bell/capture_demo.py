#!/usr/bin/env python3
"""Capture current Bell judge-path frames for a demo edit or Hyperframe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import quote


def slug(value: str) -> str:
    return ''.join(character.lower() if character.isalnum() else '-' for character in value).strip('-')


def capture(base: str, output: Path, channel: str) -> dict:
    from playwright.sync_api import sync_playwright

    output.mkdir(parents=True, exist_ok=True)
    manifest = {'schema_version': 'bell.demo-capture.v1', 'base': base.rstrip('/'), 'frames': [], 'console_errors': []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, **({'channel': channel} if channel else {}))
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
        errors: list[str] = []
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)

        page.goto(base.rstrip('/') + '/', wait_until='domcontentloaded', timeout=30_000)
        page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
        receipt = page.request.get(base.rstrip('/') + '/api/integrity', timeout=30_000).json()
        manifest['observed_at'] = receipt.get('observed_at')
        manifest['published_at'] = receipt.get('_publication', {}).get('published_at')

        def save_frame(name: str, label: str, reference: str | None = None, viewport: dict | None = None, wait_for: str | None = None) -> None:
            if reference is not None:
                page.set_viewport_size(viewport or {'width': 1440, 'height': 1100})
                page.goto(f"{base.rstrip('/')}/?reference={quote(reference)}", wait_until='domcontentloaded', timeout=30_000)
                page.wait_for_function("document.querySelector('#receipt-status-label')?.textContent?.includes('LOADING') === false", timeout=30_000)
            if wait_for:
                page.locator(wait_for).wait_for(state='visible', timeout=30_000)
            page.wait_for_timeout(250)
            filename = f'{name}.png'
            page.screenshot(path=str(output / filename), full_page=False)
            manifest['frames'].append({'file': filename, 'label': label, 'reference': reference, 'viewport': page.viewport_size})

        save_frame('01-hero-live', 'Live first viewport with current case')
        save_frame('02-silver-blocked', 'Silver blocked case and observed quote endpoints', '5', wait_for='#decision-hero h3')
        save_frame('03-silver-mobile', 'Silver blocked case on mobile', '5', {'width': 390, 'height': 844}, '#decision-hero h3')
        marvell = next((item for item in receipt.get('alert_index', []) if 'marvell' in str(item.get('name', '')).lower()), None)
        if marvell:
            save_frame('04-marvell-facts-open', 'Facts-open contrast case', str(marvell['rwa_id']), wait_for='#decision-hero h3')
        save_frame('05-gold-repeat-window', 'Gold repeat-window check', '1', wait_for='#decision-hero h3')
        temporal = page.locator('#decision-hero [data-temporal-evidence]')
        if temporal.count():
            temporal.wait_for(state='visible', timeout=30_000)
            page.wait_for_function("document.querySelector('#decision-hero [data-temporal-evidence]')?.textContent?.includes('72H OVERLAP')", timeout=30_000)
            page.screenshot(path=str(output / '05-gold-repeat-window.png'), full_page=False)

        manifest['console_errors'] = errors
        browser.close()
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://bell.dyplux.com', help='public Bell origin')
    parser.add_argument('--output', type=Path, default=Path('/tmp/bell-demo-capture'), help='directory for frames and manifest')
    parser.add_argument('--channel', default='chrome', help='Playwright browser channel, or empty for bundled Chromium')
    args = parser.parse_args()
    manifest = capture(args.base, args.output, args.channel)
    if manifest['console_errors']:
        raise SystemExit(f"console errors captured: {manifest['console_errors']}")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

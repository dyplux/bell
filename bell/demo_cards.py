#!/usr/bin/env python3
"""Render the statement cards for the Bell demo cut, in the product's own type.

One statement per product segment, each its own full frame rather than a
caption laid over the interface. Numbers appear on a card only when the
capture's own manifest carries them, or when the card names the command and the
date that produce them.
"""
from pathlib import Path
import json
import os
import sys

HERE = Path(__file__).resolve().parent
CAPTURE_ROOT = Path(
    os.environ.get('BELL_DEMO_DIR', '/tmp/bell-demo-video'))
FONT = HERE / 'site' / 'assets' / 'SpaceGrotesk-Variable.ttf'
OUT = CAPTURE_ROOT / 'cards'

MANIFEST = json.loads((CAPTURE_ROOT / 'manifest.json').read_text())
R = MANIFEST['receipt']
OBSERVED = R['observed_at'].replace('T', ' ').replace('Z', ' UTC')

CARDS = [
    ('Five tokens track the same silver,\nso take the cheapest one',
     'That move assumes they can be compared'),
    ('CoinMarketCap shows which assets are tokenised.\nBell checks whether they can be compared',
     f"Observed {OBSERVED} · {R['tokenised_references']} references · "
     f"{R['representations']} representations"),
    ('Start from the asset you are researching',
     'No account, no key, no trading signal'),
    ('A contradiction between two published surfaces,\nnot a discount and not fraud',
     'Route: DO NOT SHORTLIST · read from the receipt, not from this video'),
    ('The shape of the whole scan,\nnot one hand-picked case',
     None),
    ('How concentrated the representations are,\nand how many issuers that really is',
     None),
    ('When no critical rule fires, the route changes',
     'FACTS OPEN is not approval, and still ranks nothing'),
    ('Evidence that repeats across a 72-hour window',
     'A dated check, not a snapshot'),
    ('A reference with no published case\nis routed, not failed',
     None),
    ('Every answer ties to a dated, credential-free receipt',
     'The inputs ship with it, so it re-derives with no API key'),
    ('Bell does not prove backing, redemption,\ncustody or liquidity',
     'It proves two surfaces disagree, with a date on it'),
]

TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: 'Space Grotesk'; src: url('file://{font}'); }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; height: 100%; }}
body {{
  background: #0a0e14; color: #f4f1ea;
  font-family: 'Space Grotesk', Arial, sans-serif;
  display: flex; flex-direction: column; justify-content: center;
  padding: 0 168px; height: 1080px; width: 1920px;
}}
.rule {{ width: 96px; height: 6px; background: #ffcc00; margin-bottom: 44px; }}
h1 {{
  font-size: 72px; line-height: 1.14; font-weight: 600;
  letter-spacing: -0.02em; margin: 0; max-width: 1400px;
  text-wrap: balance;
}}
p {{ font-size: 30px; line-height: 1.45; color: #91a0b2; margin: 38px 0 0; }}
.mark {{
  position: absolute; bottom: 68px; left: 168px;
  font-size: 21px; letter-spacing: .20em; color: #ffcc00; font-weight: 600;
}}
</style></head><body>
<div class="rule"></div>
<h1>{head}</h1>
{kicker}
<div class="mark">BELL</div>
</body></html>"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        for index, (head, kicker) in enumerate(CARDS):
            html = TEMPLATE.format(
                font=FONT, head=head.replace('\n', ' '),
                kicker=f'<p>{kicker}</p>' if kicker else '')
            path = OUT / f'card-{index:02d}.html'
            path.write_text(html, encoding='utf-8')
            page.goto(f'file://{path}')
            page.wait_for_timeout(260)
            page.screenshot(path=str(OUT / f'card-{index:02d}.png'))
            print(f'  card-{index:02d}  {head.splitlines()[0][:52]}')
        browser.close()
    print(f'{len(CARDS)} cards -> {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

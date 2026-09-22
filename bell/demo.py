#!/usr/bin/env python3
"""The judged capability, offline, in about ten seconds.

Run: `make demo`  (or `PYTHONPATH=bell python3 bell/demo.py`)

No API key, no account, no network. It reads the receipt this repository ships,
re-derives every number it prints from that receipt, and shows both halves of the
product on one screen:

  the refusal  - references whose representations cannot honestly be compared,
                 and the coded rule that blocked each one
  the answer   - references that clear every rule, with the comparison actually
                 performed: cheapest route, spread, and whether the cheapest is
                 also the one carrying volume

A monitor that only ever refuses is a gate with no door. This prints the door.
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rwa_integrity import asset_scan  # noqa: E402

BOLD, DIM, RESET = '\033[1m', '\033[2m', '\033[0m'
GREEN, AMBER, RED = '\033[32m', '\033[33m', '\033[31m'


def load_receipt() -> tuple[dict, str]:
    candidates = sorted(glob.glob(os.path.join(HERE, 'site', 'proof', '*replay*.json')))
    if not candidates:
        candidates = sorted(glob.glob(os.path.join(HERE, 'site', 'proof', '*.json')))
    if not candidates:
        sys.exit('No shipped receipt found under bell/site/proof/.')
    path = candidates[-1]
    with open(path, encoding='utf-8') as handle:
        return json.load(handle), os.path.basename(path)


def money(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return '--'
    for cut, suffix in ((1e9, 'bn'), (1e6, 'm'), (1e3, 'k')):
        if abs(value) >= cut:
            return f'${value / cut:,.1f}{suffix}'
    return f'${value:,.2f}'


def main() -> int:
    receipt, filename = load_receipt()
    alerts = receipt.get('alerts') or receipt.get('alert_index') or []

    print()
    print(f'{BOLD}Can these tokens be compared?{RESET}')
    print(f'{DIM}receipt {filename} · observed {receipt.get("observed_at", "?")} · '
          f'no API key used{RESET}')
    print()

    # The receipt stores the state its own run computed. This re-runs the gate
    # over the recorded token rows instead of trusting that field, so what you
    # see below is this checkout's logic applied to that day's data - which is
    # also what makes the demo a test of the engine rather than a pretty printer.
    blocked, cleared, held = [], [], []
    for stored in alerts:
        if not isinstance(stored, dict):
            continue
        asset = asset_scan({
            'rwa_id': stored.get('rwa_id'),
            'name': stored.get('name'),
            'symbol': stored.get('symbol'),
            'asset_type': stored.get('asset_type'),
            'tokens': stored.get('tokens') or [],
            'tradfi_markets': stored.get('tradfi_markets') or [],
        })
        if asset['comparison']:
            cleared.append(asset)
        elif asset['state'] == 'do_not_compare':
            blocked.append(asset)
        else:
            held.append(asset)

    print(f'{BOLD}{RED}REFUSED{RESET} — a rule fired, so no ranking is published')
    print(f'{DIM}{"reference":<26}{"rule that blocked it":<34}reps{RESET}')
    for asset in blocked[:6]:
        codes = [s.get('code') for s in asset.get('signals', [])
                 if s.get('severity') == 'critical']
        name = (asset.get('name') or asset.get('symbol') or '?')[:25]
        print(f'  {name:<26}{(codes[0] if codes else "-"):<34}{asset.get("token_count", 0)}')
    if len(blocked) > 6:
        print(f'{DIM}  ... {len(blocked) - 6} more refused in this receipt{RESET}')
    print()

    print(f'{BOLD}{GREEN}COMPARABLE{RESET} — the prices can be set side by side, '
          f'so the comparison is published')
    if not cleared:
        print(f'{DIM}  Nothing in this receipt cleared the gate with two or more'
              f' tradable representations.{RESET}')
    else:
        print(f'{DIM}{"reference":<26}{"cheapest route":<16}{"spread":<13}'
              f'{"cheapest also deepest":<24}{"24h volume":<12}unresolved{RESET}')
        for asset in cleared[:8]:
            routes = asset['comparison']
            name = (asset.get('name') or asset.get('symbol') or '?')[:25]
            cheapest = (routes['cheapest']['symbol'] or '?')[:15]
            same = 'yes' if routes['cheapest_is_deepest'] else f"no, {routes['deepest']['symbol'][:12]}"
            print(f'  {name:<26}{cheapest:<16}{routes["spread_bps"]:>7.1f} bps  '
                  f'{same:<24}{money(routes["traded_volume_24h"]):<12}'
                  f'{len(routes["unresolved"])}')
        if len(cleared) > 8:
            print(f'{DIM}  ... {len(cleared) - 8} more comparable in this receipt{RESET}')
        print()
        print(f'{DIM}  "unresolved" counts warnings still open on that reference. The route'
              f' filter already{RESET}')
        print(f'{DIM}  neutralises them - derivatives dropped, ticker never used as the'
              f' identity key, rows{RESET}')
        print(f'{DIM}  without a price or traded volume excluded - so the comparison is'
              f' safe to publish, but{RESET}')
        print(f'{DIM}  it is published with the count attached rather than as a clean bill'
              f' of health.{RESET}')
    print()

    total = len(alerts)
    print(f'{BOLD}Of {total} references in this receipt:{RESET} '
          f'{RED}{len(blocked)} refused{RESET}, '
          f'{GREEN}{len(cleared)} comparable{RESET}, '
          f'{AMBER}{len(held)} held for investigation{RESET}')
    print()
    print(f'{DIM}Every number above was recomputed from {filename} by this script.')
    print(f'The comparison is a price fact about the representations CoinMarketCap')
    print(f'returned. Backing, redemption, eligibility and custody are not observed')
    print(f'by this monitor and no allocation advice is implied.{RESET}')
    print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

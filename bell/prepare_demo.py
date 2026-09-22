#!/usr/bin/env python3
"""Prepare a current, credential-free Bell demo shot list from the public receipt."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen


def fetch_receipt(base: str) -> dict:
    url = base.rstrip('/') + '/api/integrity'
    request = Request(url, headers={'Accept': 'application/json', 'User-Agent': 'bell-demo-prep/1.0'})
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f'public receipt returned HTTP {response.status}')
        return json.load(response)


def find_reference(receipt: dict, reference: str) -> dict:
    needle = reference.strip().lower()
    rows = receipt.get('alerts') or receipt.get('alert_index') or []
    exact = next(
        (row for row in rows if any(str(row.get(key) or '').strip().lower() == needle for key in ('name', 'symbol', 'rwa_id'))),
        None,
    )
    match = exact or next(
        (row for row in rows if needle in str(row.get('name') or '').lower()),
        None,
    )
    if not match:
        raise RuntimeError(f'reference not found in the current receipt: {reference}')
    return match


def demo_snapshot(receipt: dict, reference: str = 'Silver') -> dict:
    row = find_reference(receipt, reference)
    tokens = [token for token in row.get('tokens', []) if isinstance(token, dict)]
    priced = sorted((token for token in tokens if isinstance(token.get('price'), (int, float))), key=lambda token: token['price'])
    critical = [signal for signal in row.get('signals', []) if signal.get('severity') == 'critical']
    ratio = next(
        (signal.get('evidence', {}).get('max_min_ratio') for signal in row.get('signals', []) if signal.get('code') == 'PRICE_DENOMINATION_BREAK'),
        None,
    )
    return {
        'observed_at': receipt.get('observed_at'),
        'published_at': receipt.get('_publication', {}).get('published_at'),
        'reference': {
            'rwa_id': row.get('rwa_id'),
            'name': row.get('name'),
            'symbol': row.get('symbol'),
            'state': row.get('state'),
            'token_count': row.get('token_count') or len(tokens),
            'issuer_count': row.get('issuer_count'),
            'critical_signal_count': len(critical),
            'observed_ratio': ratio,
            'low': {
                'symbol': priced[0].get('symbol') if priced else None,
                'issuer': priced[0].get('issuer_name') if priced else None,
                'price': priced[0].get('price') if priced else None,
            },
            'high': {
                'symbol': priced[-1].get('symbol') if priced else None,
                'issuer': priced[-1].get('issuer_name') if priced else None,
                'price': priced[-1].get('price') if priced else None,
            },
        },
    }


def markdown(snapshot: dict, base: str) -> str:
    ref = snapshot['reference']
    ratio = f"{ref['observed_ratio']:.2f}×" if isinstance(ref['observed_ratio'], (int, float)) else 'not reported'
    low = ref['low']
    high = ref['high']
    low_price = f"{low['price']:.2f}" if isinstance(low['price'], (int, float)) else 'N/A'
    high_price = f"{high['price']:.2f}" if isinstance(high['price'], (int, float)) else 'N/A'
    return f"""# Current Bell demo values

Generated from the credential-free public receipt. Read this file immediately before recording.

- Observed: `{snapshot['observed_at'] or 'N/A'}`
- Published: `{snapshot['published_at'] or 'N/A'}`
- Reference: **{ref['name']}** (`rwa_id={ref['rwa_id']}`)
- Route: **{ref['state']}**
- Representations: **{ref['token_count']}**
- Issuers: **{ref['issuer_count']}**
- Observed quote spread: **{ratio}**
- Low endpoint: **{low.get('symbol') or 'N/A'} · {low_price} · {low.get('issuer') or 'issuer unresolved'}**
- High endpoint: **{high.get('symbol') or 'N/A'} · {high_price} · {high.get('issuer') or 'issuer unresolved'}**

## Capture URLs

- [Root product]({base.rstrip('/')}/)
- [Direct reference case]({base.rstrip('/')}/?reference={ref['rwa_id']})
- [Credential-free receipt]({base.rstrip('/')}/api/integrity)

## Narration boundary

Say that Bell observed a contradiction and routes the user to diligence. Do not call the spread a discount, parity gap, fraud finding, executable saving or investment recommendation.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='https://bell.dyplux.com', help='public Bell origin')
    parser.add_argument('--reference', default='Silver', help='reference to prepare')
    parser.add_argument('--json', action='store_true', help='print machine-readable JSON instead of Markdown')
    args = parser.parse_args()
    try:
        receipt = fetch_receipt(args.base)
        snapshot = demo_snapshot(receipt, args.reference)
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f'error: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(snapshot, indent=2) if args.json else markdown(snapshot, args.base))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

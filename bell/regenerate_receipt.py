#!/usr/bin/env python3
"""Recompute the published receipt from the shipped credential-free inputs.

The receipt is a deterministic function of the input package this repository
ships, so when the scan changes, the receipt can be regenerated offline with no
API key and no network. `verify_integrity_receipt.py` then re-runs the same scan
and asserts structural equality, which is what makes the "replayable" claim mean
something.

Usage: PYTHONPATH=bell python3 bell/regenerate_receipt.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rwa_integrity import scan  # noqa: E402

PROOF = os.path.join(HERE, 'site', 'proof')
INPUTS = os.path.join(PROOF, 'rwa-surface-integrity-inputs-2026-09-21.json')
RECEIPT = os.path.join(PROOF, 'rwa-surface-integrity-latest-replay-2026-09-21.json')


def main() -> int:
    if not os.path.exists(INPUTS):
        sys.exit(f'input package not found: {INPUTS}')
    with open(INPUTS, encoding='utf-8') as handle:
        package = json.load(handle)
    if package.get('credential_free') is not True:
        sys.exit('refusing to regenerate from a package that is not credential-free')

    surfaces = package['surfaces']
    recomputed = scan(
        surfaces['map'], surfaces['asset_list'], surfaces['quotes'],
        surfaces['info'], surfaces['issuers'],
        observed_at=package['observed_at'],
        crypto_info_payload=surfaces['crypto_info'],
    )

    with open(RECEIPT, encoding='utf-8') as handle:
        previous = json.load(handle)

    before = sum(1 for a in previous.get('alerts', []) if a.get('comparison'))
    after = sum(1 for a in recomputed.get('alerts', []) if a.get('comparison'))

    with open(RECEIPT, 'w', encoding='utf-8') as handle:
        json.dump(recomputed, handle, indent=2, sort_keys=False)
        handle.write('\n')

    print(f'receipt regenerated from {os.path.basename(INPUTS)}')
    print(f'observed_at: {recomputed.get("observed_at")}')
    print(f'references carrying a published comparison: {before} -> {after}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

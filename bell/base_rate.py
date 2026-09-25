#!/usr/bin/env python3
"""How often is a tokenised-asset comparison safe to make at all?

    PYTHONPATH=bell python3 bell/base_rate.py
    PYTHONPATH=bell python3 bell/base_rate.py --json bell/site/proof/base-rate.json

A screener puts two tokens of the same underlying side by side and shows you the
cheaper one. That is only meaningful if they are the same thing: same instrument,
same unit, same market state. CoinMarketCap's RWA surfaces carry no field that
says whether they are, and nothing in the catalogue refuses the comparison on
your behalf.

`demo.py` shows that a comparison *can* be unsafe, on a handful of worked
references. That is a demonstration. This measures how often it is unsafe across
the whole catalogue, which is a different claim and a much harder one to wave
away.

METHOD, stated before the number so it cannot be tuned afterwards:

  population   every reference in CoinMarketCap's RWA map that the shipped
               credential-free input package covers. No sampling, no ranking, no
               selection: the whole catalogue as captured.
  denominator  references carrying TWO OR MORE token representations - the only
               ones where a comparison is a thing a user could attempt. A
               single-representation reference is EXCLUDED, not counted as a
               negative: there is nothing to compare, so the question does not
               arise and scoring it either way would be dishonest.
  numerator    of those, the ones this monitor refuses to compare, by coded rule:
               a critical signal (identity, unit or market state contradictory),
               price dispersion beyond a plausible wrapper spread, or a spread
               above the published publishable ceiling.
  reported     the refusal rate with a Wilson 95% interval, and the refusals
               broken down by which rule fired, so the rate can be argued with
               rather than only believed.

WHAT THIS IS NOT. It measures one captured observation of the catalogue, not a
24-hour average, and a reference's state can change between runs. "Comparable"
here means the prices can honestly be set side by side - it says nothing about
backing, redemption, eligibility or custody, none of which this monitor observes.
A refusal is not an accusation against an issuer; most refusals are missing or
contradictory data in the surfaces, not misconduct.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rwa_integrity import comparable_routes, scan  # noqa: E402

INPUTS = os.path.join(HERE, 'site', 'proof',
                      'rwa-surface-integrity-inputs-2026-09-21.json')

# A comparison needs at least two things to compare. Below this the question
# does not arise, so the reference leaves the denominator rather than counting
# against the rate.
MIN_REPRESENTATIONS = 2


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval. Normal approximation is unreliable near 0 and 1,
    and a base rate that sits near either end is exactly the case here."""
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    margin = (z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))) / denom
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def _no_route_reason(representations: list) -> str:
    """Why did the route filter leave fewer than two comparable rows?

    Reported separately because the three causes say different things about the
    catalogue: one is a data gap, one is a catalogue of untraded listings, and
    one is a price that cannot belong to the same instrument.
    """
    from rwa_integrity import MAX_PUBLISHABLE_SPREAD_BPS, number

    priced_and_traded = []
    unpriced = 0
    untraded = 0
    for token in representations:
        if token.get('is_derivative'):
            continue
        price = number(token.get('price'))
        volume = number(token.get('volume_24h'))
        if price is None or price <= 0:
            unpriced += 1
        elif volume is None or volume <= 0:
            untraded += 1
        else:
            priced_and_traded.append(float(price))

    if len(priced_and_traded) >= 2:
        lo, hi = min(priced_and_traded), max(priced_and_traded)
        if (hi / lo - 1) * 10_000 > MAX_PUBLISHABLE_SPREAD_BPS:
            return 'SPREAD_ABOVE_PUBLISHABLE_CEILING'
        return 'NO_TRADABLE_PAIR'
    if untraded:
        return 'REPRESENTATIONS_QUOTED_BUT_UNTRADED'
    if unpriced:
        return 'REPRESENTATIONS_WITHOUT_A_PRICE'
    return 'FEWER_THAN_TWO_SPOT_REPRESENTATIONS'


COVERAGE_CODES = {'REPRESENTATIONS_WITHOUT_A_PRICE', 'REPRESENTATIONS_QUOTED_BUT_UNTRADED'}


def _split_refusals(reasons) -> dict:
    """Source incompleteness versus data that contradicts itself.

    Anything unrecognised counts as a contradiction, so a rule added later is
    never quietly filed under "not our problem".
    """
    coverage = sum(n for code, n in reasons.items() if code in COVERAGE_CODES)
    contradiction = sum(n for code, n in reasons.items() if code not in COVERAGE_CODES)
    total = coverage + contradiction
    return {
        'source_coverage': coverage,
        'data_contradiction': contradiction,
        'coverage_share': round(coverage / total, 4) if total else 0.0,
        'coverage_codes': sorted(COVERAGE_CODES),
        'counts': 'reasons, not references: one reference can fail more than one rule',
    }


def measure(receipt: dict) -> dict:
    index = receipt.get('alert_index') or []
    population = len(index)

    single, considered = [], []
    for row in index:
        reps = row.get('representations') or []
        if len(reps) < MIN_REPRESENTATIONS:
            single.append(row)
        else:
            considered.append(row)

    refused, comparable = [], []
    reasons = Counter()
    for row in considered:
        codes = row.get('signal_codes') or []
        severities = row.get('signal_severities') or []
        critical = any(s == 'critical' for s in severities)
        routes = comparable_routes(row.get('representations') or [])
        if critical:
            refused.append(row)
            for code, sev in zip(codes, severities):
                if sev == 'critical':
                    reasons[code] += 1
        elif 'PRICE_DISPERSION' in codes:
            refused.append(row)
            reasons['PRICE_DISPERSION'] += 1
        elif routes is None:
            refused.append(row)
            # `routes is None` has three distinct causes and lumping them
            # together hides the most interesting one. Re-derive which it was,
            # because "the catalogue lists wrappers nobody trades" and "the
            # prices are too far apart to be the same instrument" are different
            # findings about the surface.
            reasons[_no_route_reason(row.get('representations') or [])] += 1
        else:
            comparable.append((row, routes))

    lo, hi = wilson(len(refused), len(considered))
    return {
        'observed_at': receipt.get('observed_at'),
        'population': population,
        'excluded_single_representation': len(single),
        'denominator_two_or_more_representations': len(considered),
        'refused': len(refused),
        'comparable': len(comparable),
        'refusal_rate': (len(refused) / len(considered)) if considered else 0.0,
        'refusal_rate_ci95': [lo, hi],
        'refusal_reasons': dict(reasons.most_common()),
        # Two different things were being added into one rate. A refusal because
        # CoinMarketCap publishes no price for the second wrapper is a COVERAGE
        # fact about the source; a refusal because the rows that exist disagree
        # is a CONTRADICTION found in the data. Reported as one 64.3%, it reads
        # as an indictment of the market when most of it is an incomplete
        # catalogue. Publish the split so nobody has to re-derive it.
        'refusal_split': _split_refusals(reasons),
        'method': {
            'population': 'every reference in the captured RWA map',
            'denominator': f'references with >= {MIN_REPRESENTATIONS} token representations',
            'excluded': 'single-representation references, which cannot be compared at all',
            'numerator': 'references this monitor refuses to compare, by coded rule',
            'interval': 'Wilson score, 95%',
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Measure the comparability base rate.')
    parser.add_argument('--json', help='write the result to this path as well')
    args = parser.parse_args()

    if not os.path.exists(INPUTS):
        sys.exit(f'input package not found: {INPUTS}')
    with open(INPUTS, encoding='utf-8') as handle:
        package = json.load(handle)
    surfaces = package['surfaces']
    receipt = scan(
        surfaces['map'], surfaces['asset_list'], surfaces['quotes'],
        surfaces['info'], surfaces['issuers'],
        observed_at=package['observed_at'],
        crypto_info_payload=surfaces['crypto_info'],
    )

    result = measure(receipt)
    rate = result['refusal_rate'] * 100
    lo, hi = (x * 100 for x in result['refusal_rate_ci95'])

    print()
    print('How often is a tokenised-asset comparison safe to make at all?')
    print(f"observed {result['observed_at']} · no API key used · whole catalogue, not a sample")
    print()
    print(f"  {result['population']:>5}  references in the catalogue")
    print(f"  {result['excluded_single_representation']:>5}  have one representation - "
          f"nothing to compare, excluded rather than counted against the rate")
    print(f"  {result['denominator_two_or_more_representations']:>5}  carry two or more, "
          f"so a comparison is something a user could attempt")
    print()
    print(f"  {result['refused']:>5}  of those are refused by a coded rule")
    print(f"  {result['comparable']:>5}  are published with the comparison performed")
    print()
    print(f"  Refusal rate  {rate:.1f}%   (95% CI {lo:.1f}% to {hi:.1f}%, "
          f"n = {result['denominator_two_or_more_representations']})")
    print()
    split = result['refusal_split']
    reason_total = split['source_coverage'] + split['data_contradiction']
    print(f"  the {reason_total} reasons behind those {result['refused']} refusals:")
    print(f"    {split['source_coverage']:>4}  the catalogue offers no second number to compare "
          f"({split['coverage_share']:.0%})")
    print(f"    {split['data_contradiction']:>4}  the rows that do exist contradict each other")
    if reason_total != result['refused']:
        # Say it rather than let the arithmetic look wrong: a reference can fail
        # more than one rule, so reasons outnumber references.
        print(f"    (reasons exceed references by {reason_total - result['refused']}: "
              f"a reference can fail more than one rule)")
    print()
    print('  The first group is CoinMarketCap coverage, not a finding about the market.')
    print('  The second is a contradiction this scanner located in the published data.')
    print()
    print('  why the refusals fire:')
    for code, count in result['refusal_reasons'].items():
        marker = '  (coverage)' if code in COVERAGE_CODES else ''
        print(f'    {count:>4}  {code}{marker}')
    print()
    print('  Comparable means the prices can honestly be set side by side. It says')
    print('  nothing about backing, redemption, eligibility or custody. A refusal is')
    print('  a statement about the data, not an accusation against an issuer.')
    print()

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
        print(f'  written to {args.json}')
        print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

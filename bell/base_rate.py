#!/usr/bin/env python3
"""How often is a tokenised-asset comparison safe to make at all?

    PYTHONPATH=bell python3 bell/base_rate.py
    PYTHONPATH=bell python3 bell/base_rate.py --json bell/site/proof/base-rate.json

A screener can put two tokens under one CMC RWA reference side by side and show
their observed quotes. That alone does not establish the same instrument, unit
or market state. CoinMarketCap's RWA surfaces carry no field that proves those
claims, so this measurement concerns what Bell's coded filters permit, not proof
that two wrappers are economically equivalent.

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
  numerator    of those, the ones this monitor refuses to compare, by coded
               review rule. Some rules flag quote or field combinations; they
               do not prove economic equivalence or contradiction.
  reported     the refusal rate with a Wilson 95% interval, and the refusals
               broken down by which rule fired, so the rate can be argued with
               rather than only believed.

WHAT THIS IS NOT. It measures one captured observation of the catalogue, not a
24-hour average, and a reference's state can change between runs. "Comparable"
here means filtered prices can be read side by side - it does not establish
equivalent units or claims, or backing, redemption, eligibility or custody.
A refusal is not an accusation against an issuer; missing coverage and review
triggers are observations about the returned surfaces, not misconduct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rwa_integrity import is_derivative_row, BLOCKING_WARNINGS, comparable_routes, number, scan  # noqa: E402

INPUTS = os.path.join(HERE, 'site', 'proof',
                      'rwa-surface-integrity-inputs-2026-09-28.json')
RULE_FILES = {
    'bell/base_rate.py': os.path.abspath(__file__),
    'bell/rwa_integrity.py': os.path.join(HERE, 'rwa_integrity.py'),
}

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
        # CMC never sends is_derivative; reading it alone let every derivative
        # row into this count. One detector, in rwa_integrity.
        if is_derivative_row(token):
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
NOT_APPLICABLE_CODES = {'FEWER_THAN_TWO_SPOT_REPRESENTATIONS'}
DATA_REVIEW_CODES = {
    'ZERO_MCAP_POSITIVE_VOLUME', 'PRICE_DENOMINATION_BREAK', 'PRICE_DISPERSION',
    'SPREAD_ABOVE_PUBLISHABLE_CEILING',
}


def _split_refusals(reasons) -> dict:
    """Separate missing coverage, review triggers, and no eligible spot pair.

    Unknown future rules stay visible in `unclassified`; they are never
    silently described as contradictions or as source coverage.
    """
    coverage = sum(n for code, n in reasons.items() if code in COVERAGE_CODES)
    not_applicable = sum(n for code, n in reasons.items() if code in NOT_APPLICABLE_CODES)
    data_review = sum(n for code, n in reasons.items() if code in DATA_REVIEW_CODES)
    known = COVERAGE_CODES | NOT_APPLICABLE_CODES | DATA_REVIEW_CODES
    unclassified = sum(n for code, n in reasons.items() if code not in known)
    total = coverage + not_applicable + data_review + unclassified
    return {
        'source_coverage': coverage,
        'data_review': data_review,
        'not_applicable': not_applicable,
        'unclassified': unclassified,
        'reason_total': total,
        'coverage_share': round(coverage / total, 4) if total else 0.0,
        'coverage_codes': sorted(COVERAGE_CODES),
        'not_applicable_codes': sorted(NOT_APPLICABLE_CODES),
        'data_review_codes': sorted(DATA_REVIEW_CODES),
        'counts': 'rule hits, not references: one reference can trigger more than one rule',
    }


def _single_representation_lens(single: list) -> dict:
    """What CMC does and does not report about the references that cannot be compared.

    547 of 791 references carry one representation, so the comparison rate
    excludes 69% of the catalogue - correctly, because there was never a
    comparison to refuse. But excluding them was the only thing this product
    said about them, and a research desk holding one of those 547 was handed
    nothing.

    The first version of this counted CODES and printed two of them, so the
    published lines added to 541 of 547 and the six in between included two
    references whose fields triggered a review rule, hidden by the only
    measurement it makes over most of its
    catalogue. A reviewer did the arithmetic.

    So it partitions REFERENCES, by the most serious thing observed about each,
    and the parts sum to the whole. A reference can carry several codes; it
    cannot be in two parts. The market-data category is a review trigger, not
    proof that the asset itself is inconsistent.
    """
    review_codes = {'ZERO_MCAP_POSITIVE_VOLUME', 'PRICE_DENOMINATION_BREAK',
                    'PRICE_DISPERSION', 'SYMBOL_COLLISION', 'DERIVATIVE_MIX',
                    'SPREAD_ABOVE_PUBLISHABLE_CEILING'}
    review, incomplete, context_only, complete = [], [], [], []
    for row in single:
        codes = set(row.get('signal_codes') or [])
        if codes & review_codes:
            review.append(row)
        elif 'MARKET_FIELDS_MISSING' in codes or 'TOKEN_INFO_MISSING' in codes:
            incomplete.append(row)
        elif codes:
            context_only.append(row)
        else:
            complete.append(row)
    total = len(single)
    parts = {
        'review_trigger_rows': len(review),
        'incomplete_source_fields': len(incomplete),
        'context_only': len(context_only),
        'fully_reported': len(complete),
    }
    # A bare `assert` over an if/elif/else partition: it vanishes under
    # `python3 -O` and could not fail anyway, so it looked like a guarantee and
    # was neither. Raised, and it now checks the thing that CAN go wrong -
    # a reference counted in no part because a new signal code was added
    # without deciding which part it belongs to.
    if sum(parts.values()) != total:
        raise SystemExit(
            f'the single-representation lens accounts for {sum(parts.values())} of {total} '
            'references. A new signal code was added without deciding which part it belongs to.')
    return {
        'references': total,
        'reasons': dict(Counter(code for row in single
                                for code in (row.get('signal_codes') or [])).most_common()),
        'incomplete_share': round(parts['incomplete_source_fields'] / total, 4) if total else 0.0,
        'partition': ('by reference, by the most serious thing observed about each, so the parts '
                      'sum to the whole. These references are excluded from the refusal rate '
                      'because there was never a comparison to refuse, not because they were '
                      'approved.'),
        **parts,
    }


def read_json(path):
    """Read a JSON file and say what is wrong with it if it will not read.

    verify_integrity_receipt.py was hardened and these two entry points were
    not, though the README leads with them: a truncated or wrong-typed file
    answered with a raw JSONDecodeError stack in the command a reader is told
    to run first.
    """
    try:
        with open(path, encoding='utf-8') as handle:
            value = json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f'{path} is missing')
    except json.JSONDecodeError as error:
        raise SystemExit(f'{path} is not readable JSON: {error.msg.rstrip(" at")} '
                         f'at line {error.lineno}, column {error.colno}') from None
    except UnicodeDecodeError as error:
        raise SystemExit(f'{path} is not valid UTF-8: {error.reason}') from None
    if not isinstance(value, dict):
        raise SystemExit(f'{path} is not a JSON object')
    return value


def measure(receipt: dict) -> dict:
    index = receipt.get('alert_index') or []
    population = len(index)
    if not population:
        raise SystemExit(
            'the receipt carries no alert_index, so there is no population to measure. '
            'This is a broken input, not a refusal rate of 100%.')
    # Poisoning every price with NaN made this command exit 0 and publish
    # "Refusal rate 100.0%", because a non-numeric price is correctly read as no
    # price and every comparison is correctly refused. Each step is right and
    # the published sentence is not: that is a measurement of a broken input,
    # not of the catalogue. The product refuses to compare when the evidence
    # cannot carry the comparison; it has to hold itself to that here too.
    priced = [row for row in index
              if len([token for token in (row.get('representations') or [])
                      if number(token.get('price')) is not None
                      and number(token.get('price')) > 0]) >= MIN_REPRESENTATIONS]
    if not priced:
        raise SystemExit(
            f'no reference in {population} carries two positive prices, so no comparison could '
            'be attempted anywhere in the catalogue. That is a degenerate input, not a refusal '
            'rate: check the quotes surface before reading a number off this.')

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
        elif BLOCKING_WARNINGS & set(codes):
            # Was a hardcoded 'PRICE_DISPERSION', a second copy of a rule the
            # engine already names. The two numbers this file produces are the
            # headline figures on the judge page, so a divergence here would
            # publish the old rules under the new ones.
            blocked_by = sorted(BLOCKING_WARNINGS & set(codes))
            refused.append(row)
            for code in blocked_by:
                reasons[code] += 1
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
        'schema_version': 'bell.base_rate.v2',
        'observed_at': receipt.get('observed_at'),
        'population': population,
        'excluded_single_representation': len(single),
        'denominator_two_or_more_representations': len(considered),
        'refused': len(refused),
        'comparable': len(comparable),
        'refusal_rate': (len(refused) / len(considered)) if considered else 0.0,
        'refusal_rate_ci95': [lo, hi],
        'refusal_reasons': dict(reasons.most_common()),
    # Keep source coverage, data-review triggers, and absence of an eligible
    # pair separate. A review rule is not proof that the underlying asset or
    # market is contradictory.
        'refusal_split': _split_refusals(reasons),
        'single_representation_lens': _single_representation_lens(single),
        'method': {
            'population': 'every reference in the captured RWA map',
            'denominator': f'references with >= {MIN_REPRESENTATIONS} token representations',
            'excluded': 'single-representation references, which cannot be compared at all',
            'numerator': 'references this monitor refuses to compare, by coded rule',
            'interval': 'Wilson score, 95%',
        },
    }


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def measure_input_package(path: str) -> dict:
    """Recompute one dated result and bind it to the exact inputs and rules."""
    package = read_json(path)
    surfaces = package.get('surfaces')
    required = {'map', 'asset_list', 'quotes', 'info', 'issuers', 'crypto_info'}
    if not isinstance(surfaces, dict) or required - surfaces.keys():
        missing = sorted(required - set(surfaces or {}))
        raise SystemExit(f'{path} is missing scan surfaces: {", ".join(missing)}')
    receipt = scan(
        surfaces['map'], surfaces['asset_list'], surfaces['quotes'],
        surfaces['info'], surfaces['issuers'],
        observed_at=package.get('observed_at'),
        crypto_info_payload=surfaces['crypto_info'],
    )
    result = measure(receipt)
    repository = os.path.dirname(HERE)
    def relative(source: str) -> str:
        try:
            return os.path.relpath(os.path.abspath(source), repository)
        except ValueError:
            return os.path.abspath(source)
    rule_hashes = {name: sha256_file(source) for name, source in RULE_FILES.items()}
    rules_fingerprint = hashlib.sha256(
        '\n'.join(f'{name}:{rule_hashes[name]}' for name in sorted(rule_hashes)).encode('utf-8')
    ).hexdigest()
    result['provenance'] = {
        'inputs_file': relative(path),
        'inputs_sha256': sha256_file(path),
        'rules_files': rule_hashes,
        'rules_sha256': rules_fingerprint,
        'description': 'normalized captured CMC inputs recomputed by the checked-in Bell rules',
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description='Measure the comparability base rate.')
    parser.add_argument('--inputs', default=INPUTS,
                        help='normalized input package (defaults to the latest dated capture)')
    parser.add_argument('--json', help='write the result to this path as well')
    args = parser.parse_args()

    if not os.path.exists(args.inputs):
        sys.exit(f'input package not found: {args.inputs}')
    result = measure_input_package(args.inputs)
    rate = result['refusal_rate'] * 100
    lo, hi = (x * 100 for x in result['refusal_rate_ci95'])

    print()
    print('How often is a tokenised-asset comparison safe to make at all?')
    print(f"observed {result['observed_at']} · no API key used · whole catalogue, not a sample")
    print()
    # "791 references in the catalogue" sat beside a README sentence saying
    # the page searches a 7,811-entry catalogue. Both numbers were right and
    # the word was doing two jobs: 7,811 is the CMC map, 791 is the subset
    # carrying tokenised representations, which is the only population a
    # comparison rate can be measured over.
    print(f"  {result['population']:>5}  references carrying tokenised representations")
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
    reason_total = split['reason_total']
    print(f"  the {reason_total} reasons behind those {result['refused']} refusals:")
    print(f"    {split['source_coverage']:>4}  the catalogue offers no second number to compare "
          f"({split['coverage_share']:.0%})")
    print(f"    {split['data_review']:>4}  price or field review rules fired; this does not prove an economic contradiction")
    print(f"    {split['not_applicable']:>4}  fewer than two eligible spot routes; no pair to compare")
    if split['unclassified']:
        print(f"    {split['unclassified']:>4}  unclassified rule hits")
    if reason_total != result['refused']:
        # Say it rather than let the arithmetic look wrong: a reference can fail
        # more than one rule, so reasons outnumber references.
        print(f"    (reasons exceed references by {reason_total - result['refused']}: "
              f"a reference can fail more than one rule)")
    print()
    print('  The first group is CoinMarketCap coverage, not a finding about the market.')
    print('  The review group is a set of rule triggers, not proof of economic contradiction.')
    print()
    # The 547 excluded references were 69% of the catalogue and the only thing
    # the product said about them was that they were excluded. Excluding them
    # from the RATE is right; saying nothing about them is not.
    lens = result['single_representation_lens']
    print(f"  the {lens['references']} references excluded above, because one representation "
          f"is nothing to compare:")
    print(f"    {lens['incomplete_source_fields']:>4}  a field CoinMarketCap does not report "
          f"({lens['incomplete_share']:.0%})")
    print(f"    {lens['review_trigger_rows']:>4}  references triggered quote or field review rules")
    print(f"    {lens['context_only']:>4}  complete, with a context note such as no tracked "
          f"TradFi market")
    print(f"    {lens['fully_reported']:>4}  complete, with nothing observed against them")
    print(f"       = {sum((lens['incomplete_source_fields'], lens['review_trigger_rows'], lens['context_only'], lens['fully_reported']))}, "
          f"a partition of references and not a count of reasons")
    print()
    print('  So the majority of the catalogue cannot be compared, and for most of that')
    print('  majority the reason is the source rather than the asset. That is a coverage')
    print('  fact about CoinMarketCap, not a verdict on any issuer, and these references')
    print('  are excluded from the rate above rather than counted as passes.')
    print()
    print('  why the refusals fire:')
    for code, count in result['refusal_reasons'].items():
        marker = '  (coverage)' if code in COVERAGE_CODES else ''
        print(f'    {count:>4}  {code}{marker}')
    print()
    print('  A published comparison means filtered prices can be read side by side;')
    print('  equivalent units are not established. It says nothing about backing,')
    print('  redemption, eligibility or custody. A refusal is')
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

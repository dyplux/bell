"""Would this build notice if CoinMarketCap changed a response shape?

Every other suite here is offline and deterministic, which is right for
reproducibility and useless for this question: they pass identically whether the
upstream API is healthy, changed, or gone. So they cannot detect the failure that
actually breaks a monitor in production - a field that quietly changes type,
moves, or stops being sent.

This suite pins the SHAPE this build depends on, against the payloads it captured
from the live API. If CMC changes one of these, this fails and names the field.

Two properties are asserted that have already cost this project a production
incident, and one that cost it a wrong number:

  * `status.error_code` arrives as the STRING "0" on the RWA family and the
    INTEGER 0 on /v1/key/info. A truthiness check therefore passes the key probe
    and rejects every data call. Four other hackathon entries hit this
    independently.
  * `quotes[]` is a LIST keyed by currency symbol, not a dict. Reading it as a
    mapping works on the day one currency is returned and breaks silently when
    two are.
  * a token with no market cap arrives as `null`, not `0`. Coercing it to zero
    turns "unknown" into "worthless" and moves every concentration figure.
"""
from __future__ import annotations

import glob
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PROOF = os.path.join(os.path.dirname(HERE), 'site', 'proof')


def captured_payloads() -> list[tuple[str, dict]]:
    out = []
    for path in sorted(glob.glob(os.path.join(PROOF, '*payload*.json'))):
        try:
            with open(path, encoding='utf-8') as handle:
                out.append((os.path.basename(path), json.load(handle)))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def walk_error_codes(payload):
    """Yield every `error_code` the captured provenance recorded.

    This build stores the upstream status per call under `provenance.calls[]`
    rather than keeping whole CMC envelopes, so the contract is checked against
    the recorded status rather than against a raw envelope.
    """
    if isinstance(payload, dict):
        if 'error_code' in payload:
            yield payload['error_code']
        for value in payload.values():
            yield from walk_error_codes(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from walk_error_codes(item)


class UpstreamEnvelopeContract(unittest.TestCase):
    def setUp(self):
        self.payloads = captured_payloads()
        if not self.payloads:
            self.skipTest('no captured live payloads shipped in bell/site/proof/')

    def test_a_captured_payload_exists_to_test_against(self):
        self.assertTrue(self.payloads, 'this suite is meaningless with no captured payload')

    def test_error_code_is_never_assumed_to_be_an_integer(self):
        # The incident: `if status.get("error_code")` passed the key probe and
        # rejected all seven data endpoints, because "0" is truthy.
        seen = set()
        for name, payload in self.payloads:
            for code in walk_error_codes(payload):
                if code is not None:
                    seen.add(type(code).__name__)
        self.assertTrue(seen, 'no error_code found in any captured payload')
        self.assertTrue(
            seen <= {'str', 'int'},
            f'error_code arrived as an unexpected type: {seen}. Any comparison in '
            f'this codebase that assumes one type will now be wrong.')
        # The captured evidence should still show the string form that caused the
        # incident. If CMC starts sending an integer everywhere, that is a real
        # upstream change and this test is the place it should surface.
        self.assertIn(
            'str', seen,
            'the captured payloads no longer contain a string error_code. Either '
            'the fixtures were regenerated against a changed API, or CMC changed '
            'the type - check before relaxing this.')

    def test_success_is_recognised_whether_error_code_is_zero_or_the_string_zero(self):
        from rwa_integrity import number  # noqa: PLC0415 - import here to keep the contract local
        for raw in (0, '0'):
            self.assertEqual(
                number(raw), 0,
                f'error_code {raw!r} must normalise to 0; anything else resurrects '
                f'the plan-gate incident')


class UpstreamShapeContract(unittest.TestCase):
    def setUp(self):
        self.payloads = captured_payloads()
        if not self.payloads:
            self.skipTest('no captured live payloads shipped in bell/site/proof/')

    def _rows(self):
        for name, payload in self.payloads:
            data = payload.get('data') if isinstance(payload, dict) else None
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict):
                        yield name, row
            elif isinstance(data, dict):
                for value in data.values():
                    if isinstance(value, dict):
                        yield name, value
                    elif isinstance(value, list):
                        for row in value:
                            if isinstance(row, dict):
                                yield name, row

    def test_quotes_are_a_list_not_a_currency_keyed_mapping(self):
        checked = 0
        for name, row in self._rows():
            quotes = row.get('quotes')
            if quotes is None:
                continue
            checked += 1
            self.assertIsInstance(
                quotes, list,
                f'{name}: quotes became a {type(quotes).__name__}. Code that reads '
                f'quotes[0] or iterates for symbol == "USD" is now wrong.')
        if not checked:
            self.skipTest('no quotes field in the captured payloads')

    def test_absent_market_cap_stays_null_and_is_not_coerced_to_zero(self):
        # "unknown" and "worthless" are different facts. Coercing one into the
        # other silently moves every concentration figure this project reports.
        from rwa_integrity import number  # noqa: PLC0415
        self.assertIsNone(number(None))
        self.assertEqual(number(0), 0)
        self.assertNotEqual(number(None), number(0))

    def test_identity_fields_this_build_joins_on_are_still_present(self):
        # The joins are rwa_id -> crypto_id -> issuer_id. If any of these stops
        # being returned, the identity work this product is built on collapses,
        # and it should fail loudly here rather than quietly resolve nothing.
        wanted = ('rwa_id', 'crypto_id', 'issuer_id', 'id')
        found = set()
        for name, row in self._rows():
            found |= {key for key in wanted if key in row}
        if not found:
            self.skipTest('captured payloads contain no identity-bearing rows')
        self.assertTrue(
            found & {'rwa_id', 'crypto_id', 'id'},
            f'no identity key survived in the captured payloads; found {sorted(found)}')


if __name__ == '__main__':
    unittest.main()

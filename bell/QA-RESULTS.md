# Bell public release verification

This file records reproducible software checks for the public Bell release.

## Automated checks

Run from the repository root:

```bash
pytest -q bell/tests
node --test cloudflare/tests/worker.test.mjs
node --check bell/site/app.js
node --check bell/site/integrity.js
python3 bell/verify_public_integrity.py
git diff --check
```

The checks cover the deterministic integrity rules, the public receipt
verifier, the Cloudflare publication adapter and JavaScript syntax. The exact
counts can change as the test suite evolves; the commands above are the
release contract.

## Public runtime contract

The public monitor is designed to work without an API key:

- the browser reads a normalized receipt from `GET /api/integrity`;
- a dated replay is available under `bell/docs/proof/`;
- the receipt exposes observation and publication timestamps, freshness state,
  source hashes, stable-ID join coverage and rule evidence;
- raw authenticated CMC responses and credentials are not part of the public
  response;
- a stale or dated response is labelled as such rather than presented as a
  current quote.

The current release checks the full published population index and detailed
evidence for priority cases. Search, state filters, pagination, evidence
disclosures and decision-brief export are browser features covered by the
public site and its deterministic fixtures.

## Product boundaries checked in release review

Bell does not establish backing, redemption, custody, legal eligibility,
solvency or executable liquidity. `FACTUAL COMPARISON OPEN` means only that
the published contradiction rules did not fire for that receipt. It is not an
approval, ranking or trading signal.

The Startup plan does not expose every venue-level market surface. Bell keeps
that limitation visible and routes the unresolved question to external due
diligence instead of converting unavailable data into a conclusion.

## Evidence layout

Public evidence is intentionally split into small, inspectable artifacts:

- `bell/docs/proof/` contains normalized receipts, replay data and the
  sanitized input manifest;
- `bell/integrity_review.py` contains the deterministic calculation path;
- `bell/verify_public_integrity.py` checks the public response contract;
- `bell/tests/` contains unit and integration tests using fixtures;
- `cloudflare/tests/` covers the publication edge.

The commands above are sufficient to reproduce the software checks locally.

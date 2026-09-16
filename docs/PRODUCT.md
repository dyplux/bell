# Bell public product brief

## Flagship product

Bell's RWA Surface Integrity Monitor is a pre-comparison decision gate. It
scans the CoinMarketCap RWA population, joins the map, asset, quote, metadata
and issuer surfaces by stable identifiers, and records whether a user should
compare representations under the same reference.

It is not a token leaderboard, safety score or investment recommendation.

## The public user journey

1. Open the [Integrity Monitor](https://bell.dyplux.com/integrity).
2. Read the observation time, freshness state and population totals.
3. Open the current case, normally the highest-priority contradiction.
4. Search the main queue or the [neutral review queue](https://rwa-surface-review.pages.dev/)
   for an RWA such as Silver, Gold, Tesla or SPY.
5. Inspect the decision, next action and representation rows. Compare two rows
   only when Bell leaves the factual route open; otherwise keep them separate
   and save the handoff.
6. Open the live JSON receipt or the dated replay and verify the timestamps,
   source hashes and stable-ID join coverage.

The output is explicit:

- `COMPARISON WITHHELD`: a critical identity, denomination or market contradiction
  fired; stop ranking the wrapper;
- `INVESTIGATE BEFORE SHORTLIST`: a warning requires classification before
  treating rows as equivalent;
- `FACTUAL COMPARISON OPEN`: no published Bell rule fired, so observed fields
  may be inspected without creating a winner;
- `SINGLE REPRESENTATION`: one wrapper exists, so there is no wrapper ranking.

Every state remains outside investment approval. The lower-level rule labels
are retained in the JSON receipt for audit traceability.

## What Bell adds to CMC discovery

CMC provides RWA references, token representations, issuers and quote fields.
Bell adds the decision protocol around those surfaces:

- population-wide rather than hand-picked review;
- `rwa_id`, `crypto_id` and `issuer_id` joins rather than ticker-only matching;
- explicit distinction between missing and zero values;
- numerical contradiction evidence such as price spread and positive volume with
  zero market cap;
- a next action and allocation boundary for every published decision;
- a credential-free, timestamped receipt that can be replayed offline.

## Public evidence contract

The live response is [`GET /api/integrity`](https://bell.dyplux.com/api/integrity).
The dated replay and sanitized input manifest live in
[`bell/docs/proof/`](../bell/docs/proof/). The manifest records surface counts,
stable-ID coverage and SHA-256 fingerprints. It deliberately does not publish
raw authenticated CMC response bodies.

The browser never receives a CMC key. A Mac mini publisher reads the credential
from a private process environment, runs the deterministic scan and publishes
only normalized evidence through an authenticated Cloudflare Worker route.

## Boundaries

Bell does not independently prove backing, redemption, custody, legal
eligibility, solvency, manipulation or executable liquidity. The Startup plan
does not expose the CMC market-pairs surface used for venue/depth analysis, so
the product records that as an explicit Growth-plan boundary instead of
inventing empty-market evidence.

## Local verification

Replay the dated calculation without credentials:

```bash
python3 bell/integrity_review.py
python3 bell/verify_public_integrity.py
```

Run the public test surface:

```bash
pytest -q bell/tests
node --test cloudflare/tests/worker.test.mjs
node --check bell/site/integrity.js
```

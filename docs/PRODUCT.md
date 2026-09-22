# Bell public product brief

## Flagship product

Bell's RWA Surface Integrity Monitor is a pre-comparison decision gate. It
scans the CoinMarketCap RWA population, joins the map, asset, quote, metadata
and issuer surfaces by stable identifiers, and records whether a user should
compare representations under the same reference.

It is not a token leaderboard, safety score or investment recommendation.

## The public user journey

1. Open the [Bell public page](https://bell.dyplux.com/).
2. Read the observation time, freshness state and population totals.
3. Open the current case, normally the highest-priority contradiction.
4. Search the main `Explore RWA` queue at [Bell](https://bell.dyplux.com/#explorer)
   for an RWA such as Silver, Gold, Tesla or SPY.
5. Inspect the decision, next action and representation rows. Bell changes the
   route for a no-token reference, a single representation or a multi-token
   comparison. It never ranks a single wrapper.
6. For a multi-row reference, inspect the observed quote band and the
   illustrative capital consequence. The band compares rows with the observed
   median only; it is not a fair-value or executable-spread calculation. The
   capital check also shows the proposed amount as a share of reported token
   row volume when positive 24-hour volume is available. That is context, not
   depth or exit capacity.
7. For Gold or Tesla, inspect the published temporal check when present. It
   compares dated movement across the reference group and keeps the result
   descriptive rather than selecting a wrapper.
8. Open the live JSON receipt or the dated replay and verify the timestamps,
   source hashes and stable-ID join coverage.

The output is explicit:

- `DO NOT SHORTLIST`: a critical identity, denomination or market contradiction
  fired; stop ranking the wrapper;
- `INVESTIGATE`: a warning requires classification before
  treating rows as equivalent;
- `FACTS OPEN`: no published Bell rule fired, so observed fields
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
- an observed quote band and explicit capital-preservation handoff for
  references with multiple positive quote rows;
- an amount-to-reported-volume context metric that makes the size question
  visible without presenting rolling volume as executable liquidity;
- a dated temporal check for published Gold and Tesla windows, with the
  underlying receipt and replay inputs linked from the same case;
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

Run `python3 bell/verify_public_surface.py` to check the public page, health
endpoint, live receipt and a published dossier without a CMC credential.

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

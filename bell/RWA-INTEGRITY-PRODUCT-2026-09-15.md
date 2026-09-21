# RWA Surface Integrity Monitor

> Historical product specification based on the 15 September 2026 receipt. The
> current public release is described in `README.md` and `QA-RESULTS.md`; live
> counts may differ as the publisher refreshes the receipt.

## The new product decision

Bell's original promise was too broad: search an RWA, inspect tokens, compare
their sessions and save a brief. CoinMarketCap already provides most of that
discovery surface. The stronger product is a pre-comparison integrity monitor:

> Before comparing representations under a CMC RWA reference, prove that the
> CMC surfaces agree on identity, denomination and market state.

This is not another RWA leaderboard and it does not produce an opaque safety
score. It produces deterministic states and the evidence needed to clear them.

## Why this is a CMC-shaped gap

The [official RWA API](https://coinmarketcap.com/api/real-world-assets-api/)
exposes a stable ID map, a paginated asset list and a quotes endpoint. The
[CMC RWA page](https://coinmarketcap.com/real-world-assets/?type=rwa) already
handles discovery and aggregate display. The API also recommends using `rwa_id`
rather than ambiguous symbols. A user or institution still has to join those
surfaces and notice when the inputs do not line up.

The public table itself shows the gap: it exposes columns such as `RWA / Avg.
Token Price`, market cap and volume, but it does not expose a deterministic
state saying that the underlying representations should not be compared. In the
current page capture, Silver is shown with an RWA price and an average token
price while the detailed receipt resolves the individual representations,
units, issuers and missing market fields. That is the distinction Bell owns:
not more rows, but a decision boundary around the rows.

The live Startup scan captured at `2026-09-15T22:22:00Z` found:

- 7,811 map rows and 7,942 asset-list rows;
- 131 asset-list rows without a stable `rwa_id`;
- 790 tokenised references and 1,428 token representations in the quote scan;
- 790/790 tokenised references resolved again through the metadata endpoint;
- 25 issuer records cross-checked against all 21 issuer IDs seen in quotes;
- captured publisher run: 34 `DO NOT COMPARE`, 662 `INVESTIGATE`, 94 `NO RULE HIT`;
- 4 price groups with a greater-than-10x spread;
- 31 groups with positive 24-hour volume and zero market cap;
- 114 groups mixing derivative-labelled and non-derivative representations;
- 60 groups where the same symbol is reused across representations;
- 647 groups with at least one missing price, market-cap or volume field.

The published receipt also contains a compact `alert_index` for all 790
references. The neutral review route exposes this index as a searchable queue
with state filters, while retaining full token evidence for the highest-priority
alerts.

The monitor records the endpoint boundary as part of the receipt. CMC documents
the map, metadata, issuer and issuer-list surfaces at 30 seconds, and the RWA
list and latest quotes at 60 seconds. A mismatch between surfaces is therefore
treated as a time-sensitive join condition, not as proof of a CMC defect.

These are observations from one dated run, not claims about fraud, backing or
issuer quality. The monitor refuses to turn them into a comparison without
resolving the contradiction. `NO RULE HIT` means only that the published rules
did not fire; it is never a safety approval.

## The 30-second demo

```sh
python3 bell/integrity_review.py
```

The default path reads the dated receipt at
`bell/docs/proof/rwa-surface-integrity-2026-09-15.json`. The live path is:

```sh
CMC_API_KEY='key in the process only' python3 bell/integrity_review.py --live
```

The live run calls the map, info, asset-list, quotes and issuer-list endpoints,
hashes the credential-free evidence and prints the same deterministic summary.
The Mac mini publisher uses the same collector and publishes only the receipt
to `/api/integrity`; it never prints or stores the API key.

An independent viewer can verify the public contract without credentials:

```sh
python3 bell/verify_public_integrity.py
```

The verifier checks HTTP 200, schema, publication freshness metadata, state
counts and the presence of an operational decision effect on the first alert.

## Rules

`PRICE_DENOMINATION_BREAK` is critical at a 10x token-price spread. This can be
a unit difference, a wrapper mismatch or a bad quote; it is not called an
arbitrage opportunity.

`ZERO_MCAP_POSITIVE_VOLUME` is critical because volume cannot safely be read as
an investable market when the same representation reports zero market cap.

Derivative mixing, symbol collisions and missing market fields create an
`INVESTIGATE` state. A ticker never joins two representations; `crypto_id` and
`issuer_id` remain the identity keys.

## CMC surface coverage

| CMC RWA surface | Role in the monitor | Startup boundary |
|---|---|---|
| `map` | population and stable `rwa_id` discovery | used for the full scan |
| `info` | second identity and asset-type join | used for all 790 tokenised references |
| `assets/list` | paginated catalogue surface | used for surface-drift comparison |
| `quotes/latest` | token, aggregate and TradFi market observations | used for all tokenised references |
| `issuers/list` | issuer directory cross-check | used for all 25 tracked issuers |
| `issuers` | single-issuer token roster drill-down | available for follow-up, not needed to classify the population |
| `market-pairs/list` | venue-level market evidence | Growth and above; recorded as a plan boundary, never faked as empty data |

The Startup boundary was tested live for a blocked reference on 15 September:
the endpoint returned HTTP 403, CMC error `1006`, with zero credits. The raw
credential-free result is in
[`bell/docs/proof/startup-market-pairs-boundary-2026-09-15.json`](docs/proof/startup-market-pairs-boundary-2026-09-15.json).
Bell therefore stops before making a venue or execution claim; it does not turn
an unavailable endpoint into a false “no market pairs” result.
The accompanying [sanitized input manifest](docs/proof/rwa-surface-integrity-input-manifest-2026-09-15.json)
records endpoint shapes, row counts, stable-ID coverage and SHA-256 fingerprints
without publishing authenticated CMC response bodies.

## Why this can beat the current Bell

The current Bell asks a user to choose an asset and explore a terminal. The new
monitor starts with a claim a CMC judge can verify immediately: **the RWA
catalogue contains join and comparability conditions that a normal page does
not surface as a decision.** It scans the population, chooses cases by a
published rule and shows raw evidence for Gold, Silver, Tesla and the next
highest-severity alerts.

The product is useful to both sides of the market:

- a normal user is stopped from treating different units or derivatives as the
  same asset;
- an analyst receives a triage queue with exact missing fields;
- an issuer or CMC data team receives a reproducible data-quality report;
- a website can show the warning without pretending to verify legal rights.

## Honest boundary

CMC's RWA fields do not establish redemption, custody, legal eligibility,
reserves, settlement or size-specific execution. Those are explicit next
checks, not hidden assumptions. A monitor that says `DO NOT COMPARE` is more
useful than a score that looks precise while silently combining incompatible
claims.

The dated receipt is a replay artifact. The public page labels whether it is
showing a live Worker receipt or this fallback. A public claim about current
market conditions requires a fresh receipt.

## What a 99-point version must prove

The build is judged on the product loop, not on the existence of a large JSON
file. A live presentation must show the same sequence every time:

1. start with the full RWA population, not a hand-picked token;
2. show the stable `rwa_id` join and the separate endpoint cadences;
3. open Silver or Tesla from the alert queue;
4. expand the raw token evidence and the exact next action;
5. refuse the comparison when the quote state is contradictory;
6. open the public `GET /api/integrity` response and verify its publication
   metadata without a credential;
7. replay the result from the credential-free receipt.

That is the proof of usefulness. It gives a normal user a safe stopping point,
an analyst a triage queue, and a CMC data team a reproducible candidate for
quality review. It does not claim to verify backing, redemption or legal rights.

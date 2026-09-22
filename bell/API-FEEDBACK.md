# CMC API feedback from the Bell surface

This note records what the Bell collection needed from the CMC surfaces and
which user-facing checks those fields enabled. It is feedback from one dated
RWA workflow, not a claim that the API contract is permanent.

## The useful composition

Bell combines several CMC surfaces before it lets a user compare wrappers:

| CMC surface | What Bell uses it for | User consequence |
|---|---|---|
| `/v5/real-world-assets/map` | discover the reference asset and stable RWA ID | search the complete stock, ETF and commodity map |
| `/v5/real-world-assets/assets/list` | reconcile the map with the asset list | expose missing or duplicate identity joins |
| `/v5/real-world-assets/quotes/latest` | read token rows, price, market cap, volume and issuer IDs | show the observed wrapper set without inventing equivalence |
| `/v5/real-world-assets/info` | read reference metadata and TradFi context | distinguish an underlying reference from its token layer |
| `/v5/real-world-assets/issuers/list` | resolve issuer catalogue records | show issuer labels and unresolved joins explicitly |
| `/v2/cryptocurrency/info` | resolve token identity, chain and contract fields | route incomplete identity to diligence before comparison |

The important step is the join. A quote row is not treated as a complete
instrument identity merely because it sits under a familiar reference name.

## What the dated receipt exposed

The live receipt observed on 22 September 2026 covered 791 tokenised
references and 1,435 representations. Its deterministic signals included:

| Signal | Observed count | Route |
|---|---:|---|
| Missing market fields | 646 | investigate completeness and freshness |
| Derivative mix | 119 | separate instrument types |
| Symbol collision | 60 | resolve identity before using the ticker |
| Positive volume with zero market cap | 33 | do not treat the quote row as ready for comparison |
| No tracked TradFi market | 13 | keep the underlying relationship unresolved |
| Price denomination break | 4 | check units, decimals and wrapper claims |
| Missing token information | 4 | resolve chain and contract identity |

The counts are a dated observation from the public `/api/integrity` receipt,
not a permanent property of CMC data. The receipt remains the source of truth.

## Why this became a product, not just an API call

The fields above are transformed into a route a normal investor can act on:

- `DO NOT SHORTLIST` when a critical contradiction makes wrapper ranking unsafe
- `INVESTIGATE` when identity, instrument or market fields need review
- `FACTS OPEN` when Bell has no critical rule hit but external diligence is still required
- `SINGLE REPRESENTATION` when there is no peer wrapper to rank

Each route keeps the observed rows, endpoint context, timestamp, next check and
limitations. Bell does not infer backing, redemption, solvency, liquidity or
executable size from these fields.

## Reproduce the evidence

The 22 September map refresh is bound to
[`site/proof/rwa-catalogue-refresh-2026-09-22.json`](site/proof/rwa-catalogue-refresh-2026-09-22.json).
The earlier multi-surface collection boundary is in
[`site/proof/rwa-surface-integrity-live-collection-2026-09-21.md`](site/proof/rwa-surface-integrity-live-collection-2026-09-21.md).
The credential-free verification commands are:

```sh
python3 bell/verify_catalogue_receipt.py
python3 bell/verify_integrity_receipt.py
python3 bell/verify_public_surface.py
```

The public browser reads published evidence and never receives the CMC key.

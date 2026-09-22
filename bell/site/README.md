# Bell public website

This directory is the public, credential-free Bell surface. It is a single
page product: search a stock, ETF, commodity or other CMC RWA reference, read
the current route, inspect the evidence and open the relevant receipt.

The browser does not call CMC and no API key is bundled in the assets. The
public Worker serves the page and published dossiers. A live receipt is marked
`FRESH`; an older observation is labelled `DATED REPLAY` instead of being
presented as live.

## Run locally

```sh
cd bell/site
python3 -m http.server 8080
```

Open <http://localhost:8080>. The static page works without installation or
credentials. It uses the committed map snapshot and published evidence files.

## Product flow

1. Search a published reference such as Silver, Gold, Tesla or SPY
2. Read the route: `DO NOT SHORTLIST`, `INVESTIGATE`, `FACTS OPEN`,
   `SINGLE REPRESENTATION` or `REFERENCE ONLY`
3. Read the observed quote endpoints, ratio and boundary note before opening deeper evidence
4. Open the representation rows, issuer and market evidence
5. Follow the next diligence step and inspect the dated receipt

After a search, the page keeps the first useful evidence in view: mobile and tablet show the
compact searched-reference result, while desktop opens the wider decision card with capital and
issuer context. The endpoint values are derived from the current receipt rows; they are not
hardcoded examples.

The result can be shared with a stable URL. The page accepts
`?reference=<CMC RWA ID>` and the decision card includes a copy-link action,
so a reviewer can open the same reference without repeating the search.
If the live receipt has no case for a query, the result card sends the user to
the complete RWA map instead of presenting that absence as proof that the asset
does not exist. Map-only searches are preserved as `?map_reference=<name or
slug>` links, so the full-map dossier survives a refresh.

`DO NOT SHORTLIST` means that a critical contradiction was observed. `FACTS
OPEN` is descriptive only and is not approval, ranking or a trading signal.
The 10× value shown in the method panel is a review threshold. A case can show
a higher observed quote ratio, which remains labelled as an observation rather
than a discount, parity claim or execution estimate.

## Public evidence

- `index.html` is the single public product page
- `integrity.js` renders search, filters, routes, evidence and exports
- `integrity.css` and `visual-overrides.css` define the responsive interface
- `catalogue-live.js` contains the dated, credential-free map snapshot
- `proof/rwa-surface-integrity-history.json` contains the public receipt history
- `proof/rwa-surface-integrity-latest-replay-2026-09-21.json` contains the last replay record captured on 21 September
- `proof/rwa-surface-integrity-inputs-2026-09-21.json` contains the normalized public inputs for that 21 September replay
- `proof/rwa-surface-integrity-live-collection-2026-09-21.md` records the live collection boundary

The inputs and replay package are published so that dated deterministic receipt
can be checked without an API key. They are separate from the current live
receipt, which can change on the next scheduled publication. Authenticated
transport headers and raw secrets are never published.

## Verification

From the repository root:

```sh
python3 bell/verify_integrity_receipt.py
python3 bell/verify_public_surface.py
node --test bell/tests/*.cjs
```

The current public release covers a map snapshot of 7,811 references and a
separate live integrity receipt over 791 tokenised references and 1,435
representation rows. These are different datasets with different timestamps.

The deployed page was checked in Chrome at mobile, tablet and desktop widths.
The Silver flow returned `DO NOT SHORTLIST`, while Marvell returned `FACTS
OPEN`; both searches completed without horizontal overflow at a 390px mobile
viewport.

## Boundary

CMC remains the discovery and market-data source. Bell adds deterministic
identity, unit, derivative, issuer and quote-coherence checks before a user
compares wrappers. It does not certify backing, redemption, custody,
eligibility, solvency, liquidity or executable size.

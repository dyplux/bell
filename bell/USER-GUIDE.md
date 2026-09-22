# Bell RWA Surface Integrity Monitor

## What the product does

Bell is a pre-comparison check for tokenised real-world assets. It does not
replace CoinMarketCap's RWA catalogue and it does not issue a safety score. It
answers a narrower question:

> Can these representations be compared as if they were the same exposure?

For an investor, the practical job is simpler: search the reference you are
considering and learn whether it can enter a comparison shortlist yet. Bell
returns a comparison state, the evidence behind it and the next diligence
question. It never turns a clean scan into a buy approval.

The monitor scans the CMC RWA population, joins the available surfaces through
stable identifiers, and turns contradictions into a visible next action.

## A normal user's journey

1. Open the [integrity monitor](https://bell.dyplux.com/).
2. Follow the small `3-MINUTE INVESTOR TASK` in the hero. It is a local browser
   checklist, not an account or a telemetry feature: search the asset, inspect
   the evidence, compare two wrappers only when Bell leaves that route open, or
   keep them separate and record the next check, then save the brief or worksheet.
3. Start with the asset search in the hero. Search for `Silver`, `Gold`, `Tesla`,
   `SPY` or an RWA ID. The result is mirrored in the population queue below.
   When a match exists, use `Open first evidence` above the queue to open the
   first representation disclosure and continue without guessing where to
   click.
   If you want to browse beyond the published integrity receipt, use
   `Explore RWA` in the top navigation. That search covers the complete
   credential-free CMC map snapshot, including stocks, ETFs, commodities and
   references with no mapped wrapper. Select a result to open its route:
   `PUBLISHED RWA DOSSIER` when Bell has investigated it, `SINGLE
   REPRESENTATION` when there is one wrapper, or `REFERENCE ONLY` / `DOSSIER
   PENDING` when comparison evidence is not available. A map entry is not
   silently treated as a clean comparison. If a single wrapper still has a
   critical contradiction or unresolved warning, that evidence state takes
   priority over the single-token label.
4. Check the receipt badge. `LIVE RECEIPT · FRESH` means the current publication
   is inside its 15-minute freshness contract. `STALE` means the last observed
   run is visible but should not be read as current. `DATED REPLAY` means the
   page is using the bundled evidence snapshot.
5. Read the four population numbers: tokenised references, representations,
   blocked comparisons and rows without a stable RWA ID.
6. Follow the decision path: scan the population, join by stable IDs, stop the
   wrapper choice, then route the contradiction to diligence.
7. Open the current flagged case, normally Silver or another highest-severity
   reference. Expand `Inspect evidence` or `Inspect representations` to see
   the RWA ID to `crypto_id` and `issuer_id` identity path, CMC token links, chain/contract identity, prices, issuers, issuer
   websites when CMC publishes them, market cap, volume and the next action.
   Each representation also exposes a compact source path when available:
   CMC token page, issuer site, project site, explorer and technical docs. These
   links are handoff routes for primary-source diligence, not proof that the
   linked material is complete or accurate.
   Select two rows to receive a facts-only summary of observed price, market-cap
   and 24h-volume differences. Bell shows the gap without ranking a wrapper;
   those fields are not normalized for unit, backing, eligibility, liquidity or
   execution.
   When positive market-cap fields are available, the selected case also shows
   issuer concentration for that reference: top-issuer share, HHI, effective
   issuer count and coverage. Use the `NEXT CHECK` line to decide whether the
   issuer terms deserve priority. This is reported token-row value, not legal
   issuer concentration or proof of backing.
   The selected case also shows an observed activity check: positive 24h-volume
   coverage, the top representation's share and rows with zero or missing
   volume. Use it to ask whether an apparent quote difference depends on one
   reported route. CMC token-row volume is a rolling field, not order-book depth
   or executable liquidity.
8. Use the filters to distinguish the operational states:

   | State | Meaning | What the user may do |
   |---|---|---|
   | `DO NOT SHORTLIST` | A critical contradiction fired, such as an observed quote ratio above the 10x review threshold or positive volume with zero market cap. | Stop ranking or substituting a wrapper until the identity, unit or quote issue is resolved. |
   | `INVESTIGATE` | A warning fired, such as derivative mixing, symbol collision or missing fields. | Continue research, but do not present the rows as equivalent exposure. |
   | `FACTS OPEN` | No published Bell rule fired for a reference with multiple representations. | Inspect the observed rows and compare facts, then complete external diligence. This is not approval. |
   | `SINGLE REPRESENTATION` | CMC returned one representation for the reference. | There is no wrapper ranking to perform. Verify the instrument and issuer externally. |

   Use `Save decision brief` on the selected decision card or a queue row to export a Markdown handoff with
   the state, evidence, timestamps, next action and the investment questions
   Bell did not answer. It is a research memo, not a recommendation.

   Open `Open research worksheet` to record the five external checks and one
   research note locally in the browser. The worksheet is a personal handoff,
   not evidence supplied by Bell; the saved decision brief includes its state.

   Use `Watch reference` on a queue row when you want to revisit it. Bell saves
   the reference and the receipt state in this browser only. When a later
   receipt reports a different state, the watchlist shows `STATE CHANGED`.
   This is a local review aid, not a server-side alert or a promise of
   continuous monitoring.

   The first-check strip near the top summarizes the current population route:
   blocked references, references that need investigation and references with
   no published Bell rule hit. It also shows concentration among positive
   market-cap fields by issuer label. These are research observations, not a
   safety score, legal issuer concentration or an approval label.

   Each row also shows a resolution handoff. For a blocked case, resolve the
   Match the RWA ID to the token ID and issuer ID, resolve the identity and unit
   first, then verify issuer and redemption terms and obtain
   execution evidence. For an investigate case, classify the representation and
   keep unresolved wrappers separate. If CMC returns one representation, Bell
   shows a `SINGLE REPRESENTATION PATH`: there is no wrapper ranking to perform.

9. Use the `Previous` and `Next` controls under the main queue to browse every
   matching reference in Bell. The same public page's `Explore RWA` route
   remains the single searchable population queue with state filters and
   pagination.
10. Open the credential-free JSON receipt to verify the observed time, published
    time, freshness state, endpoint method, source hashes and exact evidence.

The explorer and the integrity monitor are two views of the same product. The
monitor answers whether a grouped set should enter a comparison shortlist. The
explorer answers what CMC currently maps for a specific stock, ETF, commodity or
other RWA reference and whether Bell has a published dossier for it. When no
dossier exists, the public edge queues a server-side refresh and shows the
map-only state instead of pretending that missing evidence is a negative result.

## What the product does not claim

CMC RWA and `cryptocurrency/info` fields do not establish backing, redemption, custody, legal eligibility,
settlement or size-specific execution. The Startup plan also does not expose
the market-pairs surface used for venue, depth or spread evidence. Those are
explicit next checks, never silently converted into a clean result.

## Receipts and freshness

The Mac mini collects CMC data with the key kept in its process environment. It
publishes a normalised receipt to Cloudflare D1. The browser receives only the
receipt, never the CMC key.

Each receipt records:

- `observed_at`: when the CMC surfaces were collected;
- the public input manifest also records each surface's first request and last response window, making refresh skew visible instead of hiding it behind one global timestamp;
- `published_at`: when the receipt reached the public edge;
- `status`: `fresh`, `stale` or `dated`;
- `stale_after_seconds`: the current freshness contract;
- `source_hashes`: deterministic hashes of the credential-free input surfaces;
- `alert_index`: the population queue with the representation observations for every indexed reference;
- `alerts`: expanded signal narratives for the highest-priority cases.

The installed launch agents run the asset publisher and the integrity publisher
every 15 minutes. A failed run must remain visible as stale; it must never be
presented as fresh data.

## Local replay

No key is required to replay the dated integrity scan:

```sh
python3 bell/integrity_review.py
```

The public receipt can be checked without credentials:

```sh
python3 bell/verify_public_integrity.py
```

The live publisher is an operator command and reads the CMC key only from the
process environment loaded from `~/.config/dyplux/bell.env`:

```sh
python3 bell/integrity_publisher.py
```

Do not put keys in this repository, in the browser or in a receipt.

## 60-second demo script

1. Show the hero: “Before the comparison, test the surface.”
2. Point to the population count and the live receipt timestamp.
3. Open Silver and show the 31x price spread across representations.
4. Show `DO NOT SHORTLIST` and the concrete next action.
5. Open the population queue and filter `INVESTIGATE`.
6. Show the JSON receipt, observed/published times and the market-pairs plan
   boundary.
7. Close with the distinction: CMC shows the catalogue; Bell tests whether the
   catalogue can support a comparison.

## Submission readiness

The product path and receipts are live and the repository contains the source,
tests, setup guide, receipt verifier and public integrity evidence. The public
source package contains no credentials, jury material, competitor dossiers or
private research artefacts.

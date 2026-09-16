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

1. Open the [integrity monitor](https://bell.dyplux.com/integrity).
2. Follow the small `3-MINUTE INVESTOR TASK` in the hero. It is a local browser
   checklist, not an account or a telemetry feature: search the asset, inspect
   the evidence, select two wrappers only when a factual comparison is useful,
   then save the brief or worksheet.
3. Start with the asset search in the hero. Search for `Silver`, `Gold`, `Tesla`,
   `SPY` or an RWA ID. The result is mirrored in the population queue below.
   When a match exists, use `Open first evidence` above the queue to open the
   first representation disclosure and continue without guessing where to
   click.
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
8. Use the filters to distinguish the operational states:

   | State | Meaning | What the user may do |
   |---|---|---|
   | `COMPARISON WITHHELD` | A critical contradiction fired, such as a 10x price spread or positive volume with zero market cap. | Stop ranking or substituting a wrapper until the identity, unit or quote issue is resolved. |
   | `INVESTIGATE BEFORE SHORTLIST` | A warning fired, such as derivative mixing, symbol collision or missing fields. | Continue research, but do not present the rows as equivalent exposure. |
   | `FACTUAL COMPARISON OPEN` | No published Bell rule fired for a reference with multiple representations. | Inspect the observed rows and compare facts, then complete external diligence. This is not approval. |
   | `SINGLE REPRESENTATION` | CMC returned one representation for the reference. | There is no wrapper ranking to perform. Verify the instrument and issuer externally. |

   Use `Save decision brief` on a queue row to export a Markdown handoff with
   the state, evidence, timestamps, next action and the investment questions
   Bell did not answer. It is a research memo, not a recommendation.

   Open `Open research worksheet` to record the five external checks and one
   research note locally in the browser. The worksheet is a personal handoff,
   not evidence supplied by Bell; the saved decision brief includes its state.

   Each row also shows a resolution handoff. For a blocked case, resolve the
   Match the RWA ID to the token ID and issuer ID, resolve the identity and unit
   first, then verify issuer and redemption terms and obtain
   execution evidence. For an investigate case, classify the representation and
   keep unresolved wrappers separate. If CMC returns one representation, Bell
   shows a `SINGLE REPRESENTATION PATH`: there is no wrapper ranking to perform.

9. Open the [complete searchable population queue](https://rwa-surface-review.pages.dev/)
   when the first twelve detailed cases are not enough. It provides search,
   state filters and pagination for the full index.
10. Open the credential-free JSON receipt to verify the observed time, published
   time, freshness state, endpoint method, source hashes and exact evidence.

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
- `published_at`: when the receipt reached the public edge;
- `status`: `fresh`, `stale` or `dated`;
- `stale_after_seconds`: the current freshness contract;
- `source_hashes`: deterministic hashes of the credential-free input surfaces;
- `alert_index`: the compact population queue;
- `alerts`: detailed evidence for the highest-priority cases.

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
4. Show `COMPARISON WITHHELD` and the concrete next action.
5. Open the population queue and filter `INVESTIGATE`.
6. Show the JSON receipt, observed/published times and the market-pairs plan
   boundary.
7. Close with the distinction: CMC shows the catalogue; Bell tests whether the
   catalogue can support a comparison.

## Submission readiness

The product path and receipts are live and the repository contains the source,
tests, CMC documentation snapshot, jury evidence and dated receipts. Before
sharing the repository with an external juror, use the sanitized public Bell
repository at `https://github.com/dyplux/bell`. The private `desk` repository
continues to hold the internal research desk, jury ballots and competitor
dossiers. The public source package contains the product, tests, setup guide,
receipt verifier and public integrity evidence, but no credentials or private
research artefacts.

## Human validation

The reproducible six-person pilot is documented in
[`HUMAN-PILOT-2026-09-16.md`](HUMAN-PILOT-2026-09-16.md). It tests state
comprehension, next-action comprehension, brief export, boundary comprehension
and repeat-use intent without briefing participants on Bell's thesis.

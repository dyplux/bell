# Bell - RWA Comparability Evidence

> **Live demo:** [bell.dyplux.com](https://bell.dyplux.com/) · **Track:** Real World Assets

Bell is the pre-comparison integrity gate for tokenised stocks, ETFs and commodities. It
does not rank wrappers or tell an investor what to buy. It checks identity and quote fields
for representations grouped under one CMC reference, publishes a filtered price comparison
when its rules allow, and keeps equivalent units, claims and executable markets explicitly
unverified.

## The 60-second judge path

1. Open the [live monitor](https://bell.dyplux.com/)
2. Search `Silver` and read the `DO NOT SHORTLIST` route, observed endpoints and capital hold
3. Search `Marvell` and see the filtered price comparison: the rows pass Bell's
   identity and quote filters, while equivalent units and claims remain unverified;
   Bell names the observed spread without ranking a wrapper
4. Search `Gold` and open the repeat-window evidence
5. Scroll to `POPULATION SHAPE` to see the full-scan route counts and observed spread bands
6. Open `Receipt` or `Inspect credential-free receipt` to verify the dated source evidence

The public page requires no account and no API key. The current live receipt is fresh when the
badge says `LIVE RECEIPT · FRESH`; otherwise the page labels the fallback as dated replay.

## Competition focus

The flagship build is the **RWA Surface Integrity Monitor**. It scans the full
CMC RWA population before a user compares tokenised representations and returns
an evidence-backed decision. The public UI presents five plain-language
routes: `FILTERED QUOTE COMPARISON`, `DO NOT SHORTLIST`, `INVESTIGATE`,
`FACTS OPEN` or `SINGLE REPRESENTATION`. The receipt also keeps
the lower-level rule decision for audit traceability.

The keyless command-line replay is:

```sh
python3 bell/integrity_review.py
```

It reads the shipped receipt and makes no CMC request. For the human-facing
interface, use the `make app` quick start below and open
<http://127.0.0.1:8080/workspace.html>. Opening the HTML file directly or using
Python's static file server does not provide the local receipt or agent API.
The deployed public page reads the latest credential-free receipt and falls
back to a dated replay when needed; older captures remain available as evidence.

To refresh the public integrity receipt from the Mac mini publisher:

```sh
source ~/.config/dyplux/bell.env
python3 bell/integrity_publisher.py
```

The dated CMC surface composition and its user consequences are in
[API-FEEDBACK.md](API-FEEDBACK.md).
The complete visitor journey, receipt lifecycle and demo script are in
[USER-GUIDE.md](USER-GUIDE.md).
The
credential-free public audit pack is available from the single product page at
`https://bell.dyplux.com/`; it explains the setup path, receipt contract,
endpoint map and product boundaries for a reviewer who does not have the
repository checkout.

Bell is also the server-side publisher. `publisher.py` refreshes current CMC evidence into the
credential-free `runtime/` store, while `/api/published?slug=...` lets the website read the latest
dossier without exposing the CMC key. The deployment and refresh boundary are documented in
[`LIVE-PUBLICATION-POLICY.md`](LIVE-PUBLICATION-POLICY.md) and the
[website README](site/README.md).

Bell is a universal real-world asset terminal with a comparability evidence gate and a population-wide RWA Surface Integrity Monitor. It searches the full CMC RWA map and changes its workflow
according to the token layer: underlying-only, one-token dossier or multi-token comparison. The
current credential-free map snapshot contains 7,811 references, including stocks, ETFs,
commodities and other categories returned by CMC. The explorer preserves the asset type returned
by CMC so future RWA categories can use the same route without being presented as covered before
they appear in a receipt.
Comparability and session review are evidence modules inside the terminal, not the whole product.
Bell is a research instrument, not a trading signal.

For the public product rationale and judge path, read the public Bell repository documentation.
The flagship RWA demo is the Surface Integrity Monitor:
run `python3 bell/integrity_review.py` to inspect the latest credential-free replay, or open
`bell/site/index.html` for the visual receipt.
The receipt comparison utility in [`receipt_compare.py`](receipt_compare.py)
compares two dated windows and reports flat-bar diagnostics without treating them as liquidity.
The public integrity receipt also has a [sanitized input manifest](site/proof/rwa-surface-integrity-inputs-2026-09-28.json)
with surface counts, stable-ID join coverage and source fingerprints.
Of the 35 dated observations in the population history, two legacy observations have separately
bundled receipts. New observations retain a full receipt archive and compare its complete summary with the chained
history; per-reference rows are checked when that receipt has a same-rule series step. The
separate 28 September capture has all six inputs but is outside that history. The
population history is at
[`site/proof/rwa-surface-integrity-history.json`](site/proof/rwa-surface-integrity-history.json),
and the latest committed credential-free normalized input package is at
[`site/proof/rwa-surface-integrity-inputs-2026-09-28.json`](site/proof/rwa-surface-integrity-inputs-2026-09-28.json), paired with its
[dated receipt](site/proof/rwa-surface-integrity-capture-2026-09-28.json).
`python3 bell/verify_legacy_replay.py` reproduces the original 21 September state distribution
from the six normalized inputs using a hash-pinned copy of the original scanner, then checks it
against the recovered original receipt and the history entry. `python3 bell/verify_integrity_receipt.py`
separately verifies the later-rule replay and history. Authenticated request headers and transport
metadata are not committed. Both replays are dated artifacts; the live receipt can move independently
when the scheduled publisher observes a new window.
Run `make verify-capture` to reproduce the 28 September capture as a self-contained receipt/input
pair; this remains verifiable after the live endpoint advances.
The dated-series job now archives each new full receipt as deterministic gzip and binds its SHA-256
to the chained history record. `make verify` checks every retained archive against the complete
history summary, including observations that cannot enter the current comparable series after a
rule change. For series steps with retained receipts it also checks every per-reference row.
Retained observations under a newer rule set form a separate same-rule segment in
[`reference-deltas-v3.json`](site/proof/reference-deltas-v3.json); it is never merged into the v2
series. The first v3 interval records two observations 15 minutes apart, including the iShares
Russell 2000 ETF route changing from `do_not_compare` to `investigate` as
`ZERO_MCAP_POSITIVE_VOLUME` disappears. This is a short observed interval, not a daily history.
Older history entries are not backfilled from later data and remain explicitly unverified at row
level where no receipt was retained.
`python3 bell/verify_public_surface.py` performs a credential-free smoke check against the public
page, health endpoint, live receipt and published Gold dossier; it does not call CMC directly.
For the visitor journey and the product boundary, read [USER-GUIDE.md](USER-GUIDE.md).
For the dated population finding behind the catalogue insight, read [MAP-INSIGHT-2026-09-11.md](MAP-INSIGHT-2026-09-11.md).
The public page and receipts are the source of truth for the currently exposed CMC surfaces;
private API-plan notes and internal research records are intentionally not part of this release.

## Terminal brief

The terminal generates a deterministic brief from the selected CMC map entry. A reference with
no token is kept in underlying research mode; one mapped token gets a representation dossier; two
or more tokens unlock a comparison and issuer/network concentration view. The brief is deliberately
not an AI opinion. It can be enriched later with CMC AI or MCP when access is confirmed, but the
facts, state and limitations remain reproducible from the CMC API.

## Investor research brief

Open a published Gold or Tesla review to see an illustrative investor question, the observed
contrast, the comparison clock, unmeasured investment inputs and a pending diligence checklist.
`Save research memo` downloads a Markdown record generated locally from the same bundled
snapshot as that asset's comparison table. It includes the observation date and window,
method, wrapper medians, approximate ratios, unresolved questions, evidence links and disclosure.
The save timestamp is an export time, not a fresh market observation.

This is research triage. A complete calculation does not approve a wrapper or support a buy
decision. The illustrative amount shown on the page supplies context; Bell has no size-specific execution quote.
Map-only assets such as IBKR keep their explicit state and do not receive an example's memo.

Gold links to its dated receipt and replay inputs. Tesla's memo uses the nine-entry receipt
ending 13 September, with the insufficient-data wrapper and replay payload preserved explicitly.
Public export and browsing require no credentials or API calls; online proof links require
connectivity, while bundled copies can be inspected offline.

## Current state

- `bell.py` contains the explicit offline/live CLI and CMC response adapter.
- `rwa_audit.py` composes RWA quotes, metadata, market pairs, issuers and crypto metadata
  including resolved network/contract fields when CMC returns them, then enriches each
  resolvable wrapper with optional DEX detail, price, pools, contract-security and holder-count
  evidence. A missing contract, an unsupported DEX lookup and a plan-limited CMC market-pair
  endpoint remain separate states; none is presented as zero liquidity.
- `--catalog` fetches the paginated, searchable RWA map; the current offline catalogue snapshot is
  `site/catalog.json`.
- `engine.py` contains the network-free deterministic calculations.
- `tests/` contains unit fixtures; all test data is clearly marked as synthetic fixture data.
- `site/` is a universal RWA terminal with published Gold and Tesla session reviews; the public
  Cloudflare deployment also loads credential-free published dossiers and queues refreshes for
  assets that have not been researched yet.
- The hackathon Startup key is not stored in this workspace. Never use `assay/.env` for Bell.

## Run offline

From the workspace root:

```sh
python3 bell/quick_review.py
python3 bell/quick_review.py --output /tmp/bell-gold-review.json
python3 bell/bell.py --offline
python3 bell/bell.py --offline --output /tmp/bell-receipt.json
python3 bell/rwa_audit.py --asset tesla
```

Run the public-surface contract checks as well:

```sh
node --test bell/tests/*.cjs
PYTHONPATH=bell python3 -m unittest discover -s bell/tests -p 'test_*.py' -q
python3 bell/verify_integrity_receipt.py
python3 bell/verify_legacy_replay.py
python3 bell/verify_catalogue_receipt.py
python3 bell/verify_public_surface.py
python3 bell/verify_submission.py
make check  # includes the documentation link check
```

Offline mode reads `tests/fixtures/offline.json`, emits a versioned receipt and demonstrates how
partial coverage and venue context are reported. It is not a market snapshot.

## Open the downloadable tool

From the repository root, run:

```sh
make app
```

Open <http://127.0.0.1:8080/workspace.html>. The visual mode and dated
credential-free evidence work immediately. The localhost-only **Agent
interface** gives scripts and agents a JSON tool manifest at `/api/agent` and
the evidence routes listed there. To enable live CMC queries, paste your own
CMC API key into the visual workspace; it stays in server memory and is used
server-side. It is never written to local storage, a file or the repository,
and is cleared when the server stops. A live request can consume the CMC plan
quota. The deployed website does not accept user API keys. For headless runs,
set `CMC_API_KEY` in the local server process environment instead.

The agent surface is an HTTP JSON API, not MCP. `GET /api/agent` describes its
tools, and `GET /api/catalog?q=tesla` searches the dated map without a CMC
request. The dated `/api/integrity` receipt is offline; `/api/rwa`,
`/api/terminal`, `/api/audit` and `/api/session` make explicit live CMC
requests. The workspace sets up a key with `POST /api/key`; the key remains in
local server memory, never in browser storage or a repo file. A headless agent
can instead set `CMC_API_KEY` in the server environment.

The local/static website at <https://bell.dyplux.com/> searches all 7,811 RWAs included in the
dated 22 September 2026, credential-free CMC map snapshot by name, symbol, slug or asset type through the `Explore RWA`
route. The live publication edge is
currently <https://bell.dyplux.com/>; it serves the same site and adds the published-dossier API.
The technical `workers.dev` hostname is only an infrastructure fallback, not the product URL. Bell
is not a direct browser-to-CMC client.
Decision cases can be shared through the same single URL with
`?reference=<CMC RWA ID>`; the result card also copies this stable case link.
Gold and Tesla have published session reviews. Gold shows seven wrappers with complete
168-hour coverage; the featured Tesla receipt contains nine entries, eight with complete 168-hour coverage and one explicitly insufficient-data row.
Other assets, including IBKR, open with identity, category and an explicit `Map entry only` or
`DOSSIER PENDING` state, while the terminal still generates an underlying/token-coverage brief.
No wrapper dossier or session review is published for those entries until the server-side
publisher completes the work. This is a valid catalogue result, not an API failure or proof that
the asset has insufficient history.

The Alphabet Class A case has a dated pairwise review for GOOGLX and GOOGLon.
It records the CMC route rows from the 28 September capture and issuer pages
checked on 29 September: Ondo's asset page displayed 1.0025 GOOGL per GOOGLon
at 18:15:11 UTC. The checked sources do not establish GOOGLX's effective unit
or the unit basis of CMC's displayed quote. The result is to withhold a
like-for-like price comparison until both are established. Open
the [pair-review receipt](site/proof/alphabet-class-a-pair-review-2026-09-29.json)
or run `make verify-pair-review` to match its route values and source hash to
the shipped CMC capture and verify four dated, hashed excerpts from Backed,
Ondo and xStocks documentation. Raw pages and signed legal archives are not
included; this review does not establish equivalent rights,
backing, redemption or fair value. A case JSON export includes a fingerprinted
link to this separate review when its token rows contain both exact CMC IDs.

For a code-first review, use the [public source map](SOURCE-MAP.md). It links the live
rendering path, receipt publisher, exact CMC endpoints and the credential-free case-receipt
verifier in one place.

A public session review appears only where published. Computing a review requires sufficient
hourly wrapper coverage; a CMC map listing does not guarantee that coverage. Missing or partial
coverage is retained in live receipts. The public site makes no CMC calls and requires no key.
If the generated map is absent, the illustrative fallback is not the complete catalogue.

## Refresh the catalogue

The map endpoint is paginated and returns a lightweight index. Refresh it locally with the Startup
credential in the process environment; the generated file contains no key:

```sh
export CMC_API_KEY='your-hackathon-key'
python3 bell/bell.py --catalog --output bell/site/catalog.json
```

The 22 September map snapshot used for catalogue replay contained 7,811 records. The observation
published on 29 September records 794 tokenised references and 1,456 token rows. The live receipt
can advance independently; use its `observed_at` field for the observation being served.
CMC's map is used for discovery; the selected asset's
`quotes/latest` response supplies wrapper details, and the session review only runs when historical
OHLCV coverage is sufficient. Gold has also passed the seven-day session review with seven ready wrappers;
Tesla remains the featured visual case because its contrast is easier to explain in the first 30 seconds.

## Local live API

`make app` starts the local server on `127.0.0.1:8080`. If running it manually,
the server can instead read `CMC_API_KEY` from its process environment:

```sh
export CMC_API_KEY='your-hackathon-key'
python3 bell/server.py --port 8080
```

With `make app`, the static catalogue and dated receipts work without a key;
the local live routes become available after a key is configured. A plain static
HTTP server cannot provide Bell's local API. The public deployment exposes
`/api/published?slug=<slug>` for the latest credential-free dossier;
it never sends the CMC key to the browser. The local server exposes `/api/rwa?slug=<slug>` for a
basic current dossier, `/api/terminal?slug=<slug>` for the full deterministic terminal evidence,
`/api/audit?slug=<slug>` for the deterministic RWA comparability audit, and
`/api/session?slug=<slug>&days=7` for a live Session Review; the key remains in
the server process and responses contain no credential or raw HTTP response. If the CMC plan
does not expose an optional surface such as RWA market pairs, Bell preserves the rest of the
evidence, records the HTTP limitation in provenance and labels the comparison as incomplete.
The live terminal shows DEX coverage separately, wrapper by wrapper.

## Run tests

```sh
PYTHONPATH=bell python3 -m unittest discover -s bell/tests -p 'test_*.py' -v
python3 -m py_compile bell/engine.py bell/bell.py bell/rwa_audit.py bell/server.py
```

## Live mode

Set the hackathon key in the process environment locally; do not paste it into chat or commit it:

```sh
export CMC_API_KEY='your-hackathon-key'
python3 bell/bell.py --live --asset tesla --days 7 --output bell/docs/proof/tesla.json
# RWA comparability evidence: quotes, info, market pairs, issuers, token metadata and optional DEX surfaces.
python3 bell/rwa_audit.py --asset tesla --output /tmp/bell-tesla-audit.json
# Optional audit artifact: keep the normalised public bars for offline recomputation.
python3 bell/bell.py --live --asset tesla --days 7 \
  --payload-output bell/docs/proof/tesla-live.payload.json \
  --output bell/docs/proof/tesla-live.receipt.json
```

Live mode calls the CMC RWA wrapper grouping, hourly OHLCV and latest cryptocurrency quote
endpoints. The key is sent only as `X-CMC_PRO_API_KEY`; the CLI does not print it. Before a public
run, inspect the generated receipt and remove any raw/private response content. A live smoke test
on 2026-09-13 reached all three endpoints with HTTP 200; eight of nine Tesla wrappers returned
complete 168-hour coverage and one wrapper returned no OHLCV data, so Bell reports `partial`.
The optional payload output contains only the normalised public dataset and provenance, never the
API key or raw HTTP response.

## Method boundary

The engine assigns each bar by its opening timestamp after conversion to `America/New_York`:

- cash: weekdays, 09:30 inclusive to 16:00 exclusive;
- after-hours: remaining weekday hours;
- weekend: Saturday and Sunday.

It calculates `((high - low) / open) * 100` and takes the median by session. It does not use hourly
`volume` as hourly flow, does not fetch a TradFi price, and does not infer liquidity, causality,
solvency, rights or an investment action.

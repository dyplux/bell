# Bell: RWA Surface Integrity Monitor

Bell starts with the complete CoinMarketCap RWA map, then tests whether the CMC surfaces
can support a trustworthy wrapper comparison before showing a user a ranking.

For this submission, judge the **RWA Surface Integrity Monitor** first. The older
terminal and session-review workflow is supporting evidence, not the headline
claim. The monitor is the public path at `/` and the credential-free replay
CLI is `python3 bell/integrity_review.py`.

Build with CMC API Hackathon, Real World Assets track. Bell is a research instrument,
not a trading signal.

The product rationale and spoken demo narrative are in [STORY.md](STORY.md).

## The claim

CMC exposes the pieces needed to discover RWA references, tokens, issuers and quotes.
Bell adds a pre-comparison integrity gate: before a user treats two representations
as the same exposure, Bell joins the CMC surfaces through stable IDs, checks identity,
unit and market-field coherence, and returns a visible state with evidence and a next
research action. It does not issue a safety score or approve a wrapper.

The flagship proof is population-wide. Bell scans the tokenised references in the
published receipt and keeps the whole queue inspectable. A critical contradiction is
`DO NOT SHORTLIST`, a warning is `INVESTIGATE`, a single wrapper becomes a dossier
instead of a ranking, and a map-only reference remains `REFERENCE ONLY` or `DOSSIER
PENDING`. The current public release also exposes the complete 7,811-reference map
through `Explore RWA`, so an absent dossier is not silently treated as a clean result.

The session review is supporting evidence for the same boundary. Gold has a complete
published review with seven wrappers and 168 hourly candles; Tesla has a nine-entry
replayable receipt that retains one insufficient-data wrapper. Their weekend-to-cash
ratios are observations about selected CMC data and method, not quality rankings,
mispricing or investment conclusions.

## The 30-second path

Start with the public demo at <https://bell.dyplux.com/>. This is the judge path for the
current submission and does not require an API key.

1. Enter `Gold` in the visible search and press `Check comparability`.
2. Read `DO NOT SHORTLIST`, the representation and issuer counts, the observed quote ratio,
   and the low/high quote endpoints with their issuer labels.
3. Read the boundary below the endpoints: these are CMC quote rows, not a discount, backing,
   liquidity or executable spread.
4. Open `Inspect this evidence` to see the published receipt, rule evidence, identity/unit/
   market checks, token rows and the resolution route.
5. Open `Explore RWA` and search a reference without a published case. Bell routes it to the
   complete map instead of inventing a clean result.

On desktop the search lands on the full decision card, including the capital check and issuer
concentration view. On mobile and tablet it lands on the compact searched-reference result so
the first evidence is visible without a long scroll. The public page reads the current
credential-free `/api/integrity` receipt, shows the publication time and freshness, and falls
back to the latest replay receipt only when the live publication is unavailable.

For a local credential-free replay, run:

```sh
python3 bell/quick_review.py
python3 bell/integrity_review.py
cd bell/site && python3 -m http.server 8080
```

The optional session-review receipts for Gold and Tesla are supporting evidence for the same
boundary. They are not required to judge the flagship monitor.

For an optional local live dossier, use a server-side environment variable:

```sh
export CMC_API_KEY='your-hackathon-key'
python3 bell/server.py --port 8080
```

The browser never receives the key. The public demo is available at
<https://bell.dyplux.com/>. The local server remains useful for testing the optional live
dossier without placing a credential in the public site.

## What the product does

| Layer | User job | Output |
|---|---|---|
| RWA Explorer | Find an asset in the CMC map | 7,811 entries in the dated map snapshot, filters and deep links |
| Map entry | Inspect a reference without a published review, such as IBKR | Identity, category, explicit map-only state and links to Gold or Tesla |
| Optional live dossier | Request current wrapper details with the local server | Wrapper, issuer, price and market-cap data when CMC supplies it; unavailable on the static public site |
| Session Review | Compare wrapper movement across sessions | Published Gold and Tesla reviews on the public site; new live calculations require sufficient hourly coverage and preserve warnings |
| Investor research brief | Turn a saved observation into a research queue | Illustrative question, snapshot-derived contrast, missing investment inputs and pending diligence; no approval or buy decision |
| Research memo | Carry the research record into a desk review | Offline-generated Markdown from the displayed snapshot, with date, method, medians, unresolved questions, evidence and disclosure |
| Evidence | Check the result | Session receipts include a normalised replay payload where published; the population monitor includes a dated summary, counts, hashes and explicit limitations |

The public contract is discovery across the complete dated CMC map, with session review only
where published. An asset appearing in search does not imply a published dossier or sufficient
historical coverage. A map-only result means no review is published in this release; it does not
claim that CMC has no history for that asset. Public browsing is static and makes no CMC calls.
If the generated map is missing, the illustrative fallback is not the complete catalogue.

## Method

1. `/v5/real-world-assets/map` supplies the searchable discovery index.
2. `/v5/real-world-assets/quotes/latest` supplies the selected RWA and its wrappers.
3. `/v2/cryptocurrency/ohlcv/historical` supplies hourly bars.
4. `/v2/cryptocurrency/quotes/latest` supplies the latest CEX and DEX context.

Each bar is assigned by its opening timestamp after conversion to
`America/New_York`:

- cash: weekdays, 09:30 inclusive to 16:00 exclusive;
- after-hours: remaining weekday hours;
- weekend: Saturday and Sunday.

The metric is `((high - low) / open) * 100`, aggregated with a median per session.
Hourly `volume` is not treated as hourly flow. Bell does not fetch a TradFi price and
does not infer liquidity, solvency, ownership rights, causality or an action.

## Proof files

- [Gold live receipt](docs/proof/gold-live-2026-09-13.json)
- [Gold normalised replay payload](docs/proof/gold-live-2026-09-13.payload.json)
- [Tesla live receipt](docs/proof/tesla-live-2026-09-13.json)
- [Tesla normalised replay payload](docs/proof/tesla-live-2026-09-13.payload.json)
- [Population integrity history](site/proof/rwa-surface-integrity-history.json)
- [Latest normalized population inputs](site/proof/rwa-surface-integrity-inputs-2026-09-21.json)
- [Population receipt verifier](verify_integrity_receipt.py)
- [Public submission gate](verify_submission.py)
- [QA results](QA-RESULTS.md)

A receipt is a machine-readable record of a run. It is not a payment receipt. Session receipts
record the schema, asset, time window, session results, coverage, warnings and endpoint
provenance. Their sibling payload contains the normalised public bars needed to replay the
calculation without the API key. The population integrity receipt records summary counts and
source fingerprints for the authenticated audit. The latest dated run also bundles credential-free
normalized input surfaces so the deterministic receipt can be recomputed. Authenticated HTTP
headers, request metadata and credentials are not committed.

The static Tesla page is bound to the dated receipt and normalised replay payload. It does not
contain raw CMC HTTP responses, credentials or legal/execution evidence.

Run `python3 bell/verify_integrity_receipt.py` to verify that the public history agrees with the
dated and latest bundled integrity summaries and that the normalized latest inputs recompute the
receipt exactly. This is a publication-integrity check, not a claim that authenticated transport
metadata or upstream source correctness has been independently attested.

## Why Bell is distinct

The CMC map is the broad entry point. Bell's differentiated job is the transition from
asset discovery to a temporal, cross-wrapper review. It does not present a generic chat
agent, a copy of a token screener, or a new opaque score.

The public release makes the judge path, dated proof, credential-free replay,
visible refusal states and numerical API feedback inspectable. Bell's question,
session-clock method and RWA Explorer plus Session Review workflow are its own
implementation and product framing.

## Honest limits

- The catalogue is a dated snapshot unless refreshed.
- Coverage depends on what CMC returns for each wrapper and window.
- Range is not volume, liquidity, depth or a spread.
- A broad weekend ratio does not explain why a wrapper moved.
- CMC's grouping defines which wrappers Bell compares.
- A result can be ready for calculation while still being insufficient for a causal claim.

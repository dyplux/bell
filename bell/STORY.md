# Bell: a decision terminal for every real-world asset

Judge narrative, grounded in the workspace and published-site source inspected on 13 September 2026.

Bell is a universal RWA decision terminal. Built by Dyplux for the Real World Assets track, it starts with the economic exposure and changes its workflow according to the CMC token layer: underlying-only, one-token dossier or multi-token comparison. The current public snapshot covers stocks, ETFs and commodities; additional CMC asset types follow the same schema when they are present in a dated receipt. Comparability and session analysis remain evidence modules inside the terminal.

The strategic direction changed after auditing CoinMarketCap's own RWA surface. CMC already offers discovery, issuers, tokens, contracts, markets, depth, liquidity, charts and token detail. Bell's job is not to reproduce that explorer; it is to turn the complete RWA universe into a decision workflow and an automatic, evidence-bound brief.

## The problem that led us here

Imagine preparing a research note on tokenised Tesla or Silver. Several tokens carry the same familiar reference name, but that name does not tell you whether they represent the same unit, claim, issuer structure or market type. A price gap can be a real market dislocation, a different denomination, a derivative, stale data or an unusable market. CMC exposes much of the raw material, but does not turn those contradictions into a comparability decision.

That is the task Bell is designed to shorten. The intended user is an RWA researcher or market-operations analyst deciding what deserves further investigation and what evidence can support a note. This is a proposed use case, not a claim of institutional adoption or validated customer demand.

Dyplux's approach is to build instruments from measured questions. Our initial Tesla research recorded different median hourly ranges across four wrappers in a seven-day window ending 11 September 2026. That remains useful evidence, but the new CMC surface audit exposed a more important question: before measuring behaviour, are the instruments comparable at all?

The name Bell expresses the need for a clear signal before acting on a market comparison: what deserves investigation, what should be excluded, and what evidence is still missing?

## Why another RWA screen is not enough

A catalogue answers which assets exist. CMC's RWA page already groups assets, shows issuers and tokens, compares aggregate prices, and exposes market details. A token page adds holders, contracts, audits, markets and descriptions. Bell must therefore answer the question those pages leave open: **are the things shown together actually comparable, and what evidence supports that conclusion?**

A researcher can build this audit with scripts or a spreadsheet; Bell packages it into a repeatable evidence path that distinguishes facts, inferences and unresolved ambiguity.

The product is designed around a concrete question, accessible discovery,
visible evidence and dated records. Those are design choices for Bell, not a
claim that other products lack comparable capabilities.

The strategic gap we are testing is narrow: discovery should lead to a reviewable integrity decision about the selected asset's wrappers. Search is the entrance; the audit and its evidence are the reason to stay.

## The Bell insight

Shared reference identity does not establish shared economic equivalence. Bell joins the CMC wrapper grouping to token metadata, issuer identity, market pairs and historical evidence, then applies explicit tests for:

- unresolved unit or denomination differences;
- ticker collisions across issuers;
- derivatives or perpetuals mixed with spot representations;
- positive volume with missing or zero market cap;
- stale, missing or incomplete data;
- extreme price dispersion between tokens in the same RWA group.

The result is not a buy/sell signal. It is a comparability state: provisionally comparable, investigate, do not compare, or insufficient evidence.

For each valid bar, it calculates `(high - low) / open * 100`, then takes the median in each time bucket. The comparison can show the absolute median hourly range or its size relative to the cash-bucket median. Normalising each bar to its own opening price avoids comparing raw token price levels, but does not establish economic or legal equivalence.

The range/session module now supports the audit as secondary evidence. It cannot establish backing, redemption, denomination or liquidity on its own.

The Gold receipt demonstrates the calculation on a second reference: seven wrappers, each with 168 hourly bars, over 6 September at 10:00 UTC to 13 September at 10:00 UTC. Weekend medians were approximately 12% to 93% of the respective cash-bucket medians. That is variation within this dataset and window, not a ranking of issuers or proof of a persistent effect.

## The user workflow and what works today

The investor test is documented separately in [USE-CASE-INVESTOR.md](USE-CASE-INVESTOR.md). It
is deliberately stricter than the hackathon demo: Bell must change what an analyst investigates,
without pretending to approve an investment.

1. Open [Bell](https://bell.dyplux.com/) and search by name, ticker, slug or category. The bundled CMC map contains 7,811 observed reference entries. Catalogue presence does not guarantee available tokens or analysable history.
2. Run the selected RWA through the audit path. The collector composes quotes, RWA metadata, market pairs, issuers and crypto metadata while retaining endpoint provenance.
3. Inspect the token table and findings. Silver is the strongest unit/aggregation case; Tesla is the strongest identity/market outlier case; Gold is a useful multi-issuer and denomination case.
4. Open the evidence drawer/receipt to inspect the method, calls, timestamps, findings and limitations. Session-review receipts link to a normalised payload when the published bars are available; the population integrity receipt is a dated summary with source fingerprints, not a raw-response replay bundle.
5. Read the investor research brief: an illustrative USD 100,000 research question, the snapshot-derived contrast, what Bell does not measure and the pending diligence queue. Save the Markdown memo to carry the same finding, method, dates, evidence and disclosure into a desk review. No wrapper is approved by this step.
6. Investigate identity, legal claim, eligibility, actual route hours and size-specific entry and exit costs. Repeat the observation over independent windows where possible. Automated monitoring and comparisons between saved runs remain future work.

The website is the interactive demonstration; the repository explains and reproduces the audit. The public site serves dated surface-audit snapshots and session evidence. The optional local server can request a current dossier, run the deterministic comparability audit, and request session reviews using a server-side key, subject to API access and data coverage. That capability must not be presented as arbitrary live analysis already available on the public website.

If a judge searches IBKR or another reference without a published review, the honest outcome is a catalogue entry with limited coverage. It is not evidence that the asset has no history. If there is no search match, it means no match in this snapshot, not that the asset does not exist.

## Why CoinMarketCap is necessary to this implementation

CMC supplies the connected source data that makes Bell's workflow possible:

| API endpoint | Role in Bell |
|---|---|
| `/v5/real-world-assets/map` | Discover reference assets and build the searchable index |
| `/v5/real-world-assets/quotes/latest` | Resolve the selected reference into aggregate quotes, wrappers, crypto IDs and issuer details |
| `/v5/real-world-assets/info` | Supply static RWA identity and asset metadata |
| `/v5/real-world-assets/market-pairs/list` | Supply exchange, pair, category, fee type, price, volume and timestamps |
| `/v5/real-world-assets/issuers` | Resolve issuer identity and linked tokens |
| `/v2/cryptocurrency/info` | Enrich token descriptions, platforms, contracts and links |
| `/v2/cryptocurrency/ohlcv/historical` | Supply the hourly bars used in the comparison |
| `/v2/cryptocurrency/quotes/latest` | Supply reported CEX/DEX volume context where available |

The important connection is reference to wrapper to issuer to market to history. One latest-price call cannot establish comparability. Bell adds deterministic classification, contradiction detection, coverage reporting and exportable evidence. Its calculations do not require an LLM.

CMC is necessary to Bell as implemented, not claimed to be the only possible provider. The static demonstration preserves outputs of prior API work; it does not make fresh CMC calls when a judge opens the page.

## What is genuinely new in Bell

Bell's contribution is the assembled integrity workflow: start from a real-world reference, join multiple CMC RWA surfaces, test whether wrappers are comparable, expose contradictions and incomplete coverage, and preserve the conclusion with its method and inputs.

The current product thesis is: **CMC shows the ingredients; Bell checks whether the recipe makes sense.**

The range formula, session analysis, search and receipts are established
techniques. We claim a focused implementation and product framing around
comparability integrity, not invention of those techniques, a proprietary
financial discovery or a verified world first.

## Honest limits

- The clock is a convention: weekdays 09:30 to 16:00 in `America/New_York`, remaining weekday hours, and weekends. Bars are assigned by opening timestamp. There is no exchange holiday calendar, and an hourly bar can cross a boundary.
- For Gold and other non-US-equity references, the New York cash bucket is a comparison baseline, not the asset's verified opening hours. Gold does not have one universal equity-style closing bell.
- Range does not measure return, bid-ask spread, depth, executable liquidity, trading activity or price discovery. A quiet range cannot prove an inactive market; a wide range cannot prove healthy trading.
- The RWA API does not directly provide every underlying TradFi price or physical denomination. Bell cannot measure tracking error, fair value, premium/discount to the underlying, backing, redemption rights or investor eligibility. It must mark denomination as unresolved rather than invent it.
- Venue totals are latest 24-hour context, not session-specific flow or a cause of the observed contrast. The documented rolling 24-hour volume field is not summed as hourly flow.
- A complete seven-day dataset establishes coverage for that calculation, not statistical significance, persistence or predictive power. A receipt makes the transformation inspectable; it is not an independent attestation of CMC data accuracy.
- The current Tesla evidence is a nine-entry receipt ending 13 September: eight entries have complete history and one is explicitly insufficient. The session payload supports replay of the displayed medians; the population integrity monitor has a separate summary receipt and source fingerprints rather than raw authenticated responses.

## A 30-second demo narrative

Start at the terminal with Gold selected, then open SPY and a map-only asset. Speak the following:

> Bell starts with the economic exposure, not a ticker. For Gold, CMC maps seven token entries, so Bell opens comparison mode and explains the unresolved unit and issuer differences. For SPY, one representation exists, so there is no fake ranking: Bell opens a single-token dossier. For an asset with no mapped token, Bell stays on the underlying. Every mode produces a deterministic brief with facts, gaps and next checks.

Use Gold to show multi-token analysis, SPY to show the single-token path and an asset with
`has_tokens: false` to show that the terminal does not invent wrappers. The dated session review
and receipt then provide deeper evidence for the Gold case.

## The investor's decision record

The concrete scenario is an analyst investigating USD 100,000 of tokenised gold over a weekend.
Bell narrows the research queue by showing a reported behavioural contrast under a declared clock.
The analyst still needs to establish which instruments and routes are permitted, what an entry and
exit would cost, and whether the source data is adequate. These are pending checks, not inferred
properties of a quiet or wide range.

The public brief now makes this workflow visible. Its downloadable memo uses exactly the same
published summary inputs as the comparison table, carries their observation date and limitations,
and leaves approval pending. The amount is a scenario assumption; no quote or client mandate
has been supplied. Gold and Tesla link to their dated session payloads; the population integrity
receipt is independently checkable for schema, counts and source fingerprints, but is not a raw
response replay. Producing this memo is an implemented task;
time saved, investor adoption and willingness to reuse it still require user testing.

## Keep the story aligned with the product

Prefer: "Start with any CMC RWA exposure. Bell decides whether to show an underlying brief, a single-token dossier or a multi-token comparison, then exposes the evidence and limits."

Avoid: "find the safest wrapper", "detect institutional flows", "prove weekend liquidity", "prove backing", or "the first platform to do this". Bell maps every reference in the offline CMC snapshot, but live token detail and institutional suitability remain evidence-dependent.

The public copy now makes the contract explicit: all references in the dated map are searchable,
and every selected reference receives an underlying/token-layer brief. Gold and Tesla have
published reviews; assets such as IBKR show an honest map-only state. The public site is static and
credential-free; current dossiers and new calculations require the optional local server.

The highest-value next improvements are a public server-side live path with rate-limit handling, a
visible comparison-clock label for each asset class, and receipts tied to the exact displayed
dataset. Broader live coverage and repeated-window comparisons should follow evidence that
researchers need them.

To test the product hypothesis, ask target users to compare wrappers manually and with Bell, explain the result's limits, and identify a follow-up question. Measure completion time and interpretation errors. Until that happens, time savings and institutional usefulness remain hypotheses.

## Evidence and disclosure

This narrative is supported by the public [JUDGE.md](JUDGE.md),
[README.md](README.md), [USER-GUIDE.md](USER-GUIDE.md),
[QA-RESULTS.md](QA-RESULTS.md), the [website README](site/README.md), and the
dated receipts under [site/proof](site/proof). The public release does not
include private competitor notes, internal jury reports or model transcripts.

Calculation evidence: [Gold receipt](docs/proof/gold-live-2026-09-13.json), [Gold replay payload](docs/proof/gold-live-2026-09-13.payload.json), [newer Tesla receipt](docs/proof/tesla-live-2026-09-13.json), and [engine](engine.py).

Built by Dyplux, Lisbon. Research, not a trading signal.

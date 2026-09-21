# Bell value delta against CMC

Date: 16 September 2026

This is a dated value ledger, not a current count. The live public map now has
7,811 searchable references and the current population receipt is reported in
`QA-RESULTS.md`.

This ledger records what Bell adds to the CMC RWA discovery surfaces. It does
not claim that Bell owns RWA discovery, issuer lookup, contract display or
structural comparison. Those already exist elsewhere.

| Bell improvement | CMC surface already provides | Bell adds | Verification |
|---|---|---|---|
| Pre-comparison gate | References, token rows, issuers and latest quote fields | A deterministic answer to whether a grouped reference should be compared yet, with a stop/investigate/continue state | Live Silver, Marvell and SPY cases; public receipt rules |
| Identity handoff | Stable `rwa_id`, `crypto_id`, issuer and token metadata | The join path is printed beside the selected rows so the user knows exactly which wrapper and issuer require diligence | Browser comparison output and exported decision brief |
| Contradiction evidence | CMC can display the underlying fields | Fired rules, affected rows, observed values, timestamp and next action are kept together | Credential-free JSON receipt and queue evidence |
| Facts-only pair view | Quote fields and aggregate values | Selected wrappers receive descriptive price, market-cap and volume gaps without a winner or approval claim | Marvell live pair test; Silver blocked pair test |
| Population-wide decision queue | CMC exposes RWA listings and metrics, but listing coverage is not a Bell decision workflow | The full Bell population is navigable in place with a state, evidence route and next action for each reference; this is a completeness improvement, not a claim that Bell discovered the assets | Historical 790-reference queue, 66-page Chrome check, search and state-filter acceptance |
| Reproducibility | Public page presentation | Dated receipt, publication freshness, source hashes and an offline replay path | `/api/integrity`, verifier and replay receipt |
| Investor handoff | No Bell-specific diligence workflow | Markdown decision brief and local worksheet carrying unresolved backing, redemption, eligibility, custody and execution questions | Browser download acceptance and `USER-GUIDE.md` |

## Evidence boundary

CMC's public RWA page and API documentation remain the discovery and quote
layer. Bell uses their available surfaces and cannot establish backing,
redemption, custody, legal eligibility, solvency or executable liquidity from
CMC Startup fields alone. A `FACTS OPEN` result therefore means
only that Bell's published contradiction rules did not fire in that receipt.

The competitive boundary was checked against the [CMC RWA surface](https://coinmarketcap.com/real-world-assets/?type=rwa),
[CMC RWA API documentation](https://coinmarketcap.com/api/real-world-assets-api/),
[Asortino](https://asortino.com/) and
[TokenizedXonChain comparisons](https://www.tokenizedxonchain.com/compare/).
Those checks are dated research, not a permanent claim that no adjacent tool
can add a similar workflow.

## Current CMC boundary check

On 16 September 2026, the current CMC RWA surface still exposed the discovery
layer as `Grouped by RWA`, `All Tokens` and `RWA Protocols`, with RWA/average
token price, market cap, volume, token market cap, token volume and a seven-day
chart. The current RWA API reference describes seven endpoints, stable
`rwa_id`/`crypto_id` joins, and `Quotes Latest` returning aggregate values,
individual token rows and TradFi markets.

That confirms what Bell must not claim as novel. Bell's delta is the
deterministic pre-comparison decision, preserved contradiction evidence and
investor handoff around those existing fields. In the same current CMC page,
the Silver row displayed separate RWA-average and token-price values; Bell
turns that kind of surface discrepancy into a stop/investigate route rather
than leaving it as a number for a user to interpret alone.

Sources: [CMC RWA surface](https://coinmarketcap.com/real-world-assets/?type=rwa)
and [CMC RWA API reference](https://coinmarketcap.com/api/real-world-assets-api/).

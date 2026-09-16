# Bell competitive boundary

This note prevents the product from claiming novelty that the market already
has. It was checked against the public CMC RWA surface, the current CMC RWA API
documentation, Asortino and TokenizedXonChain on 16 September 2026.

## What already exists

CoinMarketCap's public RWA surface already groups stocks, ETFs, commodities and
other references, shows an RWA average price beside a token price, and links to
the asset pages. Its RWA API documentation says that `Quotes Latest` returns
tokenised aggregate values, the underlying token rows and TradFi markets where
available. The API also exposes stable `rwa_id`, `crypto_id`, issuer and latest
quote paths.

Asortino already offers a tokenised stock and ETF screener with one asset shown
across issuers and chains. It presents issuer, token, chain, dividend policy and
contract fields, and claims checks against official issuer deployments and live
on-chain supply. It also presents underlying fundamentals and backing/custodian
descriptions.

TokenizedXonChain already publishes human-reviewed structural comparisons. Its
comparison pages cover issuer, legal wrapper, chain, eligibility and redemption,
with a review date, reviewer and a description of what changed.

Therefore Bell must not claim to invent RWA comparison, issuer discovery,
contract display, backing research or structural comparison.

## Bell's defensible job

Bell is narrower and more mechanical:

> Before a user treats a CMC RWA group as one comparable market, Bell tests the
> grouping across the population and preserves the stop/investigate decision.

It joins the CMC surfaces through `rwa_id`, `crypto_id` and `issuer_id`, then
checks for contradictions that a catalogue can display without interpreting:

- denomination or unit-like price breaks;
- derivative rows mixed with spot-like rows;
- ticker collisions across issuers;
- volume with zero market cap;
- missing market fields or unresolved token identity;
- incomplete issuer joins and stale publication state.

The output is a deterministic state, evidence and next action. A critical state
withholds wrapper comparison. A clean state is still explicitly not approval.
The receipt is credential-free and dated, so a reviewer can inspect what was
observed instead of trusting a screenshot or an opaque model score.

## Product implication

The public story should say **surface integrity before wrapper selection**. It
should not say “the best token”, “the safest issuer”, “backing verified” or
“the only RWA comparison tool”. The useful question is whether Bell changes the
first decision in a research workflow: *do these rows deserve to be compared at
all?*

## Sources

- [CMC public RWA surface](https://coinmarketcap.com/real-world-assets/?type=rwa)
- [CMC RWA API documentation](https://coinmarketcap.com/api/real-world-assets-api/)
- [Asortino](https://asortino.com/)
- [TokenizedXonChain comparisons](https://www.tokenizedxonchain.com/compare)

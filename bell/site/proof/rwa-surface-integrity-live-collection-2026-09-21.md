# Live collection receipt · 2026-09-21

This receipt records the server-side collection evidence behind the latest
credential-free replay package. It is a transport audit summary, not a claim
that the public browser can authenticate to CoinMarketCap.

| Surface | Endpoint | Requests | Successful JSON responses | Status codes | Window |
|---|---|---:|---:|---|---|
| Map | `/v5/real-world-assets/map` | 32 | 32 | 200 × 32 | 19:19:31–19:19:39Z |
| Asset list | `/v5/real-world-assets/assets/list` | 32 | 32 | 200 × 32 | 19:19:39–19:19:48Z |
| Quotes | `/v5/real-world-assets/quotes/latest` | 4 | 4 | 200 × 4 | 19:19:48–19:19:50Z |
| Info | `/v5/real-world-assets/info` | 4 | 4 | 200 × 4 | 19:19:48–19:19:50Z |
| Issuers | `/v5/real-world-assets/issuers/list` | 1 | 1 | 200 × 1 | 19:19:54–19:19:54Z |
| Token info | `/v2/cryptocurrency/info` | 15 | 15 | 200 × 15 | 19:19:50–19:19:54Z |

The manifest stores one SHA-256 body hash for every successful response. The
hashes bind the published collection record to the received response bytes
without publishing raw bodies, API keys or request headers.

The map and asset-list surfaces each required 32 paginated requests at a limit
of 250. Info and quote requests covered the 791 tokenised references in four
batches. Token metadata was requested in 15 batches. This is evidence of the
collection path and response shape at this observation, not a permanent
guarantee against future schema or pagination changes.

The verifier recomputes the deterministic receipt from the normalized package.
It does not independently prove provider authenticity, backing, redemption,
legal eligibility, liquidity or executable size.

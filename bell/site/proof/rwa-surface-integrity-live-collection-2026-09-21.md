# Live collection receipt · 21 September 2026

This is the collection manifest paired with the recovered, credential-free
replay package observed at `2026-09-21T21:25:01Z`. It describes server-side
collection metadata; it is not an independent authentication of CMC transport.

| Surface | Endpoint | Requests | Successful JSON responses | Status codes | Window |
|---|---|---:|---:|---|---|
| Map | `/v5/real-world-assets/map` | 32 | 32 | 200 × 32 | 21:25:01–21:25:08Z |
| Asset list | `/v5/real-world-assets/assets/list` | 32 | 32 | 200 × 32 | 21:25:08–21:25:17Z |
| Quotes | `/v5/real-world-assets/quotes/latest` | 4 | 4 | 200 × 4 | 21:25:17–21:25:19Z |
| Info | `/v5/real-world-assets/info` | 4 | 4 | 200 × 4 | 21:25:17–21:25:19Z |
| Issuers | `/v5/real-world-assets/issuers/list` | 1 | 1 | 200 × 1 | 21:25:23–21:25:23Z |
| Token info | `/v2/cryptocurrency/info` | 15 | 15 | 200 × 15 | 21:25:19–21:25:23Z |

The manifest contains one SHA-256 body fingerprint for each of 88 successful
responses. The fingerprints bind the manifest to the response bytes claimed by
the publisher without publishing raw bodies, API keys or request headers.
The map and asset-list surfaces each used 32 paginated requests at a limit of
250. Info and quote requests covered the 791 tokenised references in four
batches. Token metadata was requested in 15 batches.

The paired [normalized package](rwa-surface-integrity-inputs-2026-09-21.json)
and [recovered original receipt](rwa-surface-integrity-original-2026-09-21.json)
are observed at `21:25:01Z`. The earlier `19:19:31Z` history summary is a
different observation and is not verified by these request windows.

The verifier checks the manifest's response counts, HTTP statuses, SHA-256
shapes, and ordered UTC windows against the normalized payload package. It
cannot independently prove provider authenticity, backing, redemption, legal
eligibility, liquidity or executable size.

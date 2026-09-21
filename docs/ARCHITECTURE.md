# Bell public architecture

## Runtime shape

```text
CoinMarketCap RWA surfaces
        |
        v
Mac mini integrity publisher
  map + assets/list + quotes/latest
  info + issuers/list
  stable-ID joins + deterministic rules
        |
        v
credential-free normalized receipt
        |
        v
Cloudflare Worker + D1
  authenticated publish route
  public GET /api/integrity
        |
        v
Bell Integrity Monitor   Neutral Review Queue
```

The browser never calls CMC directly. It reads a published receipt and can
fall back to an explicitly dated static replay. The publisher owns the CMC
credential and the Worker stores only normalized receipt data.

## Surfaces and joins

The current integrity scan uses:

| Surface | Role |
|---|---|
| `/v5/real-world-assets/map` | population and stable `rwa_id` discovery |
| `/v5/real-world-assets/assets/list` | paginated catalogue and surface drift |
| `/v5/real-world-assets/quotes/latest` | token, quote and market fields |
| `/v5/real-world-assets/info` | second identity and asset-type join |
| `/v5/real-world-assets/issuers/list` | issuer catalogue cross-check |

`rwa_id` is the primary reference key. `crypto_id` identifies token rows and
`issuer_id` identifies issuers. A ticker is evidence to display, not a join key.

The CMC market-pairs endpoint is not available on the Startup plan. Bell records
the tested 403/error-1006 boundary and does not convert unavailable venue data
into zero liquidity.

## Publication lifecycle

1. A scheduled launchd process reads the private CMC credential.
2. The publisher captures the required surfaces and records observation time.
3. The deterministic monitor emits decisions, evidence and source hashes.
4. The publisher posts the normalized receipt to the authenticated Worker.
5. D1 stores the latest receipt and its publication timestamp.
6. Public clients receive `_publication` freshness metadata.
7. The UI recalculates age while open and labels static fallback as `DATED REPLAY`.

The public API exposes no CMC key, raw authenticated response or private
publisher configuration. The sanitized input manifest documents counts,
endpoint identities, join coverage and fingerprints for the captured run.

## Local and public surfaces

- Product: <https://bell.dyplux.com/>
- Public receipt: <https://bell.dyplux.com/api/integrity>
- Neutral queue: <https://rwa-surface-review.pages.dev/>
- Source: <https://github.com/dyplux/bell>

The public release is intentionally separate from Dyplux's private research
desk, jury ballots and competitor dossiers.

# RWA integrity evidence index

This page separates the current publication from the credential-free replay package so a reviewer can tell exactly what is being verified.

## Current observation

The live receipt at [`/api/integrity`](https://bell.dyplux.com/api/integrity) is produced by a server-side authenticated collection from the documented CMC RWA surfaces. The API key and transport headers stay on the publisher. The public payload contains the observation timestamp, endpoint method, join rules, source fingerprints, normalized findings and the publication freshness state.

The live receipt is allowed to change when the scheduled publisher observes a new source window. It is the current observation, not a permanent dataset.

## Credential-free replay

The latest committed replay package is dated 21 September 2026

- [normalized replay receipt](rwa-surface-integrity-latest-replay-2026-09-21.json)
- [normalized input surfaces](rwa-surface-integrity-inputs-2026-09-21.json)
- [verification note](rwa-surface-integrity-verification-2026-09-21.md)
- [live collection boundary](rwa-surface-integrity-live-collection-2026-09-21.md)

The normalized inputs contain no API key, request headers or private transport metadata. They are sufficient to recompute the dated deterministic receipt with the committed verifier

```bash
python3 bell/verify_integrity_receipt.py
```

The verifier proves that the dated receipt matches its published normalized inputs. It does not claim that a later live receipt has the same values.

## What this evidence does not establish

The collection and replay packages do not prove backing, custody, redemption, legal eligibility, liquidity, depth, price discovery or executable size. Those remain explicit diligence questions.

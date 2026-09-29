# RWA integrity evidence index

This page separates the current publication from the credential-free replay package so a reviewer can tell exactly what is being verified.

## Current observation

The live receipt at [`/api/integrity`](https://bell.dyplux.com/api/integrity) is produced by a server-side authenticated collection from the documented CMC RWA surfaces. The API key and transport headers stay on the publisher. The public payload contains the observation timestamp, endpoint method, join rules, source fingerprints, normalized findings and the publication freshness state.

The live receipt is allowed to change when the scheduled publisher observes a new source window. It is the current observation, not a permanent dataset.

The 28 September 2026 publication is also preserved as a dated, credential-free capture so its exact inputs can be checked after the live endpoint advances:

- [published receipt capture](rwa-surface-integrity-capture-2026-09-28.json)
- [normalized CMC inputs](rwa-surface-integrity-inputs-2026-09-28.json)
- Observed at `2026-09-28T15:14:11Z`; 793 tokenised references and 1,449 token rows.
- The publisher reports 38 stop-state references, 97 requiring investigation, 658 with no rule hit, and 88 filtered price comparisons.

Run `make verify-capture` to recompute this dated capture from the normalized inputs without an API key. The collection manifest records endpoint hashes, request counts and status codes, but excludes API credentials and transport headers.

The dated [28 September base-rate result](base-rate-2026-09-28.json) recomputes the comparison filter over those same inputs with the checked-in measurement and rule code. It records the input SHA-256 and both code-file SHA-256 values so the 88/250 result can be reproduced independently with `make base-rate`. This is a derived population calculation; it is distinct from the receipt's 38/97/658 state counts and from the advancing live observation.

## Credential-free replay

The committed historical replay package below is dated 21 September 2026

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

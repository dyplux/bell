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

From the next newly appended observation onward, the dated-series workflow retains the full credential-free receipt in deterministic gzip under `rwa-surface-integrity-receipts/`. The history record carries its SHA-256 and path. `make verify` checks every retained archive against the full history summary, whether or not that observation has a per-reference series step. When a receipt is also a comparable series step, the verifier additionally compares every reference row with the replayed series. This retention begins prospectively; older summaries are not reconstructed from a later capture.

## Credential-free replay

The 21 September history entry has two distinct artifacts. The original receipt was recovered from the publisher runtime on 29 September; its recorded state split is not replaced by a later-rule result. The frozen scanner and all six normalized inputs reproduce the original receipt's historical distribution:

- [recovered original receipt](rwa-surface-integrity-original-2026-09-21.json)
- [frozen historical scanner source](https://github.com/dyplux/bell/blob/main/bell/rwa_integrity_legacy_2026_09_21.py.txt)
- [six normalized input surfaces](rwa-surface-integrity-inputs-2026-09-21.json)
- Scanner SHA-256: `6bc17c2b4403f6c15eb149fec76297de71b7c2d47a4237407fecdfa6c13c5324`
- Receipt SHA-256: `a878f175d9144dfbbc0e57771cf2183c3f8d2fe647a37a41f73b04cab468ea2b`
- Original state distribution: 35 `do_not_compare`, 662 `investigate`, 94 `no_flags`.

Run `make verify` or `python3 bell/verify_legacy_replay.py` to replay the original result and compare it with the immutable history entry. The verifier removes only the two fields added after that observation (`population_attribution` and `rule_calibration`) from the replayed object before requiring an exact match to the recovered receipt.

The later-rule replay package below is also dated 21 September 2026. It intentionally applies the subsequent rules to the same inputs, so its state distribution differs from the original receipt:

- [later-rule replay receipt](rwa-surface-integrity-latest-replay-2026-09-21.json)
- [normalized input surfaces](rwa-surface-integrity-inputs-2026-09-21.json)
- [verification note](rwa-surface-integrity-verification-2026-09-21.md)
- [live collection boundary](rwa-surface-integrity-live-collection-2026-09-21.md)

The normalized inputs contain no API key, request headers or private transport metadata. They are sufficient to recompute the dated deterministic receipt with the committed verifier

```bash
python3 bell/verify_integrity_receipt.py
```

The later-rule verifier proves that its receipt matches the normalized inputs. It does not claim that this reinterprets the original rule result, or that a later live receipt has the same values.

## What this evidence does not establish

The collection and replay packages do not prove backing, custody, redemption, legal eligibility, liquidity, depth, price discovery or executable size. Those remain explicit diligence questions.

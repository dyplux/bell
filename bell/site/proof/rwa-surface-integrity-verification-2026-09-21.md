# RWA Surface Integrity Monitor · public verification

This note records how the latest population receipt can be checked without a
CMC credential. It is a verification of the published computation, not a
claim that the public browser calls CMC directly.

## Latest observation

- Observed at: `2026-09-21T19:19:31Z`
- Published by the server-side publisher at the same refresh cycle
- Published state at capture: `fresh`
- Tokenised references: `791`
- Representation rows: `1,435`
- States: `37` blocked, `661` investigate, `93` no rule hit
- Source surfaces: map, asset list, quotes, info, issuers and cryptocurrency info

## Replay path

The latest credential-free input package is available at
[`rwa-surface-integrity-inputs-2026-09-21.json`](rwa-surface-integrity-inputs-2026-09-21.json).
It contains the normalized six-surface payloads used by the deterministic
scanner. Its collection manifest names the six CMC endpoint surfaces and
records a SHA-256 fingerprint for each normalized payload. The package
contains no API key and no request headers.

From the repository root:

```sh
python3 bell/verify_integrity_receipt.py
```

The verifier checks the package schema, the six required surfaces, the matching
observation timestamp, the scanner output and the public collection manifest
against the published local receipt. The expected result for this observation
is ten verified dated receipts, including two bundled cross-checks and eight
public summary records. The manifest also records 88 successful JSON responses
across six surfaces, their HTTP status codes, collection windows and body
hashes. Raw response bodies, request headers and credentials are not published.

## Boundary

The public replay proves that the receipt is internally consistent with the
published normalized inputs and scanner code. It does not prove the upstream
provider's authenticated transport, backing, redemption, legal eligibility,
liquidity or executable size. Those remain external diligence questions.

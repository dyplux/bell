# RWA Surface Integrity Monitor · public verification

This note explains how the recovered 21 September population receipt can be
recomputed without a CMC credential. It verifies the published computation;
it does not claim that the public browser calls CMC directly.

## Recovered observation

- Observed at: `2026-09-21T21:25:01Z`
- Tokenised references: `791`
- Original states: `35` DO NOT COMPARE, `662` INVESTIGATE, `94` NO FLAGS
- Replayed with the later rule set on the same inputs: `35` DO NOT COMPARE,
  `90` INVESTIGATE, `666` NO FLAGS
- The two distributions differ because the replay deliberately uses later
  rules. The original receipt remains unchanged.

An older history summary at `19:19:31Z` reports `37 / 661 / 93`. The six-surface
input package preserved here is from `21:25:01Z`, not that earlier observation;
the earlier full input package is not available in this repository and its
transport details cannot be replayed from these files. Do not treat this
package as verification of the 19:19 summary.

## Replay path

The credential-free [normalized input package](rwa-surface-integrity-inputs-2026-09-21.json)
contains the six surfaces used by the deterministic scanner and a collection
manifest with SHA-256 fingerprints for each response. It contains no API key
or request headers.

From the repository root:

```sh
python3 bell/verify_integrity_receipt.py
```

The verifier checks the package schema, required surfaces, response status and
hash shapes, ordered UTC collection windows, observation timestamp, scanner
output, and manifest against the recovered original receipt. It also checks
the later-rule replay against the same inputs. In the then-current history,
ten observation summaries were present; only two observations had separately
bundled population receipts. The other summaries do not gain row-level proof
from this package.

## Boundary

The replay proves that the receipt is internally consistent with the published
normalized inputs and scanner code. It does not independently authenticate the
upstream provider transport, establish backing, redemption, legal eligibility,
liquidity or executable size. Those remain external diligence questions.

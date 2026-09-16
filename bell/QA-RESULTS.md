# Bell QA results

Release audit: 2026-09-15. The flagship path is the RWA Surface Integrity
Monitor. The older catalogue and dossier modules remain available, but are not
the primary hackathon claim.

## Automated checks

| Check | Result | Evidence |
|---|---|---|
| Integrity rule suite | PASS | `36 passed, 1 skipped` in `bell/tests` |
| Public sanitized Bell suite | PASS | `30 passed` in the release repository |
| Cloudflare Worker | PASS | `7 passed` in `cloudflare/tests/worker.test.mjs` |
| JavaScript syntax | PASS | `node --check bell/site/integrity.js` and `node --check rwa-review/app.js` |
| Public receipt verifier | PASS | HTTP 200, schema `rwa_surface_integrity.v1`, complete required surfaces |
| Secret scan | PASS | no live CMC, XAI or private-key material in the public release |
| Git whitespace | PASS | `git diff --check` |

## Public runtime check

The credential-free API was verified at `2026-09-15T22:22:00Z`:

- 790 tokenised references;
- 1,428 representations;
- 34 `DO NOT COMPARE`;
- 662 `INVESTIGATE`;
- 94 `NO RULE HIT`;
- 31 positive-volume/zero-market-cap groups;
- 790 population index records;
- Silver as the first blocked case, with a 31.12x observed spread.

The API, monitor, audit pack, dated replay and neutral queue all returned HTTP
200. The two Mac mini launch agents completed with exit code 0. A one-shot
launchd publisher normally appears as `not running` between scheduled runs;
that is expected and is not a failed persistent server.

## Product checks

- The main monitor exposes population search, `ALL`, `BLOCKED`, `INVESTIGATE`
  and `NO RULE HIT` filters.
- A search result can be a full priority record or a compact population-index
  record. The UI labels that distinction instead of implying full token
  evidence for every row.
- Live freshness is recalculated in the browser. Static receipts are labelled
  `DATED REPLAY` and cannot present themselves as live.
- The neutral review route provides 25-row pagination, search, state filters,
  decision records and compact numerical evidence.
- The public Audit Pack documents setup, the user path, the receipt contract,
  CMC surfaces and product boundaries.

## Deliberate boundaries

The monitor does not prove backing, redemption, custody, legal eligibility,
solvency or executable liquidity. The Startup plan does not expose the CMC
market-pairs endpoint, so Bell records that limitation rather than inventing
venue or depth evidence. `NO RULE HIT` is not an approval.

The public release contains normalized receipts and an input manifest, not raw
authenticated CMC responses. Source hashes prove the identity of the captured
surfaces; independent recomputation still requires access to the relevant CMC
plan and a fresh observation.

## External review

The final blind juror audit after publishing `dyplux/bell` scored the public
build 84/100 and recommended shortlisting it. The remaining deductions were
reproducibility depth, lack of browser E2E coverage and the fact that the full
queue remains on a separate neutral route.

## Follow-up public build audit: 16 September 2026

The public build subsequently added the investor task, searched-reference
focus, human-readable outcome states, facts-only pair deltas and first-viewport
case shortcuts. The current deterministic test run is `29 passed, 1 skipped`.

The live browser acceptance run verified:

- the three-minute task progresses `0/4 -> 4/4` through search, evidence,
  either two-row selection or an explicit withheld/single-representation
  handoff, and brief or worksheet export;
- `Silver` produces `COMPARISON WITHHELD` and the three-step resolution handoff;
- `Marvell` produces `FACTUAL COMPARISON OPEN` and the external-diligence
  handoff;
- `SPY` produces `COMPARISON WITHHELD`;
- unknown search input produces an explicit no-reference state;
- selected pairs show observed price, market-cap and volume gaps without a
  ranking;
- no page or console errors and no horizontal overflow at 390, 768 or 1440
  pixels.

These checks prove the public workflow and receipts, not willingness to pay or
repeat use. The outstanding validation gate is the six-person human pilot
defined in `PRODUCT-THESIS-2026-09-16.md`.

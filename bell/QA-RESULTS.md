# Bell QA results

This file preserves dated audit history, but the current release is the
22 September 2026 public-surface verification near the end of the document.
The flagship path is the RWA Surface Integrity Monitor. The catalogue explorer
and dossier modules remain available as part of the same product, not as a
separate competing claim.

## Current automated checks: 2026-09-22

| Check | Result | Evidence |
|---|---|---|
| Integrity rule suite | PASS | `31 passed, 1 skipped` in `bell/tests` |
| Public surface contract suite | PASS | `25 passed` in `bell/tests/*.cjs` |
| Cloudflare Worker | PASS | `9 passed` in `cloudflare/tests/worker.test.mjs` |
| JavaScript syntax | PASS | `node --check bell/site/integrity.js` and `node --check bell/site/explorer.js` |
| Public receipt verifier | PASS | HTTP 200, schema `rwa_surface_integrity.v1`, complete required surfaces |
| Public surface smoke check | PASS | page, health endpoint, live receipt and Gold dossier |
| Secret scan | PASS | no live CMC, XAI or private-key material in the public release |
| Git whitespace | PASS | `git diff --check` |

## Current public runtime check

The credential-free API was verified at `2026-09-21T23:43:13Z`:

- 791 tokenised references;
- 1,435 representations;
- 32 `DO NOT COMPARE`;
- 664 `INVESTIGATE`;
- 95 `FACTS OPEN`;
- 791 population index records;
- a fresh publication contract with a 900-second stale threshold.

The API and receipt verifier returned successfully. The browser surface exposes
Gold as a published critical dossier, Palladium as a published investigation,
and Royal Bank of Canada as a reference-only map result. A one-shot publisher
normally exits between scheduled runs; that is expected and is not a failed
persistent server.

## Product checks

- The main monitor exposes population search, `ALL`, `BLOCKED`, `INVESTIGATE`
  and `FACTS OPEN` filters.
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
venue or depth evidence. `FACTS OPEN` is not an approval.

The public release contains normalized receipts and an input manifest, not raw
authenticated CMC responses. Source hashes prove the identity of the captured
surfaces; independent recomputation still requires access to the relevant CMC
plan and a fresh observation.

## Archived audits

The following sections are retained so a reviewer can see how the public build
changed over time. Their counts and test totals are historical and must not be
read as the current receipt.

### Follow-up public build audit: 16 September 2026

The public build subsequently added the investor task, searched-reference
focus, human-readable outcome states, facts-only pair deltas and first-viewport
case shortcuts. The current deterministic test run is `29 passed, 1 skipped`.

The live browser acceptance run verified:

- the three-minute task progresses `0/4 -> 4/4` through search, evidence,
  either two-row selection or an explicit withheld/single-representation
  handoff, and brief or worksheet export;
- `Silver` produces `DO NOT SHORTLIST` and the three-step resolution handoff;
- `Marvell` produces `FACTS OPEN` and the external-diligence
  handoff;
- `SPY` produces `DO NOT SHORTLIST`;
- unknown search input produces an explicit no-reference state;
- selected pairs show observed price, market-cap and volume gaps without a
  ranking;
- no page or console errors and no horizontal overflow at 390, 768 or 1440
  pixels.

These checks prove the public workflow and receipts, not willingness to pay or
repeat use. The outstanding validation gate is the six-person human pilot
defined in `PRODUCT-THESIS-2026-09-16.md`.

### State-aware browser acceptance: 16 September 2026

After the follow-up wording change, a real Chrome E2E run covered all four
decision routes and a reference outside the priority alert set:

| Case | Evidence rows | Expected state | Brief | Task result |
|---|---:|---|---|---|
| Marvell | 6 | `FACTS OPEN` | state and boundary present | `4/4` |
| Silver | 5 | `DO NOT SHORTLIST` | state and boundary present | `4/4` |
| CRWD | 6 | `INVESTIGATE` | state and boundary present | `4/4` |
| AAL | 1 | `SINGLE REPRESENTATION` | state and boundary present | `4/4` |
| Gold | 7 | indexed reference, full rows | state and boundary present | `4/4` |

The run also confirmed no page or console errors, no horizontal overflow at
390, 768 or 1440px, table captions and scoped headers, and accessible labels
for local research notes. These browser checks do not claim human demand
validation.

At that point the main monitor paginated the complete 790-reference index in place. The
neutral queue is retained as an independent replay/review surface rather than
being required to browse beyond the first page.

The post-pagination Chrome check confirmed the public behavior directly:

- the first page shows `1–12 of 790` and `Page 1 of 66`;
- `Next` changes the first visible reference from Silver to SPDR Gold Trust and
  advances to `Page 2 of 66`;
- searching `Gold` returns all seven Gold rows in the main monitor;
- the `INVESTIGATE` filter resets to its own matching set; and
- the 390px viewport has no horizontal overflow or browser errors.

## Current public-surface verification: 21 September 2026

The public surface now includes the complete credential-free RWA map explorer,
published-dossier freshness states and DEX coverage where the dossier contains
that evidence. The explorer distinguishes `REFERENCE ONLY`, `DOSSIER PENDING`,
`SINGLE REPRESENTATION`, `INVESTIGATE` and `DO NOT SHORTLIST`; it does not turn a
map entry into a failed analysis or a clean rule result into an approval.

The release checks currently pass:

- `node --test bell/tests/*.cjs` — 23 passed
- `python3 -m unittest discover -s bell/tests -p 'test_*.py' -q` — 31 passed, 1 skipped
- `python3 bell/verify_integrity_receipt.py` — receipt verification passed
- `python3 bell/verify_public_surface.py` — public page, receipt and Gold dossier passed
- live `https://bell.dyplux.com/` — freshness label, explorer route and receipt chip served

The live receipt observed at `2026-09-21T22:40:36Z` covered 791 tokenised
references and 1,435 representation rows, with 32 `do_not_compare`, 664
`investigate` and 95 `no_flags` groups. The public label for `no_flags` is
`FACTS OPEN`. These are dated observations, not
investment approval or market-wide safety scores.

The hero receipt label now carries the same freshness state as the evidence
section. A stale live publication cannot be presented as an unqualified live
receipt, and a dated fallback is labelled `DATED REPLAY`.

The public explorer was also exercised in a real Chrome session against the
deployed page:

| Query | Route observed | Freshness copy |
|---|---|---|
| Gold | `DO NOT SHORTLIST` | published evidence inside freshness contract |
| Palladium | `INVESTIGATE` | published evidence inside freshness contract |
| Royal Bank of Canada | `REFERENCE ONLY` | map route, no wrapper dossier asserted |

These cases cover a published critical dossier, a published non-critical
investigation and a map reference without a token wrapper. The explorer keeps
those routes distinct instead of presenting all search results as equivalent
analysis.

The documentation was also reconciled with the actual map composition. The
current snapshot contains 4,686 stocks, 3,121 ETFs and 4 commodities. It does
not claim that currencies, government securities or real estate were observed
in this receipt; those categories remain schema-compatible future routes rather
than fabricated coverage.

## Responsive decision-flow verification: 22 September 2026

We repeated the deployed flow in Chrome with emulated `390×844`, tablet and
desktop viewports. The page reported no horizontal overflow at any tested
viewport, and the first search form remained inside the viewport with a visible
button and result area.

| Query | Route observed | Evidence shown |
|---|---|---|
| Silver | `DO NOT SHORTLIST` | 5 representations, 4 issuers, current observed quote ratio |
| Marvell | `FACTS OPEN` | 6 representations, 5 issuers, factual comparison route |

The Silver result displayed a `31.25×` observed quote range during this run.
The value is read from the published receipt and is not hardcoded into the
video script. Both flows kept the document width equal to the viewport at `390px`, so a normal
mobile user can reach the search action and read the decision without sideways
scrolling.

## Normal-user live acceptance: 22 September 2026

Starting from the public page with no prior context, Chromium submitted the
visible asset search and reopened each result through its stable URL:

| Query | Result | First useful output |
|---|---|---|
| Silver | `DO NOT SHORTLIST` | 31.25× observed quote spread, supporting signals and next check |
| Netflix | `INVESTIGATE` | seven representations, six issuers and a classification handoff |
| Marvell | `FACTS OPEN` | six representations, five issuers and descriptive-only comparison |
| Royal Bank of Canada | no live case | explicit full-map handoff, not a fabricated failure |

All four runs produced no page errors. The first three results preserved the
decision label in the hero and queue; the last route distinguished the live
receipt from the complete RWA map. The desktop document remained 1,440px wide
with no horizontal overflow.

## Mobile navigation verification: 22 September 2026

The first deployed mobile render showed that the horizontal navigation could
leave `References` and `Receipt` partially outside the first view. The mobile
override now fits all six primary destinations visibly in the 390px viewport:
`Start`, `How it works`, `Your result`, `Explore RWA`, `References` and
`Receipt`. The updated render was checked against the deployed page after the
CSS publication; the document remains 390px wide with no horizontal overflow.

The case result also exposes a stable copy-link action. A copied URL uses
`?reference=<CMC RWA ID>` so a reviewer can reopen the same evidence case
without repeating the search.

## Mobile evidence-line verification: 22 September 2026

On the published Silver case at 390×844, signal evidence lines wrap over multiple
lines instead of being ellipsized. The first decision and evidence CTA remain
visible, while full evidence remains available in the expanded row.

## Scheduled publication verification: 22 September 2026

The local launchd jobs were checked after the public Worker and site updates.
The integrity publisher completed with exit code `0`, published the receipt
observed at `2026-09-21T23:11:55Z`, and recorded `remote_published: true`.
The dossier publisher also completed with exit code `0`. An upstream CMC `400`
for one invalid quote request is recorded as a failed refresh job rather than
left leased indefinitely; other queued work can continue.

This confirms the public freshness contract is backed by a repeatable scheduled
publisher, not a manually refreshed screenshot. The current live receipt may
change independently of the dated replay package.

The scheduled job was then run once through launchd as an operational check.
It exited cleanly, published a new receipt at `2026-09-21T23:27:52Z`, and the
public endpoint reported `FRESH` 25 seconds later. That receipt covered 791
tokenised references and 1,435 representation rows with 33 `do_not_compare`,
663 `investigate` and 95 `no_flags` groups.

## Live-receipt to full-map handoff: 22 September 2026

The main search and the full RWA explorer now state their coverage boundary.
Opening `?reference=Royal%20Bank%20of%20Canada` produces a visible `No live case
found` result and a `Search the full RWA map` action; it does not describe the
map-only reference as a failed analysis. This preserves the distinction between
the 791-reference live integrity receipt and the 7,811-reference credential-free
map snapshot.

The handoff was exercised in Chromium at `390×844`: clicking the action filled
the full-map search with `Royal Bank of Canada`, loaded the underlying-only
dossier, and kept the document width at 390px.

The resulting map route is also reloadable as
`?map_reference=royal-bank-of-canada`; Chromium reopened the same underlying
dossier from that URL at the same mobile width.

Numeric deep links now prefer exact RWA IDs over substring matches. The live
`?reference=5` route shows `Silver`, `1 MATCH · EXACT MATCH` and a one-row
queue, rather than presenting unrelated IDs that merely contain the digit 5.

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
| Public surface contract suite | PASS | `29 passed` in `bell/tests/*.cjs` |
| Cloudflare Worker | PASS | `10 passed` in `cloudflare/tests/worker.test.mjs` |
| JavaScript syntax | PASS | `node --check bell/site/integrity.js` and `node --check bell/site/explorer.js` |
| Public receipt verifier | PASS | HTTP 200, schema `rwa_surface_integrity.v1`, complete required surfaces |
| Public surface smoke check | PASS | page, health endpoint, live receipt and Gold dossier |
| Secret scan | PASS | no live CMC, XAI or private-key material in the public release |
| Git whitespace | PASS | `git diff --check` |

## Current public runtime check

The credential-free API was verified at `2026-09-22T00:43:25Z`:

- 791 tokenised references;
- 1,435 representations;
- 37 `DO NOT COMPARE`;
- 661 `INVESTIGATE`;
- 93 `FACTS OPEN`;
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
the 7,811-entry dated map snapshot had 4,686 stocks, 3,121 ETFs and 4
commodities. This is the historical map composition, not the current live
integrity receipt; it does not claim that currencies, government securities or
real estate were observed in that snapshot. Those categories remain
schema-compatible future routes rather than fabricated coverage.

## Credential-free map refresh: 22 September 2026

The browser-served `catalog.json` was refreshed from `/v5/real-world-assets/map`
before this release. The collection made 79 paginated calls, all returned HTTP
200, and the result contained 7,811 references: 4,686 stocks, 3,121 ETFs and 4
commodities. Seven hundred and ninety-one references had a mapped token layer.
The last observed historical-data timestamp in the map was
`2026-09-22T01:03:00.000Z`.

The machine-readable refresh receipt is
`site/proof/rwa-catalogue-refresh-2026-09-22.json`. Its SHA-256 binds the
receipt to the exact browser-served `catalog.json`. This refresh is a discovery
map update, not a replacement for the separate live integrity receipt.

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

## Runtime alignment and fresh publication: 22 September 2026

The Mac mini publisher runtime was aligned with the current integrity collector
and then exercised through its scheduled launchd entry. The run exited cleanly,
published remotely and produced a fresh receipt observed at `2026-09-22T00:28:03Z`.
The public smoke check reported 791 tokenised references and 1,435 representation
rows with 37 `do_not_compare`, 661 `investigate` and 93 `no_flags` groups.

This check confirms that the live publication path and the public replay method
use the same current collector boundary. It does not claim that every optional
asset dossier is available or that CMC data proves backing, liquidity or execution.

## Responsive release verification: 22 September 2026 · final11

The final11 public release was checked against the deployed domain after the
responsive layout fix:

- 390px mobile: the hero copy wraps inside the viewport, the search action is
  fully visible and the investor task remains readable
- 768px tablet: the header moves its navigation to a second row so the receipt
  action does not leave the viewport
- 1440px desktop: the two-column hero and live evidence card remain intact
- the live browser reported `documentWidth = viewportWidth` at 390px
- `LIVE RECEIPT · FRESH` was visible on the deployed page
- a live Gold search returned `DO NOT SHORTLIST`, 7 representations, 6
  issuers and the observed quote-range evidence from the current receipt

The release is published as Git commit `16d44c3` and tag
`hackathon-submission-2026-09-22-final11`. These are presentation and
navigation checks; they do not claim that a clean result proves backing,
liquidity, redemption or investment suitability.

## Evidence-first search verification: 22 September 2026 · final14

The public Gold route was checked after the evidence-first search update. A
user who searches the visible form now receives, before opening the deeper
evidence table:

- the human-readable decision state
- the observed quote ratio used by the route
- the lowest and highest priced representation symbols
- the corresponding issuer labels and observed quote values
- an explicit boundary stating that the rows are not a discount, backing,
  liquidity or executable spread

The endpoint panel is derived from the current published receipt at runtime; no
asset-specific values are hardcoded into the interface. The live browser check
returned `LIVE RECEIPT · FRESH`, kept `documentWidth = viewportWidth` at 390px
and returned Gold as `DO NOT SHORTLIST` with seven representations and six
issuer labels.

The public contract suite for this release passed `28/28`, including a source
test that requires the endpoint panel and its boundary language to remain
present.

## Normal-user mobile acceptance: 22 September 2026 · final16

Starting from the deployed public page with no prior context, a Chromium run at
390px searched three routes:

| Search | Result shown | Handoff observed |
|---|---|---|
| Gold | `DO NOT SHORTLIST` | endpoint panel with low/high representation and issuer rows |
| Marvell | `FACTS OPEN` | factual side-by-side route and external diligence handoff |
| Royal Bank of Canada | no live case | explicit full RWA map handoff |

All three routes retained `LIVE RECEIPT · FRESH`, reported
`documentWidth = viewportWidth`, and produced no browser console errors. The
first two routes exposed their quote evidence before the deeper representation
table; the third did not fabricate a result outside the published receipt.

## Search interaction handoff: 22 September 2026 · final18

The mobile acceptance was repeated as an actual form submission rather than a
deep-link load. After entering `Gold` and pressing the visible action button,
the result card landed at the top of the viewport, with the endpoint panel
visible immediately. The deeper live decision card remained in the same page
flow below it. The run reported `searchTop = 104px`,
`LIVE RECEIPT · FRESH`, endpoint evidence present and
`documentWidth = innerWidth = 390px`.

This closes the first-click gap where a submitted search previously jumped over
its own result and sent the user to a much later section of the page.

## Viewport-aware evidence handoff: 22 September 2026 · final20

The same Gold submission was checked at both ends of the responsive layout:

- at 390px, the compact searched-reference result and endpoint panel are the
  immediate destination
- at 1440px, the full `WHY THE RESULT MATTERS` card is the immediate destination,
  keeping the decision, capital check and issuer concentration visible together
- both routes preserve the current live receipt label and endpoint evidence
- both routes keep the document width equal to the viewport width

This avoids showing a narrow result card beside an empty desktop column while
preserving the shorter first-click path on mobile and tablet.

## Quote-band mobile acceptance: 22 September 2026 · final21

The deployed Silver route was checked after the observed quote-band addition:

- desktop, tablet and 390px mobile all returned the same four priced rows;
- the band shows the observed median, each row's distance from that median and
  the reported 24-hour volume state;
- mobile adds `SWIPE FOR QUOTE · MEDIAN GAP · VOLUME →` above the horizontal
  table and keeps the representation column sticky while the remaining fields
  are revealed;
- all three viewports kept `documentWidth = viewportWidth` and produced no
  browser console errors;
- the route continued to state that the band is not a ranking, discount,
  backing, liquidity or executable-spread claim.

This is a presentation and navigation improvement. It does not change the
underlying receipt or claim that the observed rows are executable quotes.

## Reported-volume context acceptance: 22 September 2026 · final22

The capital check now recalculates an amount-to-reported-volume percentage as
the user changes the amount under consideration. The metric sums only positive
token-row `volume_24h` fields and labels the result as rolling reported volume
rather than depth or executable exit capacity. The no-volume case remains
explicit and does not render a zero as if it were evidence.

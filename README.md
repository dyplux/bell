# Bell - RWA Surface Integrity

Bell turns CoinMarketCap RWA discovery into a pre-shortlist check: which
representations pass its reported-price filters, and what still needs review?

## At a glance

| | |
|---|---|
| **Live** | <https://bell.dyplux.com/> |
| **For judges** | <https://bell.dyplux.com/judge> - the claim, the 30-second check and the receipts on one page, no auth |
| **BUIDL logo** | [`bell/site/assets/buidl-logo-480.png`](bell/site/assets/buidl-logo-480.png) - 480 × 480 PNG of Bell's wordmark; the vector source is beside it |
| **Track** | Build with CMC API, Real World Assets. MIT licence |
| **Local interface** | `make app` - visual workspace, local agent API, and optional own CMC key |
| **Whole-catalogue base rate · 28 Sep** | In the preserved 28 September capture, 88 of 250 multi-representation references pass Bell's filtered quote comparison. The other 162 are routed to review (64.8%; Wilson 95% interval 58.7–70.5%), producing 163 rule hits: 107 missing-coverage reasons, 40 price or field review triggers, and 16 cases with fewer than two eligible spot routes. A review trigger is not proof of economic contradiction |
| **Run it yourself** | `git clone https://github.com/dyplux/bell.git && cd bell && make app` - local visual workspace at `http://127.0.0.1:8080/workspace.html`; no API key or install required for dated evidence. `make base-rate` reproduces the keyless 28 Sep population calculation; `make base-rate RATE_INPUTS=...` selects another normalized capture |
| **Verify the whole thing** | `make check-offline` - 600 tests, no credentials or network required. It replays the original 21 Sep observation with a frozen, hash-pinned scanner, separately recomputes the later-rule 21 Sep replay and complete 28 Sep capture from their shipped inputs, and verifies the dated Alphabet pair review against its CMC rows. Of the 38 dated observations in the population history, two legacy observations have separately bundled receipts; new observations retain their full receipt archive and compare the complete history summary. Per-reference rows are checked when a retained receipt has a same-rule series step. The separate v3 segment is derived only from its retained receipts; it is not merged with the v2 series. Older steps without receipts remain UNVERIFIED at row level. A separate 28 Sep capture ships all six inputs but is outside that history. The offline gate was observed between 17.71 and 33.63 seconds across 2 machines |
| **Rules as an executable spec** | `python3 bell/verify_rule_boundaries.py` - 0.2s, 8 boundary checks, no network |
| **Receipts** | [live](https://bell.dyplux.com/api/integrity) · [28 Sep capture](bell/site/proof/rwa-surface-integrity-capture-2026-09-28.json) · [normalized inputs](bell/site/proof/rwa-surface-integrity-inputs-2026-09-28.json) · [original 21 Sep receipt](bell/site/proof/rwa-surface-integrity-original-2026-09-21.json) · [frozen legacy replay source](bell/rwa_integrity_legacy_2026_09_21.py.txt) · [later-rule 21 Sep replay](bell/site/proof/rwa-surface-integrity-latest-replay-2026-09-21.json) · [21 Sep base rate](bell/site/proof/base-rate-2026-09-21.json) |
| **Alphabet pair review** | [dated GOOGLX / GOOGLon terms check](bell/site/proof/alphabet-class-a-pair-review-2026-09-29.json) · `make verify-pair-review` checks the CMC rows and four dated, hashed excerpts from Backed, Ondo and xStocks docs; raw pages and legal archives are not included |


## What the product does

Bell joins CMC RWA references, token rows, quotes, metadata and issuers through
stable identifiers, then routes each reference into the honest workflow:

- `COMPARABLE` (a filtered quote comparison, not an endorsement) when routes under one CMC RWA reference pass Bell's
  price and reported-volume filters. This does not establish equivalent units
  or claims. Bell names the observed spread, the cheapest route and which route
  has the highest reported 24h volume; that volume is not market depth.
- `DO NOT SHORTLIST` when a critical comparison stop rule fires; field
  inconsistencies trigger verification, not a claim about market behaviour
- `INVESTIGATE` when evidence is incomplete or ambiguous
- `FACTS OPEN` when observed fields can be inspected without creating a winner
- `SINGLE REPRESENTATION` when there is no valid wrapper comparison

The product is not a safety score, investment recommendation or proof of
backing, redemption, custody, solvency or executable liquidity.

For the Alphabet Class A reference, the comparison view also includes a
source-backed pair review of GOOGLX and GOOGLon. It records what the two issuer
pages align on, the unit evidence each page publishes, the missing current
GOOGLX multiplier, and the resulting `DO NOT COMPARE AS LIKE-FOR-LIKE` action.
CMC quotes are dated 28 September 2026; issuer pages were checked 29 September
2026. Four factual excerpts from three official pages/docs are shipped with
SHA-256 checks; raw pages and signed legal archives are not. The review
withholds a like-for-like claim while unit equivalence remains unproven.

For a selected reference, the public page also makes the immediate review
consequence visible: an illustrative amount can be kept uncommitted, held for
verification or routed to descriptive diligence. Where at least two positive
quote rows exist, Bell shows the observed quote band, each row's distance from
the observed median and the reported 24-hour volume state. These are evidence
fields, not a discount, fair-value, liquidity or execution claim.

## What does the latest reproducible filter observe?

A monitor that refuses is only worth reading if you know how often it refuses,
so the rate is measured over the whole captured catalogue rather than argued
from examples. `bell/base_rate.py` states its method in its own docstring,
above the number, so the method cannot be tuned to the result afterwards. The
default is the preserved 28 September capture. Reproduce it offline, with no
API key, using `make base-rate`:

```
    793  references carrying tokenised representations
    543  have one representation - nothing to compare, excluded rather than
         counted against the rate
    250  carry two or more, so a comparison is something a user could attempt

    162  of those are refused by a coded rule
     88  are published with the comparison performed

  Refusal rate  64.8%   (95% CI 58.7% to 70.5%, n = 250)
```

Read on its own, 64.8% sounds like a verdict on the market. The reasons include
missing source coverage, rule triggers that require review, and cases where no
eligible spot pair exists:

```
    107  the catalogue offers no second number to compare   (66%)
     40  price or field review rules fired
     16  fewer than two eligible spot routes; no pair to compare
```

The 107 coverage reasons are missing prices or quotes without positive reported
volume. The 16 no-pair reasons mean the route filter found fewer than two
eligible spot rows. The 40 review triggers include price-denomination, dispersion,
market-cap/volume-field and publishable-spread rules: 4 price-denomination, 33
zero-market-cap/positive-volume field pairs, 3 price-dispersion and no spread-ceiling
trigger. They guide review; they do not prove that two assets have different
rights or that a market is invalid.

(163 rule hits against 162 refused references because one reference can trigger more than one rule.)

The interval is a Wilson score interval, which stays honest near the edges of
the distribution where the normal approximation does not. The single-
representation majority is excluded from the denominator rather than scored as
a pass, because there was never a comparison to refuse. The rate is a recomputation
of the 28 September 2026 15:14 UTC observation, bound to the normalized-input and
rule-code SHA-256 values in its receipt. It is not today's live result or a verdict
on any issuer. The older 21 September calculation remains a separate historical artifact.


## The public surface

The single public page combines the monitor, the RWA explorer and published
dossiers. It searches the 7,811-entry dated CMC map snapshot, while keeping
that catalogue separate from the live integrity receipt.

The historical replay observed on 21 September 2026 contained 791 tokenised references
and 1,435 representation rows. The later, fully reproducible 28 September capture
contains 793 references and 1,449 token rows; its normalized inputs let a reviewer
recompute the receipt without credentials using `make verify-capture`. The live page
renders the latest server-side receipt and can show a different count again. Each
dated package is a separate observation, not a conflicting version of the same data.
The live receipt exposes observation time, publication time, freshness state, rule
evidence and source fingerprints without exposing the CMC credential.

CMC provides the discovery surfaces. Bell adds stable-ID joins, reported-field
review triggers, missing-versus-zero handling, next action and a replayable evidence path.
The result is a research handoff rather than another RWA leaderboard: the user
gets a decision state, the rows that produced it and the next unresolved check.
Each selected case can also be exported as a compact `bell.case-receipt.v1`
JSON containing the exact rows, signals, source fingerprints and stable-ID join
method used for that decision.

## Download and run locally

Clone the public repository and start Bell from its root:

```bash
git clone https://github.com/dyplux/bell.git
cd bell
make app
```

Prerequisites: Python 3.10+ and `make`. The app uses Python's standard library;
it needs no pip packages to serve the interface.

Open <http://127.0.0.1:8080/workspace.html>. The **Visual workspace** works
immediately from the committed CMC catalogue and dated evidence; no package
installation, account or API key is needed for this mode. Stop the local app
with `Ctrl+C` in the terminal.
The **Save review** action exports the selected receipt's timestamp, verdict,
all token IDs and observed quote fields, plus CMC-reported source links. It
uses the receipt already on screen and makes no new API request.

The same page has an **Agent interface** tab for scripts and local agents. Its
JSON API starts at `GET /api/agent` (tool manifest); `GET /api/catalog?q=tesla`
searches the dated 7,811-entry catalogue, and `GET /api/integrity` returns the
dated population receipt. These routes do not call CMC.

For current CMC data, enter your own key in the Visual workspace. The key is
sent only to this local server, held in process memory, and used for
server-side CMC requests. It is not saved in browser storage, written to disk,
or included in Git. It is cleared when the server stops. Live requests may
consume your CMC plan quota. The hosted website never accepts this key.

Example local agent calls:

```sh
curl http://127.0.0.1:8080/api/agent
curl 'http://127.0.0.1:8080/api/catalog?q=tesla'
curl http://127.0.0.1:8080/api/integrity
curl 'http://127.0.0.1:8080/api/audit?slug=tesla'
```

Live tools are `GET /api/rwa?slug=...`, `/api/terminal?slug=...`,
`/api/audit?slug=...` and `/api/session?slug=...&days=7`. They require a key
configured in the Visual workspace or in the local server's `CMC_API_KEY`
environment. The agent API is a local HTTP JSON interface; it is not an MCP
server. For a headless integration, set `CMC_API_KEY` in the server process;
never put it in a URL or a checked-in file.

## Verify the release

One command, no API key and no account:

```bash
make check
```

`make check-offline` runs the suites and receipt verifiers without network access
or a browser. `make check` adds a browser check against the deployed public site
when Playwright is installed. Neither command needs a CMC credential.

If a browser is present, `make check` then drives the deployed site with
Playwright and verifies the interface rather than describing it: search, the
decision brief, the case-receipt download, the two-wrapper comparison, the
watchlist, the mobile layout and the network-failure fallback. If no browser is
present it prints exactly which of those it did not verify and continues, so
the gate degrades honestly instead of quietly checking less than it claims.

```bash
make install        # installs Playwright and a browser, so check can verify the UI
make check-offline  # the same gate with no network and no browser
make check-live     # force the browser audit and fail if it cannot run
make deploy         # deploy a clean commit and stamp its SHA in the public health route
```

The homepage shows the current comparison count with its multi-representation
denominator, plus a link to the exact Git commit reported by the deployed Worker.

`make check-offline` is what CI runs: a red build should mean this repository is
wrong, never that a deployed site was briefly unreachable.

### Is the upstream contract still intact today?

Every contract test here reads payloads captured on 13, 17 and 21 September, so
it catches a regression against those captures and cannot notice that CMC
changed afterwards. `make liveness` calls the API and writes a dated receipt of
what it observed — status, a response fingerprint and whether each property the
code depends on still holds. It records no payload, no row of data and no
credential, so the receipt ships in this repository and is readable by someone
with no account:

    bell/site/proof/upstream-liveness-<date>.json

The probe needs a key. Reading its result does not.

Two more, also keyless:

```bash
make demo        # answer one comparability question from the shipped receipt
make base-rate   # reproduce the published population measurement
```

`make check-live` additionally drives a real browser against the deployed site.
It needs network and a browser, which is why it is separate from `make check`.

`make help` lists everything.

Before recording the demo, refresh the values used in the narration from the
public receipt:

```bash
python3 bell/prepare_demo.py --reference Silver > /tmp/bell-demo-values.md
```

This command uses no credential and prevents a screen recording from carrying
an older quote, issuer or timestamp.

For current visual frames, use the credential-free browser capture:

```bash
PYTHONPATH=bell python3 bell/capture_demo.py --output /tmp/bell-demo-capture
```

It records the live hero, blocked Silver case, mobile case, the published Marvell comparison
case and Gold repeat-window panel without committing generated screenshots.

For the complete paced walkthrough used as an editing source:

```bash
python3 bell/record_demo.py --long --output /tmp/bell-demo-video-long
```

The long recording covers the first search, evidence rows, population shape,
facts-open contrast, repeat-window evidence, map-only handoff and receipt
boundary. It uses the public credential-free surface only.

`verify_public_surface.py` checks the public page, health endpoint, live
receipt and a published dossier without credentials.

## Evidence and limits

Public normalized receipts and sanitized inputs are under
[`bell/site/proof/`](bell/site/proof/), which is what the site serves and what
`make verify` reads. [`bell/docs/proof/`](bell/docs/proof/) holds superseded
copies and says so in its own README; do not verify against it. The browser never calls CMC directly.
The Mac mini publisher owns the credential, runs the deterministic scan and
publishes normalized evidence through the authenticated Worker route.

The CMC market-pairs surface is not available on the Startup plan. Bell records
that limitation rather than presenting missing venue data as zero liquidity.

Read the [public product brief](docs/PRODUCT.md),
[architecture](docs/ARCHITECTURE.md) and [judge path](bell/JUDGE.md) for the
method and boundaries. `make check` is the QA record: it runs the suite and
re-derives the published receipt from the shipped inputs, so the test result is
something you reproduce rather than something this repository asserts.

This repository contains the public product, tests, receipts and deployment
adapter. Private research, competitor dossiers, jury reports and credentials
are intentionally excluded.

## Licence

MIT. See [`LICENSE`](LICENSE).

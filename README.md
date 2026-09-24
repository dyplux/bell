# Bell - RWA Surface Integrity

Bell turns CoinMarketCap RWA discovery into an evidence gate for the question
that matters before a shortlist: can these representations be compared at all?

Live product: [bell.dyplux.com](https://bell.dyplux.com/)

## What the product does

Bell joins CMC RWA references, token rows, quotes, metadata and issuers through
stable identifiers, then routes each reference into the honest workflow:

- `COMPARABLE, NOT ENDORSED` when the representations share an identity, a unit
  and a market state, so their prices can honestly be set side by side. Bell
  names the observed spread, the cheapest route and whether that route is also
  the deepest
- `DO NOT SHORTLIST` when a critical contradiction is observed
- `INVESTIGATE` when evidence is incomplete or ambiguous
- `FACTS OPEN` when observed fields can be inspected without creating a winner
- `SINGLE REPRESENTATION` when there is no valid wrapper comparison

The product is not a safety score, investment recommendation or proof of
backing, redemption, custody, solvency or executable liquidity.

For a selected reference, the public page also makes the immediate review
consequence visible: an illustrative amount can be kept uncommitted, held for
verification or routed to descriptive diligence. Where at least two positive
quote rows exist, Bell shows the observed quote band, each row's distance from
the observed median and the reported 24-hour volume state. These are evidence
fields, not a discount, fair-value, liquidity or execution claim.

## How often is a comparison safe at all?

A monitor that refuses is only worth reading if you know how often it refuses,
so the rate is measured over the whole catalogue rather than argued from
examples. `bell/base_rate.py` states its method in its own docstring, above the
number, so the method cannot be tuned to the result afterwards. Reproduce it
with `make base-rate`, offline, with no API key:

```
    791  references in the catalogue
    547  have one representation - nothing to compare, excluded rather than
         counted against the rate
    244  carry two or more, so a comparison is something a user could attempt

    157  of those are refused by a coded rule
     87  are published with the comparison performed

  Refusal rate  64.3%   (95% CI 58.2% to 70.1%, n = 244)
```

The interval is a Wilson score interval, which stays honest near the edges of
the distribution where the normal approximation does not. The single-
representation majority is excluded from the denominator rather than scored as
a pass, because there was never a comparison to refuse. The rate is a statement
about the data on one dated observation, not a verdict on any issuer.


## The public surface

The single public page combines the monitor, the RWA explorer and published
dossiers. It searches the 7,811-entry dated CMC map snapshot, while keeping
that catalogue separate from the live integrity receipt.

The receipt observed on 21 September 2026 contained 791 tokenised references
and 1,440 representation rows. The receipt is published
server-side and exposes observation time, publication time, freshness state,
rule evidence and source fingerprints without exposing the CMC credential.

CMC provides the discovery surfaces. Bell adds the join logic, contradiction
checks, missing-versus-zero handling, next action and replayable evidence path.
The result is a research handoff rather than another RWA leaderboard: the user
gets a decision state, the rows that produced it and the next unresolved check.
Each selected case can also be exported as a compact `bell.case-receipt.v1`
JSON containing the exact rows, signals, source fingerprints and stable-ID join
method used for that decision.

## Run locally

The credential-free website needs no install or API key:

```bash
python3 -m http.server 4173 --directory bell/site
```

Open <http://localhost:4173>. The explorer and dated receipts work offline.
Published live dossiers are read from the public Cloudflare endpoint when the
site is deployed.

For a local live dossier, keep the CMC key outside the repository:

```bash
export CMC_API_KEY="your-startup-key"
python3 bell/server.py --host 127.0.0.1 --port 8080
```

The key remains in the server process and is never sent to the browser.

## Verify the release

One command, no API key, no account, offline:

```bash
make check
```

That runs every suite, re-hashes the published receipt against the shipped
credential-free input package, re-runs the scan asserting structural equality,
and audits the public surface. The offline part takes about a second.

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
```

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

It records the live hero, blocked Silver case, mobile case, facts-open Marvell
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
[`bell/docs/proof/`](bell/docs/proof/). The browser never calls CMC directly.
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

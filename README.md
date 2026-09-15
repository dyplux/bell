# Bell — RWA Decision Desk

Bell is Dyplux's universal real-world-asset research terminal. It maps CMC references across
stocks, ETFs, commodities, currencies, government securities and real estate, then chooses the
honest workflow for the representation layer:

- no token: keep the case on the underlying;
- one token: open a representation dossier;
- multiple tokens: compare only after separating identity, issuer, network and market evidence.

Live product: **[bell.dyplux.com](https://bell.dyplux.com/)**

## Flagship build: RWA Surface Integrity Monitor

The public integrity monitor is the decision gate for the comparison problem:

- **790** tokenised RWA references scanned;
- **1,428** token representations inspected;
- stable joins by `rwa_id`, `crypto_id` and `issuer_id`;
- explicit `DO NOT SELECT A WRAPPER` and `HOLD COMPARISON` outcomes;
- credential-free live receipt at [`/api/integrity`](https://bell.dyplux.com/api/integrity);
- dated replay at [`bell/site/proof/`](bell/site/proof/);
- searchable blind review at [`rwa-surface-review.pages.dev`](https://rwa-surface-review.pages.dev/);
- public setup and reviewer route in the [Audit Pack](https://bell.dyplux.com/guide.html).

Start with the [Integrity Monitor](https://bell.dyplux.com/integrity), then use the
[Audit Pack](https://bell.dyplux.com/guide.html) to understand the receipt contract,
the normal-user journey, the CMC surfaces and the product boundaries.

## Why Bell exists

CMC provides discovery, quotes and token/issuer surfaces. Bell adds the decision protocol around
those surfaces: it preserves evidence timestamps, detects contradictory representations, keeps
unavailable data separate from zero, and produces a deterministic brief with a next research queue.
It is a research instrument, not a trading signal and does not claim legal backing, redemption,
solvency, suitability or executable liquidity.

## What is public here

This repository contains the product, its reproducible calculation layer, public receipts, the
credential-free website and the Cloudflare publication adapter. Dyplux's internal research desk,
strategy, competitor maps, operational notes and credentials are kept in a separate private
repository.

## Run the website locally

```bash
python3 -m http.server 4173 --directory bell/site
```

Open <http://localhost:4173>. The catalogue works without credentials or API calls. Gold and
Tesla include dated public evidence; other assets explicitly show when they are map entries only.

## Run a live local dossier

Keep the CMC key in the process environment or a private local file. It is never sent to the
browser.

```bash
export CMC_API_KEY="your-startup-key"
python3 bell/server.py --host 127.0.0.1 --port 8080
```

The server exposes `/api/terminal`, `/api/audit`, `/api/session` and `/api/published`. The
Cloudflare Worker exposes the credential-free published route; the Mac publisher owns the CMC
key and publishes normalized dossiers through an authenticated internal route.

## Evidence and receipts

Public normalized receipts live in [`bell/docs/proof/`](bell/docs/proof/). They contain no API
credentials or raw authenticated responses. The method and deployment flow are documented in
[`docs/PRODUCT.md`](docs/PRODUCT.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

The integrity release includes a [sanitized input manifest](bell/docs/proof/rwa-surface-integrity-input-manifest-2026-09-15.json)
with surface counts, stable-ID join coverage and source fingerprints.

The integrity publisher runs outside the browser. It reads the CMC credential from a private
process environment, scans the required RWA surfaces, and publishes only the normalized receipt
through an authenticated Cloudflare route. A public response exposes its observation time,
publication time, freshness state, source hashes and rule evidence, never the credential.

The dated receipt is deliberately labelled `DATED`; it is an offline replay, not a claim that a
cached file is live. `NO RULE HIT` is not an approval and the monitor does not prove backing,
redemption, custody, legal eligibility, solvency or executable liquidity.

## Test

```bash
pytest -q bell/tests
node --test cloudflare/tests/worker.test.mjs
node --check bell/site/app.js
node --check bell/site/integrity.js
```

## Licence

MIT. See [`LICENSE`](LICENSE).

# Cloudflare live publication adapter

This directory contains the public edge for Bell. It serves `bell/site/` as static assets and
exposes a small D1-backed API:

- `GET /api/published?slug=gold` returns the latest normalized dossier;
- stale or missing dossiers create a deduplicated refresh job;
- `GET /internal/jobs` leases refresh jobs to the Mac mini publisher;
- `POST /internal/fail` records a failed leased job so an upstream rejection is visible and retryable;
- `POST /internal/publish` accepts a credential-free dossier from the publisher.
- `GET /api/integrity` returns the latest population-wide integrity receipt and freshness state;
- `POST /internal/integrity` accepts a credential-free integrity receipt from the Mac mini.

The CMC API key never enters this Worker. Keep it on the Mac mini and set `PUBLISHER_TOKEN` as a
Cloudflare secret and on the publisher machine.

The Mac mini environment template is [`../bell/launchd/bell.env.example`](../bell/launchd/bell.env.example).

## Local setup

```bash
cd cloudflare
npm install
npx wrangler d1 execute dyplux-rwa --file=schema.sql --remote
npx wrangler secret put PUBLISHER_TOKEN
npx wrangler dev
```

The current deployment already has the `dyplux-rwa` D1 database configured in
`wrangler.toml`. If you deploy to a different Cloudflare account, create a new database and
replace its ID there before applying the schema.

The Worker configuration uses the current Workers Static Assets model: `/api/*` runs the Worker
and all other routes are served from `bell/site/`. See the official [Static Assets binding
documentation](https://developers.cloudflare.com/workers/static-assets/binding/).

## Publish from the Mac mini

```bash
export BELL_PUBLICATION_URL="https://rwa.example.com/internal/publish"
export BELL_JOBS_URL="https://rwa.example.com/internal/jobs"
export PUBLISHER_TOKEN="..."
CMC_API_KEY="..." python3 bell/publisher.py gold tesla
```

For user-triggered refreshes, run the queue worker instead of a fixed slug list:

```bash
CMC_API_KEY="..." python3 bell/publisher.py --pull-queue --limit 5
```

The Worker leases queued slugs and the Mac mini publishes each completed dossier back to
`/internal/publish`.

If CMC rejects one slug, the publisher records the failure at `/internal/fail` and continues the
queue. The public site keeps the last valid dossier and exposes freshness instead of treating an
upstream rejection as a successful refresh.

The local store is still written first, so a failed network publish does not destroy the latest
local receipt. The publisher reports remote publication failure rather than claiming success.

## Deploy

The checked-in `wrangler.toml` targets the current Dyplux Cloudflare account. Deploy with:

```bash
npx wrangler deploy
```

The public product hostname is [`https://bell.dyplux.com/`](https://bell.dyplux.com/). The
`workers.dev` hostname remains only as a technical fallback.

The integrity monitor is refreshed independently from the per-asset queue:

```bash
CMC_API_KEY="..." python3 bell/integrity_publisher.py
```

The example launchd job is [`../bell/launchd/com.dyplux.bell-integrity-publisher.plist.example`](../bell/launchd/com.dyplux.bell-integrity-publisher.plist.example).
The public page first reads `/api/integrity` and falls back to the dated receipt
only when no live receipt exists. It labels the source and freshness state.

Do not commit `.dev.vars`, tokens or API keys.

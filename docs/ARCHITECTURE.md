# Live publication architecture

## Product decision

The public website should not remain a frozen demo once Bell is live. The intended product is:

> Bell collects and verifies the latest CMC evidence; the website reads the latest published dossier when a user searches an RWA.

The browser never receives the CMC key and never fans out to CMC endpoints. This keeps the API contract, rate limits and evidence rules on the server side.

## Request flow

```text
user searches RWA
        |
        v
public website -> /api/published?slug=gold
        |                  |
        |                  +--> latest normalized dossier + observed_at
        |                  +--> stale/missing status + refresh_queued
        v
show current published evidence

Mac mini Bell publisher -> CMC API -> audit -> credential-free receipt
                         -> publish latest dossier -> public store/API
```

The first query for an unresearched asset may return `MAP ENTRY / refresh queued`. It must not
pretend that a map row is a completed audit. Once the Mac mini finishes, the next request shows
the real result — including `DO NOT COMPARE`, `INVESTIGATE` or `INSUFFICIENT EVIDENCE`.

## Implemented locally now

- `bell/live_store.py` writes atomic, credential-free JSON records under `bell/runtime/`.
- `bell/server.py` exposes `/api/published?slug=...` for the latest stored dossier.
- A live `/api/terminal` run persists its result automatically.
- `bell/publisher.py` can refresh one or more slugs from the Mac mini:

```bash
CMC_API_KEY="..." python3 bell/publisher.py gold tesla
```

- `cloudflare/` contains the D1 schema, Worker API and Static Assets configuration. It is deployed
  at `https://bell.dyplux.com/` with D1 and the publisher secret configured.
- `bell/launchd/com.dyplux.bell-publisher.plist.example` shows the Mac mini queue-poll schedule.
- The publisher can pull user-triggered jobs with `--pull-queue`; the installed launchd job polls
  the Worker every 15 minutes and publishes each leased slug back to `/internal/publish`.

- The Bell website prefers the published dossier and falls back to a one-off live request when
  an asset has never been published.

The runtime directory is ignored by Git. Only normalized receipts intended for publication belong
in the repository.

## Mac mini deployment

The Mac mini is the first production-shaped publisher:

1. Run Bell with `CMC_API_KEY` and a persistent `BELL_STORE_DIR`.
2. Put `CMC_API_KEY`, `BELL_PUBLICATION_URL`, `BELL_JOBS_URL` and `PUBLISHER_TOKEN` in a mode-600
   `~/.config/dyplux/bell.env` file on the Mac mini. Never put those values in the plist or Git.
3. Copy `bell/launchd/com.dyplux.bell-publisher.plist.example` into
   `~/Library/LaunchAgents/`, replace the `CHANGE_ME` paths, and schedule `bell/publisher.py`
   with `launchd`. The current machine has this job installed at 15-minute intervals.
4. The public Worker serves the Bell website and `/api/published`; the Mac mini only publishes
   normalized dossiers and does not need an inbound web server.
5. Use a small authenticated refresh endpoint or a pull queue; never allow arbitrary public
   requests to spend the CMC quota repeatedly.

Cloudflare Tunnel uses an outbound-only `cloudflared` connection from the origin, so the Mac mini
does not need a publicly routable IP. See the official [Cloudflare Tunnel documentation](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/).

## Cloudflare Free shape

Cloudflare can become the public edge without becoming the research worker:

- static frontend assets can be served at the edge;
- a Worker handles `/api/published`, freshness and deduplication;
- D1 stores indexed asset metadata, dossier status, publication timestamps and queue rows;
- R2 or the Mac mini stores larger raw/normalized receipts when needed;
- the Mac mini owns the CMC key and publishes normalized results through an authenticated Worker
  route.

The current official limits make this suitable for a hackathon and an early desk: Workers Free
allows 100,000 requests/day, five Cron Triggers and 50 subrequests per invocation; D1 Free
includes 5 million rows read/day, 100,000 rows written/day and 5 GB total storage. KV is useful
for hot cache entries but its Free limit is 1,000 writes/day, so it should not be the primary
append-only receipt store. See [Workers limits](https://developers.cloudflare.com/workers/platform/limits/),
[Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/),
and [D1 limits](https://developers.cloudflare.com/d1/platform/limits/).

## Freshness contract

Every published response must expose:

- `observed_at`: when CMC evidence was collected;
- `published_at`: when Bell made it public;
- `fresh_until` or `stale_after`: the product's freshness decision;
- `source`: cached publication, scheduled refresh or live fallback;
- `receipt`: a credential-free evidence path;
- `status`: published, stale, queued, map-only or insufficient evidence.

The UI must never label a cached dossier as a live quote. It should say `last observed`, show the
timestamp and explain when a refresh is queued. That is what makes the system useful to a normal
user and defensible to an institutional analyst.

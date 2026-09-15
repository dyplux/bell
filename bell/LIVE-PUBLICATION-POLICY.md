# Bell live publication policy

This is the operating contract for the public Bell publication edge. It keeps
CMC credentials server-side and makes staleness visible instead of presenting a
cached dossier as a current quote.

## Defaults

- Public HTTP cache: 30 seconds (`BELL_PUBLIC_MAX_AGE_SECONDS`).
- Dossier becomes stale after 3,600 seconds (`BELL_FRESHNESS_SECONDS`).
- Stale dossiers may still be served with `status: stale`, so the site remains
  useful during a temporary API outage.
- Publication records include `published_at`, `observed_at`, cache policy and
  the CMC request metadata. Raw responses and API keys are never published.
- On-demand `/api/rwa`, `/api/audit`, `/api/terminal` and `/api/session` calls
  are `no-store`; operators must rate-limit them at the edge or reverse proxy.

## Production gate

Before public launch, configure a reverse-proxy/API budget for the CMC plan,
monitor request credits and test stale/error states. The static site remains the
fallback. Bell does not promise that every CMC RWA map entry has a fresh dossier.


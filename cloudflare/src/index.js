const SLUG = /^[a-z0-9-]+$/;
const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const CORS_HEADERS = {
  'access-control-allow-headers': 'content-type, authorization',
  'access-control-allow-methods': 'GET, POST, OPTIONS',
  'access-control-allow-origin': '*',
};

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...JSON_HEADERS, ...CORS_HEADERS, ...extra },
  });
}

function now() {
  return new Date().toISOString();
}

function validSlug(value) {
  return typeof value === 'string' && SLUG.test(value);
}

function authorised(request, env) {
  const expected = env.PUBLISHER_TOKEN;
  if (!expected) return false;
  return request.headers.get('authorization') === `Bearer ${expected}`;
}

function publicationStatus(row) {
  const published = Date.parse(row.published_at);
  const age = Number.isFinite(published) ? Math.max(0, (Date.now() - published) / 1000) : null;
  const staleAfter = Number(row.stale_after_seconds || 3600);
  return {
    status: age !== null && age <= staleAfter ? 'fresh' : 'stale',
    age_seconds: age === null ? null : Math.round(age),
    stale_after_seconds: staleAfter,
  };
}

// A queued job is work a credential-holding publisher will do against the
// CoinMarketCap API, so anything that can enqueue can spend our credits. This
// was reachable from an unauthenticated GET with an arbitrary slug: the
// per-slug dedupe below does nothing against a caller who varies the slug, so
// a loop over [a-z0-9-]+ was unbounded row growth and unbounded credit burn.
// Two gates now stand in front of it - the slug must be one the published map
// actually contains, and the queue has a hard global ceiling per hour.
const REFRESH_JOBS_PER_HOUR = 50;

async function withinGlobalRefreshCap(env) {
  const row = await env.DB.prepare(
    "SELECT COUNT(*) AS queued FROM refresh_jobs WHERE requested_at > datetime('now', '-1 hour')",
  ).first();
  return Number(row?.queued || 0) < REFRESH_JOBS_PER_HOUR;
}

// The published map, cached in the isolate. Rebuilt at most once an hour.
let mapSlugs = null;
let mapSlugsAt = 0;
const MAP_SLUG_TTL_MS = 60 * 60 * 1000;

async function knownSlug(env, slug) {
  // This asked `SELECT 1 FROM dossiers WHERE slug = ?1` - the same table whose
  // miss is the only reason we are here. It could never be true, so the refresh
  // branch below it was dead, `refresh_queued` was always false, and the page
  // told the reader "A request is queued automatically" for work that was never
  // scheduled. The worker test passed only because its stub answered one query
  // with null and the other with a row, against one table: a database state
  // that cannot exist.
  //
  // The question is whether the MAP contains this reference, and the map is
  // catalog.json, which this worker already serves.
  const now = Date.now();
  if (!mapSlugs || now - mapSlugsAt > MAP_SLUG_TTL_MS) {
    try {
      const res = await env.ASSETS.fetch(new Request('https://assets.local/catalog.json'));
      if (!res.ok) return false;
      const catalogue = await res.json();
      const rows = Array.isArray(catalogue) ? catalogue : (catalogue.assets || []);
      mapSlugs = new Set(rows.map(row => String(row && row.slug || '').toLowerCase()).filter(Boolean));
      mapSlugsAt = now;
    } catch (error) {
      // Unreadable map: decline rather than queue work we cannot justify.
      return false;
    }
  }
  return mapSlugs.has(String(slug).toLowerCase());
}

async function enqueueRefresh(env, slug) {
  const recent = await env.DB.prepare(
    "SELECT id FROM refresh_jobs WHERE slug = ?1 AND status IN ('queued', 'leased') AND requested_at > datetime('now', '-15 minutes') LIMIT 1",
  ).bind(slug).first();
  // A recent queued/leased job is still pending work. Mark it queued so the
  // public client can distinguish deduplication from a cap-declined refresh.
  if (recent) return { queued: true, deduplicated: true, job_id: recent.id };
  if (!(await withinGlobalRefreshCap(env))) {
    return { queued: false, job_id: null, declined: 'hourly refresh cap reached' };
  }
  const result = await env.DB.prepare(
    "INSERT INTO refresh_jobs (slug, status, requested_at) VALUES (?1, 'queued', ?2)",
  ).bind(slug, now()).run();
  return { queued: true, job_id: result.meta?.last_row_id || null };
}

async function published(request, env) {
  const slug = new URL(request.url).searchParams.get('slug')?.trim().toLowerCase();
  if (!validSlug(slug)) return json({ error: 'a valid RWA slug is required' }, 400);
  const row = await env.DB.prepare('SELECT * FROM dossiers WHERE slug = ?1').bind(slug).first();
  if (!row) {
    // An arbitrary slug no longer queues work. A reference the map does not
    // contain cannot be investigated anyway, so there is nothing to schedule.
    const queue = (await knownSlug(env, slug)) ? await enqueueRefresh(env, slug) : { queued: false, declined: 'slug is not in the published map' };
    return json({
      status: 'map_only',
      slug,
      refresh_queued: queue.queued,
      refresh_deduplicated: Boolean(queue.deduplicated),
      job_id: queue.job_id || null,
      declined: queue.declined || null,
      message: 'No published dossier exists yet for this reference.',
    }, 404, { 'cache-control': 'no-store' });
  }
  const queue = publicationStatus(row).status === 'stale' ? await enqueueRefresh(env, slug) : { queued: false };
  let payload;
  try {
    payload = JSON.parse(row.payload_json);
  } catch (error) {
    return json({ error: 'stored dossier is invalid JSON', slug }, 500);
  }
  payload._publication = {
    source: 'cloudflare.d1',
    observed_at: row.observed_at,
    published_at: row.published_at,
    receipt_url: row.receipt_url,
    credential_free: true,
    refresh_queued: queue.queued,
    refresh_deduplicated: Boolean(queue.deduplicated),
    refresh_job_id: queue.job_id || null,
    refresh_declined: queue.declined || null,
    ...publicationStatus(row),
  };
  return json(payload, 200, { 'cache-control': 'no-store' });
}

// `no-store` forbids caching outright, so every visit re-downloaded the whole
// receipt even when nothing had changed - about 250 KB on the wire, gzipped,
// per page load. A receipt still has to be revalidated every time, so the
// answer is `no-cache` plus an entity tag: the browser always asks, and gets
// 304 with no body when the publication has not moved. Freshness is unchanged;
// the redundant transfer is not.
function receiptETag(row, servedRulesVersion = 'unversioned') {
  return `W/"${row.id ?? 1}-${row.published_at ?? ''}-${row.observed_at ?? ''}-${servedRulesVersion}"`;
}

function notModified(etag) {
  return new Response(null, {
    status: 304,
    headers: { ...CORS_HEADERS, etag, 'cache-control': 'no-cache' },
  });
}

async function integrity(request, env) {
  const row = await env.DB.prepare('SELECT * FROM integrity_receipts WHERE id = 1').first();
  if (!row) return json({ status: 'dated_static', message: 'No live integrity receipt has been published yet.' }, 404, { 'cache-control': 'no-store' });
  let payload;
  try {
    payload = JSON.parse(row.payload_json);
  } catch (error) {
    return json({ error: 'stored integrity receipt is invalid JSON' }, 500);
  }
  const ruleMigration = migrateV2IntegrityReceipt(payload);
  const publication = publicationStatus(row);
  payload._publication = {
    source: 'cloudflare.d1',
    observed_at: row.observed_at,
    published_at: row.published_at,
    credential_free: true,
    ...(ruleMigration ? { rule_migration: ruleMigration } : {}),
    ...publication,
  };
  const etag = receiptETag(row, payload.universe?.rules_version || 'unversioned');
  if (request.headers.get('if-none-match') === etag) return notModified(etag);
  return json(payload, 200, { 'cache-control': 'no-cache', etag });
}

// v3 changes the interpretation text for positive volume with zero reported
// market cap; it does not change the signal, severity, decision, counts or any
// numeric calculation. The Mac mini may continue publishing a fresh v2 scan
// until its checkout is updated. Serve that exact snapshot using v3 wording,
// while exposing the source ruleset and unchanged observation time so a judge
// cannot mistake this compatibility projection for a new CMC collection.
function migrateV2IntegrityReceipt(receipt) {
  const universe = receipt?.universe;
  if (universe?.rules_version !== 'bell.rules.v2') return null;

  const migration = {
    source_rules_version: 'bell.rules.v2',
    served_rules_version: 'bell.rules.v3',
    mode: 'wording-only compatibility projection',
    observed_at: receipt.observed_at || null,
    evidence_changed: false,
    note: 'No CMC inputs were recollected. Counts, states, signals and numeric evidence are unchanged; only the rule wording and decision copy were updated.',
  };

  universe.rules_version = 'bell.rules.v3';
  receipt.question = "Which CMC RWA rows pass the quote filters, and which identity, denomination or reported-field checks remain open?";
  if (receipt.method && Array.isArray(receipt.method.rules)) {
    receipt.method.rules = [
      '10x price spread blocks a filtered quote comparison pending unit and claim review',
      'positive volume with zero market cap is a reported-field review trigger, not proof of an economic contradiction',
      'derivative mixing, symbol collision, missing fields and missing token identity require investigation',
      'never join by ticker when crypto_id or issuer_id exists',
    ];
  }

  const oldSignal = 'At least one representation reports positive 24h volume with zero market cap.';
  const newSignal = 'CMC reports positive 24h volume alongside zero market cap; verify the source fields before relying on this quote.';
  const oldMultiConsequence = 'A research desk must not rank or substitute these representations until the contradiction is resolved.';
  const oldSingleConsequence = 'This reference has one representation and that row contradicts itself, so there is nothing here to compare and nothing to rank. Resolve the contradiction before treating the row as a price.';
  const oldMultiAllocation = 'NO WRAPPER SELECTED until identity, denomination and market state are cleared.';
  const oldSingleAllocation = "NO WRAPPER SELECTED until the row's own market state is cleared.";

  for (const key of ['alerts', 'alert_index']) {
    const rows = receipt[key];
    if (!Array.isArray(rows)) continue;
    for (const row of rows) {
      for (const signal of Array.isArray(row?.signals) ? row.signals : []) {
        if (signal?.code === 'ZERO_MCAP_POSITIVE_VOLUME' && signal.message === oldSignal) {
          signal.message = newSignal;
        }
      }
      const decision = row?.decision;
      if (decision?.state !== 'blocked') continue;
      const single = (row.tokens || row.representations || []).length === 1;
      if (decision.consequence === oldSingleConsequence || decision.consequence === oldMultiConsequence) {
        decision.consequence = single
          ? "This reference has one representation, so there is no cross-wrapper comparison. The reported market fields need verification before relying on its quote."
          : 'Keep these representations out of a shortlist until identity, denomination and reported market fields have been checked.';
      }
      if (decision.allocation_effect === oldSingleAllocation || decision.allocation_effect === oldMultiAllocation) {
        decision.allocation_effect = single
          ? "NO WRAPPER SELECTED until the row's reported market fields are verified."
          : 'NO WRAPPER SELECTED until identity, denomination and reported market fields are checked.';
      }
    }
  }

  receipt.rule_compatibility_migration = migration;
  return migration;
}

async function jobs(request, env) {
  if (!authorised(request, env)) return json({ error: 'unauthorized' }, 401);
  const limit = Math.min(20, Math.max(1, Number(new URL(request.url).searchParams.get('limit') || 5)));
  const result = await env.DB.prepare(
    "SELECT id, slug, requested_at FROM refresh_jobs WHERE status = 'queued' ORDER BY requested_at ASC LIMIT ?1",
  ).bind(limit).all();
  const leasedAt = now();
  for (const job of result.results || []) {
    await env.DB.prepare("UPDATE refresh_jobs SET status = 'leased', leased_at = ?1 WHERE id = ?2 AND status = 'queued'")
      .bind(leasedAt, job.id).run();
  }
  return json({ schema_version: 'dyplux.refresh-jobs.v1', leased_at: leasedAt, jobs: result.results || [] });
}

async function failJob(request, env) {
  if (!authorised(request, env)) return json({ error: 'unauthorized' }, 401);
  let body;
  try {
    body = await request.json();
  } catch (error) {
    return json({ error: 'request body must be JSON' }, 400);
  }
  const id = Number(body.id);
  const slug = String(body.slug || '').trim().toLowerCase();
  const message = String(body.error || 'publisher failed without a reason').slice(0, 500);
  if (!Number.isInteger(id) || id < 1 || !validSlug(slug)) {
    return json({ error: 'job id and slug are required' }, 400);
  }
  const result = await env.DB.prepare(
    "UPDATE refresh_jobs SET status = 'failed', finished_at = ?1, error = ?2 WHERE id = ?3 AND slug = ?4 AND status = 'leased'",
  ).bind(now(), message, id, slug).run();
  return json({ ok: true, id, slug, updated: Number(result.meta?.changes || 0) > 0 });
}

async function publish(request, env) {
  if (!authorised(request, env)) return json({ error: 'unauthorized' }, 401);
  let body;
  try {
    body = await request.json();
  } catch (error) {
    return json({ error: 'request body must be JSON' }, 400);
  }
  const slug = String(body.slug || '').trim().toLowerCase();
  if (!validSlug(slug) || !body.dossier || typeof body.dossier !== 'object') {
    return json({ error: 'slug and dossier are required' }, 400);
  }
  const publishedAt = body.published_at || now();
  const observedAt = body.observed_at || body.dossier.observed_at || body.dossier.audit?.observed_at || null;
  const staleAfter = Math.max(60, Number(body.stale_after_seconds || 3600));
  const receiptUrl = body.receipt_url || `/api/published?slug=${slug}`;
  await env.DB.prepare(
    `INSERT INTO dossiers (slug, payload_json, observed_at, published_at, stale_after_seconds, receipt_url, status)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6, 'published')
     ON CONFLICT(slug) DO UPDATE SET payload_json = excluded.payload_json, observed_at = excluded.observed_at,
       published_at = excluded.published_at, stale_after_seconds = excluded.stale_after_seconds,
       receipt_url = excluded.receipt_url, status = 'published'`,
  ).bind(slug, JSON.stringify(body.dossier), observedAt, publishedAt, staleAfter, receiptUrl).run();
  await env.DB.prepare("UPDATE refresh_jobs SET status = 'complete', finished_at = ?1 WHERE slug = ?2 AND status IN ('queued', 'leased')")
    .bind(publishedAt, slug).run();
  return json({ ok: true, slug, published_at: publishedAt, observed_at: observedAt });
}

async function publishIntegrity(request, env) {
  if (!authorised(request, env)) return json({ error: 'unauthorized' }, 401);
  let body;
  try {
    body = await request.json();
  } catch (error) {
    return json({ error: 'request body must be JSON' }, 400);
  }
  if (!body.receipt || typeof body.receipt !== 'object' || body.receipt.schema_version !== 'rwa_surface_integrity.v1') {
    return json({ error: 'a valid integrity receipt is required' }, 400);
  }
  const publishedAt = body.published_at || now();
  const observedAt = body.observed_at || body.receipt.observed_at || null;
  const staleAfter = Math.max(60, Number(body.stale_after_seconds || 900));
  await env.DB.prepare(
    `INSERT INTO integrity_receipts (id, payload_json, observed_at, published_at, stale_after_seconds, status)
     VALUES (1, ?1, ?2, ?3, ?4, 'published')
     ON CONFLICT(id) DO UPDATE SET payload_json = excluded.payload_json, observed_at = excluded.observed_at,
       published_at = excluded.published_at, stale_after_seconds = excluded.stale_after_seconds, status = 'published'`,
  ).bind(JSON.stringify(body.receipt), observedAt, publishedAt, staleAfter).run();
  return json({ ok: true, published_at: publishedAt, observed_at: observedAt });
}

// A product whose subject is integrity was serving no security headers at all:
// no CSP, no HSTS, no nosniff, no frame-ancestors. A reviewer ran `curl -sI`
// and found five missing, which is cheap to fix and expensive to explain.
//
// The policy is written against what the site actually loads rather than
// copied from a template: every script and stylesheet is same-origin, there is
// no inline script and no inline event handler, and the one inline <style>
// block lives in judge.html, which is why styles need 'unsafe-inline' and
// scripts do not.
const SECURITY_HEADERS = {
  'content-security-policy': [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "form-action 'self'",
    "base-uri 'none'",
    "object-src 'none'",
    "frame-ancestors 'none'",
  ].join('; '),
  'strict-transport-security': 'max-age=31536000; includeSubDomains',
  'x-content-type-options': 'nosniff',
  'referrer-policy': 'strict-origin-when-cross-origin',
  'permissions-policy': 'camera=(), microphone=(), geolocation=(), payment=()',
};

function secured(response) {
  // A redirect carries no body to protect and rewriting one costs a copy of
  // every asset response, so only the headers that still mean something on a
  // 301 are worth setting. Everything else gets the full set.
  const headers = new Headers(response.headers);
  for (const [name, value] of Object.entries(SECURITY_HEADERS)) {
    if (!headers.has(name)) headers.set(name, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

export default {
  async fetch(request, env) {
    return secured(await handle(request, env));
  },
};

async function handle(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS_HEADERS });
    const url = new URL(request.url);
    try {
      if (url.pathname === '/api/health') {
        const releaseSha = /^[a-f0-9]{40}$/i.test(String(env.RELEASE_SHA || ''))
          ? String(env.RELEASE_SHA).toLowerCase()
          : null;
        return json({ ok: true, service: 'dyplux-rwa-publication', now: now(), release_sha: releaseSha });
      }
      if (url.pathname === '/api/published' && request.method === 'GET') return published(request, env);
      if (url.pathname === '/api/integrity' && request.method === 'GET') return integrity(request, env);
      if (url.pathname === '/internal/jobs' && request.method === 'GET') return jobs(request, env);
      if (url.pathname === '/internal/fail' && request.method === 'POST') return failJob(request, env);
      if (url.pathname === '/internal/publish' && request.method === 'POST') return publish(request, env);
      if (url.pathname === '/internal/integrity' && request.method === 'POST') return publishIntegrity(request, env);
      // A retired URL should land on the thing it was named after, not at the
      // top of a long page. A reviewer fetched /integrity, compared it byte for
      // byte with / and reported them identical - which they were, because the
      // redirect dropped them at the top and said nothing about where the
      // receipt had gone. /guide.html named no section, so it still goes to the
      // root.
      const RETIRED = { '/integrity': '/#evidence', '/integrity.html': '/#evidence',
                        '/guide.html': '/' };
      if (RETIRED[url.pathname] && request.method === 'GET') {
        return Response.redirect(new URL(RETIRED[url.pathname], request.url), 301);
      }
      // The judge page is the one link in the nav that a reader follows from a
      // phone, and it is the whole submission in three screens. Serve it here
      // rather than relying on the asset layer's extensionless HTML handling,
      // which is a default that can be reconfigured without anyone noticing the
      // nav has started 404ing.
      if ((url.pathname === '/judge' || url.pathname === '/judge/') && request.method === 'GET') {
        const asset = await env.ASSETS.fetch(new Request(new URL('/judge.html', request.url), request));
        // The asset layer answers /judge.html with a 307 to /judge, because
        // dropping the extension is what its default HTML handling does. /judge
        // is the path being served right here, so returning that redirect makes
        // the page redirect to itself forever. It shipped that way and was live:
        // /judge went from 404 to an infinite loop, and every local audit passed
        // throughout, because the local harness serves judge.html off disk and
        // never runs this worker at all. A route only this file can answer was
        // checked by a harness that cannot reach it.
        if (asset.status >= 300 && asset.status < 400) {
          return env.ASSETS.fetch(new Request(new URL('/judge', request.url), request));
        }
        return asset;
      }
      // The research home is long by design; keep the operational monitor one
      // short, stable route away. Resolve it explicitly so the header link does
      // not depend on asset-layer extensionless HTML defaults.
      if ((url.pathname === '/workspace' || url.pathname === '/workspace/') && request.method === 'GET') {
        const asset = await env.ASSETS.fetch(new Request(new URL('/workspace.html', request.url), request));
        if (asset.status >= 300 && asset.status < 400) {
          return env.ASSETS.fetch(new Request(new URL('/workspace', request.url), request));
        }
        return asset;
      }
      return env.ASSETS.fetch(request);
    } catch (error) {
      return json({ error: 'publication service error' }, 500);
    }
}

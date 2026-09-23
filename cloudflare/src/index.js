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

async function knownSlug(env, slug) {
  const row = await env.DB.prepare('SELECT 1 AS hit FROM dossiers WHERE slug = ?1').bind(slug).first();
  return Boolean(row);
}

async function enqueueRefresh(env, slug) {
  const recent = await env.DB.prepare(
    "SELECT id FROM refresh_jobs WHERE slug = ?1 AND status IN ('queued', 'leased') AND requested_at > datetime('now', '-15 minutes') LIMIT 1",
  ).bind(slug).first();
  if (recent) return { queued: false, job_id: recent.id };
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
    ...publicationStatus(row),
  };
  return json(payload, 200, { 'cache-control': 'no-store' });
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
  const publication = publicationStatus(row);
  payload._publication = {
    source: 'cloudflare.d1',
    observed_at: row.observed_at,
    published_at: row.published_at,
    credential_free: true,
    ...publication,
  };
  return json(payload, 200, { 'cache-control': 'no-store' });
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

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS_HEADERS });
    const url = new URL(request.url);
    try {
      if (url.pathname === '/api/health') return json({ ok: true, service: 'dyplux-rwa-publication', now: now() });
      if (url.pathname === '/api/published' && request.method === 'GET') return published(request, env);
      if (url.pathname === '/api/integrity' && request.method === 'GET') return integrity(request, env);
      if (url.pathname === '/internal/jobs' && request.method === 'GET') return jobs(request, env);
      if (url.pathname === '/internal/fail' && request.method === 'POST') return failJob(request, env);
      if (url.pathname === '/internal/publish' && request.method === 'POST') return publish(request, env);
      if (url.pathname === '/internal/integrity' && request.method === 'POST') return publishIntegrity(request, env);
      if (['/integrity', '/integrity.html', '/guide.html'].includes(url.pathname) && request.method === 'GET') {
        return Response.redirect(new URL('/', request.url), 301);
      }
      return env.ASSETS.fetch(request);
    } catch (error) {
      return json({ error: 'publication service error' }, 500);
    }
  },
};

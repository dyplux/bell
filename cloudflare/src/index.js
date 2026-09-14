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

async function enqueueRefresh(env, slug) {
  const recent = await env.DB.prepare(
    "SELECT id FROM refresh_jobs WHERE slug = ?1 AND status IN ('queued', 'leased') AND requested_at > datetime('now', '-15 minutes') LIMIT 1",
  ).bind(slug).first();
  if (recent) return { queued: false, job_id: recent.id };
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
    const queue = await enqueueRefresh(env, slug);
    return json({
      status: 'map_only',
      slug,
      refresh_queued: queue.queued,
      job_id: queue.job_id,
      message: 'No published dossier exists yet; Bell will investigate this RWA server-side.',
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
  return json(payload, 200, { 'cache-control': 'public, max-age=30, stale-while-revalidate=300' });
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

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS_HEADERS });
    const url = new URL(request.url);
    try {
      if (url.pathname === '/api/health') return json({ ok: true, service: 'dyplux-rwa-publication', now: now() });
      if (url.pathname === '/api/published' && request.method === 'GET') return published(request, env);
      if (url.pathname === '/internal/jobs' && request.method === 'GET') return jobs(request, env);
      if (url.pathname === '/internal/publish' && request.method === 'POST') return publish(request, env);
      return env.ASSETS.fetch(request);
    } catch (error) {
      return json({ error: 'publication service error' }, 500);
    }
  },
};

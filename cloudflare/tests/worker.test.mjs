import assert from 'node:assert/strict';
import test from 'node:test';

import worker from '../src/index.js';

const assets = { fetch: async () => new Response('asset', { status: 200 }) };

// A map containing one reference. The refresh branch asks the published map
// whether a slug exists, so a test of that branch has to serve a map - the
// previous stubs answered two queries against ONE table with a miss and a hit,
// which is a database state that cannot occur, and the branch they covered was
// unreachable in production.
// One map, as in production. The worker caches it in the isolate, so handing
// different tests different maps made them depend on execution order - a
// fragility that would have hidden a real bug rather than revealed one.
const mapWith = (...slugs) => ({
  fetch: async request => (new URL(request.url).pathname === '/catalog.json'
    ? new Response(JSON.stringify({ assets: slugs.map(slug => ({ slug })) }), { status: 200 })
    : new Response('asset', { status: 200 })),
});

test('health endpoint is public and JSON', async () => {
  const response = await worker.fetch(new Request('https://example.test/api/health'), { ASSETS: assets });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).ok, true);
});

test('publisher endpoints require the publisher token', async () => {
  const response = await worker.fetch(new Request('https://example.test/internal/jobs'), { ASSETS: assets, PUBLISHER_TOKEN: 'secret' });
  assert.equal(response.status, 401);
});

test('failed refresh jobs require the publisher token and valid job data', async () => {
  const unauthorized = await worker.fetch(new Request('https://example.test/internal/fail', {
    method: 'POST',
    body: JSON.stringify({ id: 7, slug: 'marvell', error: 'upstream rejected the request' }),
  }), { ASSETS: assets, PUBLISHER_TOKEN: 'secret' });
  assert.equal(unauthorized.status, 401);
  const invalid = await worker.fetch(new Request('https://example.test/internal/fail', {
    method: 'POST',
    headers: { authorization: 'Bearer secret' },
    body: JSON.stringify({ id: 'bad', slug: 'marvell', error: 'upstream rejected the request' }),
  }), { ASSETS: assets, PUBLISHER_TOKEN: 'secret', DB: { prepare() { return { bind() { return { run: async () => ({ meta: { changes: 0 } }) }; } }; } } });
  assert.equal(invalid.status, 400);
});

test('unknown routes are delegated to static assets', async () => {
  const response = await worker.fetch(new Request('https://example.test/index.html'), { ASSETS: assets });
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'asset');
});

test('the root serves the single public product page', async () => {
  let requestedPath = null;
  const rootAssets = { fetch: async request => {
    requestedPath = new URL(request.url).pathname;
    return new Response('integrity page', { status: 200 });
  } };
  const response = await worker.fetch(new Request('https://example.test/'), { ASSETS: rootAssets });
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'integrity page');
  assert.equal(requestedPath, '/');
});

test('legacy page paths redirect to the single public product page', async () => {
  const response = await worker.fetch(new Request('https://example.test/guide.html'), { ASSETS: assets });
  assert.equal(response.status, 301);
  assert.equal(response.headers.get('location'), 'https://example.test/');
});

function fakeDb(row = null) {
  return {
    prepare(sql) {
      return {
        first: async () => sql.includes('integrity_receipts') ? row : null,
        bind() {
          return {
            first: async () => sql.includes('SELECT * FROM dossiers') ? row : null,
            run: async () => ({ meta: { last_row_id: 7 } }),
            all: async () => ({ results: [] }),
          };
        },
      };
    },
  };
}

test('a reference in the published map queues a refresh; an unknown one does not', async () => {
  // This test previously asserted that ANY slug queues a refresh. That was the
  // vulnerability written down as a requirement: a queued job is work a
  // credential-holding publisher performs against the CoinMarketCap API, so an
  // unauthenticated GET with an arbitrary slug could spend our credits without
  // bound. Only a reference the map actually contains may queue.
  const known = { ASSETS: mapWith('nvidia', 'silver'), DB: { prepare(sql) { return {
    bind() { return this; },
    async first() {
      if (/SELECT \* FROM dossiers/.test(sql)) return null;      // nothing published yet
      if (/status IN \('queued', 'leased'\)/.test(sql)) return null;
      if (/COUNT\(\*\)/.test(sql)) return { queued: 0 };
      return null;
    },
    async run() { return { meta: { last_row_id: 7 } }; },
  }; } } };
  const queued = await worker.fetch(new Request('https://example.test/api/published?slug=nvidia'), known);
  const queuedBody = await queued.json();
  assert.equal(queued.status, 404);
  assert.equal(queuedBody.status, 'map_only');
  assert.equal(queuedBody.refresh_queued, true);

  const inserts = [];
  const unknown = { ASSETS: assets, DB: { prepare(sql) { return {
    bind() { return this; },
    async first() {
      if (/COUNT\(\*\)/.test(sql)) return { queued: 0 };
      return null;                                               // not published, not in the map
    },
    async run() { inserts.push(sql); return { meta: { last_row_id: 1 } }; },
  }; } } };
  const declined = await worker.fetch(
    new Request('https://example.test/api/published?slug=not-a-real-reference'), unknown);
  const declinedBody = await declined.json();
  assert.equal(declinedBody.refresh_queued, false);
  assert.equal(declinedBody.declined, 'slug is not in the published map');
  assert.equal(inserts.length, 0, 'an unknown slug must not insert a refresh job');
});

test('published dossier returns freshness metadata', async () => {
  const row = {
    payload_json: JSON.stringify({ audit: { conclusion: 'investigate' } }),
    observed_at: '2026-09-14T12:00:00Z',
    published_at: new Date().toISOString(),
    stale_after_seconds: 3600,
    receipt_url: 'receipts/nvidia.json',
  };
  const response = await worker.fetch(new Request('https://example.test/api/published?slug=nvidia'), { ASSETS: assets, DB: fakeDb(row) });
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.audit.conclusion, 'investigate');
  assert.equal(body._publication.status, 'fresh');
  assert.equal(body._publication.receipt_url, 'receipts/nvidia.json');
});

test('integrity endpoint returns a published receipt with freshness metadata', async () => {
  const row = {
    payload_json: JSON.stringify({ schema_version: 'rwa_surface_integrity.v1', universe: { states: {} } }),
    observed_at: '2026-09-15T12:00:00Z',
    published_at: new Date().toISOString(),
    stale_after_seconds: 900,
  };
  const db = {
    prepare(sql) {
      return {
        first: async () => sql.includes('integrity_receipts') ? row : null,
        bind() {
          return {
            first: async () => sql.includes('integrity_receipts') ? row : null,
            run: async () => ({ meta: {} }),
            all: async () => ({ results: [] }),
          };
        },
      };
    },
  };
  const response = await worker.fetch(new Request('https://example.test/api/integrity'), { ASSETS: assets, DB: db });
  const body = await response.json();
  assert.equal(response.status, 200);
  // The guarantee is "never serve a stale receipt without asking", not the
  // literal token `no-store`. `no-cache` keeps the guarantee and allows a 304,
  // which stops every page load re-downloading an unchanged receipt.
  assert.equal(response.headers.get('cache-control'), 'no-cache');
  assert.ok(response.headers.get('etag'), 'the receipt must be revalidatable');
  assert.equal(body.schema_version, 'rwa_surface_integrity.v1');
  assert.equal(body._publication.status, 'fresh');
});

test('integrity publication requires the publisher token', async () => {
  const response = await worker.fetch(new Request('https://example.test/internal/integrity', { method: 'POST', body: JSON.stringify({}) }), { ASSETS: assets, PUBLISHER_TOKEN: 'secret' });
  assert.equal(response.status, 401);
});


test('the refresh queue has a hard hourly ceiling', async () => {
  const inserts = [];
  // The slug must be in the map, or it is declined before the cap is reached -
  // the cap is what this test is about.
  const env = { ASSETS: mapWith('nvidia', 'silver'), DB: { prepare(sql) { return {
    bind() { return this; },
    async first() {
      if (/SELECT \* FROM dossiers/.test(sql)) return null;
      if (/status IN \('queued', 'leased'\)/.test(sql)) return null;
      if (/COUNT\(\*\)/.test(sql)) return { queued: 50 };        // cap already reached
      return null;
    },
    async run() { inserts.push(sql); return { meta: { last_row_id: 1 } }; },
  }; } } };
  const response = await worker.fetch(
    new Request('https://example.test/api/published?slug=silver'), env);
  const body = await response.json();
  assert.equal(body.refresh_queued, false);
  assert.equal(body.declined, 'hourly refresh cap reached');
  assert.equal(inserts.length, 0, 'no insert once the hourly cap is reached');
});

test('the receipt revalidates instead of re-downloading unchanged', async () => {
  // `no-store` forbade caching outright, so every page load pulled the whole
  // receipt again - about 250 KB gzipped - even when the publication had not
  // moved. A receipt must still be revalidated every time, so the answer is
  // `no-cache` plus an entity tag, not a cache lifetime.
  const row = {
    id: 1,
    payload_json: JSON.stringify({ universe: { states: {} } }),
    observed_at: '2026-09-23T20:00:00Z',
    published_at: '2026-09-23T20:05:00Z',
    stale_after_seconds: 3600,
  };
  const env = { ASSETS: assets, DB: { prepare() { return { bind() { return this; }, async first() { return row; } }; } } };

  const first = await worker.fetch(new Request('https://example.test/api/integrity'), env);
  assert.equal(first.status, 200);
  const etag = first.headers.get('etag');
  assert.ok(etag, 'the receipt must carry an entity tag');
  assert.equal(first.headers.get('cache-control'), 'no-cache');

  const second = await worker.fetch(
    new Request('https://example.test/api/integrity', { headers: { 'if-none-match': etag } }), env);
  assert.equal(second.status, 304, 'an unchanged publication must answer 304');
  assert.equal(await second.text(), '', '304 must carry no body');

  // A new publication must invalidate the tag, or a reader would be pinned to
  // a stale receipt - the opposite of what this product promises.
  row.published_at = '2026-09-23T21:00:00Z';
  const third = await worker.fetch(
    new Request('https://example.test/api/integrity', { headers: { 'if-none-match': etag } }), env);
  assert.equal(third.status, 200, 'a republished receipt must not answer 304');
  assert.notEqual(third.headers.get('etag'), etag);
});

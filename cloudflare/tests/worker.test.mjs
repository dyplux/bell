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
  const releaseSha = 'a'.repeat(40);
  const response = await worker.fetch(new Request('https://example.test/api/health'), {
    ASSETS: assets,
    RELEASE_SHA: releaseSha,
  });
  assert.equal(response.status, 200);
  const health = await response.json();
  assert.equal(health.ok, true);
  assert.equal(health.release_sha, releaseSha);
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

test('a stale dossier reports an existing refresh as queued and deduplicated', async () => {
  const row = {
    id: 1,
    payload_json: JSON.stringify({ audit: { conclusion: 'investigate' } }),
    observed_at: '2026-09-14T12:00:00Z',
    published_at: new Date(Date.now() - 4_000_000).toISOString(),
    stale_after_seconds: 3600,
    receipt_url: 'receipts/nvidia.json',
  };
  const env = { ASSETS: assets, DB: { prepare(sql) { return {
    bind() { return this; },
    async first() {
      if (/SELECT \* FROM dossiers/.test(sql)) return row;
      if (/status IN \('queued', 'leased'\)/.test(sql)) return { id: 42 };
      throw new Error(`unexpected query: ${sql}`);
    },
  }; } } };
  const response = await worker.fetch(
    new Request('https://example.test/api/published?slug=nvidia'), env);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body._publication.status, 'stale');
  assert.equal(body._publication.refresh_queued, true);
  assert.equal(body._publication.refresh_deduplicated, true);
  assert.equal(body._publication.refresh_job_id, 42);
  assert.equal(body._publication.refresh_declined, null);
});

test('a stale dossier exposes why its refresh was not queued', async () => {
  const row = {
    id: 1,
    payload_json: JSON.stringify({ audit: { conclusion: 'investigate' } }),
    observed_at: '2026-09-14T12:00:00Z',
    published_at: new Date(Date.now() - 4_000_000).toISOString(),
    stale_after_seconds: 3600,
    receipt_url: 'receipts/nvidia.json',
  };
  const env = { ASSETS: assets, DB: { prepare(sql) { return {
    bind() { return this; },
    async first() {
      if (/SELECT \* FROM dossiers/.test(sql)) return row;
      if (/status IN \('queued', 'leased'\)/.test(sql)) return null;
      if (/COUNT\(\*\)/.test(sql)) return { queued: 50 };
      throw new Error(`unexpected query: ${sql}`);
    },
  }; } } };
  const response = await worker.fetch(
    new Request('https://example.test/api/published?slug=nvidia'), env);
  const body = await response.json();
  assert.equal(body._publication.status, 'stale');
  assert.equal(body._publication.refresh_queued, false);
  assert.equal(body._publication.refresh_declined, 'hourly refresh cap reached');
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

test('integrity endpoint projects the v2 receipt with transparent v3 wording only', async () => {
  const storedReceipt = {
    schema_version: 'rwa_surface_integrity.v1',
    observed_at: '2026-09-29T16:59:08Z',
    question: "Can CMC's RWA surfaces be joined into a trustworthy comparison without resolving identity, unit and market-data contradictions?",
    method: { rules: [
      '10x price spread is a critical denomination break',
      'positive volume with zero market cap is a critical market contradiction',
    ] },
    universe: {
      rules_version: 'bell.rules.v2',
      tokenised_references_scanned: 793,
      tokens_scanned: 1449,
      states: { do_not_compare: 38, investigate: 97, no_flags: 658 },
    },
    alerts: [{
      tokens: [{ crypto_id: 1 }, { crypto_id: 2 }],
      signals: [{ code: 'ZERO_MCAP_POSITIVE_VOLUME', severity: 'critical', message: 'At least one representation reports positive 24h volume with zero market cap.' }],
      decision: {
        state: 'blocked',
        consequence: 'A research desk must not rank or substitute these representations until the contradiction is resolved.',
        allocation_effect: 'NO WRAPPER SELECTED until identity, denomination and market state are cleared.',
      },
    }],
  };
  const originalJson = JSON.stringify(storedReceipt);
  const row = {
    id: 1,
    payload_json: originalJson,
    observed_at: storedReceipt.observed_at,
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
  const response = await worker.fetch(new Request('https://example.test/api/integrity', {
    headers: { 'if-none-match': `W/"1-${row.published_at}-${row.observed_at}"` },
  }), { ASSETS: assets, DB: db });
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.universe.rules_version, 'bell.rules.v3');
  assert.equal(body.universe.tokenised_references_scanned, 793);
  assert.deepEqual(body.universe.states, storedReceipt.universe.states);
  assert.equal(body.alerts[0].signals[0].message, 'CMC reports positive 24h volume alongside zero market cap; verify the source fields before relying on this quote.');
  assert.equal(body.alerts[0].decision.consequence, 'Keep these representations out of a shortlist until identity, denomination and reported market fields have been checked.');
  assert.equal(body.rule_compatibility_migration.source_rules_version, 'bell.rules.v2');
  assert.equal(body.rule_compatibility_migration.evidence_changed, false);
  assert.equal(body._publication.rule_migration.served_rules_version, 'bell.rules.v3');
  assert.equal(body._publication.observed_at, storedReceipt.observed_at);
  assert.notEqual(response.headers.get('etag'), `W/"1-${row.published_at}-${row.observed_at}"`,
    'the served rules version must invalidate a pre-migration cache entry');
  assert.equal(row.payload_json, originalJson, 'the stored v2 receipt remains immutable');
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

test('the judge page is served at /judge, not left to a default', async () => {
  // /judge is the one nav link a reader follows from a phone, and it is the
  // whole submission in three screens. Serving it depended on the asset
  // layer's extensionless HTML handling, which is a default someone can
  // reconfigure without noticing the nav has started 404ing.
  const asked = [];
  const env = {
    ASSETS: {
      fetch: async request => {
        asked.push(new URL(request.url).pathname);
        return new Response('<!doctype html>judge', { status: 200 });
      },
    },
  };
  for (const pathname of ['/judge', '/judge/']) {
    asked.length = 0;
    const response = await worker.fetch(new Request(`https://bell.dyplux.com${pathname}`), env, {});
    assert.equal(response.status, 200, `${pathname} did not return the page`);
    assert.deepEqual(asked, ['/judge.html'],
      `${pathname} did not resolve to judge.html`);
  }

  // A POST is not a page request and must not be answered with one.
  asked.length = 0;
  await worker.fetch(new Request('https://bell.dyplux.com/judge', { method: 'POST' }), env, {});
  assert.notDeepEqual(asked, ['/judge.html'], 'a POST was served the judge page');
});

test('/judge does not redirect to itself when the asset layer drops the extension', async () => {
  // This shipped and was live. The asset layer answers /judge.html with a 307
  // to /judge, because dropping the extension is what its default HTML
  // handling does, and the worker returned that redirect from the very path it
  // names. /judge went from 404 to an infinite loop.
  //
  // The test above did not catch it because its ASSETS double answers every
  // request with 200. The double was more cooperative than the thing it stands
  // for, so the suite was green about a route that could not load. This one
  // makes the double behave like the platform.
  const asked = [];
  const env = {
    ASSETS: {
      fetch: async request => {
        const { pathname } = new URL(request.url);
        asked.push(pathname);
        if (pathname === '/judge.html') {
          return new Response(null, { status: 307, headers: { location: '/judge' } });
        }
        return new Response('<!doctype html>judge', { status: 200 });
      },
    },
  };

  for (const pathname of ['/judge', '/judge/']) {
    asked.length = 0;
    const response = await worker.fetch(new Request(`https://bell.dyplux.com${pathname}`), env, {});
    assert.equal(response.status, 200,
      `${pathname} answered ${response.status} instead of the page`);
    assert.equal(await response.text(), '<!doctype html>judge');
    assert.ok(asked.includes('/judge'),
      'the worker never asked for the path the asset layer actually serves');
  }

  // The property that matters, stated directly: whatever the asset layer does,
  // /judge may never answer with a redirect back to /judge.
  const response = await worker.fetch(new Request('https://bell.dyplux.com/judge'), env, {});
  if (response.status >= 300 && response.status < 400) {
    const target = new URL(response.headers.get('location'), 'https://bell.dyplux.com');
    assert.notEqual(target.pathname, '/judge', '/judge redirects to itself');
  }
});

test('the workspace route resolves its static page with or without extension redirects', async () => {
  const asked = [];
  const env = {
    ASSETS: {
      fetch: async request => {
        const { pathname } = new URL(request.url);
        asked.push(pathname);
        if (pathname === '/workspace.html') {
          return new Response(null, { status: 307, headers: { location: '/workspace' } });
        }
        return new Response('<!doctype html>workspace', { status: 200 });
      },
    },
  };
  for (const pathname of ['/workspace', '/workspace/']) {
    asked.length = 0;
    const response = await worker.fetch(new Request(`https://bell.dyplux.com${pathname}`), env, {});
    assert.equal(response.status, 200, `${pathname} did not return the workspace`);
    assert.equal(await response.text(), '<!doctype html>workspace');
    assert.ok(asked.includes('/workspace.html'));
    assert.ok(asked.includes('/workspace'));
  }
});

test('a retired URL lands on the section it was named after', async () => {
  // /integrity redirected to the top of the root page, so a reviewer who
  // fetched it and compared it byte for byte with / reported the two
  // identical, and concluded the receipt page did not exist. It does; the
  // redirect just never said where it went.
  const assets = { fetch: async () => new Response('asset', { status: 200 }) };
  for (const [from, to] of [['/integrity', '/#evidence'],
                            ['/integrity.html', '/#evidence'],
                            ['/guide.html', '/']]) {
    const response = await worker.fetch(new Request(`https://bell.dyplux.com${from}`), assetsEnv(assets), {});
    assert.equal(response.status, 301, `${from} did not redirect`);
    assert.equal(new URL(response.headers.get('location')).pathname
                 + new URL(response.headers.get('location')).hash,
                 to, `${from} went somewhere else`);
  }
});

function assetsEnv(assets) { return { ASSETS: assets }; }

test('every response carries the security headers the product asks of others', async () => {
  // A reviewer ran `curl -sI` against the live site and found no CSP, no HSTS,
  // no nosniff, no frame-ancestors and no referrer policy. Five missing
  // headers on a product whose subject is integrity.
  const assets = { fetch: async () => new Response('asset', { status: 200 }) };
  const required = ['content-security-policy', 'strict-transport-security',
                    'x-content-type-options', 'referrer-policy', 'permissions-policy'];
  for (const path of ['/', '/judge', '/api/health', '/integrity', '/not-a-route']) {
    const response = await worker.fetch(new Request(`https://bell.dyplux.com${path}`),
                                        { ASSETS: assets }, {});
    for (const header of required) {
      assert.ok(response.headers.get(header), `${path} carries no ${header}`);
    }
  }
});

test('the policy allows what the site loads and nothing it does not', async () => {
  // Written against the pages rather than copied from a template: no inline
  // script and no inline handler anywhere, one inline <style> in judge.html.
  // So styles need 'unsafe-inline' and scripts must not have it - a CSP that
  // permits inline script is a CSP that permits the injection it exists to
  // stop.
  const fs = await import('node:fs');
  const path = await import('node:path');
  const url = await import('node:url');
  const here = path.dirname(url.fileURLToPath(import.meta.url));
  const site = path.resolve(here, '../../bell/site');

  const assets = { fetch: async () => new Response('asset', { status: 200 }) };
  const response = await worker.fetch(new Request('https://bell.dyplux.com/'), { ASSETS: assets }, {});
  const policy = response.headers.get('content-security-policy');
  assert.match(policy, /script-src 'self'(;|$)/, "script-src must not allow inline");
  assert.doesNotMatch(policy, /script-src[^;]*unsafe-inline/);
  assert.match(policy, /frame-ancestors 'none'/);
  assert.match(policy, /object-src 'none'/);

  for (const page of ['index.html', 'judge.html', 'workspace.html']) {
    const html = fs.readFileSync(path.join(site, page), 'utf8');
    assert.doesNotMatch(html, /<script(?![^>]*\bsrc=)[^>]*>/,
      `${page} gained an inline script, which the policy above forbids`);
    assert.doesNotMatch(html, /\son[a-z]+\s*=\s*"/,
      `${page} gained an inline event handler, which the policy above forbids`);
  }
});

test('the asset layer states the same policy the worker does', async () => {
  // The Worker sets security headers on everything it answers, and a reviewer
  // still found none of them on the live root: / is served straight off the
  // asset layer and never reaches the Worker. Only run_worker_first paths do.
  // So _headers has to carry the same policy, and this is what stops the two
  // copies drifting.
  const fs = await import('node:fs');
  const path = await import('node:path');
  const url = await import('node:url');
  const here = path.dirname(url.fileURLToPath(import.meta.url));
  const headersFile = fs.readFileSync(
    path.resolve(here, '../../bell/site/_headers'), 'utf8');

  const assets = { fetch: async () => new Response('asset', { status: 200 }) };
  const response = await worker.fetch(new Request('https://bell.dyplux.com/judge'),
                                      { ASSETS: assets }, {});
  for (const header of ['content-security-policy', 'strict-transport-security',
                        'x-content-type-options', 'referrer-policy', 'permissions-policy']) {
    const value = response.headers.get(header);
    assert.ok(value, `the worker no longer sets ${header}`);
    const stated = headersFile.split('\n')
      .map(line => line.trim())
      .find(line => line.toLowerCase().startsWith(`${header}:`));
    assert.ok(stated, `_headers does not state ${header}, so the root will not carry it`);
    assert.equal(stated.slice(header.length + 1).trim(), value,
      `_headers and the worker disagree about ${header}`);
  }
  assert.match(headersFile, /^\/\*$/m, '_headers no longer applies to every path');
});

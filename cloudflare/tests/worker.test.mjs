import assert from 'node:assert/strict';
import test from 'node:test';

import worker from '../src/index.js';

const assets = { fetch: async () => new Response('asset', { status: 200 }) };

test('health endpoint is public and JSON', async () => {
  const response = await worker.fetch(new Request('https://example.test/api/health'), { ASSETS: assets });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).ok, true);
});

test('publisher endpoints require the publisher token', async () => {
  const response = await worker.fetch(new Request('https://example.test/internal/jobs'), { ASSETS: assets, PUBLISHER_TOKEN: 'secret' });
  assert.equal(response.status, 401);
});

test('unknown routes are delegated to static assets', async () => {
  const response = await worker.fetch(new Request('https://example.test/index.html'), { ASSETS: assets });
  assert.equal(response.status, 200);
  assert.equal(await response.text(), 'asset');
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

test('missing dossier is explicit and queues a refresh', async () => {
  const response = await worker.fetch(new Request('https://example.test/api/published?slug=nvidia'), { ASSETS: assets, DB: fakeDb() });
  const body = await response.json();
  assert.equal(response.status, 404);
  assert.equal(body.status, 'map_only');
  assert.equal(body.refresh_queued, true);
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
  assert.equal(body.schema_version, 'rwa_surface_integrity.v1');
  assert.equal(body._publication.status, 'fresh');
});

test('integrity publication requires the publisher token', async () => {
  const response = await worker.fetch(new Request('https://example.test/internal/integrity', { method: 'POST', body: JSON.stringify({}) }), { ASSETS: assets, PUBLISHER_TOKEN: 'secret' });
  assert.equal(response.status, 401);
});

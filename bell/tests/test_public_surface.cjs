const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve(__dirname, '../site');
const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
const explorer = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
const visualOverrides = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
const catalogue = JSON.parse(fs.readFileSync(path.join(site, 'catalog.json'), 'utf8'));

test('public page exposes the single-URL RWA discovery and evidence path', () => {
  assert.match(page, /id="explorer"/);
  assert.match(page, /href="#explorer">Explore RWA/);
  assert.match(page, /src="explorer\.js(?:\?v=[^"]+)?"/);
  assert.match(page, /href="\/api\/integrity"/);
  assert.match(page, /separate from live receipt/);
  assert.match(page, /id="explorer-map-freshness"/);
  assert.match(page, /data-filter="no_flags">FACTS OPEN<\/button>/);
});

test('public page carries a shareable social preview', () => {
  assert.match(page, /property="og:title"/);
  assert.match(page, /property="og:description"/);
  assert.match(page, /property="og:url" content="https:\/\/bell\.dyplux\.com\/"/);
  assert.match(page, /property="og:image" content="https:\/\/bell\.dyplux\.com\/assets\/og-card\.png"/);
  assert.match(page, /name="twitter:card" content="summary_large_image"/);
});

test('explorer keeps all four RWA routes and the freshness boundary visible', () => {
  for (const label of ['DO NOT SHORTLIST', 'INVESTIGATE', 'SINGLE REPRESENTATION', 'REFERENCE ONLY', 'DOSSIER PENDING']) {
    assert.match(explorer, new RegExp(label.replaceAll(' ', '\\s+')));
  }
  assert.match(explorer, /publication\.status/);
  assert.match(explorer, /catalog\.json/);
  assert.match(explorer, /observed \$\{mapDate\(/);
  assert.match(explorer, /separate from live receipt/);
  assert.match(explorer, /dex_covered_token_count/);
  assert.match(explorer, /market_pair_count/);
  assert.match(explorer, /does not infer backing/);
});

test('hero receipt label preserves the live freshness state', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /LIVE RECEIPT.*String\(status\)\.toUpperCase\(\)/s);
  assert.match(integrity, /publication\?\.source === 'dated_static'/);
  const index = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  assert.match(index, /id="hero-receipt-trail"/);
  assert.match(integrity, /RECEIPT TRAIL/);
  assert.match(integrity, /hero-receipt-link/);
  assert.match(integrity, /liveObservation = receipt\?\.observed_at/);
  assert.match(integrity, /storedObservations\.at\(-1\)\?\.observed_at/);
});

test('first case exposes the population concentration lens from the receipt', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(page, /id="hero-population-signal"/);
  assert.match(integrity, /hero-population-headline/);
  assert.match(integrity, /five issuer labels/);
  assert.match(integrity, /not a legal issuer or backing measure/);
});

test('case results can be shared as stable single-URL deep links', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /searchParams\.set\('reference', query\)/);
  assert.match(integrity, /data-copy-case/);
  assert.match(integrity, /searchParams\.set\('reference', String\(item\.rwa_id\)\)/);
  assert.match(integrity, /const exactMatches = normalizedQuery/);
  assert.match(integrity, /const matchLabel = exact/);
  assert.match(integrity, /heroSearchInput\.value = alert\.name/);
  assert.match(integrity, /bell\.case-receipt\.v1/);
  assert.match(integrity, /Download case JSON/);
  assert.match(integrity, /source_hashes: receipt\?\.source_hashes/);
});

test('search result exposes the observed quote endpoints before the evidence table', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const visual = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(integrity, /function observedQuoteEndpoints/);
  assert.match(integrity, /OBSERVED QUOTE BAND/);
  assert.match(integrity, /relative to the observed median/);
  assert.match(integrity, /not a ranking, discount, backing, liquidity or executable spread/);
  assert.match(integrity, /SWIPE FOR QUOTE/);
  assert.match(visual, /\.quote-band-table/);
});

test('flagged Gold and Tesla cases expose dated temporal proof without turning it into a ranking', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const visual = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(integrity, /PUBLISHED TEMPORAL CHECK/);
  assert.match(integrity, /REPEAT-WINDOW CHECK/);
  assert.match(integrity, /gold-live-2026-09-13\.json/);
  assert.match(integrity, /gold-live-2026-09-17\.json/);
  assert.match(integrity, /tesla-live-2026-09-13\.json/);
  assert.match(integrity, /tesla-live-2026-09-17\.json/);
  assert.match(integrity, /overlap by/);
  assert.match(integrity, /not independent validation or a trend claim/);
  assert.match(integrity, /not a ranking, fair-value, liquidity or execution test/);
  assert.match(visual, /\.temporal-evidence/);
  assert.equal(fs.existsSync(path.join(site, 'proof/gold-live-2026-09-13.json')), true);
  assert.equal(fs.existsSync(path.join(site, 'proof/tesla-live-2026-09-13.json')), true);
  assert.equal(fs.existsSync(path.join(site, 'proof/gold-live-2026-09-17.json')), true);
  assert.equal(fs.existsSync(path.join(site, 'proof/gold-live-2026-09-17.payload.json')), true);
  assert.equal(fs.existsSync(path.join(site, 'proof/tesla-live-2026-09-17.json')), true);
  assert.equal(fs.existsSync(path.join(site, 'proof/tesla-live-2026-09-17.payload.json')), true);
});

test('hero search lands on the result it just generated', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /const target = window\.matchMedia/);
  assert.match(integrity, /target\?\.scrollIntoView/);
  assert.match(integrity, /matchMedia\('\(max-width: 900px\)'\)/);
  assert.match(integrity, /byId\('decision'\)/);
});

test('a query outside the live receipt is routed to the complete RWA map', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const explorer = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  assert.match(integrity, /No live case found for/);
  assert.match(integrity, /data-open-map-query/);
  assert.match(integrity, /mapForm\.requestSubmit\(\)/);
  assert.match(integrity, /renderAlerts\(\);\s*renderSearchResult\(\);\s*renderSignals\(\)/);
  assert.match(integrity, /searchParams\.set\('map_reference', mapInput\.value\)/);
  assert.match(explorer, /searchParams\.get\('map_reference'\)/);
  assert.match(explorer, /form\.requestSubmit\(\)/);
});

test('mobile navigation keeps every primary destination visible', () => {
  assert.match(visualOverrides, /\.topbar nav\{overflow-x:visible;gap:7px\}/);
  assert.match(visualOverrides, /\.topbar nav a\{font-size:10px/);
});

test('mobile evidence text wraps instead of hiding the source line', () => {
  assert.match(visualOverrides, /\.hero-signal-list small\{grid-column:2;white-space:normal;overflow:visible/);
});

test('public decision vocabulary stays canonical', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /return 'INVESTIGATE';/);
  assert.doesNotMatch(integrity, /INVESTIGATE BEFORE SHORTLIST|FACTUAL COMPARISON OPEN/);
});

test('public catalogue is a complete credential-free map snapshot', () => {
  assert.equal(catalogue.schema_version, 'bell.catalog.v1');
  assert.match(catalogue.observed_at, /^2026-09-22T/);
  assert.equal(catalogue.total_size, catalogue.assets.length);
  assert.ok(catalogue.total_size >= 7000);
  assert.ok(catalogue.assets.some(asset => asset.slug === 'gold' && asset.has_tokens));
  assert.ok(catalogue.assets.some(asset => asset.asset_type === 'stock'));
  assert.ok(catalogue.assets.some(asset => asset.asset_type === 'etf'));
  assert.ok(catalogue.assets.some(asset => asset.asset_type === 'commodity'));
  assert.ok(catalogue.assets.every(asset => asset.slug && asset.rwa_id));
});

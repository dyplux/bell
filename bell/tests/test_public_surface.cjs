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

test('public release includes a credential-free executable rule specification', () => {
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_rule_boundaries.py'), 'utf8');
  assert.match(verifier, /bell\.rule_boundary_verifier\.v1/);
  assert.match(verifier, /9\.99x stays a warning/);
  assert.match(verifier, /1\.99x stays below the dispersion rule/);
  assert.match(verifier, /2x is an inclusive investigation warning/);
  assert.match(verifier, /10x is an inclusive critical stop/);
  assert.match(verifier, /missing and zero prices do not fabricate a ratio/);
  assert.match(verifier, /resolved crypto identity exposes chain and contract/);
  const receipt = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../site/proof/rule-boundary-verifier-2026-09-22.json'), 'utf8'));
  assert.equal(receipt.schema_version, 'bell.rule_boundary_verifier.v1');
  assert.equal(receipt.checks.every(check => check.pass), true);
});

test('public release names the observed threshold population and inclusivity', () => {
  const source = fs.readFileSync(path.resolve(__dirname, '../rwa_integrity.py'), 'utf8');
  assert.match(source, /def rule_calibration/);
  assert.match(source, /references_with_two_positive_prices/);
  assert.match(source, /price_denomination_break.*inclusive/s);
  const integrity = fs.readFileSync(path.resolve(__dirname, '../site/integrity.js'), 'utf8');
  assert.match(integrity, /receipt\.rule_calibration/);
  assert.match(integrity, /references_with_insufficient_positive_prices/);
});

test('threshold language stays distinct from the observed case ratio', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const capital = fs.readFileSync(path.join(site, 'capital-impact.js'), 'utf8');
  assert.match(page, /≥10× BLOCK/);
  assert.match(page, /the observed value can be higher/);
  assert.match(integrity, /formatNumber\(primaryEvidence\.max_min_ratio\).*observed price spread/);
  assert.match(integrity, /observed quote ratio ≥10× block floor/);
  assert.match(capital, /quote range/);
  assert.match(capital, /not a discount or a proven saving/);
});

test('public page carries a shareable social preview', () => {
  assert.match(page, /property="og:title"/);
  assert.match(page, /property="og:description"/);
  assert.match(page, /property="og:url" content="https:\/\/bell\.dyplux\.com\/"/);
  assert.match(page, /property="og:image" content="https:\/\/bell\.dyplux\.com\/assets\/og-card\.png"/);
  assert.match(page, /name="twitter:card" content="summary_large_image"/);
});

test('public documentation points to receipts that exist in the export', () => {
  const judge = fs.readFileSync(path.resolve(__dirname, '../JUDGE.md'), 'utf8');
  assert.match(judge, /site\/proof\/gold-live-2026-09-17\.json/);
  assert.match(judge, /site\/proof\/tesla-live-2026-09-17\.json/);
  assert.doesNotMatch(judge, /docs\/proof\/(gold|tesla)-live-2026-09-17/);
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

test('hero receipt label states the observation time, not a freshness adjective', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(page, /id="refresh-receipt"/);
  assert.match(integrity, /window\.location\.reload\(\)/);
  assert.match(integrity, /fetch\(source, \{ cache: 'no-store'/);
  // "LIVE RECEIPT / FRESH" was read as "measured just now" when it only meant
  // "published recently", so the label must carry the observation timestamp.
  assert.match(integrity, /OBSERVED \$\{observedStamp\} UTC/);
  assert.doesNotMatch(integrity, /LIVE RECEIPT · \$\{String\(status\)/);
  // The displayed receipt must never be presented as the byte-verifiable one.
  assert.match(integrity, /replay-receipt-note/);
  assert.match(integrity, /byte-verifiable replay receipt/);
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
  assert.match(integrity, /SURFACE RECONCILIATION/);
  assert.match(integrity, /tokenized_market_cap/);
});

test('population lens keeps an auditable row-level export available', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(page, /id="hero-mobile-decision"/);
  assert.match(page, /id="download-population-attribution"/);
  assert.match(page, /Inspect source fields/);
  assert.match(integrity, /function downloadPopulationAttribution/);
  assert.match(integrity, /market_cap_status/);
  assert.match(integrity, /zero_or_non_positive/);
  assert.match(integrity, /reference\.rwa_id/);
  assert.match(integrity, /token\.issuer_id/);
  assert.match(visualOverrides, /\.hero-mobile-decision/);
  assert.match(visualOverrides, /\.population-attribution-actions/);
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

test('browser verifier checks a second multi-wrapper reference', () => {
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.match(verifier, /tesla_state = search_and_check\("Tesla"\)/);
  assert.match(verifier, /tesla_state == "INVESTIGATE"/);
  assert.match(verifier, /\(320, 800\)/);
  assert.match(verifier, /\(375, 812\)/);
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

test('decision preview is mobile-only and cannot leak into desktop layout', () => {
  assert.match(visualOverrides, /\.hero-mobile-decision\{display:none!important\}/);
  assert.match(visualOverrides, /\.hero-mobile-decision\{display:block!important/);
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

test('population route guidance is published once, not repeated per card', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // Repeating the same route on every card made roughly half the population
  // list constant prose and buried the per-reference signals that differ.
  assert.match(integrity, /function renderRouteLegend/);
  assert.match(integrity, /renderRouteLegend\(visible\)/);
  assert.doesNotMatch(integrity, /\$\{renderHandoff\(alert\)\}/);
  assert.doesNotMatch(integrity, /\$\{renderCompactRoute\(item\)\}/);
});

test('publication history labels stay distinct when receipts share a day', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // Several receipts can land on one calendar day; MM-DD labels then repeat
  // and read as a broken axis.
  assert.match(integrity, /const distinctDays = new Set/);
  assert.match(integrity, /labelByTime/);
  assert.match(integrity, /Short series/);
});

test('the headline finding is read from the measurement, never typed into the page', () => {
  const index = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // The page and the receipt drifting apart is the exact defect this product
  // exists to catch, so the headline number must come from the published
  // measurement and not be written into the markup.
  assert.match(integrity, /async function renderFinding/);
  assert.match(integrity, /base-rate-[0-9]{4}-[0-9]{2}-[0-9]{2}\.json/);
  assert.match(index, /id="finding-headline"/);
  assert.match(index, /id="finding-lede"/);
  // No percentage, interval or count may be hardcoded in the hero copy.
  const hero = index.slice(index.indexOf('id="finding-headline"'), index.indexOf('hero-search-form'));
  assert.doesNotMatch(hero, /\d+\.\d+\s*%/);
  assert.doesNotMatch(hero, /95%\s*interval\s*\d/);
});

test('a missing measurement says so instead of leaving a number-shaped hole', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /could not be loaded/);
  assert.match(integrity, /make base-rate/);
});

test('the population list can be filtered to the references that have an answer', () => {
  const index = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const engine = fs.readFileSync(path.resolve(__dirname, '../rwa_integrity.py'), 'utf8');
  // The affirmative half sat at positions 35-47 of the list, so a reader saw
  // twelve refusals and left. "comparable" is not a state the scan emits; it is
  // the outcome a reader wants, and it must be reachable in one click.
  assert.match(index, /data-filter="comparable"/);
  assert.match(integrity, /filter === 'comparable'/);
  assert.match(integrity, /Boolean\(item\.comparison\)/);
  // The filter is useless unless the index carries the field it filters on.
  assert.match(engine, /"comparison": asset\.get\("comparison"\)/);
});

test('the dated map and the live receipt are joined, not kept apart', () => {
  const explorerSrc = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  // A reader searching the map used to be told the answer lived somewhere else,
  // which read as a dated artefact even though the receipt is current. Where the
  // live scan covers a reference, its verdict belongs on the same screen.
  assert.match(explorerSrc, /\/api\/integrity/);
  assert.match(explorerSrc, /function liveVerdictBlock/);
  assert.match(explorerSrc, /\$\{liveVerdictBlock\(asset\)\}/);
  // A reference absent from the scan must say why, not show an empty panel.
  assert.match(explorerSrc, /NOT IN THE CURRENT SCAN/);
  assert.match(explorerSrc, /carried no token representation/);
  // The verdict must carry the observation time, not imply it is live-now.
  assert.match(explorerSrc, /CURRENT VERDICT · OBSERVED/);
});

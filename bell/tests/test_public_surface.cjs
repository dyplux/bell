const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve(__dirname, '../site');
const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
const explorer = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
const visualOverrides = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
const integrityCss = fs.readFileSync(path.join(site, 'integrity.css'), 'utf8');
const catalogue = JSON.parse(fs.readFileSync(path.join(site, 'catalog.json'), 'utf8'));

test('public page exposes the single-URL RWA discovery and evidence path', () => {
  assert.match(page, /id="explorer"/);
  assert.match(page, /href="#explorer">Explore RWA/);
  assert.match(page, /src="explorer\.js(?:\?v=[^"]+)?"/);
  assert.match(page, /href="\/api\/integrity"/);
  assert.match(page, /separate from live receipt/);
  assert.match(page, /id="explorer-map-freshness"/);
  assert.match(page, /data-filter="FACTS OPEN">FACTS OPEN<\/button>/);
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
  // COMPARABLE was missing from this list, so the suite stayed green while the
  // explorer printed INVESTIGATE for all 87 references that publish one - the
  // product's headline number, and the reference the judge page names.
  for (const label of ['COMPARABLE', 'DO NOT SHORTLIST', 'INVESTIGATE', 'SINGLE REPRESENTATION',
    'REFERENCE ONLY', 'DOSSIER PENDING']) {
    assert.match(explorer, new RegExp(label.replaceAll(' ', '\\s+')));
  }
  // And it must reach that word through the one published function, not a
  // fourth private copy of the mapping.
  assert.match(explorer, /window\.BellDecisionLabel/);
  const integritySource = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integritySource, /window\.BellDecisionLabel = \(item, fallback\)/);
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
  // The receipt must never be served from cache without asking. That was
  // expressed as `no-store`, which forbids caching outright and so re-downloaded
  // an unchanged receipt on every load; `no-cache` keeps the guarantee and
  // allows a 304. Assert the guarantee - always revalidate - not the token.
  assert.match(integrity, /fetch\(source, \{ cache: 'no-cache'/);
  assert.doesNotMatch(integrity, /fetch\(source, \{ cache: '(default|force-cache|only-if-cached)'/);
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
  // The live observation must never be duplicated into the series. This used
  // to compare only against the last stored entry; it now checks every one,
  // because the series is sorted by observation time rather than arrival.
  assert.match(integrity, /storedObservations\.some\(item => item\.observed_at === liveObservation\.observed_at\)/);
  assert.match(integrity, /\.sort\(\(left, right\) => String\(left\.observed_at/);
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
  assert.match(verifier, /\(320, 800\)/);
  assert.match(verifier, /\(375, 812\)/);
});

test('the browser verifier pins the product, not one day of market data', () => {
  // This test used to require the source contain `tesla_state == "INVESTIGATE"`,
  // so it defended a brittle assertion instead of a guarantee: the moment
  // Tesla's representations became comparable, the live check failed and this
  // test insisted the failure was correct. A reference may move between states
  // as the data moves; what it may never do is render a state outside the
  // published vocabulary.
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.ok(!/tesla_state == "INVESTIGATE"/.test(verifier),
    'the verifier pins a named reference to a named verdict again');
  assert.match(verifier, /PUBLIC_STATES/);
  for (const state of ['COMPARABLE', 'FACTS OPEN', 'INVESTIGATE', 'DO NOT SHORTLIST', 'SINGLE REPRESENTATION']) {
    assert.ok(verifier.includes(`"${state}"`), `the published vocabulary lost ${state}`);
  }
});

test('an affirmative on the page has to carry its consequence', () => {
  // The live site showed COMPARABLE while the capital check underneath still
  // read "not ready for a clean shortlist" - one screen, two answers, which is
  // the exact failure this product exists to catch in other people's data.
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.match(verifier, /shows COMPARABLE without naming the spread and cheapest route/);
  assert.match(verifier, /shows COMPARABLE and the unresolved copy at the same time/);
  const capital = fs.readFileSync(path.join(site, 'capital-impact.js'), 'utf8');
  assert.match(capital, /mode: 'comparable'/);
  assert.match(capital, /cheapest route/);
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
  // This test used to assert that one CSS string existed, and passed happily
  // while "Receipt" and "For judges" sat past the right edge at 390px: the nav
  // scrolled horizontally with `scrollbar-width:none`, so it moved but nothing
  // said it could. A judge on a phone never reached the page written for them.
  // Pin the guarantee - the nav wraps, it does not hide overflow.
  const navRules = visualOverrides.match(/\.topbar nav\{[^}]*\}/g) || [];
  assert.ok(navRules.length, 'the topbar nav lost its responsive rules');
  for (const rule of navRules) {
    if (!/overflow-x:auto/.test(rule)) continue;
    assert.fail(`the nav scrolls its overflow out of sight: ${rule}`);
  }
  const wrapping = navRules.filter(rule => /flex-wrap:wrap/.test(rule));
  assert.ok(wrapping.length >= 2,
    'the narrow-viewport nav no longer wraps, so entries can leave the screen');
  assert.match(visualOverrides, /\.topbar nav a\{font-size:1[2-9]px/);

  // Every destination must lead somewhere that exists: an anchor on this page,
  // or a route the site actually serves.
  const routes = new Set(['/', '/judge']);
  for (const [, href] of page.matchAll(/<nav[^>]*>[\s\S]*?<\/nav>/g).next().value[0]
    .matchAll(/href="([^"]+)"/g)) {
    if (href.startsWith('#')) {
      assert.match(page, new RegExp(`id="${href.slice(1)}"`), `nav points at a missing section: ${href}`);
    } else {
      assert.ok(routes.has(href), `nav points at an unserved route: ${href}`);
    }
  }
});

// This assertion used to pin `font-size:10px`, which meant the suite was
// guarding the defect: 79% of declared sizes sat at 12px or below and three
// rules rendered at 7px. A floor is the thing worth pinning, not one number.
test('no declared font size falls below the legibility floor', () => {
  const FLOOR = 11;
  const offenders = [];
  for (const [name, sheet] of [['integrity.css', integrityCss], ['visual-overrides.css', visualOverrides]]) {
    for (const decl of sheet.match(/(?:font|font-size)\s*:[^;}]+/g) || []) {
      for (const px of decl.match(/\b(\d+(?:\.\d+)?)px/g) || []) {
        if (parseFloat(px) < FLOOR) offenders.push(`${name}: ${decl.trim().slice(0, 60)}`);
      }
    }
  }
  assert.deepEqual(offenders, [], `font sizes below ${FLOOR}px: ${offenders.join(' | ')}`);
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
  assert.match(index, /data-filter="COMPARABLE"/);
  assert.match(integrity, /displayDecisionLabel\(item, 'FACTS OPEN'\) === filter/);
  assert.match(integrity, /if \(item\?\.comparison\) return 'COMPARABLE'/);
  // The filter is useless unless the index carries the field it filters on.
  assert.match(engine, /"comparison": asset\.get\("comparison"\)/);
});

test('the dated map and the live receipt are joined, not kept apart', () => {
  const explorerSrc = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  // A reader searching the map used to be told the answer lived somewhere else,
  // which read as a dated artefact even though the receipt is current. Where the
  // live scan covers a reference, its verdict belongs on the same screen.
  // The receipt reaches the explorer through the promise integrity.js publishes.
  // Fetching it here a second time downloaded 2.4 MB of identical bytes on every
  // load, and cache:'no-cache' on both calls stopped the HTTP cache collapsing
  // them. Assert the shared handoff, and that the second request stays gone.
  const integritySrc = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // Publishing the network request meant localhost, which has no /api/integrity,
  // handed the explorer null and its cross-reference went dead: it told a reader
  // that Gold carried no token representation while the replay loaded on the
  // same page held Gold with seven. Publish the receipt the page actually read.
  assert.match(integritySrc, /window\.BellReceipt = new Promise\(resolve => \{ announceReceipt = resolve; \}\)/);
  assert.match(integritySrc, /announceReceipt\(candidate\)/);
  // And it must settle even when no source answered, or the lookup hangs.
  assert.match(integritySrc, /announceReceipt\(null\)/);
  assert.match(explorerSrc, /window\.BellReceipt/);
  assert.doesNotMatch(explorerSrc, /fetch\('\/api\/integrity'/);
  assert.match(explorerSrc, /function liveVerdictBlock/);
  assert.match(explorerSrc, /function appendLiveVerdict/);
  assert.match(explorerSrc, /appendLiveVerdict\(asset\)/);
  // A reference absent from the scan must say why, not show an empty panel.
  assert.match(explorerSrc, /NOT IN THE CURRENT SCAN/);
  assert.match(explorerSrc, /carried no token representation/);
  // The verdict must carry the observation time, not imply it is live-now.
  // The verdict must carry its observation time and must not imply it is
  // live-now when the page has fallen back to the dated replay.
  assert.match(explorerSrc, /'DATED REPLAY VERDICT' : 'CURRENT VERDICT'/);
  assert.match(explorerSrc, /· OBSERVED \$\{escapeHTML\(String\(liveIndex\.observed_at/);
});

test('every column the population export offers is one Bell actually observed', () => {
  // `quote_source` shipped in this header and was empty on every row of every
  // export: a column promising provenance and delivering nothing. An export is
  // the artefact a reader takes away and checks, so a column that is always
  // blank is worse than a missing one.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const header = integrity.match(/const header = \[([^\]]+)\]/);
  assert.ok(header, 'the population export no longer declares a header');
  const columns = header[1].split(',').map(entry => entry.trim().replace(/^'|'$/g, ''));

  const receipt = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const observed = new Set();
  for (const reference of receipt.alert_index) {
    for (const key of Object.keys(reference)) observed.add(key);
    for (const representation of reference.representations || []) {
      for (const key of Object.keys(representation)) observed.add(key);
    }
  }
  // Names the export derives rather than reads straight off a row.
  const derived = new Set(['reference_name', 'reference_symbol', 'token_symbol', 'token_name',
    'market_cap_status', 'in_published_comparison', 'premium_to_cheapest_bps']);

  const unbacked = columns.filter(column => !observed.has(column) && !derived.has(column));
  assert.deepEqual(unbacked, [],
    'these export columns correspond to no observed field and no declared derivation');
  assert.ok(!columns.includes('quote_source'), 'the always-empty column is back');
});

test('the export separates a published route from a representation Bell would not compare', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /comparison\?\.routes/);
  assert.match(integrity, /premium_to_cheapest_bps/);
});

test('no rendering path states a rate the measurement does not support', () => {
  // The static headline read "Most tokenised assets cannot honestly be
  // compared". That is true of 157 of the 244 references carrying more than
  // one representation, and false of the 791-reference catalogue - and it was
  // what a visitor saw before the fetch resolved, and what stayed on screen if
  // it failed. Both paths now leave the question standing.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const overstated = /Most tokenised assets\s*(<br>)?\s*<em>cannot honestly/;
  assert.ok(!overstated.test(page), 'the static headline overstates the finding');
  const rendered = integrity.split('catch (error)')[1] || '';
  assert.ok(!overstated.test(rendered), 'the failure path leaves the overstated headline on screen');
  assert.match(page, /id="finding-headline"/);
  // The measured claim must always carry its denominator in the same sentence.
  assert.match(integrity, /comparable-looking/);
});

test('the one control the product asks you to use is reachable on a phone', () => {
  // On a 390px screen the search box sat below the eyebrow, the headline, the
  // measured lede, the coverage fact and three paragraphs - about a screen
  // below the fold. Source order stays as written for readers and crawlers;
  // the phone layout orders the box above the prose.
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  // Take every phone block, not the last one: a second block was added later
  // and this test started reading only that, which is how a passing test
  // stops covering what it was written for.
  const phone = css.split('@media(max-width:620px)').slice(1).join('\n');
  assert.match(phone, /\.hero>div:first-of-type\{display:flex;flex-direction:column\}/);
  const order = name => {
    const rule = new RegExp(`\\.hero>div:first-of-type>${name}\\{order:(\\d+)`);
    const found = phone.match(rule);
    assert.ok(found, `no phone order declared for ${name}`);
    return Number(found[1]);
  };
  assert.ok(order('\\.hero-search') < order('#finding-lede'),
    'the search box is still ordered below the explanatory prose on a phone');
  assert.ok(order('#finding-headline') < order('\\.hero-search'),
    'the headline should still come first: the box needs a question above it');
});

test('no hero child can float to the top of a phone screen by accident', () => {
  // A flex child with no `order` defaults to 0, so the first version of the
  // phone rule silently hoisted the four-step task panel and the results
  // container above the headline: a reader met a checklist before learning
  // what the page was for. Every child must be placed explicitly, and the
  // baseline must send an unlisted one to the end rather than the top.
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const phone = css.split('@media(max-width:620px)').slice(1).join('\n');
  assert.match(phone, /\.hero>div:first-of-type>\*\{order:(\d+)\}/);
  const baseline = Number(phone.match(/\.hero>div:first-of-type>\*\{order:(\d+)\}/)[1]);
  assert.ok(baseline > 1, 'the fallback order would place an unlisted child first');

  // Every direct child of the hero column named in the page must be placed.
  const hero = page.slice(page.indexOf('<section id="start"'), page.indexOf('<section id="how-it-works"'));
  const ids = [...hero.matchAll(/<(?:div|section|p|dl|form)\s+id="([a-z-]+)"/g)].map(m => m[1]);
  for (const id of ids) {
    if (!phone.includes(`>#${id}{order:`) && !phone.includes(`>.${id}{order:`)) {
      // Unplaced is tolerable only because the baseline sends it to the end.
      assert.ok(baseline > 11, `#${id} is unplaced and the baseline is not safely last`);
    }
  }
});

test('the page states one comparability rate, over one denominator', () => {
  // The signature strip printed (blocked + investigate) / 791 as a percentage,
  // next to a headline stating 64.3% measured over the 244 references where a
  // comparison is something anyone could attempt. Two rates, two denominators,
  // one word - the exact confusion this product exists to prevent.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const strip = integrity.split('function renderThesisStrip')[1].split('function renderCompactEvidence')[0];
  assert.ok(!/const share = \(unresolved \/ total\) \* 100/.test(strip),
    'the strip computes a second comparability share');
  assert.ok(!/share\.toFixed/.test(strip), 'the strip still prints a competing rate');
  assert.match(strip, /scanned references/);
});

test('the signature strip offers an affirmative, not only ways to be refused', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const strip = integrity.split('function renderThesisStrip')[1].split('function renderCompactEvidence')[0];
  assert.match(strip, /thesis-metric comparable/);
  assert.match(strip, /comparison published/);
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(css, /\.thesis-metrics\{grid-template-columns:repeat\(4,1fr\)\}/);
});

test('the page defines its three words before it uses its numbers', () => {
  // A first-time reader met 791, 244, 157, 64.3% and a confidence interval
  // before anyone had said what a representation or an issuer is. The glossary
  // existed, far enough down the page that you reached it only after the
  // numbers had already lost you.
  const words = page.indexOf('id="hero-words"');
  assert.ok(words > 0, 'the hero no longer defines its vocabulary');
  for (const term of ['Reference', 'Representation', 'Issuer']) {
    assert.ok(page.includes(`<dt>${term}</dt>`), `the hero vocabulary lost ${term}`);
  }
  // It has to come before the population figures, not after them.
  const monitor = page.indexOf('id="monitor"');
  assert.ok(words < monitor, 'the vocabulary sits below the population index');
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(css, /\.hero>div:first-of-type>#hero-words\{order:\d/);
});

test('the first prose on a phone is not a footnote about receipts', () => {
  // The receipt note was the first text on the page at 390px: two lines about
  // which receipt is byte-verifiable, before the reader had been told what the
  // product is or seen a control. It belongs with the status it explains.
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const phone = css.split('@media(max-width:620px)').slice(1).join('\n');
  assert.match(phone, /\.topbar \.replay-receipt-note\{order:(\d+)/);
  const note = Number(phone.match(/\.topbar \.replay-receipt-note\{order:(\d+)/)[1]);
  const nav = Number((phone.match(/\.topbar nav\{order:(\d+)\}/) || [0, 0])[1]);
  assert.ok(note > nav, 'the receipt footnote still precedes the navigation on a phone');
});

test('the desktop headline leaves room for the control below it', () => {
  // At 84px over five lines the headline filled a 1440x900 screen on its own:
  // the search box, the three definitions and the affirmative were all below
  // the fold, so the first screen carried a number and no way to act on it.
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const desktop = css.split('@media(min-width:900px)').slice(1).join('\n');
  const size = desktop.match(/\.hero h1\{font:\d+ clamp\((\d+)px,[\d.]+vw,(\d+)px\)/);
  assert.ok(size, 'the desktop headline no longer declares a clamped size');
  assert.ok(Number(size[2]) <= 60,
    `the desktop headline caps at ${size[2]}px, which pushes the search box off the first screen`);
});

test('the control sits under the finding on desktop too, not under the caveats', () => {
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const desktop = css.split('@media(min-width:900px)').slice(1).join('\n');
  const order = selector => {
    const marker = '.hero>div:first-of-type>' + selector + '{order:';
    const at = desktop.indexOf(marker);
    assert.ok(at >= 0, 'no desktop order declared for ' + selector);
    return Number(desktop.slice(at + marker.length).match(/^\d+/)[0]);
  };
  assert.ok(order('.hero-search') < order('#coverage-fact'),
    'the search box is ordered below the API-coverage panel on desktop');
  assert.ok(order('#finding-headline') < order('.hero-search'),
    'the headline should come first: the box needs a question above it');
  assert.ok(order('*') > 12, 'an unlisted desktop child would float above the headline');
});

test('the outcome key on the first screen includes the affirmative', () => {
  // It listed three ways to be refused and no way to be answered, directly
  // under a headline that already leads with a refusal count.
  assert.match(page, /COMPARABLE = PRICES LINE UP/);
  const key = page.indexOf('OUTCOME KEY');
  const affirmative = page.indexOf('COMPARABLE = PRICES LINE UP');
  const refusal = page.indexOf('DO NOT SHORTLIST = BLOCKED');
  assert.ok(key < affirmative && affirmative < refusal,
    'the affirmative does not lead the outcome key');
});

test('the reference index does not render a third of the page before you search', () => {
  // Twelve rows at ~350px each made the index 4,200px of a 13,896px page,
  // rendered before a first-time visitor had asked anything. The index is
  // where you go for the population; the search box above it is where you go
  // with a question.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // The size became viewport-dependent - two on a phone, four on a desktop -
  // so check every branch of it rather than one literal.
  const sizes = (integrity.match(/const pageSize = [^;]+;/) || [])[0];
  assert.ok(sizes, 'the index no longer declares a page size');
  const values = (sizes.match(/\b\d+\b/g) || []).map(Number).filter(value => value <= 32);
  assert.ok(values.length, 'the page size no longer resolves to a number');
  for (const value of values) {
    assert.ok(value <= 8,
      `the index renders ${value} full rows by default, which is most of a screenful each`);
  }
  // Pagination has to still exist, or this is removal rather than deferral.
  assert.match(integrity, /alert-pagination/);
  assert.match(integrity, /Math\.ceil\(matching\.length \/ pageSize\)/);
});

test('population counts on the page are derived from the receipt, never written into it', () => {
  // An auditor read "1,440" on the live page and "1,435" in the documents and
  // could not tell which was authoritative. Both are right - they are two
  // observations - but the guarantee that makes that safe is that the page
  // never states a count of its own. Pin the guarantee.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /universe\.tokens_scanned/);
  // No population-scale figure may be hardcoded into the served HTML.
  const receipt = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  for (const value of [receipt.universe.tokens_scanned, receipt.universe.tokenised_references_scanned]) {
    for (const spelling of [String(value), Number(value).toLocaleString('en-US')]) {
      assert.ok(!page.includes(`>${spelling}<`),
        `the page hardcodes the population figure ${spelling}; it must render it from the receipt`);
    }
  }
});

test('the live page is pinned to the receipt it is reading, not only the archive', () => {
  // Two independent reviewers reached the same conclusion: the README's numbers
  // were guarded from the start and stayed correct, while the live page's were
  // guarded by nothing. A reader seeing "1,440 representation rows" could not
  // tell a fresh observation from the stale figure this project had already
  // corrected once - the exact failure it exists to catch, on its own surface.
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.match(verifier, /#metric-references/);
  assert.match(verifier, /#metric-tokens/);
  assert.match(verifier, /tokenised_references_scanned/);
  assert.match(verifier, /tokens_scanned/);
  assert.match(verifier, /not in its own current receipt/);
});

test('the mobile preview is pinned to the vocabulary, not to one verdict', () => {
  // It required the literal words "DO NOT SHORTLIST" and broke the moment the
  // hero started opening on a comparable reference. A named verdict is a fact
  // about today's data; the vocabulary is a property of the product.
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  const block = verifier.split('hero-mobile-decision')[1] || '';
  assert.ok(!/"DO NOT SHORTLIST" in mobile_decision/.test(block),
    'the mobile assertion pins one verdict again');
  assert.match(block, /PUBLIC_STATES/);
});

test('the fourth tile says it is a slice, not a fourth state', () => {
  // Three states partition the population; "comparison published" cuts across
  // all three. Shown as a fourth equal tile, the band appeared to count past
  // its own population - 38 + 91 + 663 = 792, then 83 more.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /thesis-metric comparable subset/);
  assert.match(integrity, /not a fourth state/);
  assert.match(integrity, /const partition = blocked \+ investigate \+ clear/);
});

test('a single-representation reference gets an answer, not only a refusal', () => {
  // 545 of 791 references carry one representation. The page told all of them
  // "nothing to compare" while the answer sat in the same row.
  //
  // The first version of this test grepped the source for the field names and
  // passed while the code threw a ReferenceError on every call - it referred to
  // a variable that does not exist in that scope, so the whole render aborted
  // and the panel above it silently kept stale content. `node --check` saw
  // valid syntax and the browser audit searched only references with two or
  // more representations, so nothing exercised the branch. This runs it.
  const src = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const start = src.indexOf('function referenceConcentrationPanel');
  assert.ok(start > 0, 'the single-representation branch is gone');
  let depth = 0, i = src.indexOf('{', start), end = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}' && --depth === 0) { end = i; break; }
  }
  // The card reads the shared boundary constants, so the harness has to supply
  // them - running the function in isolation is what caught that coupling.
  const fn = new Function('escapeHTML', 'formatNumber', 'NOT_OBSERVED_FULL', 'NOT_OBSERVED_SHORT',
    'return ' + src.slice(start, end + 1))(
      v => String(v ?? ''), v => String(v),
      'Backing, redemption, eligibility and custody are not observed here and remain your diligence.',
      'Not observed: backing · redemption · eligibility · custody');

  const html = fn({ representations: [{
    symbol: 'wICEx', name: 'Wrapped ICE', issuer_name: 'Backed Assets',
    volume_24h: 83943, platforms: [{ name: 'X Layer', contract_address: '0xabc123' }],
  }] });
  for (const shown of ['THE ONE WRAPPER', 'wICEx', 'Backed Assets', 'X Layer', '0xabc123']) {
    assert.ok(html.includes(shown), `the single-wrapper card does not state ${shown}`);
  }
  assert.match(html, /Backing, redemption, eligibility and custody are not observed/);

  // An untraded wrapper must say so rather than print a silent zero.
  const untraded = fn({ representations: [{ symbol: 'DEAD', volume_24h: 0, platforms: [] }] });
  assert.match(untraded, /nobody traded it/);
  assert.match(untraded, /not published for this row/);
});

test('the boundary is stated, once in full and short thereafter', () => {
  // The same four words appeared five times on one screen. The monitor really
  // does not observe backing, redemption, eligibility or custody, so the
  // sentence has to be there - but said five times it stops being read and
  // crowds out the answer the reader came for.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /const NOT_OBSERVED_FULL =/);
  assert.match(integrity, /const NOT_OBSERVED_SHORT =/);
  // The boundary must still name all four things somewhere.
  for (const word of ['Backing', 'redemption', 'eligibility', 'custody']) {
    assert.ok(integrity.includes(word), `the boundary no longer names ${word}`);
  }
  // And the full sentence must not be pasted inline again.
  const inline = integrity.split('Backing, redemption, eligibility and custody are not observed here and remain').length - 1;
  assert.ok(inline <= 1, `the full boundary sentence is inlined ${inline} times; use the constant`);
});

test('every styled hero block keeps a base rule, not only a media override', () => {
  // The glossary lost its base rule when a CSS block was replaced "from this
  // marker to end of file", taking the rules that followed with it. It then
  // rendered as a default <dl> on the first screen, and no test noticed
  // because none of them look at layout. This asserts the base rules exist
  // outside any media query.
  const css = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const outsideMedia = css.split('@media')[0] + css.split(/@media[^{]*\{/).map(chunk => {
    // keep only what follows the closing brace of each media block
    const parts = chunk.split('\n}\n');
    return parts.length > 1 ? parts.slice(1).join('\n}\n') : '';
  }).join('\n');
  for (const rule of ['.hero-words{display:grid', '.thesis-metrics{grid-template-columns:repeat(4,1fr)}']) {
    assert.ok(outsideMedia.includes(rule) || css.includes('\n' + rule),
      `${rule} exists only inside a media query, or not at all`);
  }
});

test('the boundary is not abbreviated by whoever renders first', () => {
  // The first fix kept a flag and abbreviated whichever call came second. The
  // order was not what I assumed - the hero copy and the panel under it are
  // written in two passes that do not share the flag - so both kept printing
  // the sentence in full. Abbreviating belongs to the place, not to timing.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.ok(!/let boundaryShown/.test(integrity),
    'the order-dependent flag is back; it did not work the first time');
  assert.match(integrity, /const shortenBoundary =/);
  // The full sentence must still exist somewhere, and the short form must be
  // used where the panel repeats it.
  assert.match(integrity, /NOT_OBSERVED_FULL/);
  assert.match(integrity, /shortenBoundary\(assessment\.note\)/);
});

// ---------------------------------------------------------------------------
// Running the code, not reading it.
//
// An auditor counted this file: 50 tests, 123 assertions matching regexes
// against source text, and exactly one that executed anything. That is not a
// stylistic preference - a render function in this same file shipped throwing
// a ReferenceError on every call while its grep-based test passed, because a
// string being present in a file says nothing about whether the code runs.
// This helper extracts a function by name and executes it against stubs, so
// the assertions below are about behaviour.
function runFromSource(name, deps = {}) {
  const src = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const at = src.indexOf(`function ${name}(`);
  assert.ok(at > 0, `${name} no longer exists in integrity.js`);
  let depth = 0, i = src.indexOf('{', at), end = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}' && --depth === 0) { end = i; break; }
  }
  const names = Object.keys(deps);
  return new Function(...names, `return ${src.slice(at, end + 1)}`)(...names.map(k => deps[k]));
}

test('the public label follows the decision, executed not grepped', () => {
  const label = runFromSource('displayDecisionLabel');
  // A published comparison outranks the state that let it through.
  assert.equal(label({ state: 'investigate', comparison: { route_count: 3 } }), 'COMPARABLE');
  assert.equal(label({ state: 'no_flags', comparison: { route_count: 2 } }), 'COMPARABLE');
  // A blocked reference is never labelled comparable, even with a comparison.
  assert.equal(label({ state: 'do_not_compare', comparison: { route_count: 5 } }), 'DO NOT SHORTLIST');
  // One representation is not a comparison.
  assert.equal(label({ state: 'no_flags', token_count: 1 }), 'SINGLE REPRESENTATION');
  assert.equal(label({ state: 'no_flags', token_count: 4 }), 'FACTS OPEN');
  assert.equal(label({ state: 'investigate' }), 'INVESTIGATE');
  // Every label it can return must be in the published vocabulary.
  const vocabulary = new Set(['COMPARABLE', 'DO NOT SHORTLIST', 'INVESTIGATE', 'FACTS OPEN', 'SINGLE REPRESENTATION']);
  for (const item of [{ state: 'investigate', comparison: {} }, { state: 'no_flags', token_count: 1 },
                      { state: 'do_not_compare' }, { state: 'no_flags' }]) {
    assert.ok(vocabulary.has(label(item)), `${label(item)} is outside the published vocabulary`);
  }
});

test('the hero picks by the published rule, executed not grepped', () => {
  // The rule is "most comparable routes, ties broken by widest spread". If it
  // silently became "first in the list", the page would still look right and
  // the choice would no longer be checkable.
  const alerts = [
    { name: 'few', comparison: { route_count: 2, spread_bps: 900 } },
    { name: 'most', comparison: { route_count: 7, spread_bps: 10 } },
    { name: 'tie-loser', comparison: { route_count: 7, spread_bps: 5 } },
    { name: 'no comparison' },
    { name: 'single route', comparison: { route_count: 1, spread_bps: 999 } },
  ];
  const pick = runFromSource('heroComparable', { receipt: { alerts } });
  assert.equal(pick().name, 'most', 'route count must win over a wider spread');

  const tied = runFromSource('heroComparable', {
    receipt: { alerts: [alerts[2], alerts[1]] } });
  assert.equal(tied().name, 'most', 'a tie on routes must break on the wider spread');

  // A reference with one route is not a comparison and must never be chosen.
  const onlySingle = runFromSource('heroComparable', {
    receipt: { alerts: [alerts[4], alerts[3]] } });
  assert.equal(onlySingle(), null, 'a one-route reference was offered as a comparison');

  // No comparisons at all must yield null so the caller can fall back.
  assert.equal(runFromSource('heroComparable', { receipt: { alerts: [] } })(), null);
});

test('the history refuses a delta across a rule boundary, executed not grepped', () => {
  // The page used to print "-568 investigate groups, +570 clear groups" between
  // 21 and 26 September. Nothing moved in the market: MARKET_FIELDS_MISSING
  // stopped driving most of the catalogue to INVESTIGATE. The same instant,
  // 2026-09-21T21:25:01Z, is published twice with different answers - 662
  // investigate in the stored summary, 90 in the replay recomputed under
  // bell.rules.v2. A product about surfaces that quietly disagree must not do
  // it on its own front page.
  const render = (history, rulesVersion) => {
    let html = '';
    const trail = { textContent: '', insertAdjacentHTML() {} };
    const target = { set innerHTML(value) { html = value; }, get innerHTML() { return html; } };
    runFromSource('renderPublicationHistory', {
      byId: (id) => (id === 'publication-history' ? target
        : id === 'hero-receipt-trail' ? trail
        : id === 'hero-receipt-link' ? {} : null),
      escapeHTML: (value) => String(value ?? ''),
      receipt: {
        observed_at: '2026-09-26T19:37:49Z',
        universe: {
          tokenised_references_scanned: 792, tokens_scanned: 1442,
          rules_version: rulesVersion,
          states: { do_not_compare: 34, investigate: 90, no_flags: 668 },
          signals: { PRICE_DENOMINATION_BREAK: 4 },
        },
      },
    })(history);
    return html;
  };

  const stored = (observed_at, rules) => ({
    observed_at, tokenised_references_scanned: 791, tokens_scanned: 1435,
    ...(rules ? { rules_version: rules } : {}),
    states: { do_not_compare: 35, investigate: 662, no_flags: 94 },
    signals: { PRICE_DENOMINATION_BREAK: 4 },
  });

  // Across a boundary: no delta, and the reason is named.
  const crossed = render({ observations: [stored('2026-09-21T21:25:01Z')] }, 'bell.rules.v2');
  assert.match(crossed, /RULE CHANGE, NOT MARKET CHANGE/);
  assert.match(crossed, /Two receipts, two rule sets/);
  assert.doesNotMatch(crossed, /-572|\+574|investigate groups/,
    'a delta was printed across a rule boundary');

  // Same rule set on both sides: the delta is legitimate and must still appear.
  const same = render({ observations: [stored('2026-09-26T05:00:00Z', 'bell.rules.v2')] }, 'bell.rules.v2');
  assert.match(same, /investigate groups/);
  assert.doesNotMatch(same, /RULE CHANGE/, 'a rule boundary was claimed where none exists');
  assert.match(same, /-572/, 'the real delta between two v2 receipts went missing');

  // Neither side records its rules: still refuse, but do not claim they differ.
  const neither = render({ observations: [stored('2026-09-21T21:25:01Z')] }, null);
  assert.match(neither, /RULE CHANGE, NOT MARKET CHANGE/);
  assert.match(neither, /Neither summary records the rule set/);
});

test('the judge page carries the claim, a keyless check and links that exist', () => {
  // A judge with 48 submissions to read does not scroll fourteen screens. This
  // page is the whole product in three: the claim, commands that need no key,
  // and the receipts behind every number on it.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');

  // The claim must lead with what the product produces, not only what it refuses.
  assert.match(judge, /87 have a cheapest\s+route worth naming/);
  assert.match(judge, /no API key/);

  // Every command shown must be one the repository actually exposes.
  const makefile = fs.readFileSync(path.resolve(__dirname, '../../Makefile'), 'utf8');
  for (const target of ['base-rate', 'demo', 'check-offline']) {
    assert.match(judge, new RegExp(`make ${target}`), `judge page stopped offering make ${target}`);
    assert.match(makefile, new RegExp(`^${target}:`, 'm'), `make ${target} no longer exists`);
  }
  assert.match(judge, /python3 bell\/verify_rule_boundaries\.py/);
  assert.ok(fs.existsSync(path.resolve(__dirname, '../verify_rule_boundaries.py')));

  // A judge page that links to a missing receipt is worse than no judge page.
  const hrefs = [...judge.matchAll(/href="((?:proof|assets)\/[^"]+)"/g)].map(m => m[1]);
  assert.ok(hrefs.length >= 6, 'the judge page stopped linking its receipts');
  for (const href of hrefs) {
    assert.ok(fs.existsSync(path.join(site, href)), `judge page links a missing file: ${href}`);
  }

  // The boundary travels with the claim, never separately.
  assert.match(judge, /does not prove backing, redemption/);
  // And the product page has to lead there, or nobody finds it.
  assert.match(page, /href="\/judge"/);
});

test('the 2 MB map snapshot is not fetched before anyone asks for it', () => {
  // catalog.json is 2 MB and feeds one section far down the page. Fetching it at
  // module evaluation made every visit pay for it, including the ones that only
  // search a reference at the top.
  const source = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  assert.match(source, /const loadCatalogue = \(\) =>/);
  assert.match(source, /IntersectionObserver/);
  // The fetch must live inside the loader, never at the top level of the IIFE.
  const loaderAt = source.indexOf('const loadCatalogue');
  const fetchAt = source.indexOf("fetch('catalog.json'");
  assert.ok(fetchAt > loaderAt, 'catalog.json is fetched outside the lazy loader');
  assert.equal(source.split("fetch('catalog.json'").length - 1, 1, 'more than one catalogue fetch');
  // A deep link has no section to scroll to, so it must load immediately.
  assert.match(source, /if \(initialMapQuery \|\| !\('IntersectionObserver' in window\)\)/);
  // Keyboard users can tab into the field before it scrolls into view.
  assert.match(source, /input\.addEventListener\('focus'/);

  // Nothing may render a loading state that the deferred fetch never resolves:
  // the markup carries the committed snapshot total, and it has to be the real
  // one, so a stale refresh cannot leave a wrong number on screen.
  const total = JSON.parse(fs.readFileSync(path.join(site, 'catalog.json'), 'utf8')).total_size;
  const shown = page.match(/id="explorer-count"[^>]*>([\d,]+) mapped references/);
  assert.ok(shown, 'the explorer count lost its static fallback');
  assert.equal(Number(shown[1].replace(/,/g, '')), total,
    'the static reference count no longer matches catalog.json');
});

test('an out-of-order receipt cannot print the delta backwards', () => {
  // The live observation was pushed onto the end of the series regardless of
  // when it was observed. Once a scheduled job appends the series, a receipt
  // that arrives late prints "20:08 -> 13:44" with both signs inverted and
  // nothing on the page saying so.
  let html = '';
  const trail = { textContent: '', insertAdjacentHTML() {} };
  const target = { set innerHTML(value) { html = value; }, get innerHTML() { return html; } };
  runFromSource('renderPublicationHistory', {
    byId: (id) => (id === 'publication-history' ? target
      : id === 'hero-receipt-trail' ? trail
      : id === 'hero-receipt-link' ? {} : null),
    escapeHTML: (value) => String(value ?? ''),
    receipt: {
      // Observed BEFORE the newest stored observation.
      observed_at: '2026-09-26T13:44:13Z',
      universe: {
        tokenised_references_scanned: 792, tokens_scanned: 1442,
        rules_version: 'bell.rules.v2',
        states: { do_not_compare: 32, investigate: 96, no_flags: 664 },
        signals: { PRICE_DENOMINATION_BREAK: 4 },
      },
    },
  })({
    observations: [{
      observed_at: '2026-09-26T20:08:35Z', rules_version: 'bell.rules.v2',
      tokenised_references_scanned: 792, tokens_scanned: 1442,
      states: { do_not_compare: 30, investigate: 98, no_flags: 664 },
      signals: { PRICE_DENOMINATION_BREAK: 4 },
    }],
  });

  // The later observation must be on the right of the arrow, whichever arrived first.
  assert.match(html, /2026-09-26T13:44:13Z[^→]*→[^<]*2026-09-26T20:08:35Z/);
  // 32 blocked earlier, 30 later, so the delta reads -2 and never +2.
  assert.match(html, /<strong>-2<\/strong><small>blocked groups<\/small>/);
  assert.match(html, /<strong>\+2<\/strong><small>investigate groups<\/small>/);
});

test('the judge page states the JavaScript test count it actually runs', () => {
  // A page that tells a judge "217 tests" has to be right about it, the same way
  // the headline finding is read from the measurement instead of typed in. The
  // Python half is pinned by test_judge_counts.py, which asks unittest what it
  // collected rather than counting `def test_` - nine of those are helpers on
  // classes the runner never collects.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');
  const countTests = (dir, glob) => fs.readdirSync(dir)
    .filter(name => glob.test(name))
    .reduce((total, name) => total
      + (fs.readFileSync(path.join(dir, name), 'utf8').match(/^test\(/gm) || []).length, 0);
  const js = countTests(path.resolve(__dirname), /^test_.*\.cjs$/)
    + countTests(path.resolve(__dirname, '../../cloudflare/tests'), /\.mjs$/);

  const stated = judge.match(/(\d+) tests, (\d+) Python and (\d+) JavaScript/);
  assert.ok(stated, 'the judge page stopped stating its test breakdown');
  assert.equal(Number(stated[3]), js, 'the stated JavaScript test count is wrong');
  assert.equal(Number(stated[1]), Number(stated[2]) + Number(stated[3]),
    'the judge page total does not equal its own breakdown');
  assert.match(judge, new RegExp(`<strong>${stated[1]}</strong>`),
    'the headline number and the breakdown total disagree');
});

test('two counts that measure different things say so on the page', () => {
  // The hero reported 157 refusals and the strip below it reported 34 blocked,
  // with nothing reconciling them. They are different questions on different
  // dates: 157 is the dated base rate across the references carrying more than
  // one representation and counts every coded refusal; 34 is the current scan
  // across every reference and counts the critical rule alone. A product about
  // figures that quietly disagree cannot leave two of its own unexplained.
  assert.match(page, /Blocked by a critical rule/);
  assert.match(page, /<span>in this scan<\/span>/);
  assert.doesNotMatch(page, /<span>do not compare<\/span>/,
    'the blocked tile went back to a label that reads like the refusal count');
  assert.match(page, /class="metric-strip-note"/);
  assert.match(page, /not meant to add up/);
  assert.match(integrityCss, /\.metric-strip-note\{/);
  // And the dated half must keep its date, or the note describes nothing.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /Measured on \$\{measuredOn\}/);
});

test('a phone gets fewer index cards without losing any reference', () => {
  // Each index card is about 1.2 screens tall at 390px, so four of them made
  // the reference index five and a half screens of scrolling on a phone.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /const pageSize = window\.matchMedia\('\(max-width: 760px\)'\)\.matches \? 2 : 4;/);
  // Fewer cards is only acceptable because nothing becomes unreachable: the
  // pager, the search and every state filter still cover the whole population.
  assert.match(integrity, /Math\.ceil\(matching\.length \/ pageSize\)/);
  assert.match(page, /id="alert-pagination"/);
  assert.match(page, /id="alert-search"/);
  for (const state of ['all', 'COMPARABLE', 'DO NOT SHORTLIST', 'INVESTIGATE', 'FACTS OPEN',
    'SINGLE REPRESENTATION']) {
    assert.match(page, new RegExp(`data-filter="${state}"`), `the ${state} filter went missing`);
  }
});

test('the judge page names examples that hold on the receipt it ships', () => {
  // The page named Alphabet as its affirmative example. On the live receipt it
  // is COMPARABLE; on the dated replay shipped in this repository it is
  // DO NOT SHORTLIST, and localhost deliberately loads the replay. A judge
  // following the README's own clone instructions saw the opposite of what the
  // page promised, and nothing guarded it. Both named references must now hold
  // on the artifact a reader can actually run.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const byName = new Map((replay.alert_index || []).map(item => [item.name, item]));

  const affirmative = judge.match(/<li><strong>([^<]+)<\/strong> returns <strong>COMPARABLE<\/strong>/);
  assert.ok(affirmative, 'the judge page lost its affirmative example');
  const comparable = byName.get(affirmative[1]);
  assert.ok(comparable, `${affirmative[1]} is not in the shipped replay receipt`);
  assert.ok(comparable.comparison,
    `${affirmative[1]} publishes no comparison in the shipped replay, so the page promises an answer a local clone does not give`);

  const refusal = judge.match(/<li><strong>([^<]+)<\/strong> returns <strong>DO NOT SHORTLIST<\/strong>/);
  assert.ok(refusal, 'the judge page lost its refusal example');
  const blocked = byName.get(refusal[1]);
  assert.ok(blocked, `${refusal[1]} is not in the shipped replay receipt`);
  assert.equal(blocked.state, 'do_not_compare',
    `${refusal[1]} is not blocked in the shipped replay`);
});

test('nothing claims to be current while the page is reading a dated receipt', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const explorerSrc = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');

  // The first version of this test asserted one chip. That is one instance of a
  // rule, not the rule, and three other places kept asserting currency over a
  // five-day-old replay: the population lens chip, the strip's scope sentence
  // and the explorer's verdict header. Assert the rule.
  const claims = /CURRENT RECEIPT|CURRENT VERDICT|current scan|latest scan/g;
  const inMarkup = [...page.matchAll(claims)].map(match => match[0]);
  assert.deepEqual(inMarkup, [],
    `markup hard-codes a currency claim the page cannot honour on a dated receipt: ${inMarkup}`);

  // Each of those strings may exist only in code that has read publication.source.
  for (const [label, source] of [['integrity.js', integrity], ['explorer.js', explorerSrc]]) {
    if (!claims.test(source)) continue;
    assert.match(source, /dated_static/,
      `${label} prints a currency claim without consulting the publication source`);
  }
  assert.match(integrity, /const datedNow = publication\?\.source === 'dated_static'/);
  assert.match(integrity, /populationSource\.textContent = datedNow/);
  assert.match(integrity, /stripScope\.textContent = datedNow/);
  assert.match(explorerSrc, /liveIndex\.dated = receipt\?\._publication\?\.source === 'dated_static'/);
  assert.match(explorerSrc, /liveIndex\.dated \? 'DATED REPLAY VERDICT' : 'CURRENT VERDICT'/);

  // An exported case receipt named /api/integrity even when the page had fallen
  // back to the replay file, and its decision label disagreed with the screen.
  assert.match(integrity, /source: receiptSource \|\| '\/api\/integrity'/);
  assert.match(integrity, /public_label: displayDecisionLabel\(item\)/);
});

test('narrow viewports shrink their grid tracks instead of cutting them off', () => {
  // Grid and flex children default to min-width:auto, so a long signal string
  // pushed a track wider than the viewport. The page did not scroll sideways,
  // so the overflow was cut off: at 390px the state badge and the
  // representation count rendered at x=393..476, entirely off-canvas. The
  // browser audit's existing check compared documentElement.scrollWidth to the
  // viewport, which stayed false throughout, because nothing scrolled.
  assert.match(integrityCss, /\.alert-row>\*,\.compact-row>\*\{min-width:0/);
  assert.match(integrityCss, /\.output-grid,\.output-grid>article/);
  // Tables are the exception: they own a scrollable wrapper and say "swipe
  // horizontally". Forcing them to fit broke every cell into single letters.
  assert.match(integrityCss, /\.token-table-wrap,\.quote-band-scroll[^}]*overflow-x:auto/);
  assert.match(integrityCss, /\.token-table th,\.token-table td[^}]*white-space:nowrap/);
  // And the audit now counts clipped leaves rather than trusting page overflow.
  const browser = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.match(browser, /cuts \{len\(clipped\)\} elements off the right edge/);
  assert.match(browser, /parent\.scrollWidth > parent\.clientWidth \+ 1/);
});

test('an exported case pairs each hash with the endpoint and a way back', () => {
  // A hash proves the payload did not change. It does not say which endpoint
  // produced it, nor how a reader with no CoinMarketCap credential gets back to
  // it. The rival this submission trails attaches endpoint, params, status and
  // a reproducing call to every figure; this is the credential-free equivalent.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /provenance: \{/);
  assert.match(integrity, /endpoint: receipt\?\.method\?\.\[surface\] \|\| null/);
  assert.match(integrity, /reproduce: \[/);
  // Every command the artifact promises must be a target that exists.
  const makefile = fs.readFileSync(path.resolve(__dirname, '../../Makefile'), 'utf8');
  const block = integrity.slice(integrity.indexOf('reproduce: ['), integrity.indexOf('reproduce: [') + 400);
  for (const [, target] of block.matchAll(/make (\w[\w-]*)/g)) {
    assert.match(makefile, new RegExp(`^${target}:`, 'm'),
      `the case receipt promises make ${target}, which does not exist`);
  }
  // And it must name the source it was actually read from, not a fixed one.
  assert.match(integrity, /This case was read from \$\{receiptSource\}/);
});

test('the map search behaves like the search one screen above it', () => {
  // The hero search is live as you type. This one silently required Enter, so a
  // reader who typed "Gold" and waited concluded the map held nothing. Two
  // search boxes on one page may not answer to different rules.
  const explorerSrc = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  assert.match(explorerSrc, /input\.addEventListener\('input'/);
  assert.match(explorerSrc, /renderMatches\(value \? find\(value\) : \[\], value\)/);
  // Listing matches is not the same as opening a dossier: that stays deliberate,
  // or every keystroke would fire a request for a published case.
  assert.match(explorerSrc, /form\.addEventListener\('submit'/);
  const typed = explorerSrc.slice(explorerSrc.indexOf("input.addEventListener('input'"),
    explorerSrc.indexOf("form.addEventListener('submit'"));
  assert.doesNotMatch(typed, /\bload\(/, 'typing opens a dossier instead of listing matches');
});

test('every example chip promises the word the product prints for it', () => {
  // The chip read "Marvell facts open" and the hero printed OUTPUT: COMPARABLE.
  // Both are defensible - the reference is no_flags AND carries a published
  // comparison - but the advertised outcome was not the outcome. The judge
  // page's two named examples are already pinned to the shipped replay; the
  // three on the product page were not.
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const byName = new Map((replay.alert_index || []).map(item => [item.name, item]));
  const label = runFromSource('displayDecisionLabel');

  // My first version of this test pinned the DECISION EFFECT and the card
  // badge was computed somewhere else, so Coinbase advertised COMPARABLE on the
  // judge page and wore an INVESTIGATE badge on the card. One function decides
  // the word now, and this asserts that rather than assuming it.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.equal((integrity.match(/const stateLabel = displayDecisionLabel\(/g) || []).length, 2,
    'a card computes its badge somewhere other than displayDecisionLabel');
  assert.doesNotMatch(integrity, /const stateLabel = \w+\.state === 'no_flags'/,
    'the badge went back to reading the raw state');

  const chips = [...page.matchAll(/data-example-search="([^"]+)">[^<]*<em>([^<]+)<\/em>/g)];
  assert.ok(chips.length >= 3, 'the example chips went missing');
  for (const [, query, promised] of chips) {
    // The chips search the way a reader does: "Silver" is a name, "SPY" is a
    // symbol. Resolve either, as the product's own search does.
    const needle = query.toLowerCase();
    const match = [...byName.entries()].find(([name, item]) =>
      name.toLowerCase().startsWith(needle) || String(item.symbol || '').toLowerCase() === needle);
    assert.ok(match, `the example "${query}" matches nothing in the shipped replay`);
    const printed = label(match[1]);
    // The chips use the shorthand the page's own outcome key defines, so
    // resolve through that key rather than comparing strings letter for letter.
    const shorthand = {
      blocked: 'DO NOT SHORTLIST',
      comparable: 'COMPARABLE',
      'facts open': 'FACTS OPEN',
      'single representation': 'SINGLE REPRESENTATION',
    }[promised.trim().toLowerCase()];
    assert.ok(shorthand, `the chip for ${match[0]} uses "${promised.trim()}", which the outcome key does not define`);
    assert.match(page, new RegExp(`${shorthand}(</b>| =)`),
      `the outcome key stopped defining ${shorthand}`);
    assert.equal(shorthand, printed,
      `the chip promises "${promised.trim()}" for ${match[0]} but the product prints "${printed}"`);
  }
});

test('no static placeholder asserts a live case over a dated one', () => {
  // The decision aside shipped "LIVE CASE / Reading the current receipt" in the
  // markup, so it sat over five-day-old data until a 3.4 MB fetch resolved.
  assert.doesNotMatch(page, /LIVE CASE/);
  assert.doesNotMatch(page, /Reading the current receipt/);
  // The strip's sentence asserted the two counts came from different dates.
  // On the dated replay they carry the same instant, so it states them instead.
  assert.doesNotMatch(page, /on a different date/);
  assert.match(page, /id="metric-strip-dates"/);
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /scanAt !== findingObservedAt/);
});

test('the judge page counts the endpoints the repository actually calls', () => {
  // The page named five RWA endpoints and the repository uses all seven, so it
  // was under-reporting its own strongest criterion. Every count on that page
  // is pinned to its source; this one was not pinned at all.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');
  const dir = path.resolve(__dirname, '..');
  const called = new Set();
  for (const name of fs.readdirSync(dir).filter(file => file.endsWith('.py'))) {
    for (const [, endpoint] of fs.readFileSync(path.join(dir, name), 'utf8')
      .matchAll(/"(\/v\d\/[a-z0-9/_-]+)"/g)) called.add(endpoint);
  }
  const rwa = [...called].filter(endpoint => endpoint.startsWith('/v5/real-world-assets/'));
  assert.equal(rwa.length, 7, `the RWA family count moved to ${rwa.length}: ${rwa.sort()}`);
  assert.match(judge, new RegExp(`All <strong>${rwa.length}</strong> of the dedicated RWA endpoints`));
  assert.match(judge, new RegExp(`<strong>${called.size}</strong> distinct CoinMarketCap endpoints`));
  // And the two outside the published loop must still be named with the reason.
  assert.match(judge, /market-pairs\/list<\/strong> is not returned on the Startup plan/);
  assert.match(judge, /single-issuer endpoint, is used by the per-reference audit path/);
});

test('the comparison spans the card and every anchor clears the sticky header', () => {
  // At 320px the row stayed a two-column grid, so the comparison table - the
  // product's central output - was forced into a 180px scroller beside an 82px
  // stub, with the price column sliced mid-digit. At 1440 the same pinning gave
  // it 353px of a 906px card with 500px empty to its right.
  assert.match(integrityCss, /\.alert-row>\.comparison-block,\.compact-row>\.comparison-block/);
  assert.match(integrityCss, /grid-column:1 \/ -1/);
  // The table scrolls on a phone and nothing said so, so two of five columns
  // looked absent rather than reachable.
  assert.match(integrityCss, /\.comparison-scroll-hint\{display:block/);
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /class="comparison-scroll-hint"/);

  // scroll-margin-top was 0 on three of the five nav destinations against an
  // 82px sticky header, so every jump parked the heading underneath it.
  assert.match(integrityCss, /--header-height:82px/);
  assert.match(integrityCss, /scroll-margin-top:calc\(var\(--header-height\) \+ 16px\)/);
  for (const [, href] of page.matchAll(/<nav[^>]*>[\s\S]*?<\/nav>/g).next().value[0]
    .matchAll(/href="#([^"]+)"/g)) {
    assert.match(integrityCss, new RegExp(`#${href}[,{]`),
      `the nav points at #${href}, which has no scroll offset`);
  }
});

test('every filter returns the label it names, and they partition the population', () => {
  // The filters matched the raw scan state while the cards showed the decision
  // label: FACTS OPEN returned 666 rows of which 545 were badged SINGLE
  // REPRESENTATION and 44 COMPARABLE. The counts reconciled; the words did not.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /displayDecisionLabel\(item, 'FACTS OPEN'\) === filter/);
  assert.doesNotMatch(integrity, /item\.state === filter/,
    'a filter went back to matching the raw state');

  // Every published label needs a button, or a reader cannot reach 545 of the
  // 791 references. SINGLE REPRESENTATION had none.
  const buttons = [...page.matchAll(/data-filter="([^"]+)"/g)].map(match => match[1]);
  const label = runFromSource('displayDecisionLabel');
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const produced = new Set((replay.alert_index || []).map(item => label(item, 'FACTS OPEN')));
  for (const word of produced) {
    assert.ok(buttons.includes(word), `the scan produces ${word} and no filter offers it`);
  }
  // And the buttons must partition it: every one is a label, none is a state.
  for (const button of buttons.filter(value => value !== 'all')) {
    assert.ok(produced.has(button), `the filter bar offers ${button}, which the scan never produces`);
  }
});

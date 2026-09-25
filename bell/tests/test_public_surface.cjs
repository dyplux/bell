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
  assert.match(explorerSrc, /function appendLiveVerdict/);
  assert.match(explorerSrc, /appendLiveVerdict\(asset\)/);
  // A reference absent from the scan must say why, not show an empty panel.
  assert.match(explorerSrc, /NOT IN THE CURRENT SCAN/);
  assert.match(explorerSrc, /carried no token representation/);
  // The verdict must carry the observation time, not imply it is live-now.
  assert.match(explorerSrc, /CURRENT VERDICT · OBSERVED/);
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
  const size = integrity.match(/const pageSize = (\d+);/);
  assert.ok(size, 'the index no longer declares a page size');
  assert.ok(Number(size[1]) <= 8,
    `the index renders ${size[1]} full rows by default, which is most of a screenful each`);
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

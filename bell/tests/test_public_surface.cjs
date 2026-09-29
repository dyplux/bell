const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const site = path.resolve(__dirname, '../site');
const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
const explorer = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
const issuerEvidence = fs.readFileSync(path.join(site, 'issuer-evidence.js'), 'utf8');
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

test('dated pair review appears with the searched case and its export points to the checked receipt', () => {
  assert.match(issuerEvidence, /'4:37013:38001'/);
  assert.match(integrity, /if \(!pair \|\| !ids\.has\('37013'\) \|\| !ids\.has\('38001'\)\) return ''/);
  assert.match(integrity, /pairReviewMarkup\(item, tokenRowsFor\(item\)\)\}\$\{capitalPanel\(item\)\}\$\{observedQuoteEndpoints\(item\)\}/,
    'the pairwise review must appear first beside the searched case, before secondary quote details');
  assert.match(integrity, /class="pair-review-summary"/);
  assert.match(integrity, /class="pair-review-details"/,
    'secondary dates and methodology must be available through native disclosure');
  assert.match(issuerEvidence, /summary: 'Same Alphabet Class A reference, but quote units remain unresolved/);
  assert.match(page, /id="hero-search-form"[\s\S]*?<small>Search a reference[^<]*<\/small>\s*<\/form>\s*<div id="search-result"[\s\S]*?<div class="quick-search"/,
    'the answer should render below the search control, outside its native form validation, and before examples');
  assert.match(page, /class="hero-search-control"/);
  assert.match(integrityCss, /\.hero-search-control\{display:flex/);
  assert.doesNotMatch(integrityCss, /\.hero-search>div\{display:flex/,
    'the input-row layout must not collapse other result blocks inside the form');
  assert.match(page, /data-example-search="Alphabet"/,
    'the featured pairwise review must be discoverable from the first screen');
  assert.doesNotMatch(integrity.slice(integrity.indexOf('function renderComparison(item)'), integrity.indexOf('function comparisonRouteSet')), /pairReviewMarkup/,
    'the pairwise review must not be squeezed into a narrow population row');
  assert.match(integrity, /pairwise_terms_review: pairwiseTermsReview/);
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_pair_review.py'), 'utf8');
  assert.match(verifier, /CMC source SHA-256 does not match/);
  assert.match(verifier, /route .* does not match the shipped CMC row/);
  assert.match(verifier, /Ondo source capture SHA-256 does not match/);
  assert.match(verifier, /1 GOOGLon = 1\.0025 GOOGL/);
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
  assert.match(integritySource, /window\.BellAlphabetClassScopeSentence = alphabetClassScopeSentence/);
  assert.match(explorer, /window\.BellAlphabetClassScopeSentence\?\.\(row\)/);
  assert.match(explorer, /class="explorer-live-scope"/);
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
  assert.match(integrity, /comparison_exclusion_reasons/);
  assert.match(integrity, /included_crypto_ids/);
  assert.match(integrity, /excluded_crypto_ids/);
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
  assert.match(integrity, /bell\.case-receipt\.v3/);
  assert.match(integrity, /receipt_id: receiptId/);
  assert.match(integrity, /ruleset: receipt\?\.universe\?\.rules_version/);
  assert.match(integrity, /decision_interpretation: displayDecisionConsequence\(item\)/);
  assert.match(integrity, /if \(!comparison\) \{\s*\/\/ Keep the machine-derived consequence byte-for-byte aligned with the\s*\/\/ rule engine\.[\s\S]*?return \{ \.\.\.decision \};/,
    'reference-specific narrative must not alter the machine-verifiable verdict');
  assert.match(integrity, /comparison: comparisonForCaseReceipt\(item\)/);
  assert.match(integrity, /Download case JSON/);
  assert.match(integrity, /source_hashes: sourceHashes/);
});

test('human-readable and JSON handoffs preserve the comparison set and its rule context', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const verifier = fs.readFileSync(path.resolve(__dirname, '../verify_case_receipt.py'), 'utf8');
  assert.match(integrity, /## Published comparison set/);
  assert.match(integrity, /Included crypto IDs:/);
  assert.match(integrity, /Excluded crypto IDs and reasons:/);
  assert.match(integrity, /Comparison membership/);
  assert.match(integrity, /published_rule_text:/);
  assert.match(integrity, /ruleset_note:/);
  assert.match(verifier, /bell\.case-receipt\.v3/);
  assert.match(verifier, /receipt_id does not match observed_at and source_hashes/);
  assert.match(verifier, /published\.get\("alert_index"\)/);
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


test('capital quote ranges name the exact receipt rows used by the calculation', () => {
  const scope = runFromSource('capitalRangeScope');
  assert.deepEqual(scope({ tokens: [{ price: 10 }, { price: 12 }] }), {
    label: 'OBSERVED ROW QUOTE RANGE',
    note: 'Range uses reported token rows before comparison filters. No filtered comparison is published.',
  });
  assert.deepEqual(scope({ comparison: { routes: [{ crypto_id: 1 }, { crypto_id: 2 }] } }), {
    label: 'FILTERED ROUTE QUOTE RANGE',
    note: 'Capital range uses this receipt’s filtered routes; the separate quote band includes all priced representations.',
  });
  assert.deepEqual(scope({ tokens: [{ price: 10 }], comparison: null }, false), {
    label: '',
    note: 'No quote range is shown; any volume total uses reported token rows. No filtered comparison is published.',
  });
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.equal((integrity.match(/capitalRangeScope\(alert, true\)\.label/g) || []).length, 2,
    'initial render and amount updates must use the same row-scope label');
  assert.match(integrity, /capitalMetricsNote\(assessment\.mode, 'Nominal quote units only\.', alert\?\.token_count, alert,/);
  assert.match(integrity, /capitalMetricsNote\(assessment\.mode, 'Nominal unit counts only\.', alert\?\.token_count, alert,/);
});

test('near-equal quote ratios keep enough precision to remain distinct from equality', () => {
  const formatRatio = runFromSource('formatRatio', { numericValue: value => Number.isFinite(value) ? value : null });
  assert.equal(formatRatio(1), '1');
  assert.equal(formatRatio(1.00195), '1.00195');
  assert.equal(formatRatio(1.017), '1.02');
  assert.equal(formatRatio(31.17), '31.17');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.equal((integrity.match(/formatRatio\((?:assessment\.metrics|metrics)\.ratio\)/g) || []).length, 2,
    'initial and updated capital panels must preserve near-equal ratio precision');
  assert.match(integrity, /OBSERVED QUOTE BAND<\/span><b>\$\{formatRatio\(band\.ratio\)\}×/,
    'the all-representation quote band must preserve the same precision');
  assert.match(integrity, /Observed range: \$\{capital\.metrics\?\.ratio \? `\$\{formatRatio\(capital\.metrics\.ratio\)\}×/,
    'the downloaded decision brief must preserve the same precision');
  assert.match(integrity, /RECEIPT OBSERVED · \$\{escapeHTML\(observedAt \|\| 'time unavailable'\)\} UTC/,
    'the capital panel must identify when its displayed metrics were observed');
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
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /function displayDecisionConsequence/);
  assert.match(integrity, /equivalent units and claims are not established/);
  assert.match(integrity, /highest reported 24h volume/);
  assert.match(explorer, /representations with reported price and 24h volume/);
  assert.doesNotMatch(explorer, /tradable representations/);
  assert.match(integrity, /reported-field inconsistency, not proof that no market exists/);
  assert.match(integrity, /checked by crypto_id/);
  assert.match(page, /A shared CMC reference does not establish equivalent units, claims or executable markets/);
  assert.match(page, /COMPARABLE = FILTERED PRICE COMPARISON/);
  assert.match(page, /observed spread and 24h volume; units and economic claims remain unverified/);
  assert.doesNotMatch(page, /COMPARABLE = PRICES LINE UP|depth published/);
  assert.match(page, /whether the cheapest route also has the highest reported 24h volume/);
  assert.doesNotMatch(page, /whether the cheapest route is also the deepest/);
});

test('hero search lands on the result it just generated', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /const target = window\.matchMedia/);
  assert.match(integrity, /target\?\.scrollIntoView/);
  assert.match(integrity, /matchMedia\('\(max-width: 900px\)'\)/);
  assert.match(integrity, /byId\('decision'\)/);
  assert.match(integrity, /updateWorkspaceHandoff\(query\.toLowerCase\(\)\)/);
  const referenceId = runFromSource('workspaceReferenceId');
  assert.equal(referenceId('tesla', [{ rwa_id: 14, name: 'Tesla, Inc.' }]), '14');
  assert.equal(referenceId('silver', [
    { rwa_id: 5, name: 'Silver' }, { rwa_id: 99, name: 'Silver Token' },
  ]), '5');
  assert.equal(referenceId('silver', [
    { rwa_id: 5, name: 'Silver Token' }, { rwa_id: 6, name: 'Silver Wrapped' },
  ]), '');
  assert.equal(referenceId('tesla', []), '');
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
  const routes = new Set(['/', '/judge', '/workspace']);
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

test('the headline uses one current receipt and keeps the historical rate separate', () => {
  const index = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  // Do not make a visitor reconcile a frozen base rate with the current scan
  // before they can understand Bell's first result.
  assert.match(integrity, /async function renderFinding/);
  assert.match(integrity, /base-rate-[0-9]{4}-[0-9]{2}-[0-9]{2}\.json/);
  assert.match(integrity, /Current CMC receipt observed \$\{receiptStamp\}/);
  assert.match(integrity, /filtered quote comparison/);
  assert.match(index, /<details class="historical-base-rate">/);
  assert.match(index, /Historical base rate · 21 September/);
  assert.match(index, /id="finding-headline"/);
  assert.match(index, /id="finding-lede"/);
  // No percentage, interval or count may be hardcoded in the hero copy.
  const hero = index.slice(index.indexOf('id="finding-headline"'), index.indexOf('hero-search-form'));
  assert.doesNotMatch(hero, /\d+\.\d+\s*%/);
  assert.doesNotMatch(hero, /95%\s*interval\s*\d/);
});

test('filtered route comparisons expose the instrument name beside ticker and issuer', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const styles = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(integrity, /comparison-route-name/);
  assert.match(integrity, /route\.name \|\| 'Instrument name not supplied'/);
  assert.match(integrity, /\[low\.name, low\.issuer_name\]/);
  assert.match(styles, /\.comparison-route-name[^}]*white-space:normal/);
});

test('comparison evidence is attached to exact token IDs and flags the Alphabet class mismatch', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const evidence = fs.readFileSync(path.join(site, 'issuer-evidence.js'), 'utf8');
  const styles = fs.readFileSync(path.join(site, 'integrity.css'), 'utf8');
  const overrides = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  const explorer = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');
  const browserAudit = fs.readFileSync(path.resolve(__dirname, '../verify_public_browser.py'), 'utf8');
  assert.match(integrity, /issuerEvidenceMarkup\(item, c\.routes\)/);
  assert.match(integrity, /const rows = c\.routes\.map\(route =>/);
  assert.match(integrity, /catalogue\[String\(route\.crypto_id\)\]/);
  assert.match(integrity, /tokenById\.get\(String\(route\.crypto_id\)\)/);
  assert.match(integrity, /CMC contracts · \$\{platforms\.length\} networks/);
  assert.match(integrity, /Share-class mismatch/);
  assert.match(integrity, /alphabetClassScopeSentence\(item\)/);
  assert.match(integrity, /CMC-GROUPED QUOTE SPREAD · CLASS A \+ C/);
  assert.match(integrity, /the displayed spread therefore combines Class A and Class C routes, not one share class/);
  assert.match(integrity, /classScope \? `<p class="share-class-scope">/);
  assert.match(styles, /\.search-result \.share-class-scope/);
  assert.match(integrity, /window\.BellAlphabetClassScopeSentence = alphabetClassScopeSentence/);
  assert.match(explorer, /window\.BellAlphabetClassScopeSentence\?\.\(row\)/);
  assert.match(explorer, /class="explorer-live-scope"/);
  assert.match(browserAudit, /class_scope_expectation in search_summary/);
  assert.match(browserAudit, /class_scope_expectation in explorer_text/);
  assert.match(browserAudit, /this observation has no published filtered quote set/);
  assert.match(integrity, /CMC groups GOOGon \(Alphabet Class C\) under its Class A reference/);
  assert.match(integrity, /byId\('hero-mobile-note'\)\.textContent = alphabetClassScopeSentence\(alert\)/);
  assert.match(integrity, /pairReviewMarkup\(item, tokenRowsFor\(item\)\)\}\$\{capitalPanel\(item\)\}\$\{observedQuoteEndpoints\(item\)\}/);
  assert.match(page, /data-example-search="Alphabet"/);
  assert.doesNotMatch(integrity.slice(integrity.indexOf('function renderComparison(item)'), integrity.indexOf('function comparisonRouteSet')), /pairReviewMarkup/);
  assert.match(evidence, /window\.BELL_INSTRUMENT_EVIDENCE/);
  assert.match(evidence, /'37013'/);
  assert.match(evidence, /'42272'/);
  assert.match(evidence, /'40757'/);
  assert.match(evidence, /Alphabet Class C/);
  assert.match(evidence, /docs\.ondo\.finance\/ondo-stocks\/overview/);
  assert.match(evidence, /docs\.robinhood\.com\/chain\/stock-tokens/);
  assert.doesNotMatch(evidence, /robinhood\.com\/eu\/en\/crypto\/GOOGL/);
  assert.match(evidence, /Final Terms checked/);
  assert.match(integrity, /Issuer terms not mapped for \$\{unmapped\.length\} included route/);
  assert.match(integrity, /if \(!documented\.length && !classMismatch\) return ''/);
  assert.match(integrity, /Equivalent units and claims are not established/);
  assert.match(integrity, /token-specific issuer-source notes/);
  const comparison = integrity.slice(integrity.indexOf('function renderComparison'), integrity.indexOf('function comparisonRouteSet'));
  assert.ok(comparison.indexOf('${scopeNotice}') < comparison.indexOf('<div class="comparison-head">'),
    'the unit/claim boundary must be visible before the quote spread');
  assert.match(overrides, /\.comparison-scope-notice/);
});

test('mobile decision preview opens the exact rendered case card', () => {
  const index = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  const styles = fs.readFileSync(path.join(site, 'visual-overrides.css'), 'utf8');
  assert.match(index, /id="hero-mobile-decision"[\s\S]*href="#decision-hero"/);
  assert.match(index, /id="decision-hero"/);
  assert.match(styles, /\.decision-hero\{scroll-margin-top:80px\}/);
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
  assert.match(integrity, /decisionBucket\(item, 'FACTS OPEN'\) === filter/);
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
    'market_cap_status', 'in_published_comparison', 'comparison_exclusion_reasons', 'premium_to_cheapest_bps']);

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
  assert.match(integrity, /liveComparable\.toLocaleString\(\)/);
  assert.match(integrity, /This is a separate, historical population measurement, not today's receipt/);
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
  assert.match(page, /COMPARABLE = FILTERED PRICE COMPARISON/);
  const key = page.indexOf('OUTCOME KEY');
  const affirmative = page.indexOf('COMPARABLE = FILTERED PRICE COMPARISON');
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
  // and then reader-chosen, so this pins the DEFAULT rather than the keyword
  // it is declared with. An earlier version matched `const pageSize` exactly
  // and went red the moment the reader was allowed to change it, which is a
  // test failing on how a line is spelled rather than on what it does.
  // The default moved to its own binding when the URL was allowed to carry a
  // chosen size, so the default is what this reads.
  const sizes = (integrity.match(/\b(?:const|let|var) defaultPageSize = [^;]+;/)
    || integrity.match(/\b(?:const|let|var) pageSize = [^;]+;/) || [])[0];
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
  // 4 a page over 792 references is 198 pages. The default stays small because
  // these are full evidence cards, so the reader has to be able to raise it and
  // to jump, or the index is only navigable through the CSV.
  const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  assert.match(page, /id="alert-page-size"/, 'the reader cannot change the page size');
  assert.match(integrity, /id="alert-page-jump"/, 'there is no way to jump to a page');
  assert.match(integrity, /aria-label="Last population page"/, 'there is no way to reach the end');
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

function runWorkspaceFromSource(name, deps = {}) {
  const src = fs.readFileSync(path.join(site, 'workspace.js'), 'utf8');
  const at = src.indexOf(`function ${name}(`);
  assert.ok(at > 0, `${name} no longer exists in workspace.js`);
  let depth = 0, i = src.indexOf('{', at), end = i;
  for (; i < src.length; i++) {
    if (src[i] === '{') depth++;
    else if (src[i] === '}' && --depth === 0) { end = i; break; }
  }
  const names = Object.keys(deps);
  return new Function(...names, `return ${src.slice(at, end + 1)}`)(...names.map(key => deps[key]));
}

test('workspace labels the published decision and marks its exact comparison rows', () => {
  const label = runWorkspaceFromSource('displayDecisionLabel');
  const membership = runWorkspaceFromSource('comparisonMembership');
  const counts = runWorkspaceFromSource('comparisonCounts', { comparisonMembership: membership });
  const sources = runWorkspaceFromSource('tokenSourceLinks', {
    safeExternalURL: runWorkspaceFromSource('safeExternalURL'),
    escape: value => String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    })[char]),
  });
  const decisionCopy = runWorkspaceFromSource('workspaceDecisionCopy', {
    comparisonCounts: counts,
    nextSteps: { no_flags: 'Review the published fields.' },
  });
  const brief = runWorkspaceFromSource('reviewBrief', {
    comparisonCounts: counts,
    comparisonMembership: membership,
    displayDecisionLabel: label,
    safeExternalURL: runWorkspaceFromSource('safeExternalURL'),
    number: value => String(value ?? '—'),
    money: value => Number.isFinite(Number(value)) ? `$${Number(value).toFixed(2)}` : '—',
    location: { origin: 'https://bell.dyplux.com' },
    nextSteps: { no_flags: 'Review the filtered quote rows.' },
  });
  assert.equal(label({ state: 'no_flags', token_count: 6, comparison: { route_count: 6 } }), 'COMPARABLE');
  assert.equal(label({ state: 'investigate', token_count: 3, comparison: { route_count: 2 } }), 'COMPARABLE · FLAGGED');
  assert.equal(label({ state: 'do_not_compare', decision: { state: 'blocked' }, token_count: 4,
    comparison: { route_count: 2 } }), 'DO NOT SHORTLIST');
  assert.deepEqual(membership({ comparison: { included_crypto_ids: [101], excluded_crypto_ids: [
    { crypto_id: 202, reasons: ['derivative_label'] },
  ] } }, { crypto_id: 101 }), { label: 'Included', reason: 'Included in filtered quote comparison' });
  assert.deepEqual(membership({ comparison: { included_crypto_ids: [101], excluded_crypto_ids: [
    { crypto_id: 202, reasons: ['derivative_label'] },
  ] } }, { crypto_id: 202 }), { label: 'Excluded', reason: 'derivative label' });
  assert.deepEqual(counts({
    representations: [{ crypto_id: 101 }, { crypto_id: 202 }, { crypto_id: 303 }],
    comparison: { routes: [{ crypto_id: 101 }], included_crypto_ids: [101] },
  }), { included: 1, excluded: 2 });
  const calibrated = decisionCopy({
    state: 'no_flags',
    decision: { consequence: '6 representations share a unit and a market state.' },
    representations: [{ crypto_id: 101 }, { crypto_id: 202 }, { crypto_id: 303 }],
    comparison: { included_crypto_ids: [101], spread_bps: 22.2 },
  });
  assert.match(calibrated, /1 representation row passed Bell's published quote filters/);
  assert.match(calibrated, /Observed spread: 22\.2 bps/);
  assert.match(calibrated, /not evidence of equivalent units or economic rights/);
  assert.doesNotMatch(calibrated, /share a unit/);
  assert.equal(decisionCopy({ state: 'do_not_compare', decision: { consequence: 'Resolve the unit.' } }), 'Resolve the unit.');
  const sourceHTML = sources({
    cmc_url: 'https://coinmarketcap.com/currencies/tesla-xstock/',
    project_url: 'https://assets.backed.fi/products/tesla-xstock',
    technical_doc_urls: [],
    explorer_urls: [
      'https://assets.backed.fi/research/tesla.pdf',
      'https://arbiscan.io/token/0x123',
      'javascript:alert(1)',
    ],
  });
  assert.match(sourceHTML, /CMC-reported sources/);
  assert.match(sourceHTML, /assets\.backed\.fi\/products\/tesla-xstock/);
  assert.match(sourceHTML, /Document ↗/);
  assert.match(sourceHTML, /Explorer ↗/);
  assert.match(sourceHTML, /rel="noopener noreferrer"/);
  assert.doesNotMatch(sourceHTML, /javascript:/);
  assert.equal(sources({ explorer_urls: ['javascript:alert(1)'] }), '');
  const savedBrief = brief({
    rwa_id: 77, name: 'Example Inc', asset_type: 'stock', state: 'no_flags',
    token_count: 3, issuer_count: 2,
    representations: [
      { crypto_id: 101, symbol: 'EX', name: 'Example (xStock)', issuer_name: 'Issuer A', price: 12.5,
        market_cap: 1000, volume_24h: 25, cmc_url: 'https://coinmarketcap.com/currencies/example/',
        project_url: 'https://issuer.example/project', technical_doc_urls: [
          'https://issuer.example/docs.pdf', 'https://issuer.example/docs-2.pdf', 'https://issuer.example/docs-3.pdf',
        ], explorer_urls: ['https://scan.example/token/101', 'https://scan.example/token/102'] },
      { crypto_id: 202, symbol: 'EX', name: 'Example Derivative', issuer_name: 'Issuer B', price: 13,
        project_url: 'https://issuer.example/project?filter=a|b',
        market_cap: 2000, volume_24h: 50 },
      { crypto_id: 303, symbol: 'EX|2', name: 'Example Third', issuer_name: 'Issuer C' },
    ],
    comparison: { included_crypto_ids: [101], excluded_crypto_ids: [
      { crypto_id: 202, reasons: ['derivative_label'] }, { crypto_id: 303, reasons: ['no_quote'] },
    ], spread_bps: 22.2 },
    next_action: 'Check issuer terms.',
  }, '2026-09-29T12:00:00Z');
  assert.match(savedBrief, /# Bell review brief: Example Inc/);
  assert.match(savedBrief, /- Observed spread: 22\.2 bps/);
  assert.match(savedBrief, /1 included; 2 excluded/);
  assert.match(savedBrief, /Check issuer terms\./);
  assert.match(savedBrief, /\| 101 \| EX — Example \(xStock\) \| Issuer A \| Included \| \$12\.50 \| \$1000\.00 \| \$25\.00 \|/);
  assert.match(savedBrief, /\| 202 \| EX — Example Derivative \| Issuer B \| Excluded: derivative label/);
  assert.match(savedBrief, /\| EX\\\|2 — Example Third \| Issuer C \|/);
  assert.match(savedBrief, /\[CMC\]\(<https:\/\/coinmarketcap\.com\/currencies\/example\/>\)/);
  assert.match(savedBrief, /\[Project\]\(<https:\/\/issuer\.example\/project>\)/);
  assert.match(savedBrief, /\[Document\]\(<https:\/\/issuer\.example\/docs\.pdf>\)/);
  assert.match(savedBrief, /\[Document\]\(<https:\/\/issuer\.example\/docs-3\.pdf>\)/);
  assert.match(savedBrief, /\[Explorer\]\(<https:\/\/scan\.example\/token\/101>\)/);
  assert.match(savedBrief, /\[Explorer\]\(<https:\/\/scan\.example\/token\/102>\)/);
  assert.match(savedBrief, /\[Project\]\(<https:\/\/issuer\.example\/project\?filter=a%7Cb>\)/);
  assert.match(savedBrief, /Source URLs are reported by CMC/);
  assert.match(savedBrief, /https:\/\/bell\.dyplux\.com\/\?reference=77#decision/);
  const singleBrief = brief({
    rwa_id: 78, name: 'Single Wrapper', asset_type: 'stock', state: 'investigate',
    token_count: 1, issuer_count: 1, representations: [{ crypto_id: 404, symbol: 'ONE', name: 'One' }],
  }, '2026-09-29T12:00:00Z');
  assert.match(singleBrief, /Comparison rows: no filtered comparison published/);
  assert.match(singleBrief, /\| 404 \| ONE — One \| — \| No comparison \|/);
  assert.doesNotMatch(singleBrief, /Excluded:/);
});

test('the public label follows the decision, executed not grepped', () => {
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: runFromSource('decisionBucket'),
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });
  // A published comparison outranks the state that let it through, and says
  // when it did. 39 of the 75 comparisons in the live receipt were published
  // over a flagged reference and all of them read plainly COMPARABLE: the
  // affirmative word over the most doubtful half of the affirmative set. The
  // flags were always on the card; a reviewer had to do arithmetic against
  // /api/integrity to see the split.
  assert.equal(label({ state: 'investigate', comparison: { route_count: 3 } }), 'COMPARABLE \u00b7 FLAGGED');
  assert.equal(label({ state: 'no_flags', comparison: { route_count: 2 } }), 'COMPARABLE');
  // A blocked reference is not "flagged", it is refused, and the qualifier
  // must never soften that.
  assert.equal(label({ state: 'investigate', decision: { state: 'blocked' }, comparison: {} }),
    'DO NOT SHORTLIST');
  // A blocked reference is never labelled comparable, even with a comparison.
  assert.equal(label({ state: 'do_not_compare', comparison: { route_count: 5 } }), 'DO NOT SHORTLIST');
  // One representation is not a comparison.
  assert.equal(label({ state: 'no_flags', token_count: 1 }), 'SINGLE REPRESENTATION');
  // One representation is not a comparison, whatever the scan flagged about it.
  // Two references carried one row and a do_not_compare state and were told
  // "a research desk must not rank or substitute these representations": the
  // comparison vocabulary where no comparison exists, which is the error this
  // product reports about somebody else's catalogue. They also made the
  // SINGLE REPRESENTATION filter return 545 beside prose saying 547.
  assert.equal(label({ state: 'do_not_compare', token_count: 1 }),
    'SINGLE REPRESENTATION \u00b7 FLAGGED');
  assert.equal(label({ state: 'investigate', token_count: 1 }),
    'SINGLE REPRESENTATION \u00b7 FLAGGED');
  assert.equal(label({ state: 'do_not_compare', token_count: 4 }), 'DO NOT SHORTLIST');
  assert.equal(label({ state: 'no_flags', token_count: 4 }), 'FACTS OPEN');
  assert.equal(label({ state: 'investigate' }), 'INVESTIGATE');
  // Every label it can return must be in the published vocabulary.
  const vocabulary = new Set(['COMPARABLE', 'COMPARABLE \u00b7 FLAGGED', 'DO NOT SHORTLIST', 'INVESTIGATE', 'FACTS OPEN', 'SINGLE REPRESENTATION', 'SINGLE REPRESENTATION \u00b7 FLAGGED']);
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
  assert.match(integrity, /\b(?:const|let) defaultPageSize = window\.matchMedia\('\(max-width: 760px\)'\)\.matches \? 2 : 4;/,
    'the phone default is no longer two cards');
  // Fewer cards is only acceptable because nothing becomes unreachable: the
  // pager, the search and every state filter still cover the whole population.
  assert.match(integrity, /Math\.ceil\(matching\.length \/ pageSize\)/);
  // 4 a page over 792 references is 198 pages. The default stays small because
  // these are full evidence cards, so the reader has to be able to raise it and
  // to jump, or the index is only navigable through the CSV.
  const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  assert.match(page, /id="alert-page-size"/, 'the reader cannot change the page size');
  assert.match(integrity, /id="alert-page-jump"/, 'there is no way to jump to a page');
  assert.match(integrity, /aria-label="Last population page"/, 'there is no way to reach the end');
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

  // The label may carry a qualifier - COMPARABLE · FLAGGED - and this test is
  // about which reference is named and whether it carries a comparison. The
  // exact printed word is pinned by
  // "the judge page promises the words the product prints for its two examples".
  const affirmative = judge.match(
    /<li><strong>([^<]+)<\/strong> returns <strong>COMPARABLE(?:[^<]*)<\/strong>/);
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

  // The page does not just say the reference is blocked, it names the rule that
  // blocked it: "above the inclusive 10x block floor". Asserting the state alone
  // left that name unguarded, and a judge reading a rule attributed to the wrong
  // signal is reading a claim the code does not make. Proved the gap by
  // flattening the prices until PRICE_DENOMINATION_BREAK stopped firing: the
  // reference stayed blocked on ZERO_MCAP_POSITIVE_VOLUME and this suite stayed
  // green. So read the rule out of the sentence and require it to be the one
  // that actually fired.
  const named = judge.match(/<li><strong>[^<]+<\/strong> returns <strong>DO NOT SHORTLIST<\/strong>:([\s\S]*?)<\/li>/);
  assert.ok(named, 'the refusal example no longer explains which rule fired');
  const RULE_PHRASES = [
    [/10x block floor/, 'PRICE_DENOMINATION_BREAK'],
    [/traded volume against a zero market cap|zero market cap/, 'ZERO_MCAP_POSITIVE_VOLUME'],
  ];
  const codes = (blocked.signals || blocked.signal_codes || []).map(
    signal => (typeof signal === 'string' ? signal : signal.code));
  const claimed = RULE_PHRASES.filter(([phrase]) => phrase.test(named[1]));
  assert.ok(claimed.length,
    `the judge page describes a rule this test cannot map to a signal code: ${named[1].trim().slice(0, 160)}`);
  for (const [, code] of claimed) {
    assert.ok(codes.includes(code),
      `the judge page attributes ${refusal[1]}'s refusal to ${code}, but the shipped replay fired ${JSON.stringify(codes)}`);
  }
});

test('nothing claims to be current while the page is reading a dated receipt', () => {
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const explorerSrc = fs.readFileSync(path.join(site, 'explorer.js'), 'utf8');

  // The first version of this test asserted one chip. That is one instance of a
  // rule, not the rule, and three other places kept asserting currency over a
  // five-day-old replay: the population lens chip, the strip's scope sentence
  // and the explorer's verdict header. Assert the rule.
  // matchAll below needs the /g, and `test()` on a global regex advances
  // lastIndex: after the integrity.js call it sat at 50977, past
  // explorer.js's entire 22,120 bytes, so `claims.test(explorerSrc)`
  // returned false and the loop skipped a file that really does contain
  // CURRENT VERDICT. Half of a rule, in a block whose own comment says
  // 'that is one instance of a rule, not the rule'. Reset it per source.
  const claims = /CURRENT RECEIPT|CURRENT VERDICT|current scan|latest scan/g;
  const inMarkup = [...page.matchAll(claims)].map(match => match[0]);
  assert.deepEqual(inMarkup, [],
    `markup hard-codes a currency claim the page cannot honour on a dated receipt: ${inMarkup}`);

  // Each of those strings may exist only in code that has read publication.source.
  for (const [label, source] of [['integrity.js', integrity], ['explorer.js', explorerSrc]]) {
    claims.lastIndex = 0;
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
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: runFromSource('decisionBucket'),
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });

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
    if (promised.trim().toLowerCase() === 'pair review') {
      assert.equal(String(match[1].rwa_id), '4', 'the pair-review shortcut must resolve the featured Alphabet case');
      assert.match(integrity, /pairReviewMarkup\(item, tokenRowsFor\(item\)\)/,
        'the Alphabet shortcut must show the pair review with its searched case');
      continue;
    }
    const printed = label(match[1]);
    // The chips use the shorthand the page's own outcome key defines, so
    // resolve through that key rather than comparing strings letter for letter.
    const shorthand = {
      blocked: 'DO NOT SHORTLIST',
      investigate: 'INVESTIGATE',
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
      .matchAll(/"(\/v\d\/[a-z0-9/_-]+)"/g)) {
      // A trailing slash is a base path the code concatenates onto, not an
      // endpoint. bell/list_endpoints.py had the same bug and counted 18 and 8;
      // adding that file, which holds the family prefix as a constant, made
      // this count 8 too. Two implementations of one rule, wrong the same way.
      if (endpoint.endsWith('/')) continue;
      called.add(endpoint);
    }
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
  assert.match(integrity, /decisionBucket\(item, 'FACTS OPEN'\) === filter/);
  assert.doesNotMatch(integrity, /item\.state === filter/,
    'a filter went back to matching the raw state');

  // Every published label needs a button, or a reader cannot reach 545 of the
  // 791 references. SINGLE REPRESENTATION had none.
  //
  // The property is REACHABILITY, so it is asserted on the bucket a filter
  // addresses rather than on the printed label. A label may carry a qualifier
  // the filter deliberately ignores - COMPARABLE · FLAGGED is gathered by the
  // COMPARABLE button on purpose, because a reader after the comparable set
  // should not have to know there are two names for it - and that must not be
  // mistaken for a label nobody can reach.
  const buttons = [...page.matchAll(/data-filter="([^"]+)"/g)].map(match => match[1]);
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: runFromSource('decisionBucket'),
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const bucket = runFromSource('decisionBucket');
  const produced = new Set((replay.alert_index || []).map(item => bucket(item, 'FACTS OPEN')));
  for (const word of produced) {
    assert.ok(buttons.includes(word), `the scan produces ${word} and no filter offers it`);
  }
  // And every printed label still has to resolve to one of those buckets, so a
  // new label cannot appear with nothing gathering it.
  for (const printed of new Set((replay.alert_index || []).map(item => label(item, 'FACTS OPEN')))) {
    assert.ok(buttons.some(button => printed.startsWith(button)),
      `the scan prints ${printed} and no filter gathers it`);
  }
  // And the buttons must partition it: every one is a label, none is a state.
  for (const button of buttons.filter(value => value !== 'all')) {
    assert.ok(produced.has(button), `the filter bar offers ${button}, which the scan never produces`);
  }
});

test('the outcome key enumerates every state the product can print', () => {
  // The key listed four of five. INVESTIGATE was missing while carrying a
  // filter button, 47 live badges and a place in the vocabulary
  // verify_submission.py declares. A reader met the word on a card with no
  // definition anywhere above it.
  const key = page.match(/<div class="outcome-key"[\s\S]*?<\/details>\s*<\/div>/);
  assert.ok(key, 'the outcome key went missing');
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: runFromSource('decisionBucket'),
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });
  const produced = new Set((replay.alert_index || []).map(item => label(item, 'FACTS OPEN')));
  for (const word of produced) {
    assert.ok(key[0].includes(word), `the scan prints ${word} and the outcome key never defines it`);
  }
});

test('the judge page states the number of API findings the document holds', () => {
  // The contract findings are the one artefact reviewers called value returned
  // to CMC, and the page did not mention them. A count on a page has to be the
  // count in the file, like every other number here.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');
  const doc = fs.readFileSync(path.resolve(__dirname, '../API-FEEDBACK.md'), 'utf8');
  const findings = (doc.match(/^## \d+\./gm) || []).length;
  assert.ok(findings >= 6, 'the API feedback document lost its numbered findings');
  const words = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight',
    'Nine', 'Ten', 'Eleven', 'Twelve'];
  assert.match(judge, new RegExp(`${words[findings]} API contract findings`, 'i'),
    `the document holds ${findings} findings and the judge page says otherwise`);
});

test('the panels say they count scan states, not card labels', () => {
  // The population panel reports INVESTIGATE 90 and FACTS OPEN 666 from the raw
  // scan states while the filters report 47 and 77 from the decision labels.
  // Both are right about different questions, and a reader meeting 90 and 47 on
  // one screen has no way to know that. Same shape as the 547 vs 545 note.
  assert.match(page, /Scan states, not card labels/);
  assert.match(page, /the state that let it through/);
});

test('a receipt past its freshness contract can say STALE', () => {
  // The recomputation existed and was assigned to a local nothing read, while
  // the chip printed the cached `status`. A reviewer saw "PUBLISHED 10H AGO"
  // and "FRESH" four lines apart. Dead code is not a fix, so this drives the
  // shared function and requires it to be able to say both words.
  const freshness = runFromSource('freshnessStatus');
  const now = Date.now();
  const inside = new Date(now - 60_000).toISOString();
  const outside = new Date(now - 10 * 3600_000).toISOString();

  assert.equal(freshness({ status: 'fresh', published_at: inside, stale_after_seconds: 900 }),
    'fresh', 'a receipt inside its window is not fresh');
  assert.equal(freshness({ status: 'fresh', published_at: outside, stale_after_seconds: 900 }),
    'stale', 'a receipt ten hours past a 900 second contract still says fresh');
  // The exact shape a reviewer was served: published inside the window, so the
  // worker cached "fresh", read much later by a page that stayed open.
  assert.equal(freshness({ status: 'fresh', published_at: outside, stale_after_seconds: 900,
    age_seconds: 884 }), 'stale', 'the cached age_seconds overrode the real clock');
  // Not a blanket downgrade: a receipt that never claimed freshness keeps its
  // own word, and a dated replay is not silently relabelled.
  assert.equal(freshness({ status: 'dated', published_at: outside, stale_after_seconds: 900 }),
    'dated');
  assert.equal(freshness(null), 'UNKNOWN');

  // And the chip must read it, not the cached field. That was the actual bug.
  const source = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.doesNotMatch(source, /String\(publication\.status\)\.toUpperCase\(\)/,
    'the decision receipt chip went back to printing the cached status');
});

test('a stale dossier distinguishes queued refreshes from declined work', () => {
  assert.match(explorer, /publication\.refresh_deduplicated/);
  assert.match(explorer, /a refresh is already queued/);
  assert.match(explorer, /publication\.refresh_declined/);
  assert.match(explorer, /refresh not queued/);
  assert.match(explorer, /no refresh is queued/);
});

test('a per-reference change view never reads an absent field as a difference', () => {
  // The first version of this feature compared `signal_codes` against an
  // `alerts[]` item, which carries `signals: [{code}]` instead. Undefined was
  // read as empty and every reader was told every rule had stopped firing -
  // absence reported as a value, inside the feature that reports change, in a
  // product whose whole subject is that absence is not zero.
  const codes = runFromSource('signalCodesOf');
  assert.deepEqual(codes({ signal_codes: ['B', 'A'] }), ['A', 'B'],
    'the flat alert_index shape is not read');
  assert.deepEqual(codes({ signals: [{ code: 'B' }, { code: 'A' }] }), ['A', 'B'],
    'the alerts[] object shape is not read');
  assert.deepEqual(codes({ signals: [] }), [], 'an empty list is a real empty list');
  assert.equal(codes({}), null, 'a record with no signal field must be absent, not empty');
  assert.equal(codes(null), null);

  // And the comparison must refuse rather than invent when one side is absent.
  const describe = runFromSource('describeChange', { signalCodesOf: codes, displayDecisionLabel: () => 'FACTS OPEN' });
  const refused = describe({ state: 'no_flags', representations: 2 }, { state: 'no_flags', token_count: 2 });
  assert.ok(refused.some(([label, value]) => label === 'RULES' && /not compared/.test(value)),
    'a missing signal list produced a change instead of a refusal');
  const real = describe(
    { state: 'no_flags', representations: 2, signal_codes: ['A'] },
    { state: 'no_flags', token_count: 2, signals: [{ code: 'B' }] });
  assert.deepEqual(real.map(([label]) => label), ['RULES NOW FIRING', 'RULES NO LONGER FIRING'],
    'a real signal change is not reported');
});

test('the reference snapshot is the dated receipt, and carries its rule set', () => {
  // A change view whose two sides answer to different rules states a rule
  // change as a market change. The snapshot has to carry the version so the
  // page can refuse that, and it has to actually be the dated receipt.
  const proof = path.join(site, 'proof');
  const snapshot = JSON.parse(fs.readFileSync(path.join(proof, 'reference-snapshot-2026-09-21.json'), 'utf8'));
  const replay = JSON.parse(fs.readFileSync(
    path.join(proof, 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  assert.equal(snapshot.observed_at, replay.observed_at, 'the snapshot is not the dated receipt');
  assert.equal(snapshot.rules_version, replay.universe.rules_version,
    'the snapshot records a rule set the receipt does not');
  assert.ok(snapshot.rules_version, 'the snapshot records no rule set, so no diff can be refused');
  assert.equal(Object.keys(snapshot.references).length, replay.alert_index.length,
    'the snapshot covers fewer references than the receipt it came from');

  // This was a spot-check over the first 40 of 791, and it did not look at
  // signal_codes even inside the 40. A reviewer tampered entry 200 and a
  // signal list inside the slice, and the full gate stayed green - so the
  // newest feature rested on a file nothing re-derived. Re-derive all of it,
  // the way test_transport_summary.py already does for the transport record.
  const derived = {};
  for (const item of replay.alert_index) {
    const key = String(item.rwa_id ?? '').trim();
    if (!key) continue;
    derived[key] = {
      state: item.state,
      representations: Number(item.token_count ?? 0),
      comparison_published: Boolean(item.comparison),
      signal_codes: [...(item.signal_codes ?? [])].sort(),
    };
  }
  assert.deepEqual(snapshot.references, derived,
    'the committed reference snapshot is not what the extractor produces from the receipt');
  // It must stay small enough to sit beside the live receipt.
  const bytes = fs.statSync(path.join(proof, 'reference-snapshot-2026-09-21.json')).size;
  assert.ok(bytes < 200_000, `the snapshot grew to ${bytes} bytes; it exists to avoid the 3.42 MiB receipt`);
});

test('the single-representation count the prose states is the count its filter returns', () => {
  // The hero said 547 carry a single representation; the filter beside it
  // returned 545, because two of them were bucketed DO NOT SHORTLIST. A reader
  // filtering for single-representation references silently lost exactly the
  // two the scanner had something to say about.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const bucket = runFromSource('decisionBucket');
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const index = replay.alert_index || [];
  const singles = index.filter(item => Number(item.token_count) === 1);
  const bucketed = index.filter(item => bucket(item, 'FACTS OPEN') === 'SINGLE REPRESENTATION');
  assert.equal(bucketed.length, singles.length,
    `${singles.length} references carry one representation and the filter gathers ${bucketed.length}`);
  assert.ok(singles.length > 0, 'the replay has no single-representation references to check');
  // And the flagged ones are still visibly flagged rather than quietly folded in.
  const flagged = singles.filter(item => item.state !== 'no_flags');
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: bucket,
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });
  for (const item of flagged) {
    assert.match(label(item, 'FACTS OPEN'), /FLAGGED$/,
      `${item.name} has one representation and a scan flag and reads as unflagged`);
  }
});

test('the reference index puts its own view in the URL and reads it back', () => {
  // "Here is the view I was looking at" could not be sent: sort, filter, page
  // size and page number all left the address bar reading the bare origin,
  // while ?reference= and ?map_reference= - the two a reader reaches by
  // accident - were shareable. For a tool whose pitch is a defensible handoff
  // that is the wrong way round.
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.match(integrity, /const INDEX_STATE = \['state', 'sort', 'size', 'page'\]/,
    'the index no longer names the state it shares');

  // Written on every control, not just the one that was easiest to reach.
  const writes = (integrity.match(/rememberIndexState\(\)/g) || []).length;
  assert.ok(writes >= 6,
    `only ${writes} references to rememberIndexState: a control changes the view without recording it`);

  // Read back on load, or a shared link restores nothing.
  for (const pattern of [/initialURL\.searchParams\.get\('state'\)/,
                         /initialURL\.searchParams\.get\('sort'\)/,
                         /initialURL\.searchParams\.get\('size'\)/,
                         /initialURL\.searchParams\.get\('page'\)/]) {
    assert.match(integrity, pattern, `a shared link's ${pattern} is never read`);
  }
  // And the controls have to show it, or the view is restored while the page
  // says it is on its defaults.
  assert.match(integrity, /function restoreIndexControls\(\)/,
    'a restored view leaves its own controls showing the defaults');
  // replaceState, because a filter change is not a navigation: pushState would
  // make the back button walk a reader out through every filter they tried.
  assert.match(integrity, /window\.history\.replaceState\(\{\}, '', url\)/);
  assert.doesNotMatch(integrity, /history\.pushState/);
});

test('the judge page promises the words the product prints for its two examples', () => {
  // The judge page told a reader to search Coinbase and promised COMPARABLE;
  // the product printed COMPARABLE · FLAGGED. One page asserting what another
  // page prints, with nothing comparing them - the example chips were pinned
  // and this prose was not.
  const judge = fs.readFileSync(path.join(site, 'judge.html'), 'utf8');
  const replay = JSON.parse(fs.readFileSync(
    path.join(site, 'proof', 'rwa-surface-integrity-latest-replay-2026-09-21.json'), 'utf8'));
  const label = runFromSource('displayDecisionLabel', {
    decisionBucket: runFromSource('decisionBucket'),
    isFlaggedComparable: runFromSource('isFlaggedComparable'),
    isFlaggedSingle: runFromSource('isFlaggedSingle'),
  });
  const named = [...judge.matchAll(
    /<li><strong>([^<]+)<\/strong> returns <strong>([^<]+)<\/strong>/g)];
  assert.ok(named.length >= 2, 'the judge page no longer names two worked examples');
  for (const [, name, promised] of named) {
    const item = (replay.alert_index || []).find(row => row.name === name);
    assert.ok(item, `the judge page names ${name}, which the shipped replay does not carry`);
    const printed = label(item, 'FACTS OPEN');
    assert.equal(promised.replace(/&middot;/g, '·').replace(/\s+/g, ' ').trim(), printed,
      `the judge page promises "${promised}" for ${name} and the product prints "${printed}"`);
  }
});

test('a count of one is not printed with a plural', () => {
  // "1 representations · 1 issuers" was on screen for every single-row
  // reference, which is a product that reports other people's surfaces saying
  // two things at once doing it itself.
  const plural = runFromSource('plural', { formatNumber: value => String(value) });
  assert.equal(plural(1, 'representation'), '1 representation');
  assert.equal(plural(0, 'representation'), '0 representations');
  assert.equal(plural(2, 'issuer'), '2 issuers');
  assert.equal(plural(null, 'issuer'), '0 issuers');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  assert.doesNotMatch(integrity, /\$\{formatNumber\([^)]*\)\} representations/,
    'a template still hardcodes the plural after a formatted count');
});

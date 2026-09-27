const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const order = require('../site/index-order.js');

const withSpread = (rwa_id, spread_bps, extra = {}) => ({
  rwa_id, name: `Ref ${rwa_id}`, symbol: `R${rwa_id}`, asset_type: 'stock',
  token_count: 3, issuer_count: 2,
  comparison: { spread_bps, route_count: 3, cheapest_is_deepest: true,
                routes: [{ symbol: `R${rwa_id}A`, issuer_name: 'bStocks', premium_to_cheapest_bps: 0 },
                         { symbol: `R${rwa_id}B`, issuer_name: 'Reality', premium_to_cheapest_bps: spread_bps }] },
  ...extra,
});
const withoutComparison = rwa_id => ({ rwa_id, name: `Ref ${rwa_id}`, symbol: `R${rwa_id}`,
                                       asset_type: 'stock', token_count: 1, issuer_count: 1 });

test('a reference with no published comparison sorts last, not as the tightest', () => {
  // Treating absence as zero would put every unmeasured reference at the top
  // of "tightest spread first" - a clean bill of health for exactly the rows
  // Bell knows least about, which is the error this product reports in other
  // people's surfaces.
  const items = [withSpread(1, 50), withoutComparison(2), withSpread(3, 5)];
  assert.deepEqual(order.orderIndex(items, 'spread-asc').map(i => i.rwa_id), [3, 1, 2]);
  assert.deepEqual(order.orderIndex(items, 'spread-desc').map(i => i.rwa_id), [1, 3, 2]);
});

test('a spread that is not a number is absence, not zero', () => {
  for (const value of [null, undefined, 'tight', NaN, Infinity, {}]) {
    const items = [withSpread(1, 40), { rwa_id: 2, comparison: { spread_bps: value } }];
    assert.deepEqual(order.orderIndex(items, 'spread-asc').map(i => i.rwa_id), [1, 2],
      `spread_bps=${String(value)} was treated as a measurement`);
  }
});

test('severity order is the receipt order, untouched', () => {
  const items = [withSpread(1, 50), withoutComparison(2), withSpread(3, 5)];
  assert.deepEqual(order.orderIndex(items, 'severity').map(i => i.rwa_id), [1, 2, 3]);
  // And it does not mutate what it was given.
  const given = [withSpread(9, 1), withSpread(8, 2)];
  order.orderIndex(given, 'spread-desc');
  assert.deepEqual(given.map(i => i.rwa_id), [9, 8], 'ordering mutated the caller\'s array');
});

test('the export row leaves an unobserved spread empty rather than zero', () => {
  const [row] = [order.exportRow(withoutComparison(7), 'SINGLE REPRESENTATION')];
  const spread = row[order.HEADER.indexOf('observed_spread_bps')];
  assert.equal(spread, '', 'an unobserved spread was exported as a number');
  assert.equal(row[order.HEADER.indexOf('cheapest_is_deepest')], '');
  const measured = order.exportRow(withSpread(8, 12.34), 'COMPARABLE');
  assert.equal(measured[order.HEADER.indexOf('observed_spread_bps')], '12.3');
  assert.equal(measured[order.HEADER.indexOf('cheapest_route_symbol')], 'R8A');
  assert.equal(measured[order.HEADER.indexOf('cheapest_route_issuer')], 'bStocks');
});

test('the page offers every order the module implements, and no other', () => {
  const page = fs.readFileSync(path.join(__dirname, '../site/index.html'), 'utf8');
  const select = page.match(/<select id="alert-sort"[\s\S]*?<\/select>/);
  assert.ok(select, 'the reference index no longer offers an order control');
  const offered = [...select[0].matchAll(/value="([^"]+)"/g)].map(match => match[1]);
  assert.deepEqual(offered.slice().sort(), order.ORDERS.slice().sort(),
    'the control offers an order the module does not implement, or hides one it does');
  assert.match(page, /id="download-index"/);
});

test('the export button writes the list the page is showing', () => {
  // A button that exports something other than what is on screen is the quiet
  // disagreement this product exists to report.
  const source = fs.readFileSync(path.join(__dirname, '../site/integrity.js'), 'utf8');
  assert.match(source, /lastVisibleIndex = matching;/,
    'the index no longer records what it rendered');
  assert.match(source, /lastVisibleIndex\.map\(item =>\s*\n?\s*order\.exportRow/,
    'the export no longer reads the rendered list');
});

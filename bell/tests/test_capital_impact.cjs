const assert = require('node:assert/strict');
const test = require('node:test');
const { budget, quoteRange, quoteBand, volumeMetrics, capitalMetrics, assess } = require('../site/capital-impact.js');

test('quote range ignores missing, zero and negative prices', () => {
  const result = quoteRange([{ price: 0 }, { price: -2 }, { price: null }, { price: 10 }, { price: 20 }]);
  assert.deepEqual(result, { low: 10, high: 20, ratio: 2, gapPercent: 100, count: 2 });
});

test('quote range stays unavailable with fewer than two valid observations', () => {
  assert.equal(quoteRange([{ price: 10 }, { price: null }, { price: 0 }]), null);
});

test('quote band compares each row with the observed median and preserves volume state', () => {
  const result = quoteBand([
    { symbol: 'LOW', price: 90, volume_24h: 0 },
    { symbol: 'MID', price: 100, volume_24h: 12 },
    { symbol: 'HIGH', price: 110, volume_24h: null },
  ]);
  assert.equal(result.median, 100);
  assert.equal(result.ratio, 110 / 90);
  assert.deepEqual(result.rows.map(row => [row.token.symbol, Number(row.deltaPercent.toFixed(2)), row.volumeState]), [
    ['LOW', -10, 'zero'],
    ['MID', 0, 'positive'],
    ['HIGH', 10, 'missing'],
  ]);
});

test('capital metrics make the same budget consequence visible without claiming savings', () => {
  const result = capitalMetrics({ low: 2, high: 10, ratio: 5, gapPercent: 400, count: 2 }, 10000);
  assert.equal(result.unitsAtLowQuote, 5000);
  assert.equal(result.unitsAtHighQuote, 1000);
  assert.equal(result.nominalUnitGap, 4000);
});

test('reported volume comparison makes amount context visible without calling it exit capacity', () => {
  const result = volumeMetrics([{ volume_24h: 900000 }, { volume_24h: 100000 }, { volume_24h: 0 }], 10000);
  assert.equal(result.reportedVolume, 1000000);
  assert.equal(result.positiveRows, 2);
  assert.equal(result.amountSharePercent, 1);
  assert.equal(volumeMetrics([{ volume_24h: null }], 10000), null);
});

test('blocked case turns the proposed amount into a capital hold', () => {
  const result = assess({ state: 'do_not_compare', token_count: 2, tokens: [{ price: 2 }, { price: 20 }] }, 25000);
  assert.equal(result.mode, 'hold');
  assert.equal(result.budget, 25000);
  assert.match(result.headline, /25,000/);
  assert.match(result.copy, /10\.00×/);
  assert.match(result.copy, /not a discount or a proven saving/i);
  assert.equal(result.metrics.volume, null);
});

test('investigate and single-representation cases preserve the boundary', () => {
  assert.equal(assess({ state: 'investigate', token_count: 3 }, 1000).mode, 'review');
  assert.equal(assess({ state: 'no_flags', token_count: 1 }, 1000).mode, 'single');
  assert.match(assess({ state: 'no_flags', token_count: 1 }, 1000).note, /not an approval/i);
});

test('facts-open case surfaces an observed quote gap without calling it executable', () => {
  const result = assess({ state: 'no_flags', token_count: 2, tokens: [{ price: 100 }, { price: 110 }] }, 10000);
  assert.equal(result.mode, 'facts');
  assert.match(result.copy, /10\.00%/);
  assert.match(result.note, /not an executable saving/i);
});

test('published capital comparison uses only the routes in its receipt', () => {
  const result = assess({
    state: 'no_flags',
    token_count: 4,
    tokens: [
      { crypto_id: 1, symbol: 'APPROVED-A', price: 10, volume_24h: 100 },
      { crypto_id: 2, symbol: 'APPROVED-B', price: 20, volume_24h: 300 },
      { crypto_id: 3, symbol: 'EXCLUDED-DERIVATIVE', price: 2, volume_24h: 10000 },
      { crypto_id: 4, symbol: 'EXCLUDED-UNTRADED', price: 200, volume_24h: 0 },
    ],
    comparison: {
      route_count: 2,
      routes: [
        { crypto_id: 1, symbol: 'APPROVED-A', price: 10, volume_24h: 100 },
        { crypto_id: 2, symbol: 'APPROVED-B', price: 20, volume_24h: 300 },
      ],
      spread_bps: 10000,
      cheapest: { symbol: 'APPROVED-A' },
      deepest: { symbol: 'APPROVED-B' },
      cheapest_is_deepest: false,
    },
  }, 10000);
  assert.equal(result.metrics.ratio, 2);
  assert.equal(result.metrics.unitsAtLowQuote, 1000);
  assert.equal(result.metrics.unitsAtHighQuote, 500);
  assert.equal(result.metrics.volume.reportedVolume, 400);
  assert.match(result.copy, /equivalent units and claims are not established/i);
  assert.match(result.copy, /highest reported 24h volume|higher reported 24h volume/i);
});

test('2000 generated cases preserve capital-check invariants', () => {
  let seed = 9217;
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
  };
  for (let i = 0; i < 2000; i += 1) {
    const tokens = Array.from({ length: Math.floor(random() * 8) }, () => ({
      price: random() < 0.2 ? 0 : Number((random() * 1000).toFixed(6)),
    }));
    const range = quoteRange(tokens);
    if (range) {
      assert.ok(range.low > 0);
      assert.ok(range.high >= range.low);
      assert.ok(range.ratio >= 1);
      assert.ok(range.gapPercent >= 0);
    }
    const result = assess({ state: 'do_not_compare', token_count: tokens.length, tokens }, random() * 100000);
    assert.equal(result.mode, 'hold');
    assert.ok(result.budget > 0);
    assert.match(result.note, /Resolve identity/);
  }
});

test('an amount below the control\'s own minimum falls back instead of rendering zero units', () => {
  // The input declares min="1". The clamp only asked for "positive", so
  // 0.0000001 was accepted and the panel rendered "Keep 0 uncommitted" with
  // zero units at both quotes, for an amount the user had typed. The control's
  // stated contract and the code's real one disagreed.
  const { MINIMUM_BUDGET, MAXIMUM_BUDGET } = require('../site/capital-impact.js');
  for (const value of [0.0000001, 0.5, 0.999, 0, -100, '0.0000001']) {
    assert.equal(budget(value), 10000, `${value} was accepted as a budget`);
  }
  for (const value of [MINIMUM_BUDGET, 10, 10000, MAXIMUM_BUDGET]) {
    assert.equal(budget(value), Number(value), `${value} was rejected`);
  }
  assert.equal(budget(MAXIMUM_BUDGET + 1), 10000);
});

test('the markup states the bounds the code enforces', () => {
  // Two numbers in two files saying the same thing is how they drift apart.
  // The template reads them from here, so this asserts it kept doing that.
  const fs = require('node:fs');
  const { MINIMUM_BUDGET, MAXIMUM_BUDGET } = require('../site/capital-impact.js');
  const source = fs.readFileSync(require('node:path').join(__dirname, '../site/integrity.js'), 'utf8');
  assert.match(source, /min="\$\{window\.BellCapitalImpact\.MINIMUM_BUDGET\}"/,
    'the capital input hardcodes its minimum instead of reading the enforced one');
  assert.match(source, /max="\$\{window\.BellCapitalImpact\.MAXIMUM_BUDGET\}"/,
    'the capital input hardcodes its maximum instead of reading the enforced one');
  assert.equal(typeof MINIMUM_BUDGET, 'number');
  assert.ok(MINIMUM_BUDGET > 0 && MAXIMUM_BUDGET > MINIMUM_BUDGET);
});

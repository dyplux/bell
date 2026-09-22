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

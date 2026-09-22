const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const site = path.resolve(__dirname, '../site');
const context = vm.createContext({ window: {} });
for (const file of ['snapshot.js', 'research-brief.js']) {
  vm.runInContext(fs.readFileSync(path.join(site, file), 'utf8'), context);
}
const { build, memo } = context.window.BELL_RESEARCH_BRIEF;
const savedAt = '2026-09-20T12:00:00Z';

test('Gold memo binds seven entries to the dated Gold snapshot, not save time', () => {
  const source = context.window.BELL_GOLD_SNAPSHOT;
  const brief = build(source, 'gold');
  const text = memo(brief, savedAt);
  assert.equal(brief.rows.length, 7);
  assert.match(text, /Observation date: 2026-09-13/);
  assert.match(text, /Window start: 2026-09-06 10:00:00 UTC/);
  assert.match(text, /Saved locally: 2026-09-20T12:00:00Z/);
  assert.match(text, /12% \(PAXG\) to 93% \(CGO\)/);
  for (const wrapper of source.wrappers) {
    assert.ok(text.includes(`| ${wrapper.symbol} | ${wrapper.issuer} | ${wrapper.range_pct.cash.toFixed(4)}% | ${wrapper.range_pct.after_hours.toFixed(4)}% | ${wrapper.range_pct.weekend.toFixed(4)}% |`));
  }
  assert.ok(text.includes(brief.finding));
  assert.equal(source.disclosure, undefined);
  assert.doesNotMatch(text, /Disclosure|CoinMarketCap role|personal hackathon/i);
});

test('Tesla exports the replayable nine-wrapper receipt with its provenance limits', () => {
  const brief = build(context.window.BELL_SNAPSHOT, 'tesla');
  const text = memo(brief, savedAt);
  assert.equal(brief.rows.length, 9);
  assert.match(text, /Observation date: 2026-09-13/);
  assert.match(text, /Window start: 2026-09-06 09:00:00 UTC/);
  assert.match(text, /18% \(TSLA\) to 69% \(TSLA\)/);
  assert.match(text, /can be replayed offline/);
  assert.match(text, /One Dinari entry is explicitly insufficient-data/);
  assert.equal(brief.evidence.length, 2);
  assert.equal(brief.evidence[0].path, 'proof/tesla-live-2026-09-13.json');
  assert.ok(text.includes('proof/tesla-live-2026-09-13'));
});

test('both memos preserve the method, pending questions and triage decision', () => {
  for (const [id, source] of [['gold', context.window.BELL_GOLD_SNAPSHOT], ['tesla', context.window.BELL_SNAPSHOT]]) {
    const brief = build(source, id);
    const text = memo(brief, savedAt);
    assert.match(text, /Hourly range = \(\(high - low\) \/ open\) \* 100/);
    assert.match(text, /No holiday calendar/);
    assert.match(text, /Collection time: Not supplied/);
    assert.match(text, /No wrapper is approved and no buy decision/);
    assert.match(text, /no market request/);
    assert.match(text, /Illustrative|illustrative scenario assumption/);
    assert.equal((text.match(/^- \[ \]/gm) || []).length, 6);
    for (const question of brief.diligence) assert.ok(text.includes(question));
    assert.ok(text.includes(brief.limits));
    assert.ok(text.includes(brief.clock));
    for (const limit of source.limitations) assert.ok(text.includes(limit));
  }
});

test('findings change with the supplied data instead of using fixed example prose', () => {
  const changed = JSON.parse(JSON.stringify(context.window.BELL_SNAPSHOT));
  for (const wrapper of changed.wrappers) wrapper.range_pct.weekend = wrapper.range_pct.cash / 2;
  const brief = build(changed, 'tesla');
  assert.match(brief.finding, /50% .* to 50%/);
  assert.ok(!brief.finding.includes('84%'));
});

test('a zero baseline is unavailable rather than a fabricated ratio', () => {
  const changed = JSON.parse(JSON.stringify(context.window.BELL_SNAPSHOT));
  for (const wrapper of changed.wrappers) wrapper.range_pct.cash = 0;
  const brief = build(changed, 'tesla');
  assert.match(brief.finding, /ratio is unavailable/);
  const text = memo(brief, savedAt);
  assert.ok(!text.includes('Infinity'));
  assert.ok(!text.includes('NaN'));
});

test('public page and generated memo contain no personal employment disclosure', () => {
  for (const file of ['research-brief.js', 'index.html', 'integrity.html', 'snapshot.js']) {
    const text = fs.readFileSync(path.join(site, file), 'utf8');
    assert.doesNotMatch(text, /works at CoinMarketCap|CoinMarketCap role|personal hackathon|one contributor/i, file);
  }
});

test('integrity UI distinguishes the rule threshold from observed evidence', () => {
  const page = fs.readFileSync(path.join(site, 'index.html'), 'utf8');
  const integrity = fs.readFileSync(path.join(site, 'integrity.js'), 'utf8');
  const receipt = fs.readFileSync(path.join(site, 'proof', 'rwa-surface-integrity-2026-09-15.json'), 'utf8');
  assert.match(page, /quote-ratio threshold/);
  assert.match(page, /DATED RECEIPT \/ SOURCE FINGERPRINTS/);
  assert.match(page, /complete credential-free replay inputs are linked separately/);
  assert.match(integrity, /observed quote ratio above 10× review threshold/);
  assert.match(receipt, /price spread above the 10x threshold/);
  assert.doesNotMatch(integrity, /PRICE_DENOMINATION_BREAK:\s*'10× price spread'/);
  assert.doesNotMatch(page, /REPLAYABLE JSON \/ SHA-256/);
});

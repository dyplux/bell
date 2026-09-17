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
  assert.ok(text.includes(source.disclosure));
});

test('Tesla exports only the displayed four-wrapper summary with its provenance limits', () => {
  const brief = build(context.window.BELL_SNAPSHOT, 'tesla');
  const text = memo(brief, savedAt);
  assert.equal(brief.rows.length, 4);
  assert.match(text, /Observation date: 2026-09-11/);
  assert.match(text, /Window start: Not supplied/);
  assert.match(text, /20% \(TSLAX\) to 84% \(TSLA\)/);
  assert.match(text, /medians cannot be independently recomputed/);
  assert.match(text, /nine-wrapper Tesla receipt.*different dataset/);
  assert.equal(brief.evidence.length, 1);
  assert.equal(brief.evidence[0].path, 'snapshot.js');
  assert.ok(!text.includes('proof/tesla-live-2026-09-13'));
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
  assert.ok(!memo(brief, savedAt).includes('84%'));
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

test('shipped public files mirror the implementation sources byte for byte', () => {
  const publicSite = path.resolve(__dirname, '../../repo/site/public/bell');
  if (!fs.existsSync(publicSite)) return;
  for (const file of ['research-brief.js', 'app.js', 'index.html', 'overrides.css']) {
    assert.equal(fs.readFileSync(path.join(site, file), 'utf8'), fs.readFileSync(path.join(publicSite, file), 'utf8'), file);
  }
});

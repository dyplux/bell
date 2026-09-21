/* Research briefs use only the same published summaries as the comparison tables. */
(() => {
  'use strict';
  const method = 'Hourly range = ((high - low) / open) * 100; median by time bucket. Bars are assigned by opening timestamp in America/New_York: weekdays 09:30 inclusive to 16:00 exclusive, other weekday hours, Saturday/Sunday. No holiday calendar; hourly bars can cross a boundary.';
  const limits = 'Bell does not measure investor eligibility, verified backing or legal rights, executable bid/ask or depth, entry and exit costs, underlying fair value or tracking error. Range does not establish liquidity, price discovery, suitability or the reason for a difference.';
  const decision = 'Research triage only. No wrapper is approved and no buy decision follows from this brief. Use the observation to prioritise further investigation; approval remains pending instrument, access and execution evidence.';
  const diligence = [
    'Verify instrument identity, contract and chain, issuer, units per token and native or bridged relationship. Review any derivative-labelled entry separately; a shared CMC reference does not establish equivalent exposure.',
    'Confirm legal claim, backing, redemption conditions, custody compatibility and eligibility for your entity, account and route using dated primary sources.',
    'Check benchmark, issuer conversion and token venue hours separately, including holidays and maintenance. The comparison clock does not establish route availability.',
    'Obtain fresh size-specific entry and exit quotes or depth estimates for an approved route. Record quote expiry, funding, trading, chain and settlement costs; distinguish indicative prices from firm quotes.',
    'Identify a suitable underlying reference, timestamp, currency and unit. A closed or stale reference cannot establish current fair value or an executable opportunity.',
    'Investigate source venues, trades and data quality; repeat the comparison over independent windows before claiming persistence. A quiet bar alone does not establish stale trading.'
  ];
  const date = value => value ? value.replace('T', ' ').replace(/Z$/, ' UTC') : 'Not supplied in the published summary';
  const cell = value => String(value).replace(/\|/g, '\\|').replace(/[\r\n]+/g, ' ');
  function build(snapshot, reviewId) {
    const rows = snapshot.wrappers.map(wrapper => ({
      symbol: wrapper.symbol,
      issuer: wrapper.issuer,
      cash: wrapper.range_pct.cash,
      after_hours: wrapper.range_pct.after_hours,
      weekend: wrapper.range_pct.weekend,
      ratio: wrapper.range_pct.cash > 0 ? wrapper.range_pct.weekend / wrapper.range_pct.cash * 100 : null
    }));
    const ordered = rows.filter(row => Number.isFinite(row.ratio)).sort((a, b) => a.ratio - b.ratio);
    const low = ordered[0];
    const high = ordered[ordered.length - 1];
    const gold = reviewId === 'gold';
    const question = gold
      ? 'Before obtaining and later unwinding USD 100,000 of permitted tokenised gold over a weekend, which candidates need further investigation and what evidence is missing?'
      : 'Before investigating USD 100,000 of tokenised Tesla exposure outside the New York weekday window, which wrappers need further review and what must be verified before execution?';
    const finding = low && high
      ? `Across ${rows.length} CMC-grouped entries in this saved window, weekend median hourly range is approximately ${low.ratio.toFixed(0)}% (${low.symbol}) to ${high.ratio.toFixed(0)}% (${high.symbol}) of each entry's weekday comparison median. Investigate the contrast and its source data; it does not select a preferred wrapper or explain the difference.`
      : 'A weekend-to-weekday ratio is unavailable because no positive comparison median was supplied. No ranking is inferred.';
    const clock = gold
      ? 'For Gold, the New York weekday 09:30-16:00 bucket is a comparison convention, not verified gold-market opening hours. Other weekday hours include overnight and pre-market hours.'
      : 'The New York weekday 09:30-16:00 bucket is a comparison convention without an exchange holiday calendar. It does not establish that a stock market or token route was open.';
    const evidence = gold
      ? [{ label: 'Gold receipt', path: 'proof/gold-live-2026-09-13.json' }, { label: 'Gold replay inputs', path: 'proof/gold-live-2026-09-13.payload.json' }]
      : [{ label: 'Tesla replayable receipt', path: 'proof/tesla-live-2026-09-13.json' }, { label: 'Tesla replay inputs', path: 'proof/tesla-live-2026-09-13.payload.json' }];
    const provenance = gold
      ? 'Dated summary of the saved Gold CMC run. Display and memo ratios use rounded published medians; receipt medians retain greater precision. The linked Gold receipt and normalised payload support offline replay of that run.'
      : 'Nine-entry CMC receipt ending 13 September 2026. The linked normalised payload contains the hourly bars and the receipt carries a canonical dataset hash, so the displayed medians can be replayed offline. One Dinari entry is explicitly insufficient-data; this is not a general conclusion about tokenised equities.';
    return {
      reviewId, asset: snapshot.asset.name, question, finding, clock, rows,
      date: snapshot.window.end_utc ? snapshot.window.end_utc.slice(0, 10) : 'undated',
      start: date(snapshot.window.start_utc), end: date(snapshot.window.end_utc),
      duration: snapshot.window.duration_hours, bars: snapshot.window.bars_per_wrapper,
      counts: snapshot.window.session_counts, method: snapshot.methodology?.hourly_range_pct ? `${method} Relative ratios use rounded published medians.` : method,
      limits, decision, diligence: [...diligence], provenance, evidence,
      collectionTime: 'Not supplied in the published summary; observation end and export time are not collection timestamps.',
      snapshotLimits: snapshot.limitations || []
    };
  }
  function memo(brief, exportedAt = new Date().toISOString()) {
    const number = value => Number.isFinite(Number(value)) ? `${Number(value).toFixed(4)}%` : 'Unavailable';
    const table = brief.rows.map(row => `| ${cell(row.symbol)} | ${cell(row.issuer)} | ${number(row.cash)} | ${number(row.after_hours)} | ${number(row.weekend)} | ${row.ratio === null ? 'Unavailable' : `~${row.ratio.toFixed(0)}%`} |`).join('\n');
    return `# Bell investor research memo: ${brief.asset}

Observation date: ${brief.date} (UTC window end, not a current quote).
Saved locally: ${exportedAt} (export time only; no market request).
Status: Research triage. Instrument and execution approval pending.

## Investor question

${brief.question}

USD 100,000 is an illustrative scenario assumption, not a quote, mandate or measured execution size. No actual order or client research interview took place.

## Dataset and method

Window start: ${brief.start}
Window end: ${brief.end}
Coverage: ${brief.rows.length} entries, ${brief.duration} hours and ${brief.bars} hourly bars per entry. Per-entry buckets: ${brief.counts.cash} weekday comparison / ${brief.counts.after_hours} other weekday / ${brief.counts.weekend} weekend.
Collection time: ${brief.collectionTime}

${brief.method}

${brief.clock}

${brief.provenance}

## Observed finding

${brief.finding}

Values below are published summary inputs, formatted to four decimals for consistency; extra digits do not imply extra source precision. Relative values are approximate and use those inputs.

| Entry | Issuer label (unverified) | Weekday comparison median | Other weekday median | Weekend median | Weekend / comparison |
|---|---|---:|---:|---:|---:|
${table}

## What Bell does not measure

${brief.limits}

## Unresolved questions and next diligence

All checks remain pending; this memo records a research queue, not completed diligence.

${brief.diligence.map(item => `- [ ] ${item}`).join('\n')}

## Decision supported

${brief.decision}

## Evidence

${brief.evidence.map(item => `- [${item.label}](https://dyplux.com/bell/${item.path}) (local copy: ${item.path})`).join('\n')}

The memo is generated locally from the same bundled snapshot as the displayed review. It requires no credentials or API calls. Online evidence links need connectivity; use bundled copies for offline review.

## Snapshot limitations

${brief.snapshotLimits.map(item => `- ${item}`).join('\n')}

Historical observations in one saved window do not establish persistence, causality, future performance or investment suitability. This research brief is not an investment recommendation.
`;
  }
  window.BELL_RESEARCH_BRIEF = { build, memo };
})();

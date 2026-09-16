(() => {
  const escapeHTML = value => String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const byId = id => document.getElementById(id);
  let receipt;
  let filter = 'all';
  let query = '';

  const signalLabels = {
    PRICE_DENOMINATION_BREAK: '10× price spread',
    PRICE_DISPERSION: 'price dispersion',
    ZERO_MCAP_POSITIVE_VOLUME: 'volume with $0 mcap',
    DERIVATIVE_MIX: 'derivative mix',
    SYMBOL_COLLISION: 'symbol collision',
    MARKET_FIELDS_MISSING: 'missing market fields',
    TOKEN_INFO_MISSING: 'missing token identity',
    NO_TRADFI_MARKET: 'no TradFi market',
  };

  const formatNumber = value => typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—';
  const worksheetChecks = [
    ['identity_unit', 'I confirmed the exact token, chain and unit'],
    ['issuer_docs', 'I checked the issuer primary documents'],
    ['backing_redemption', 'I verified the backing and redemption terms'],
    ['eligibility_custody', 'I verified eligibility and custody for my account'],
    ['execution', 'I obtained venue, depth, spread and size-specific execution evidence'],
  ];
  const externalURL = value => {
    try {
      const url = new URL(String(value || ''));
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  };

  function sourceLinks(token, compact = false) {
    const links = [];
    const add = (label, value) => {
      const url = externalURL(value);
      if (url) links.push(`<a href="${escapeHTML(url)}" target="_blank" rel="noopener">${label} ↗</a>`);
    };
    add('CMC token', token.cmc_url);
    add('issuer', token.issuer_website);
    add('project', token.project_url);
    (token.explorer_urls || []).slice(0, compact ? 1 : 3).forEach(url => add('explorer', url));
    (token.technical_doc_urls || []).slice(0, compact ? 1 : 3).forEach(url => add('docs', url));
    return links.length ? `<span class="source-paths">${links.join(' · ')}</span>` : '<span class="source-paths muted">No linked source path</span>';
  }

  function identityLine(token, rwaId) {
    return `<small class="identity-line">Identity: RWA ${escapeHTML(rwaId || '—')} · token ${escapeHTML(token.crypto_id || 'unresolved')} · issuer ${escapeHTML(token.issuer_id || 'unresolved')}</small>`;
  }

  function renderEvidence(signal) {
    const evidence = signal.evidence || {};
    const items = [];
    if (evidence.max_min_ratio) items.push(`max/min price ratio: ${formatNumber(evidence.max_min_ratio)}×`);
    if (evidence.prices) items.push(`observed prices: ${evidence.prices.map(formatNumber).join(' · ')}`);
    if (evidence.tokens) items.push(`tokens: ${evidence.tokens.map(token => `${token.symbol || token.crypto_id || 'unknown'} (${token.crypto_id || 'no id'})`).join(' · ')}`);
    if (evidence.derivatives) items.push(`derivative-labelled: ${evidence.derivatives.join(', ') || 'none'}`);
    if (evidence.other) items.push(`other representations: ${evidence.other.filter(Boolean).join(', ') || 'none'}`);
    if (evidence.symbols) items.push(`reused symbols: ${evidence.symbols.join(', ')}`);
    if (evidence.count) items.push(`missing-field rows: ${evidence.count}`);
    return items.map(item => `<li>${escapeHTML(item)}</li>`).join('') || '<li>No additional evidence fields.</li>';
  }

  function renderTokenTable(alert) {
    const tokens = alert.tokens || alert.representations || [];
    const rows = tokens.map(token => {
      const website = externalURL(token.issuer_website);
      const cmcURL = externalURL(token.cmc_url);
      const symbol = escapeHTML(token.symbol || '—');
      const selector = token.crypto_id != null ? `<input type="checkbox" data-wrapper-select="${escapeHTML(token.crypto_id)}" aria-label="Select ${symbol} for fact comparison">` : '';
      const tokenCell = `${cmcURL ? `<a href="${escapeHTML(cmcURL)}" target="_blank" rel="noopener">${symbol} ↗</a>` : symbol}<small>${escapeHTML(token.crypto_id || 'no id')}</small>${sourceLinks(token, true)}`;
      const issuer = escapeHTML(token.issuer_name || token.issuer_catalogue_name || 'unlinked');
      const issuerCell = website ? `<a href="${escapeHTML(website)}" target="_blank" rel="noopener">${issuer} ↗</a>` : issuer;
      const platforms = (token.platforms || []).map(platform => `${escapeHTML(platform.name || 'unknown chain')} · ${escapeHTML(platform.contract_address || 'no contract')}`).join('<br>') || 'not resolved';
      return `<tr><td>${selector}</td><td>${tokenCell}${identityLine(token, alert.rwa_id)}</td><td>${escapeHTML(token.name || '—')}</td><td>${issuerCell}</td><td>${platforms}</td><td>${formatNumber(token.price)}</td><td>${formatNumber(token.market_cap)}</td><td>${formatNumber(token.volume_24h)}</td></tr>`;
    }).join('');
    return `<div class="token-table-wrap"><table class="token-table"><thead><tr><th>Select</th><th>Token</th><th>Representation</th><th>Issuer</th><th>Chain / contract</th><th>Price</th><th>MCap</th><th>24h vol</th></tr></thead><tbody>${rows || '<tr><td colspan="8">No token rows returned.</td></tr>'}</tbody></table></div><div class="wrapper-compare" data-wrapper-compare="${escapeHTML(alert.rwa_id)}"><p><b>Compare two observed wrappers</b> Select up to two rows for a factual side-by-side. Bell will not rank them or turn this into an allocation decision.</p><div data-comparison-output class="comparison-output">Select two rows to inspect their observed differences.</div></div>`;
  }

  function renderComparisonOutput(alert, selectedIds) {
    const tokens = (alert.tokens || alert.representations || []).filter(token => selectedIds.includes(String(token.crypto_id)));
    if (tokens.length < 2) return 'Select two rows to inspect their observed differences.';
    if (tokens.length > 2) return 'Select only two rows for the side-by-side view.';
    const cards = tokens.map(token => {
      const platforms = (token.platforms || []).map(platform => `${platform.name || 'unknown chain'} · ${platform.contract_address || 'no contract'}`).join(' / ') || 'not resolved';
      const website = externalURL(token.issuer_website);
      const issuer = website ? `<a href="${escapeHTML(website)}" target="_blank" rel="noopener">${escapeHTML(token.issuer_name || 'unlinked')} ↗</a>` : escapeHTML(token.issuer_name || 'unlinked');
      return `<div class="comparison-card"><strong>${escapeHTML(token.symbol || token.name || 'token')}</strong><span>${escapeHTML(token.name || '—')}</span>${identityLine(token, alert.rwa_id)}<small>Issuer: ${issuer}</small><small>Chain / contract: ${escapeHTML(platforms)}</small><small>Observed price: ${formatNumber(token.price)} · MCap: ${formatNumber(token.market_cap)} · 24h volume: ${formatNumber(token.volume_24h)}</small>${sourceLinks(token)}</div>`;
    }).join('');
    const prefix = alert.state === 'do_not_compare'
      ? '<b>COMPARISON WITHHELD</b><span>A Bell critical rule fired for this reference. These facts are shown for investigation, not as equivalent exposure.</span>'
      : '<b>FACTS ONLY · NO WRAPPER RANKING</b><span>Observed quote fields are not normalized for unit, backing, eligibility or execution.</span>';
    return `<div class="comparison-verdict">${prefix}</div><div class="comparison-cards">${cards}</div>`;
  }

  function briefButton(rwaId) {
    return `<button class="brief-button" type="button" data-brief-id="${escapeHTML(rwaId)}">Save decision brief</button>`;
  }

  function worksheetKey(rwaId) {
    return `bell-research-worksheet-${rwaId}`;
  }

  function readWorksheet(rwaId) {
    try {
      const value = JSON.parse(localStorage.getItem(worksheetKey(rwaId)) || '{}');
      return { checks: value.checks || {}, note: value.note || '' };
    } catch {
      return { checks: {}, note: '' };
    }
  }

  function saveWorksheet(rwaId, worksheet) {
    try {
      localStorage.setItem(worksheetKey(rwaId), JSON.stringify({
        checks: worksheet.checks || {},
        note: worksheet.note || '',
        saved_at: new Date().toISOString(),
      }));
    } catch {
      // The worksheet is optional; the receipt and brief still work.
    }
  }

  function worksheetStateLabel(worksheet) {
    const completed = worksheetChecks.filter(([key]) => worksheet.checks[key]).length;
    return completed === worksheetChecks.length
      ? 'DESK REVIEW PACK COMPLETE · BELL RESULT UNCHANGED'
      : `${completed}/${worksheetChecks.length} EXTERNAL CHECKS RECORDED`;
  }

  function renderWorksheet(item) {
    const worksheet = readWorksheet(item.rwa_id);
    const checks = worksheetChecks.map(([key, label]) => `<label><input type="checkbox" data-worksheet-check="${key}" data-worksheet-id="${escapeHTML(item.rwa_id)}" ${worksheet.checks[key] ? 'checked' : ''}>${escapeHTML(label)}</label>`).join('');
    return `<details class="research-worksheet"><summary>Open research worksheet</summary><p class="worksheet-note">Local handoff for your research process. These checks are your record, not Bell verification or investment approval.</p><div class="worksheet-checks">${checks}</div><textarea data-worksheet-note="${escapeHTML(item.rwa_id)}" placeholder="Add the one unresolved question or source you want to carry into the memo">${escapeHTML(worksheet.note)}</textarea><div class="worksheet-footer"><span data-worksheet-status="${escapeHTML(item.rwa_id)}">${escapeHTML(worksheetStateLabel(worksheet))}</span><button type="button" class="brief-button" data-save-worksheet="${escapeHTML(item.rwa_id)}">Save local worksheet</button></div></details>`;
  }

  function renderHandoff(item) {
    if (item.state === 'do_not_compare') {
      return '<div class="alert-handoff"><span>TO CLEAR THIS CASE</span><p>Match the RWA ID to the token ID and issuer ID. Then confirm the exact instrument and unit, verify issuer and redemption terms, and obtain venue and execution evidence before comparing wrappers.</p></div>';
    }
    if (Number(item.token_count || 0) === 1) {
      return '<div class="alert-handoff"><span>SINGLE REPRESENTATION PATH</span><p>CMC returned one representation for this reference, so there is no wrapper ranking to perform. Verify the instrument, issuer, backing, redemption, eligibility, custody and executable liquidity before treating it as investable.</p></div>';
    }
    if (item.state === 'investigate') {
      return '<div class="alert-handoff"><span>TO MOVE FORWARD</span><p>Classify the representation, confirm the issuer and missing fields, then keep unresolved wrappers separate in the research memo.</p></div>';
    }
    return '<div class="alert-handoff"><span>BEFORE ALLOCATION</span><p>Run external checks for backing, eligibility, redemption, custody and executable liquidity. A clean Bell scan is not approval.</p></div>';
  }

  function renderMetrics() {
    const universe = receipt.universe;
    byId('observed-at').textContent = `OBSERVED ${receipt.observed_at}`;
    const publication = receipt._publication;
    let status = publication?.status || 'UNKNOWN';
    if (publication?.status === 'fresh' && publication.published_at && publication.stale_after_seconds) {
      const age = Math.max(0, (Date.now() - Date.parse(publication.published_at)) / 1000);
      status = age <= Number(publication.stale_after_seconds) ? 'fresh' : 'stale';
    }
    byId('receipt-status-label').textContent = publication ? `${publication.source === 'dated_static' ? 'DATED REPLAY' : 'LIVE RECEIPT'} · ${String(status).toUpperCase()}` : 'DATED RECEIPT';
    byId('metric-references').textContent = universe.tokenised_references_scanned.toLocaleString();
    byId('metric-tokens').textContent = universe.tokens_scanned.toLocaleString();
    byId('metric-blocked').textContent = universe.states.do_not_compare.toLocaleString();
    byId('metric-unaddressable').textContent = receipt.catalogue_integrity.asset_list_rows_without_rwa_id.toLocaleString();
    if (receipt.method?.scan_status !== 'ready') byId('receipt-status-label').textContent += ' · INPUT INCOMPLETE';
  }

  function renderCompactEvidence(item) {
    const evidence = Object.entries(item.signal_evidence || {}).filter(([code]) => code !== 'NO_TRADFI_MARKET').map(([code, value]) => {
      const parts = [];
      if (value.max_min_ratio) parts.push(`${formatNumber(value.max_min_ratio)}× spread`);
      if (value.count) parts.push(`${value.count} missing-field rows`);
      if (value.tokens) parts.push(`${value.tokens.length} evidence token${value.tokens.length === 1 ? '' : 's'}`);
      if (value.symbols) parts.push(`symbols: ${value.symbols.join(', ')}`);
      return `<li><b>${escapeHTML(signalLabels[code] || code)}</b> ${escapeHTML(parts.join(' · ') || 'rule fired')}</li>`;
    }).join('');
    return evidence || '<li>No compact numerical evidence was published for this index row.</li>';
  }

  function renderAlertRow(alert) {
      const labels = alert.signals.filter(signal => signal.severity !== 'info').map(signal => signalLabels[signal.code] || signal.code).slice(0, 3).join(' · ');
      const evidence = alert.signals.filter(signal => signal.severity !== 'info').map(signal => `<div class="evidence-rule"><b>${escapeHTML(signalLabels[signal.code] || signal.code)}</b><p>${escapeHTML(signal.message)}</p><ul>${renderEvidence(signal)}</ul></div>`).join('');
      const stateLabel = alert.state === 'no_flags' ? 'NO RULE HIT' : alert.state.replaceAll('_', ' ').toUpperCase();
      const decision = alert.decision || {};
      return `<article class="alert-row"><div class="alert-name">${escapeHTML(alert.name)}<small>${escapeHTML(alert.symbol)} · ${escapeHTML(alert.asset_type)} · ${alert.issuer_count} issuers</small></div><div class="alert-state ${alert.state === 'investigate' ? 'investigate' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML(labels)}</div><div class="alert-tokens"><strong>${alert.token_count}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(decision.label || 'REVIEW')}</b><p>${escapeHTML(decision.consequence || '')}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(alert.next_action)}</div>${renderHandoff(alert)}<div class="alert-tools">${briefButton(alert.rwa_id)}</div><details class="alert-details"><summary>Inspect evidence</summary>${evidence}<h4>Representation rows</h4>${renderTokenTable(alert)}</details>${renderWorksheet(alert)}</article>`;
  }

  function renderIndexRow(item, detail) {
    if (detail) return renderAlertRow(detail);
    const stateLabel = item.state === 'no_flags' ? 'NO RULE HIT' : String(item.state || '').replaceAll('_', ' ').toUpperCase();
    const decision = item.decision || {};
    return `<article class="alert-row compact-row"><div class="alert-name">${escapeHTML(item.name)}<small>${escapeHTML(item.symbol)} · ${escapeHTML(item.asset_type)} · ${item.issuer_count || 0} issuers · RWA ${escapeHTML(item.rwa_id)}</small></div><div class="alert-state ${item.state === 'investigate' ? 'investigate' : item.state === 'no_flags' ? 'clear' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML((item.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET').slice(0, 3).map(code => signalLabels[code] || code).join(' · ') || 'No published rule hit')}</div><div class="alert-tokens"><strong>${Number(item.token_count || 0).toLocaleString()}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(decision.label || 'NO RULE HIT')}</b><p>${escapeHTML(decision.consequence || '')}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(item.next_action || '')}</div>${renderHandoff(item)}<div class="alert-tools">${briefButton(item.rwa_id)}</div><details class="alert-details"><summary>Inspect representations</summary><p class="compact-note">CMC quote rows observed in this receipt. Bell uses them to route research, not to certify backing, eligibility, liquidity or equivalence.</p><ul class="compact-evidence">${renderCompactEvidence(item)}</ul>${renderTokenTable(item)}</details>${renderWorksheet(item)}</article>`;
  }

  function markdownBrief(item) {
    const decision = item.decision || {};
    const signals = (item.signals || []).filter(signal => signal.severity !== 'info');
    const signalLines = signals.length ? signals.map(signal => {
      const evidence = signal.evidence || {};
      const facts = [];
      if (evidence.max_min_ratio) facts.push(`${formatNumber(evidence.max_min_ratio)}× observed price spread`);
      if (evidence.count) facts.push(`${evidence.count} rows with missing fields`);
      if (evidence.symbols) facts.push(`symbols ${evidence.symbols.join(', ')}`);
      return `- ${signalLabels[signal.code] || signal.code}: ${signal.message}${facts.length ? ` (${facts.join('; ')})` : ''}`;
    }).join('\n') : '- No published rule hit in this scan.';
    const tokenLines = (item.tokens || item.representations || []).map(token => {
      const issuerURL = externalURL(token.issuer_website);
      const issuer = token.issuer_name || token.issuer_catalogue_name || 'unlinked';
      const issuerCell = issuerURL ? `[${issuer}](${issuerURL})` : issuer;
      const cmcURL = externalURL(token.cmc_url);
      const tokenCell = cmcURL ? `[${token.symbol || '—'}](${cmcURL})` : (token.symbol || '—');
      const platforms = (token.platforms || []).map(platform => `${platform.name || 'unknown chain'}: ${platform.contract_address || 'no contract'}`).join('<br>') || 'not resolved';
      const sourceURLs = [token.cmc_url, token.issuer_website, token.project_url, ...(token.explorer_urls || []), ...(token.technical_doc_urls || [])].filter(Boolean);
      const sourceCells = sourceURLs.length ? sourceURLs.map(url => `[link](${url})`).join(' ') : 'none';
      return `| ${tokenCell} (${token.crypto_id || 'no id'}) | ${token.name || '—'} | ${issuerCell} (${token.issuer_id || 'no id'}) | ${platforms} | ${formatNumber(token.price)} | ${formatNumber(token.market_cap)} | ${formatNumber(token.volume_24h)} | ${sourceCells} |`;
    }).join('\n');
    const worksheet = readWorksheet(item.rwa_id);
    const worksheetLines = worksheetChecks.map(([key, label]) => `- [${worksheet.checks[key] ? 'x' : ' '}] ${label}`).join('\n');
    return `# Bell decision brief: ${item.name || 'RWA reference'}

Generated from the credential-free Bell receipt. This is research triage, not investment advice.

## Decision

- Reference: ${item.name || '—'} (${item.symbol || '—'})
- RWA ID: ${item.rwa_id || '—'}
- Asset type: ${item.asset_type || '—'}
- State: ${item.state === 'no_flags' ? 'NO RULE HIT' : String(item.state || '').replaceAll('_', ' ').toUpperCase()}
- Decision effect: ${decision.label || 'REVIEW'}
- Consequence: ${decision.consequence || 'No allocation status is produced by this monitor.'}
- Observed: ${receipt.observed_at || '—'}
- Published: ${receipt._publication?.published_at || '—'}

## Evidence

${signalLines}

## Next action

${item.next_action || 'Continue external diligence before comparing or allocating.'}

## Resolution checklist

- match the RWA ID to the token ID and issuer ID, then confirm the exact token, chain and unit;
- verify instrument type, backing, redemption and eligibility from primary documents;
- obtain venue access, depth, spread and size-specific execution evidence;
- rerun the comparison only after the unresolved contradiction has an evidence-backed explanation.

## Representation rows

| Token | Representation | Issuer | Chain / contract | Price | Market cap | 24h volume | Source paths |
|---|---|---|---|---:|---:|---:|---|
${tokenLines || '| Detailed token rows are not retained for this queue item. | | | | | |'}

## Local research worksheet

This is a local user record, not Bell verification or investment approval.

${worksheetLines}

Research note: ${worksheet.note || 'No local note recorded.'}

## Still not answered by Bell

- backing, custody, redemption and legal eligibility;
- venue access, depth, spread and size-specific execution;
- whether this asset is suitable for a particular portfolio or mandate.

Source: ${(window.location.protocol === 'http:' || window.location.protocol === 'https:') ? new URL('/api/integrity', window.location.href).href : '/api/integrity'}
`;
  }

  function downloadBrief(rwaId) {
    const item = (receipt.alerts || []).find(alert => String(alert.rwa_id) === String(rwaId))
      || (receipt.alert_index || []).find(alert => String(alert.rwa_id) === String(rwaId));
    if (!item) return;
    const filename = `bell-${String(item.symbol || item.name || 'rwa').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-decision-brief.md`;
    const blob = new Blob([markdownBrief(item)], { type: 'text/markdown;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function renderAlerts() {
    if (!receipt) return;
    const indexed = receipt.alert_index || receipt.alerts || [];
    const normalizedQuery = query.trim().toLowerCase();
    const details = new Map((receipt.alerts || []).map(alert => [String(alert.rwa_id), alert]));
    const matching = indexed.filter(item => {
      const stateMatches = filter === 'all' || item.state === filter;
      const haystack = [item.name, item.symbol, item.asset_type, item.rwa_id].join(' ').toLowerCase();
      return stateMatches && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
    const visible = matching.slice(0, 12);
    byId('alert-count').innerHTML = `Showing <strong>${visible.length}</strong> of <strong>${matching.length}</strong> matching references · ${indexed.length.toLocaleString()} references scanned. <a href="https://rwa-surface-review.pages.dev/" target="_blank" rel="noopener">Open the complete searchable queue ↗</a>`;
    byId('alert-list').innerHTML = visible.map(item => renderIndexRow(item, details.get(String(item.rwa_id)))).join('') || '<p class="section-note">No references match this filter.</p>';
  }

  function searchFromHero(event) {
    event.preventDefault();
    const input = byId('hero-search');
    query = input.value.trim();
    byId('alert-search').value = input.value;
    if (!receipt) return;
    filter = 'all';
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('selected', item.dataset.filter === 'all'));
    renderAlerts();
    byId('monitor').scrollIntoView({ behavior: 'smooth', block: 'start' });
    window.setTimeout(() => byId('alert-search').focus(), 450);
  }

  function renderSignals() {
    const signals = receipt.universe.signals;
    const cards = [
      ['PRICE_DENOMINATION_BREAK', 'price groups over 10×', 'A comparison may be mixing units or claim types.'],
      ['ZERO_MCAP_POSITIVE_VOLUME', 'volume with zero market cap', 'The quote surface needs investigation before it becomes a market claim.'],
      ['DERIVATIVE_MIX', 'groups mix derivatives', 'A derivative-labelled representation is not silently treated as spot.'],
      ['MARKET_FIELDS_MISSING', 'groups with missing fields', 'Absence stays visible. It is never converted into zero.'],
      ['TOKEN_INFO_MISSING', 'groups with missing token identity', 'A crypto ID without resolved chain or contract identity stays out of a clean shortlist.'],
    ];
    byId('signal-grid').innerHTML = cards.map(([code, title, copy]) => `<article class="signal-card"><strong>${signals[code] || 0}</strong><h3>${title}</h3><p>${copy}</p></article>`).join('');
  }

  function renderIdentity() {
    const identity = receipt.identity_integrity || {};
    byId('identity-proof').innerHTML = `<span>IDENTITY JOIN CHECK</span><strong>${formatNumber(identity.info_unique_ids || 0)} / ${formatNumber(identity.tokenised_map_ids || 0)} tokenised references resolved through info</strong><small>${formatNumber(identity.issuer_catalogue_rows || 0)} issuer records · ${formatNumber(identity.quote_issuer_ids || 0)} issuer IDs seen in quotes · ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved issuer joins · ${formatNumber(identity.crypto_info_rows || 0)} token identity rows · ${formatNumber((identity.quote_crypto_ids_missing_from_info || []).length)} unresolved token joins</small>`;
  }

  function renderDifferentiation() {
    const identity = receipt.identity_integrity || {};
    byId('differentiation').innerHTML = `<div class="diff-column"><span>CMC AND SCREENS SHOW THE CANDIDATES</span><strong>References, wrappers, issuers and latest quote fields</strong><p>That is the discovery and comparison layer. A row being grouped under one reference does not prove that its economic claim, unit or market data is equivalent.</p></div><div class="diff-arrow">→</div><div class="diff-column accent"><span>BELL STRESS-TESTS THE GROUPING</span><strong>A population-wide gate before a wrapper enters your shortlist</strong><p>${formatNumber(receipt.universe.states.do_not_compare)} blocked groups, ${formatNumber(receipt.universe.signals.PRICE_DENOMINATION_BREAK || 0)} denomination breaks and ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved issuer joins in this receipt. This is an integrity decision, not a token ranking.</p></div>`;
  }

  function renderDecisionStory() {
    const alert = receipt.alerts.find(item => item.state === 'do_not_compare') || receipt.alerts.find(item => item.state === 'investigate');
    const publication = receipt._publication || {};
    if (!alert) {
      byId('decision-hero').innerHTML = '<p class="eyebrow">CURRENT RECEIPT</p><h3>No published case</h3><p>The receipt contains no alert to route.</p>';
      return;
    }
    const decision = alert.decision || {};
    const signals = alert.signals.filter(signal => signal.severity !== 'info').slice(0, 2).map(signal => signalLabels[signal.code] || signal.code).join(' · ');
    const primaryEvidence = alert.signals.find(signal => signal.severity !== 'info')?.evidence || {};
    byId('hero-case').textContent = alert.name || 'Current flagged case';
    byId('hero-case-fact').textContent = primaryEvidence.max_min_ratio ? `${formatNumber(primaryEvidence.max_min_ratio)}× observed price spread across representations` : signals || 'Published rule hit';
    byId('hero-proof-output').textContent = decision.label || 'HOLD COMPARISON';
    byId('decision-hero').innerHTML = `<div class="decision-hero-top"><span class="eyebrow">FLAGGED REFERENCE</span><span class="decision-case">${escapeHTML(alert.symbol || 'RWA')}</span></div><h3>${escapeHTML(alert.name)}</h3><p class="decision-signal">${escapeHTML(signals || 'published rule hit')}</p><div class="decision-outcome"><span>OUTPUT</span><strong>${escapeHTML(decision.label || 'HOLD COMPARISON')}</strong><p>${escapeHTML(decision.consequence || alert.next_action || '')}</p><b class="allocation-gate">${escapeHTML(decision.allocation_effect || 'No allocation status is produced by this monitor.')}</b></div><div class="decision-receipt"><span>${escapeHTML(publication.status ? String(publication.status).toUpperCase() : 'DATED')} · ${escapeHTML(publication.observed_at || receipt.observed_at || '—')}</span><a href="/api/integrity" target="_blank" rel="noopener">Open credential-free receipt ↗</a></div>`;
  }

  async function boot() {
    try {
      const sources = ['/api/integrity', 'proof/rwa-surface-integrity-2026-09-15.json'];
      let lastError;
      for (const source of sources) {
        try {
          const response = await fetch(source, { headers: { Accept: 'application/json' } });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const candidate = await response.json();
          if (candidate.schema_version === 'rwa_surface_integrity.v1') {
            if (source !== '/api/integrity') {
              candidate._publication = {
                source: 'dated_static',
                observed_at: candidate.observed_at || null,
                published_at: null,
                credential_free: true,
                status: 'dated',
                age_seconds: null,
                stale_after_seconds: null,
              };
            }
            receipt = candidate;
            break;
          }
          throw new Error('unexpected receipt schema');
        } catch (error) {
          lastError = error;
        }
      }
      if (!receipt) throw lastError || new Error('no receipt source');
      renderMetrics();
      renderAlerts();
      renderSignals();
      renderIdentity();
      renderDifferentiation();
      renderDecisionStory();
    } catch (error) {
      byId('alert-list').innerHTML = '<p class="section-note">The dated evidence receipt could not be loaded. Open the JSON receipt directly to inspect the source.</p>';
    }
  }

  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('selected', item === button));
    renderAlerts();
  }));
  byId('alert-search').addEventListener('input', event => {
    query = event.target.value;
    byId('hero-search').value = event.target.value;
    renderAlerts();
  });
  byId('alert-list').addEventListener('click', event => {
    const button = event.target.closest('[data-brief-id]');
    if (button) downloadBrief(button.dataset.briefId);
    const saveButton = event.target.closest('[data-save-worksheet]');
    if (saveButton) {
      const worksheetId = saveButton.dataset.saveWorksheet;
      const worksheetElement = saveButton.closest('.research-worksheet');
      const worksheet = readWorksheet(worksheetId);
      worksheet.note = worksheetElement.querySelector('[data-worksheet-note]')?.value || '';
      worksheetElement.querySelectorAll('[data-worksheet-check]').forEach(input => {
        worksheet.checks[input.dataset.worksheetCheck] = input.checked;
      });
      saveWorksheet(worksheetId, worksheet);
      const status = worksheetElement.querySelector(`[data-worksheet-status="${CSS.escape(worksheetId)}"]`);
      if (status) status.textContent = worksheetStateLabel(worksheet);
      saveButton.textContent = 'Saved locally';
      window.setTimeout(() => { saveButton.textContent = 'Save local worksheet'; }, 1400);
    }
  });
  byId('alert-list').addEventListener('change', event => {
    const wrapperInput = event.target.closest('[data-wrapper-select]');
    if (wrapperInput) {
      const compare = wrapperInput.closest('.alert-details')?.querySelector('[data-wrapper-compare]') || wrapperInput.closest('.alert-row')?.querySelector('[data-wrapper-compare]');
      if (!compare) return;
      const scope = wrapperInput.closest('.alert-details') || wrapperInput.closest('.alert-row');
      const selectedIds = [...scope.querySelectorAll('[data-wrapper-select]:checked')].map(input => input.dataset.wrapperSelect);
      const alertId = compare.dataset.wrapperCompare;
      const alert = (receipt.alerts || []).find(item => String(item.rwa_id) === String(alertId)) || (receipt.alert_index || []).find(item => String(item.rwa_id) === String(alertId));
      if (alert) compare.querySelector('[data-comparison-output]').innerHTML = renderComparisonOutput(alert, selectedIds);
    }
    const input = event.target.closest('[data-worksheet-check]');
    if (!input) return;
    const worksheetId = input.dataset.worksheetId;
    const worksheet = readWorksheet(worksheetId);
    worksheet.checks[input.dataset.worksheetCheck] = input.checked;
    saveWorksheet(worksheetId, worksheet);
    const status = input.closest('.research-worksheet')?.querySelector(`[data-worksheet-status="${CSS.escape(worksheetId)}"]`);
    if (status) status.textContent = worksheetStateLabel(worksheet);
  });
  byId('hero-search-form').addEventListener('submit', searchFromHero);
  boot();
  window.setInterval(() => { if (receipt) renderMetrics(); }, 60000);
})();

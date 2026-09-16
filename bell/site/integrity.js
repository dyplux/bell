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
    NO_TRADFI_MARKET: 'no TradFi market',
  };

  const formatNumber = value => typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—';
  const externalURL = value => {
    try {
      const url = new URL(String(value || ''));
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  };

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
      const issuer = escapeHTML(token.issuer_name || token.issuer_catalogue_name || 'unlinked');
      const issuerCell = website ? `<a href="${escapeHTML(website)}" target="_blank" rel="noopener">${issuer} ↗</a>` : issuer;
      return `<tr><td>${escapeHTML(token.symbol || '—')}<small>${escapeHTML(token.crypto_id || 'no id')}</small></td><td>${escapeHTML(token.name || '—')}</td><td>${issuerCell}</td><td>${formatNumber(token.price)}</td><td>${formatNumber(token.market_cap)}</td><td>${formatNumber(token.volume_24h)}</td></tr>`;
    }).join('');
    return `<div class="token-table-wrap"><table class="token-table"><thead><tr><th>Token</th><th>Representation</th><th>Issuer</th><th>Price</th><th>MCap</th><th>24h vol</th></tr></thead><tbody>${rows || '<tr><td colspan="6">No token rows returned.</td></tr>'}</tbody></table></div>`;
  }

  function briefButton(rwaId) {
    return `<button class="brief-button" type="button" data-brief-id="${escapeHTML(rwaId)}">Save decision brief</button>`;
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
      return `<article class="alert-row"><div class="alert-name">${escapeHTML(alert.name)}<small>${escapeHTML(alert.symbol)} · ${escapeHTML(alert.asset_type)} · ${alert.issuer_count} issuers</small></div><div class="alert-state ${alert.state === 'investigate' ? 'investigate' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML(labels)}</div><div class="alert-tokens"><strong>${alert.token_count}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(decision.label || 'REVIEW')}</b><p>${escapeHTML(decision.consequence || '')}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(alert.next_action)}</div>${renderHandoff(alert)}<div class="alert-tools">${briefButton(alert.rwa_id)}</div><details class="alert-details"><summary>Inspect evidence</summary>${evidence}<h4>Representation rows</h4>${renderTokenTable(alert)}</details></article>`;
  }

  function renderIndexRow(item, detail) {
    if (detail) return renderAlertRow(detail);
    const stateLabel = item.state === 'no_flags' ? 'NO RULE HIT' : String(item.state || '').replaceAll('_', ' ').toUpperCase();
    const decision = item.decision || {};
    return `<article class="alert-row compact-row"><div class="alert-name">${escapeHTML(item.name)}<small>${escapeHTML(item.symbol)} · ${escapeHTML(item.asset_type)} · ${item.issuer_count || 0} issuers · RWA ${escapeHTML(item.rwa_id)}</small></div><div class="alert-state ${item.state === 'investigate' ? 'investigate' : item.state === 'no_flags' ? 'clear' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML((item.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET').slice(0, 3).map(code => signalLabels[code] || code).join(' · ') || 'No published rule hit')}</div><div class="alert-tokens"><strong>${Number(item.token_count || 0).toLocaleString()}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(decision.label || 'NO RULE HIT')}</b><p>${escapeHTML(decision.consequence || '')}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(item.next_action || '')}</div>${renderHandoff(item)}<div class="alert-tools">${briefButton(item.rwa_id)}</div><details class="alert-details"><summary>Inspect representations</summary><p class="compact-note">CMC quote rows observed in this receipt. Bell uses them to route research, not to certify backing, eligibility, liquidity or equivalence.</p><ul class="compact-evidence">${renderCompactEvidence(item)}</ul>${renderTokenTable(item)}</details></article>`;
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
    const tokenLines = (item.tokens || item.representations || []).map(token => `| ${token.symbol || '—'} | ${token.name || '—'} | ${token.issuer_name || token.issuer_catalogue_name || 'unlinked'} | ${formatNumber(token.price)} | ${formatNumber(token.market_cap)} | ${formatNumber(token.volume_24h)} |`).join('\n');
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

| Token | Representation | Issuer | Price | Market cap | 24h volume |
|---|---|---|---:|---:|---:|
${tokenLines || '| Detailed token rows are not retained for this queue item. | | | | | |'}

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
    ];
    byId('signal-grid').innerHTML = cards.map(([code, title, copy]) => `<article class="signal-card"><strong>${signals[code] || 0}</strong><h3>${title}</h3><p>${copy}</p></article>`).join('');
  }

  function renderIdentity() {
    const identity = receipt.identity_integrity || {};
    byId('identity-proof').innerHTML = `<span>IDENTITY JOIN CHECK</span><strong>${formatNumber(identity.info_unique_ids || 0)} / ${formatNumber(identity.tokenised_map_ids || 0)} tokenised references resolved through info</strong><small>${formatNumber(identity.issuer_catalogue_rows || 0)} issuer records · ${formatNumber(identity.quote_issuer_ids || 0)} issuer IDs seen in quotes · ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved</small>`;
  }

  function renderDifferentiation() {
    const identity = receipt.identity_integrity || {};
    byId('differentiation').innerHTML = `<div class="diff-column"><span>CMC GIVES YOU THE CANDIDATES</span><strong>References, wrappers, issuers and latest quote fields</strong><p>That is the discovery layer. It does not decide whether the representations are comparable.</p></div><div class="diff-arrow">→</div><div class="diff-column accent"><span>BELL DECIDES WHETHER THEY ARE COMPARABLE</span><strong>A population-wide gate before a wrapper enters your shortlist</strong><p>${formatNumber(receipt.universe.states.do_not_compare)} blocked groups, ${formatNumber(receipt.universe.signals.PRICE_DENOMINATION_BREAK || 0)} denomination breaks and ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved issuer joins in this receipt.</p></div>`;
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
  byId('hero-search-form').addEventListener('submit', searchFromHero);
  byId('alert-list').addEventListener('click', event => {
    const button = event.target.closest('[data-brief-id]');
    if (button) downloadBrief(button.dataset.briefId);
  });
  boot();
  window.setInterval(() => { if (receipt) renderMetrics(); }, 60000);
})();

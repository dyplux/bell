(() => {
  'use strict';

  const stateLabels = {
    do_not_compare: 'DO NOT SHORTLIST',
    investigate: 'INVESTIGATE',
    no_flags: 'FACTS OPEN',
  };
  const signalLabels = {
    PRICE_DENOMINATION_BREAK: 'Price denomination break',
    ZERO_MCAP_POSITIVE_VOLUME: 'Zero market cap · positive volume',
    DERIVATIVE_MIX: 'Derivative mix',
    MARKET_FIELDS_MISSING: 'Market fields missing',
    TOKEN_INFO_MISSING: 'Token metadata missing',
    NO_TRADFI_MARKET: 'No underlying market field',
    SYMBOL_COLLISION: 'Symbol collision',
    PRICE_DISPERSION: 'Price dispersion',
  };
  const nextSteps = {
    do_not_compare: 'Resolve the identity and unit of each representation, then verify issuer and redemption terms before attempting a comparison.',
    investigate: 'Inspect the missing or ambiguous identity and market fields; keep the wrappers separate until the evidence is resolved.',
    no_flags: 'Review the filtered quote rows. This result does not establish equivalent units, rights or executable markets.',
  };

  const form = document.querySelector('#search-form');
  const input = document.querySelector('#asset-search');
  const result = document.querySelector('#result');
  const suggestions = document.querySelector('#search-suggestions');
  const localTools = document.querySelector('#local-tools');
  const localHost = ['localhost', '127.0.0.1', '::1'].includes(location.hostname);
  let receipt;
  let entries = [];

  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[ch]);
  const hasNumber = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  const number = value => hasNumber(value) ? Number(value).toLocaleString('en-US') : '—';
  const money = value => hasNumber(value) ? '$' + Number(value).toLocaleString('en-US', { maximumFractionDigits: 4 }) : '—';
  const textKey = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

  function freshnessLabel(pub) {
    const observed = new Date(pub.observed_at);
    const shown = Number.isNaN(observed.getTime()) ? pub.observed_at : observed.toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone: 'UTC', timeZoneName: 'short' });
    document.querySelector('#receipt-time').textContent = `${shown} · ${String(pub.status || 'dated').toUpperCase()}`;
    const badge = document.querySelector('#freshness');
    badge.className = `freshness ${pub.status === 'fresh' ? '' : 'stale'}`;
    badge.innerHTML = `<i></i>${pub.status === 'fresh' ? 'LIVE RECEIPT' : 'DATED RECEIPT'}`;
  }

  function search(query) {
    const q = textKey(query);
    if (!q || !entries.length) return [];
    const exactId = entries.find(row => String(row.rwa_id) === q);
    if (exactId) return [exactId];
    const words = q.split(' ');
    return entries.map(row => {
      const name = textKey(row.name);
      const symbol = textKey(row.symbol);
      const identity = `${name} ${symbol} ${row.rwa_id}`;
      const exact = name === q || symbol === q;
      const starts = name.startsWith(q) || symbol.startsWith(q);
      const all = words.every(word => identity.includes(word));
      return { row, score: exact ? 0 : starts ? 1 : all ? 2 : 9 };
    }).filter(item => item.score < 9)
      .sort((a, b) => a.score - b.score || a.row.name.localeCompare(b.row.name))
      .slice(0, 8).map(item => item.row);
  }

  function showSuggestions() {
    const matches = search(input.value);
    if (!input.value.trim() || !matches.length) {
      suggestions.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      return;
    }
    suggestions.innerHTML = matches.map(row => `<button type="button" role="option" data-id="${escapeHTML(row.rwa_id)}"><span>${escapeHTML(row.name)} <small>${escapeHTML(row.symbol || 'RWA')}</small></span><small>${stateLabels[row.state] || 'REVIEW'}</small></button>`).join('');
    suggestions.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function render(entry) {
    if (!entry) {
      result.innerHTML = `<div class="empty-state"><span class="empty-orbit">?</span><div><span class="section-label">NO MATCH IN THIS RECEIPT</span><h3>Try another reference or a CMC RWA ID.</h3><p>An absent row is not proof that an asset does not exist.</p></div></div>`;
      return;
    }
    const route = stateLabels[entry.state] || 'REFERENCE ONLY';
    const representations = entry.representations || [];
    const significant = (entry.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET');
    const comparison = entry.comparison;
    const findings = significant.slice(0, 5).map(code => `<li class="${['PRICE_DENOMINATION_BREAK','ZERO_MCAP_POSITIVE_VOLUME'].includes(code) ? 'critical' : 'warning'}">${escapeHTML(signalLabels[code] || code.replaceAll('_', ' ').toLowerCase())}</li>`).join('');
    const compLine = comparison
      ? `${number(comparison.route_count)} quote routes · ${Number(comparison.spread_bps).toFixed(1)} bps observed spread`
      : 'No filtered price comparison in this route';
    const rows = representations.map(row => `<tr><td class="token"><strong>${escapeHTML(row.symbol || '—')}</strong><small>${escapeHTML(row.name || 'Unnamed CMC row')}</small></td><td data-label="Issuer">${escapeHTML(row.issuer_name || 'Issuer not resolved')}</td><td data-label="Quote">${money(row.price)}</td><td data-label="Market cap">${money(row.market_cap)}</td><td data-label="24h volume">${money(row.volume_24h)}</td></tr>`).join('');
    const date = receipt?._publication?.observed_at || receipt?.observed_at;
    const dateText = date ? new Date(date).toISOString().replace('T', ' ').slice(0, 16) + ' UTC' : 'dated receipt';
    result.innerHTML = `<article class="review-result">
      <div class="verdict" data-state="${escapeHTML(entry.state)}"><span class="section-label">CMC RWA #${escapeHTML(entry.rwa_id)} · ${escapeHTML(entry.asset_type || 'reference')}</span><h3>${escapeHTML(route)}</h3><p>${escapeHTML(nextSteps[entry.state] || 'Inspect the published reference fields and keep each unverified claim open.')}</p><p class="limits">A route through reported fields. It is not a backing or liquidity assessment.</p></div>
      <div><div class="result-data"><div><strong>${number(entry.token_count)}</strong><span>representations</span></div><div><strong>${number(entry.issuer_count)}</strong><span>issuer labels</span></div><div><strong>${comparison ? Number(comparison.spread_bps).toFixed(1) + ' bp' : '—'}</strong><span>observed spread</span></div></div><ul class="finding-list">${findings || '<li>No coded warning in this receipt</li>'}</ul></div>
      <section class="representation-table"><header><h4>REPRESENTATION ROWS</h4><span>${escapeHTML(compLine)}</span></header><table><thead><tr><th>Token / row</th><th>Issuer field</th><th>Quote</th><th>Market cap</th><th>24h volume</th></tr></thead><tbody>${rows}</tbody></table></section>
      <div class="review-next"><strong>NEXT DILIGENCE</strong><span>${escapeHTML(nextSteps[entry.state] || 'Keep unobserved claims open and inspect the issuer evidence.')}</span></div>
      <a class="evidence-link" href="/?reference=${encodeURIComponent(entry.rwa_id)}#decision">Open full Bell evidence and case receipt ↗</a>
    </article>`;
    history.replaceState(null, '', `?reference=${encodeURIComponent(entry.rwa_id)}`);
  }

  function renderPopulation(data) {
    const states = data.universe?.states || {};
    document.querySelector('#population-stats').innerHTML = `<div><strong>${number(data.universe?.tokenised_references_scanned)}</strong><span>tokenised references scanned</span></div><div><strong>${number(data.universe?.tokens_scanned)}</strong><span>representation rows inspected</span></div><div class="attention"><strong>${number((states.do_not_compare || 0) + (states.investigate || 0))}</strong><span>need a stop or investigation route</span></div>`;
  }

  async function load() {
    if (localHost && localTools) {
      localTools.hidden = false;
      await refreshKeyStatus();
      setupLocalModes();
    }
    try {
      const response = await fetch('/api/integrity', { cache: 'no-cache', headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error(`Receipt request returned ${response.status}`);
      receipt = await response.json();
      entries = receipt.alert_index || [];
      freshnessLabel(receipt._publication || { observed_at: receipt.observed_at, status: 'dated replay' });
      renderPopulation(receipt);
      const query = new URLSearchParams(location.search).get('reference');
      if (query) {
        const entry = entries.find(item => String(item.rwa_id) === query) || search(query)[0];
        input.value = entry?.name || query;
        render(entry);
      }
    } catch (error) {
      const badge = document.querySelector('#freshness');
      badge.className = 'freshness error';
      badge.innerHTML = '<i></i>RECEIPT UNAVAILABLE';
      document.querySelector('#receipt-time').textContent = 'Could not load a verified receipt';
      result.innerHTML = `<div class="empty-state"><span class="empty-orbit">!</span><div><span class="section-label">LIVE CHECK UNAVAILABLE</span><h3>Bell could not load its receipt.</h3><p>Try again, or use the dated evidence archive on the main site.</p></div></div>`;
    }
  }

  async function refreshKeyStatus() {
    const status = document.querySelector('#key-status');
    try {
      const response = await fetch('/api/key', { cache: 'no-store', headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Local server unavailable');
      const data = await response.json();
      status.textContent = data.configured
        ? 'CMC key is configured in this local server. The key itself is never returned.'
        : 'No local key configured. Dated evidence still works without one.';
      status.dataset.configured = String(Boolean(data.configured));
    } catch {
      status.textContent = 'Local server status unavailable.';
    }
  }

  function setupLocalModes() {
    const visualButton = document.querySelector('#visual-mode');
    const agentButton = document.querySelector('#agent-mode');
    const visualPanel = document.querySelector('#visual-panel');
    const agentPanel = document.querySelector('#agent-panel');
    const selectMode = agent => {
      visualButton.setAttribute('aria-selected', String(!agent));
      agentButton.setAttribute('aria-selected', String(agent));
      visualPanel.hidden = agent;
      agentPanel.hidden = !agent;
    };
    visualButton.addEventListener('click', () => selectMode(false));
    agentButton.addEventListener('click', () => selectMode(true));

    document.querySelector('#key-form').addEventListener('submit', async event => {
      event.preventDefault();
      const input = document.querySelector('#cmc-key');
      const status = document.querySelector('#key-status');
      const key = input.value.trim();
      if (!key) {
        status.textContent = 'Paste your CMC API key first.';
        input.focus();
        return;
      }
      status.textContent = 'Sending the key to the local server…';
      try {
        const response = await fetch('/api/key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ api_key: key }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not configure the local key');
        input.value = '';
        status.textContent = 'CMC key is configured in local server memory. It will be cleared when the server stops.';
        status.dataset.configured = 'true';
      } catch (error) {
        input.value = '';
        status.textContent = error.message;
      }
    });

    document.querySelector('#clear-key').addEventListener('click', async () => {
      const status = document.querySelector('#key-status');
      try {
        const response = await fetch('/api/key', { method: 'DELETE', headers: { Accept: 'application/json' } });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Could not clear the local key');
        status.textContent = data.configured
          ? 'Session key cleared. CMC_API_KEY from the server environment remains active.'
          : 'Local key cleared. Dated evidence still works without one.';
        status.dataset.configured = String(Boolean(data.configured));
      } catch (error) {
        status.textContent = error.message;
      }
    });

    document.querySelector('#copy-agent-url').addEventListener('click', async event => {
      try {
        await navigator.clipboard.writeText(`${location.origin}/api/agent`);
        event.currentTarget.textContent = 'Copied';
      } catch {
        event.currentTarget.textContent = `${location.origin}/api/agent`;
      }
    });
  }

  input.addEventListener('input', showSuggestions);
  input.addEventListener('focus', showSuggestions);
  document.addEventListener('click', event => {
    const option = event.target.closest('[data-id]');
    if (option) {
      const entry = entries.find(row => String(row.rwa_id) === option.dataset.id);
      input.value = entry?.name || '';
      suggestions.hidden = true;
      input.setAttribute('aria-expanded', 'false');
      render(entry);
    } else if (!event.target.closest('#search-form')) {
      suggestions.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }
  });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const match = search(input.value)[0];
    suggestions.hidden = true;
    render(match);
    if (!match) input.focus();
  });
  document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
    input.value = button.dataset.example;
    render(search(button.dataset.example)[0]);
  }));
  load();
})();

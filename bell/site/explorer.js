(() => {
  const byId = id => document.getElementById(id);
  const escapeHTML = value => String(value ?? '').replace(/[&<>\"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  const number = value => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—';
  };
  const money = value => {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return '—';
    if (Math.abs(parsed) >= 1e9) return `$${(parsed / 1e9).toFixed(2)}B`;
    if (Math.abs(parsed) >= 1e6) return `$${(parsed / 1e6).toFixed(2)}M`;
    if (Math.abs(parsed) >= 1e3) return `$${(parsed / 1e3).toFixed(1)}K`;
    return `$${parsed.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  };
  let assets = Array.isArray(window.BELL_CATALOGUE_LIVE?.assets) ? window.BELL_CATALOGUE_LIVE.assets : [];
  const initialURL = new URL(window.location.href);
  const initialMapQuery = initialURL.searchParams.get('map_reference') || '';
  const catalogueReady = assets.length
    ? Promise.resolve(window.BELL_CATALOGUE_LIVE)
    : fetch('catalog.json', { cache: 'no-cache', headers: { Accept: 'application/json' } }).then(response => {
      if (!response.ok) throw new Error(`catalogue HTTP ${response.status}`);
      return response.json();
    }).then(catalogue => {
      assets = Array.isArray(catalogue.assets) ? catalogue.assets : [];
      return catalogue;
    });
  const normalize = value => String(value || '').trim().toLowerCase();
  const slugFor = asset => asset.slug || String(asset.rwa_id || '');
  const explorer = byId('explorer');
  if (!explorer) return;

  const input = byId('explorer-search');
  const matches = byId('explorer-matches');
  const dossier = byId('explorer-dossier');
  const count = byId('explorer-count');
  const freshness = byId('explorer-map-freshness');
  const form = byId('explorer-form');
  const queryFields = asset => [asset.name, asset.symbol, asset.slug, asset.asset_type, asset.rwa_id].map(normalize);
  const mapDate = value => {
    const date = new Date(value || '');
    if (Number.isNaN(date.getTime())) return 'dated snapshot';
    const month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'][date.getUTCMonth()];
    return `${String(date.getUTCDate()).padStart(2, '0')} ${month} ${date.getUTCFullYear()}`;
  };
  const applyCatalogueMeta = catalogue => {
    count.textContent = `${number(catalogue.total_size || assets.length)} mapped references`;
    if (freshness) freshness.textContent = `credential-free map · observed ${mapDate(catalogue.observed_at)} UTC · separate from live receipt`;
  };

  function find(query) {
    const normalized = normalize(query);
    if (!normalized) return [];
    return assets
      .filter(asset => queryFields(asset).some(field => field === normalized) || queryFields(asset).some(field => field.includes(normalized)))
      .sort((left, right) => {
        const leftExact = queryFields(left).some(field => field === normalized) ? 0 : 1;
        const rightExact = queryFields(right).some(field => field === normalized) ? 0 : 1;
        return leftExact - rightExact || Number(left.rwa_rank || 999999) - Number(right.rwa_rank || 999999);
      })
      .slice(0, 8);
  }

  function renderMatches(items, query) {
    if (!query) {
      matches.innerHTML = '<p class="explorer-hint">Search the complete CMC RWA map, including stocks, ETFs, commodities and references with no token wrapper yet</p>';
      return;
    }
    if (!items.length) {
      matches.innerHTML = `<p class="explorer-hint">No reference matched “${escapeHTML(query)}” in the current map receipt</p>`;
      return;
    }
    matches.innerHTML = `<div class="explorer-match-list">${items.map(asset => `<button type="button" class="explorer-match" data-explorer-slug="${escapeHTML(slugFor(asset))}"><span><strong>${escapeHTML(asset.name || 'Unnamed reference')}</strong><small>${escapeHTML(asset.symbol || '—')} · ${escapeHTML(asset.asset_type || 'RWA')} · rank ${escapeHTML(asset.rwa_rank || '—')}</small></span><b>${asset.has_tokens ? 'TOKENISED' : 'REFERENCE ONLY'} ↗</b></button>`).join('')}</div>`;
  }

  function stateLabel(state, tokenCount) {
    if (!tokenCount) return 'REFERENCE ONLY';
    if (state === 'do_not_compare') return 'DO NOT SHORTLIST';
    if (state === 'investigate') return 'INVESTIGATE';
    if (tokenCount === 1) return 'SINGLE REPRESENTATION';
    if (state === 'no_flags') return 'FACTS OPEN';
    return state ? String(state).replaceAll('_', ' ').toUpperCase() : 'DOSSIER PENDING';
  }

  // The map is a dated snapshot of every reference CMC lists; the receipt is the
  // current scan of the ones carrying tokens. Keeping them apart was honest but
  // it made the product look dated: a reader searching the map was told the
  // answer lived somewhere else. Where the live receipt covers the reference,
  // show its current verdict here instead of sending the reader away.
  let liveIndex = null;
  const liveReady = fetch('/api/integrity', { cache: 'no-cache', headers: { Accept: 'application/json' } })
    .then(response => (response.ok ? response.json() : null))
    .then(receipt => {
      if (!receipt) return null;
      const rows = receipt.alert_index || receipt.alerts || [];
      liveIndex = new Map(rows.map(row => [String(row.rwa_id), row]));
      liveIndex.observed_at = receipt.observed_at || null;
      return liveIndex;
    })
    .catch(() => null);

  function liveVerdictFor(asset) {
    if (!liveIndex) return null;
    return liveIndex.get(String(asset.rwa_id || '')) || null;
  }

  function liveVerdictBlock(asset) {
    const row = liveVerdictFor(asset);
    if (!row) {
      return '<div class="explorer-live explorer-live-absent"><span>NOT IN THE CURRENT SCAN</span>'
        + '<p>This reference is in the CoinMarketCap RWA map but carried no token representation in the '
        + 'latest scan, so there is nothing to compare and no verdict to publish.</p></div>';
    }
    const stateLabel = row.state === 'do_not_compare' ? 'DO NOT SHORTLIST'
      : row.state === 'investigate' ? 'INVESTIGATE'
      : Number(row.token_count || 0) === 1 ? 'SINGLE REPRESENTATION' : 'FACTS OPEN';
    const cmp = row.comparison;
    const answer = cmp
      ? `<p class="explorer-live-answer"><strong>${Number(cmp.spread_bps).toFixed(1)} bps</strong> across `
        + `${cmp.route_count} tradable representations · cheapest ${escapeHTML(cmp.cheapest.symbol || '')}`
        + `${cmp.cheapest_is_deepest ? ', which also carries the most volume' : `, but ${escapeHTML(cmp.deepest.symbol || '')} carries more volume`}.</p>`
      : '<p class="explorer-live-answer">No comparison is published for this reference: a coded rule refuses it.</p>';
    return `<div class="explorer-live explorer-live-${escapeHTML(row.state || 'unknown')}">`
      + `<span>CURRENT VERDICT · OBSERVED ${escapeHTML(String(liveIndex.observed_at || '').replace('T', ' ').slice(0, 16))} UTC</span>`
      + `<strong>${escapeHTML(stateLabel)}</strong>${answer}`
      + `<small>${escapeHTML(row.next_action || '')}</small></div>`;
  }

  function renderMapOnly(asset, message = '') {
    dossier.innerHTML = `<div class="explorer-dossier-head"><div><span class="eyebrow">CMC RWA MAP</span><h3>${escapeHTML(asset.name || 'Reference')}</h3><p>${escapeHTML(asset.symbol || '—')} · ${escapeHTML(asset.asset_type || 'RWA')} · reference ID ${escapeHTML(asset.rwa_id || '—')}</p></div><span class="explorer-state">${asset.has_tokens ? 'DOSSIER PENDING' : 'REFERENCE ONLY'}</span></div><div class="explorer-map-grid"><div><small>Token wrappers</small><strong>${asset.has_tokens ? 'Mapped' : 'None mapped'}</strong></div><div><small>Historical data</small><strong>${asset.last_historical_data ? 'Available' : 'Not shown'}</strong></div><div><small>Next route</small><strong>${asset.has_tokens ? 'Wait for dossier' : 'Descriptive brief'}</strong></div></div><p class="explorer-note">${escapeHTML(message || (asset.has_tokens ? 'The reference is in the CMC map, but no server-side dossier has been published for it yet. A request is queued automatically.' : 'There is no wrapper comparison to make. Bell keeps this as a reference-level route instead of inventing a ranking.'))}</p><a class="source-link" href="/api/published?slug=${encodeURIComponent(slugFor(asset))}" target="_blank" rel="noopener">Open credential-free dossier endpoint ↗</a>`;
  }

  function renderDossier(payload, asset) {
    const terminal = payload?.terminal || {};
    const audit = payload?.audit || {};
    const source = audit.evidence || terminal || payload || {};
    const tokens = Array.isArray(source.tokens) ? source.tokens : [];
    const metrics = terminal.metrics || {};
    const findings = Array.isArray(audit.findings) ? audit.findings : (Array.isArray(terminal.findings) ? terminal.findings : []);
    const state = audit.conclusion || terminal.state || 'unknown';
    const publication = payload?._publication || {};
    const publicationStatus = publication.status || 'dated';
    const freshnessLabel = publicationStatus === 'fresh' ? 'FRESH' : publicationStatus === 'stale' ? 'STALE' : 'DATED REPLAY';
    const observed = publication.observed_at || source.observed_at || 'dated observation';
    const freshnessNote = publicationStatus === 'stale'
      ? `This dossier is stale under its ${number(publication.stale_after_seconds)} second freshness contract${publication.refresh_queued ? ' · a refresh is queued' : ''}`
      : publicationStatus === 'fresh'
        ? 'Published evidence is inside its freshness contract · recheck before acting'
        : 'This is a dated replay · it is not a live quote';
    const rows = tokens.slice(0, 10).map(token => `<tr><th>${escapeHTML(token.symbol || token.name || 'Unresolved')}<small>${escapeHTML(token.name || '')}</small></th><td>${escapeHTML(token.issuer_name || 'Unresolved')}</td><td>${token.price == null ? '—' : `$${number(token.price)}`}</td><td>${money(token.market_cap)}</td><td>${money(token.volume_24h)}</td></tr>`).join('');
    const findingMarkup = findings.length ? `<div class="explorer-findings"><span class="eyebrow">WHY THIS ROUTE</span>${findings.slice(0, 4).map(item => `<p><b>${escapeHTML(item.code || 'SIGNAL')}</b> ${escapeHTML(item.message || '')}</p>`).join('')}</div>` : '<p class="explorer-note">No deterministic contradiction was returned in this dossier. That is descriptive, not an approval.</p>';
    const pairStatus = metrics.market_pair_count == null ? 'Not reported' : metrics.market_pair_count === 0 ? 'Not loaded' : number(metrics.market_pair_count);
    const dexCoverage = Number(metrics.dex_contract_token_count || 0) > 0
      ? `${number(metrics.dex_covered_token_count || 0)} / ${number(metrics.dex_contract_token_count)} wrappers`
      : 'Not resolved';
    const networkCount = Number(metrics.network_count || 0);
    const dexContractCount = Number(metrics.dex_contract_token_count || 0);
    const dexCoverageNote = dexContractCount
      ? `${number(metrics.dex_covered_token_count || 0)} of ${number(dexContractCount)} wrappers with contract evidence`
      : `${number(metrics.dex_no_contract_token_count || tokens.length)} rows without a resolved contract`;
    const evidenceContext = `<section class="explorer-context" aria-label="Market evidence context"><div class="explorer-context-head"><span class="eyebrow">EVIDENCE CONTEXT</span><strong>What the live dossier actually resolved</strong></div><div class="explorer-context-grid"><div><small>NETWORK IDENTITY</small><strong>${networkCount ? `${number(networkCount)} networks` : 'Not resolved'}</strong><p>from token metadata</p></div><div><small>DEX CONTRACT COVERAGE</small><strong>${escapeHTML(dexCoverage)}</strong><p>${escapeHTML(dexCoverageNote)}</p></div><div><small>DEX SURFACES</small><strong>${number(metrics.dex_detail_count || 0)} detail · ${number(metrics.dex_pool_count || 0)} pools</strong><p>security ${number(metrics.dex_security_count || 0)} · holders ${number(metrics.dex_holder_count || 0)}</p></div><div><small>CMC MARKET PAIRS</small><strong>${escapeHTML(pairStatus)}</strong><p>${pairStatus === 'Not loaded' ? 'surface unavailable on this API plan, not evidence of no market' : 'observed rows only'}</p></div></div><small class="explorer-context-limit">Coverage records returned surfaces; it does not prove liquidity, backing, depth or executable size.</small></section>`;
    const dossierNote = tokens.length === 0
      ? 'No token wrapper is available for this reference. Bell keeps it as a descriptive reference-only route.'
      : tokens.length === 1
        ? 'One representation is available. Bell shows a dossier and does not rank a single wrapper.'
        : 'Rows are observed fields. Bell does not infer backing, redemption, eligibility, liquidity or executable size.';
    dossier.innerHTML = `<div class="explorer-dossier-head"><div><span class="eyebrow">${freshnessLabel} · PUBLISHED RWA DOSSIER · ${escapeHTML(observed)}</span><h3>${escapeHTML(source.asset?.name || asset.name || 'Reference')}</h3><p>${escapeHTML(source.asset?.symbol || asset.symbol || '—')} · ${escapeHTML(source.asset?.asset_type || asset.asset_type || 'RWA')} · ${tokens.length} representation${tokens.length === 1 ? '' : 's'}</p></div><span class="explorer-state ${state === 'do_not_compare' ? 'blocked' : ''}">${escapeHTML(stateLabel(state, tokens.length))}</span></div><div class="explorer-metrics"><div><small>Tokenised market cap</small><strong>${money(source.asset?.tokenized_market_cap)}</strong></div><div><small>24h tokenised volume</small><strong>${money(source.asset?.tokenized_volume_24h)}</strong></div><div><small>Issuers observed</small><strong>${number(metrics.issuer_count || new Set(tokens.map(token => token.issuer_id).filter(Boolean)).size)}</strong></div><div><small>DEX evidence</small><strong>${escapeHTML(dexCoverage)}</strong></div><div><small>CMC market pairs</small><strong>${escapeHTML(pairStatus)}</strong></div></div><p class="explorer-freshness ${publicationStatus}">${escapeHTML(freshnessNote)}</p>${evidenceContext}${findingMarkup}<div class="explorer-table-wrap"><table class="explorer-table"><thead><tr><th>Representation</th><th>Issuer</th><th>Quote</th><th>MCap</th><th>24h volume</th></tr></thead><tbody>${rows || '<tr><td colspan="5">No token rows returned</td></tr>'}</tbody></table></div><p class="explorer-note">${dossierNote}</p><div class="explorer-actions"><a class="source-link" href="/api/published?slug=${encodeURIComponent(slugFor(asset))}" target="_blank" rel="noopener">Open full receipt ↗</a><button type="button" class="explorer-refresh" data-explorer-refresh="${escapeHTML(slugFor(asset))}">Refresh dossier ↻</button></div>`;
  }

  // Both render paths end in the same container, so the current verdict is
  // appended once here rather than threaded through each of them. It is the
  // same answer whether the reference has a published dossier or only a map row.
  function appendLiveVerdict(asset) {
    if (!asset || !dossier) return;
    if (dossier.querySelector('.explorer-live')) return;
    const apply = () => {
      if (dossier.querySelector('.explorer-live')) return;
      dossier.insertAdjacentHTML('beforeend', liveVerdictBlock(asset));
    };
    if (liveIndex === null) liveReady.then(apply);
    else apply();
  }

  async function load(asset) {
    if (!asset) return;
    dossier.innerHTML = '<p class="explorer-loading">Loading the credential-free published dossier…</p>';
    try {
      const response = await fetch(`/api/published?slug=${encodeURIComponent(slugFor(asset))}`, { cache: 'no-cache', headers: { Accept: 'application/json' } });
      const payload = await response.json();
      if (response.status === 404) {
        renderMapOnly(asset, payload.message);
        appendLiveVerdict(asset);
        return;
      }
      if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
      renderDossier(payload, asset);
      appendLiveVerdict(asset);
    } catch (error) {
      appendLiveVerdict(asset);
      renderMapOnly(asset, `The dossier could not be loaded right now (${error.message}). The map entry remains available for inspection.`);
    }
  }

  function select(slug) {
    const asset = assets.find(item => slugFor(item) === slug);
    if (!asset) return;
    const shareURL = new URL(window.location.href);
    shareURL.searchParams.set('map_reference', slug);
    window.history.replaceState({}, '', shareURL);
    input.value = asset.name || asset.symbol || slug;
    renderMatches([asset], input.value);
    load(asset);
    dossier.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  count.textContent = 'Loading mapped references…';
  renderMatches([], '');
  form.addEventListener('submit', event => {
    event.preventDefault();
    const mapQuery = input.value.trim();
    const shareURL = new URL(window.location.href);
    if (mapQuery) shareURL.searchParams.set('map_reference', mapQuery);
    else shareURL.searchParams.delete('map_reference');
    window.history.replaceState({}, '', shareURL);
    catalogueReady.then(catalogue => {
      const items = find(input.value);
      renderMatches(items, input.value);
      if (items.length) load(items[0]);
      applyCatalogueMeta(catalogue);
    }).catch(error => {
      matches.innerHTML = `<p class="explorer-hint">The reference map could not be loaded (${escapeHTML(error.message)})</p>`;
    });
  });
  matches.addEventListener('click', event => {
    const button = event.target.closest('[data-explorer-slug]');
    if (button) select(button.dataset.explorerSlug);
  });
  dossier.addEventListener('click', event => {
    const button = event.target.closest('[data-explorer-refresh]');
    if (!button) return;
    const asset = assets.find(item => slugFor(item) === button.dataset.explorerRefresh);
    if (asset) load(asset);
  });
  document.querySelectorAll('[data-explorer-example]').forEach(button => button.addEventListener('click', () => {
    input.value = button.dataset.explorerExample;
    form.requestSubmit();
  }));
  catalogueReady.then(catalogue => {
    applyCatalogueMeta(catalogue);
    renderMatches([], '');
    if (initialMapQuery) {
      input.value = initialMapQuery;
      form.requestSubmit();
    }
  }).catch(() => {
    count.textContent = 'Map unavailable';
  });
})();

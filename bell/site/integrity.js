(() => {
  const escapeHTML = value => String(value ?? '').replace(/[&<>'"]/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[character]));
  const byId = id => document.getElementById(id);
  const labelDatedReplayLinks = () => {
    document.querySelectorAll('a[href*="rwa-surface-integrity-latest-replay-2026-09-21.json"]').forEach(link => {
      link.textContent = 'Open last replay receipt · 21 Sep ↗';
    });
    document.querySelectorAll('a[href*="rwa-surface-integrity-inputs-2026-09-21.json"]').forEach(link => {
      link.textContent = 'Open replay inputs · 21 Sep ↗';
    });
  };
  const setHeroProofHeading = text => {
    const element = document.querySelector('.hero-proof .proof-top .eyebrow');
    if (element) element.textContent = text;
  };
  let receipt;
  let filter = 'all';
  const initialURL = new URL(window.location.href);
  const initialReference = initialURL.searchParams.get('reference') || '';
  let query = initialReference.trim();
  let searchAttempted = Boolean(query);
  let pageNumber = 0;
  const pageSize = 12;

  labelDatedReplayLinks();

  const signalLabels = {
    PRICE_DENOMINATION_BREAK: 'observed quote ratio above 10× review threshold',
    PRICE_DISPERSION: 'price dispersion',
    ZERO_MCAP_POSITIVE_VOLUME: 'volume with $0 mcap',
    DERIVATIVE_MIX: 'derivative mix',
    SYMBOL_COLLISION: 'symbol collision',
    MARKET_FIELDS_MISSING: 'missing market fields',
    TOKEN_INFO_MISSING: 'missing token identity',
    NO_TRADFI_MARKET: 'no TradFi market',
  };

  const numericValue = value => {
    if (typeof value === 'boolean' || value === null || value === undefined) return null;
    if (typeof value === 'number') return Number.isFinite(value) ? value : null;
    if (typeof value !== 'string' || value.trim() === '') return null;
    const parsed = Number(value.trim());
    return Number.isFinite(parsed) ? parsed : null;
  };
  const formatNumber = value => {
    const parsed = numericValue(value);
    return parsed === null ? 'N/A' : parsed.toLocaleString(undefined, { maximumFractionDigits: 2 });
  };
  const temporalReceiptPaths = new Map([
    ['1', ['proof/gold-live-2026-09-13.json', 'proof/gold-live-2026-09-17.json']],
    ['14', ['proof/tesla-live-2026-09-13.json', 'proof/tesla-live-2026-09-17.json']],
  ]);
  const temporalReceiptPromises = new Map();

  function temporalReceiptPathsFor(alert) {
    return temporalReceiptPaths.get(String(alert?.rwa_id || '')) || [];
  }

  function temporalPanel(alert) {
    const paths = temporalReceiptPathsFor(alert);
    if (!paths.length) return '';
    return `<section class="temporal-evidence" data-temporal-evidence="${escapeHTML(alert.rwa_id)}"><div class="temporal-evidence-head"><span>REPEAT-WINDOW CHECK</span><b>LOADING ${paths.length} DATED WINDOWS</b></div><p class="temporal-evidence-loading">Reading the credential-free hourly receipts linked to this reference.</p></section>`;
  }

  function temporalReceipt(path) {
    if (!temporalReceiptPromises.has(path)) {
      temporalReceiptPromises.set(path, fetch(path, { headers: { Accept: 'application/json' } }).then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      }));
    }
    return temporalReceiptPromises.get(path);
  }

  function temporalReceipts(paths) {
    return Promise.all(paths.map(path => temporalReceipt(path)));
  }

  function temporalDate(value) {
    return value ? new Date(value).toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }) : 'dated window';
  }

  function temporalRows(receipt) {
    return (receipt.wrappers || []).map(wrapper => {
      const cash = numericValue(wrapper.sessions?.cash?.median_range_pct);
      const weekend = numericValue(wrapper.sessions?.weekend?.median_range_pct);
      return {
        symbol: wrapper.symbol || 'unlabelled',
        issuer: wrapper.issuer || 'issuer not supplied',
        state: wrapper.state || 'unknown',
        cash,
        weekend,
        ratio: cash && weekend !== null ? weekend / cash * 100 : null,
      };
    });
  }

  function temporalMarkup(receipts, paths) {
    const windows = receipts.map((receipt, index) => ({ receipt, path: paths[index], rows: temporalRows(receipt) })).sort((a, b) => String(a.receipt.window?.end_utc || '').localeCompare(String(b.receipt.window?.end_utc || '')));
    const latest = windows.at(-1);
    const first = windows[0];
    const latestUsable = (latest?.rows || []).filter(row => Number.isFinite(row.ratio)).sort((a, b) => a.ratio - b.ratio);
    const firstUsable = (first?.rows || []).filter(row => Number.isFinite(row.ratio)).sort((a, b) => a.ratio - b.ratio);
    const low = latestUsable[0];
    const high = latestUsable[latestUsable.length - 1];
    if (!latest || !low || !high) {
      return `<div class="temporal-evidence-head"><span>REPEAT-WINDOW CHECK</span><b>INSUFFICIENT HISTORY</b></div><p>No wrapper supplied enough valid session medians for a dated comparison.</p><small>No ranking is inferred.</small>`;
    }
    const contrast = high.ratio / low.ratio;
    const firstBySymbol = new Map(firstUsable.map(row => [row.symbol, row]));
    const paired = latestUsable.map(row => ({ latest: row, first: firstBySymbol.get(row.symbol) })).filter(row => row.first);
    const bars = paired.slice().sort((a, b) => a.latest.ratio - b.latest.ratio).slice(0, 4).map(({ first: earlier, latest: current }) => `<div class="temporal-window-row"><div><strong>${escapeHTML(current.symbol)}</strong><small>${escapeHTML(current.issuer)}</small></div><span class="temporal-dual-track"><i class="first" style="width:${Math.min(Math.max(earlier.ratio, 4), 100)}%"></i><i class="latest" style="width:${Math.min(Math.max(current.ratio, 4), 100)}%"></i></span><b>${earlier.ratio.toFixed(0)}% → ${current.ratio.toFixed(0)}%</b></div>`).join('');
    const omitted = paired.length > 4 ? `<small class="temporal-more">${paired.length - 4} more wrappers remain in the repeat-window check</small>` : '';
    const table = paired.map(({ first: earlier, latest: current }) => `<tr><th>${escapeHTML(current.symbol)}<small>${escapeHTML(current.issuer)}</small></th><td>${earlier.ratio.toFixed(0)}%</td><td>${current.ratio.toFixed(0)}%</td><td>${(current.ratio - earlier.ratio >= 0 ? '+' : '')}${(current.ratio - earlier.ratio).toFixed(0)}pp</td></tr>`).join('');
    const overlapHours = first?.receipt?.window?.end_utc && latest?.receipt?.window?.start_utc ? Math.max(0, (Date.parse(first.receipt.window.end_utc) - Date.parse(latest.receipt.window.start_utc)) / 3600000) : 0;
    const repeatLabel = windows.length > 1 ? `${windows.length} WINDOWS · ${paired.length} PAIRED · ${overlapHours > 0 ? `${overlapHours.toFixed(0)}H OVERLAP` : 'NO OVERLAP'}` : `${escapeHTML(temporalDate(latest.receipt.window?.end_utc))} · ${latestUsable.length}/${latest.rows.length} USABLE`;
    const links = windows.map(({ path }, index) => `<a href="${escapeHTML(path || '')}" target="_blank" rel="noopener">Open window ${index + 1} receipt ↗</a><a href="${escapeHTML((path || '').replace(/\.json$/, '.payload.json'))}" target="_blank" rel="noopener">Open window ${index + 1} replay ↗</a>`).join('');
    return `<div class="temporal-evidence-head"><span>${windows.length > 1 ? 'REPEAT-WINDOW CHECK' : 'PUBLISHED TEMPORAL CHECK'}</span><b>${repeatLabel}</b></div><h4>${windows.length > 1 ? 'The weekend contrast appeared in both captured windows' : 'Weekend movement was not uniform across the group'}</h4><p class="temporal-evidence-lede"><strong>${escapeHTML(low.symbol)} ${low.ratio.toFixed(0)}%</strong> of its cash-session range versus <strong>${escapeHTML(high.symbol)} ${high.ratio.toFixed(0)}%</strong> for ${escapeHTML(high.issuer)} in the latest window · ${contrast.toFixed(1)}× between the observed endpoints</p><div class="temporal-legend"><span><i class="first"></i> earlier window</span><span><i class="latest"></i> latest window</span></div><div class="temporal-rows">${bars}</div>${omitted}<details><summary>Open paired wrapper readings</summary><div class="temporal-table-scroll"><table><thead><tr><th>Wrapper</th><th>Earlier</th><th>Latest</th><th>Change</th></tr></thead><tbody>${table}</tbody></table></div></details><p class="temporal-evidence-note">CMC OHLCV receipts · ${windows.length} captured 168-hour windows · hourly range medians. The windows overlap by ${overlapHours.toFixed(0)} hours, so this is a repeat observation, not independent validation or a trend claim. This is not a ranking, fair-value, liquidity or execution test.</p><div class="temporal-evidence-links">${links}</div>`;
  }

  function loadTemporalEvidence(alert) {
    const paths = temporalReceiptPathsFor(alert);
    const target = document.querySelector(`[data-temporal-evidence="${CSS.escape(String(alert?.rwa_id || ''))}"]`);
    if (!paths.length || !target) return;
    temporalReceipts(paths).then(data => {
      if (target.isConnected) target.innerHTML = temporalMarkup(data, paths);
    }).catch(() => {
      if (target.isConnected) target.innerHTML = '<div class="temporal-evidence-head"><span>PUBLISHED TEMPORAL CHECK</span><b>RECEIPT UNAVAILABLE</b></div><p>The dated companion receipt could not be loaded. The current integrity case remains available.</p>';
    });
  }
  function searchMatches(normalizedQuery) {
    if (!receipt || !normalizedQuery) return [];
    return (receipt.alert_index || []).filter(item => [item.name, item.symbol, item.asset_type, item.rwa_id].join(' ').toLowerCase().includes(normalizedQuery));
  }
  function preferredSearchMatch(normalizedQuery) {
    const matches = searchMatches(normalizedQuery);
    const exact = matches.find(item => [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery));
    return exact || matches[0] || null;
  }
  const signalEvidenceSummary = signal => {
    const evidence = signal?.evidence || {};
    if (signal?.code === 'TOKEN_INFO_MISSING') {
      const count = Number(evidence.count || evidence.tokens?.length || 0);
      const labels = (evidence.tokens || []).slice(0, 3).map(token => typeof token === 'object' ? (token.symbol || token.crypto_id || 'unresolved token') : String(token || 'unresolved token'));
      return `${formatNumber(count)} row${count === 1 ? '' : 's'} missing resolved token identity${labels.length ? ` · ${labels.join(', ')}` : ''}`;
    }
    if (evidence.max_min_ratio) return `${formatNumber(evidence.max_min_ratio)}× observed price spread`;
    if (evidence.count && evidence.tokens?.length && evidence.tokens.every(token => typeof token !== 'object')) {
      return `${formatNumber(evidence.count)} row${evidence.count === 1 ? '' : 's'} missing price, market cap or volume · ${evidence.tokens.slice(0, 3).join(', ')}`;
    }
    if (evidence.tokens?.length) return evidence.tokens.slice(0, 2).map(token => {
      if (!token || typeof token !== 'object') return String(token || 'unknown');
      return `${token.symbol || token.crypto_id || 'unknown'} · $${formatNumber(token.market_cap)} mcap · $${formatNumber(token.volume_24h)} volume`;
    }).join(' / ');
    if (evidence.derivatives?.length || evidence.other?.length) return `${(evidence.derivatives || []).join(', ') || 'Derivative row'} vs ${(evidence.other || []).filter(Boolean).slice(0, 3).join(', ') || 'other rows'}`;
    if (evidence.count) return `${formatNumber(evidence.count)} row${evidence.count === 1 ? '' : 's'} missing price, market cap or volume`;
    return signal?.message || 'Rule fired in the current receipt';
  };
  const signalSourceLabel = code => ({
    PRICE_DENOMINATION_BREAK: 'CMC quotes',
    PRICE_DISPERSION: 'CMC quotes',
    ZERO_MCAP_POSITIVE_VOLUME: 'CMC quotes',
    DERIVATIVE_MIX: 'CMC asset list + quotes',
    SYMBOL_COLLISION: 'CMC asset list',
    MARKET_FIELDS_MISSING: 'CMC quotes',
    TOKEN_INFO_MISSING: 'CMC token info',
  }[code] || 'CMC receipt');
  const compactObservation = item => {
    const code = (item.signal_codes || []).find(value => value !== 'NO_TRADFI_MARKET');
    if (!code) return `${formatNumber(item.token_count || 0)} representation rows observed; no published rule hit`;
    return signalEvidenceSummary({ code, evidence: item.signal_evidence?.[code] || {} });
  };
  const worksheetChecks = [
    ['identity_unit', 'I confirmed the exact token, chain and unit'],
    ['issuer_docs', 'I checked the issuer primary documents'],
    ['backing_redemption', 'I verified the backing and redemption terms'],
    ['eligibility_custody', 'I verified eligibility and custody for my account'],
    ['execution', 'I obtained venue, depth, spread and size-specific execution evidence'],
  ];
  const investorTaskKey = 'bell-investor-task-v1';
  const receiptMemoryKey = 'bell-integrity-receipt-memory-v1';
  const watchlistKey = 'bell-rwa-watchlist-v1';
  const investorTaskSteps = [1, 2, 3, 4];
  const externalURL = value => {
    try {
      const url = new URL(String(value || ''));
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  };

  function readInvestorTask() {
    try {
      const value = JSON.parse(localStorage.getItem(investorTaskKey) || '{}');
      return { steps: value.steps || {} };
    } catch {
      return { steps: {} };
    }
  }

  function saveInvestorTask(task) {
    try {
      localStorage.setItem(investorTaskKey, JSON.stringify({ steps: task.steps || {}, saved_at: new Date().toISOString() }));
    } catch {
      // The task is optional and never affects the receipt.
    }
  }

  function renderInvestorTask() {
    const task = readInvestorTask();
    investorTaskSteps.forEach(step => {
      const item = document.querySelector(`[data-task-step="${step}"]`);
      if (item) item.classList.toggle('complete', Boolean(task.steps[step]));
    });
    const complete = investorTaskSteps.filter(step => task.steps[step]).length;
    const progress = byId('task-progress');
    if (progress) progress.textContent = complete === 4
      ? '4/4 complete · handoff saved locally · no investment approval'
      : `${complete}/4 complete · saved only in this browser`;
  }

  function completeInvestorTaskStep(step) {
    const task = readInvestorTask();
    task.steps[step] = true;
    saveInvestorTask(task);
    renderInvestorTask();
  }

  function readWatchlist() {
    try {
      const value = JSON.parse(localStorage.getItem(watchlistKey) || '[]');
      return Array.isArray(value) ? value : [];
    } catch {
      return [];
    }
  }

  function saveWatchlist(items) {
    try {
      localStorage.setItem(watchlistKey, JSON.stringify(items.slice(0, 50)));
    } catch {
      // Watchlist state is optional and never affects the published receipt.
    }
  }

  function watchButton(item) {
    const watched = readWatchlist().some(entry => String(entry.rwa_id) === String(item.rwa_id));
    return `<button class="watch-button${watched ? ' is-watched' : ''}" type="button" data-watch-id="${escapeHTML(item.rwa_id)}">${watched ? 'Watching reference' : 'Watch reference'}</button>`;
  }

  function renderWatchlist() {
    if (!receipt) return;
    let target = byId('watchlist-panel');
    if (!target) {
      target = document.createElement('section');
      target.id = 'watchlist-panel';
      target.className = 'watchlist-panel';
      const list = byId('alert-list');
      list?.parentNode?.insertBefore(target, list);
    }
    const items = readWatchlist();
    target.hidden = items.length === 0;
    if (!items.length) {
      target.innerHTML = '';
      return;
    }
    const current = new Map((receipt.alert_index || []).map(item => [String(item.rwa_id), item]));
    const rows = items.map(entry => {
      const now = current.get(String(entry.rwa_id));
      const changed = now && entry.state && now.state !== entry.state;
      const label = now ? displayDecisionLabel(now, 'FACTS OPEN') : 'NOT IN RECEIPT';
      return `<div class="watchlist-row"><div><strong>${escapeHTML(entry.name || `Reference ${entry.rwa_id}`)}</strong><small>${escapeHTML(entry.symbol || '')} · saved ${escapeHTML(String(entry.observed_at || '').replace('T', ' ').replace('Z', ' UTC'))}</small></div><span class="watchlist-state${changed ? ' changed' : ''}">${changed ? 'STATE CHANGED' : escapeHTML(label)}</span><button type="button" class="watch-remove" data-watch-remove="${escapeHTML(entry.rwa_id)}">Remove</button></div>`;
    }).join('');
    target.innerHTML = `<div class="watchlist-head"><div><span class="eyebrow">YOUR WATCHLIST</span><h3>Return to the references that matter</h3></div><span>${items.length} saved locally</span></div><p>Saved in this browser only. A changed state means the current receipt differs from the observation you saved.</p>${rows}`;
  }

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
    return `<small class="identity-line">Identity: RWA ${escapeHTML(rwaId || 'N/A')} · token ${escapeHTML(token.crypto_id || 'unresolved')} · issuer ${escapeHTML(token.issuer_id || 'unresolved')}</small>`;
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
    return items.map(item => `<li>${escapeHTML(item)}</li>`).join('') || '<li>No additional evidence fields</li>';
  }

  function renderTokenTable(alert) {
    const tokens = alert.tokens || alert.representations || [];
    const rows = tokens.map(token => {
      const website = externalURL(token.issuer_website);
      const cmcURL = externalURL(token.cmc_url);
      const symbol = escapeHTML(token.symbol || 'N/A');
      const selector = token.crypto_id != null ? `<input type="checkbox" data-wrapper-select="${escapeHTML(token.crypto_id)}" aria-label="Select ${symbol} for fact comparison">` : '';
      const tokenCell = `${cmcURL ? `<a href="${escapeHTML(cmcURL)}" target="_blank" rel="noopener">${symbol} ↗</a>` : symbol}<small>${escapeHTML(token.crypto_id || 'no id')}</small>${sourceLinks(token, true)}`;
      const issuer = escapeHTML(token.issuer_name || token.issuer_catalogue_name || 'unlinked');
      const issuerCell = website ? `<a href="${escapeHTML(website)}" target="_blank" rel="noopener">${issuer} ↗</a>` : issuer;
      const platforms = (token.platforms || []).map(platform => `${escapeHTML(platform.name || 'unknown chain')} · ${escapeHTML(platform.contract_address || 'no contract')}`).join('<br>') || 'not resolved';
      return `<tr><td>${selector}</td><td>${tokenCell}${identityLine(token, alert.rwa_id)}</td><td>${escapeHTML(token.name || 'N/A')}</td><td>${issuerCell}</td><td>${platforms}</td><td>${formatNumber(token.price)}</td><td>${formatNumber(token.market_cap)}</td><td>${formatNumber(token.volume_24h)}</td></tr>`;
    }).join('');
    return `<p class="token-table-note">Swipe horizontally to inspect identity, issuer, chain and quote fields</p><div class="token-table-wrap"><table class="token-table"><caption class="sr-only">Observed token representations for ${escapeHTML(alert.name || alert.symbol || 'this reference')}</caption><thead><tr><th scope="col">Select</th><th scope="col">Token</th><th scope="col">Representation</th><th scope="col">Issuer</th><th scope="col">Chain / contract</th><th scope="col">Price</th><th scope="col">MCap</th><th scope="col">24h vol</th></tr></thead><tbody>${rows || '<tr><td colspan="8">No token rows returned.</td></tr>'}</tbody></table></div><div class="wrapper-compare" data-wrapper-compare="${escapeHTML(alert.rwa_id)}"><p><b>Compare two observed wrappers</b> Select up to two rows for a factual side-by-side. Bell will not rank them or turn this into an allocation decision.</p><div data-comparison-output class="comparison-output">Select two rows to inspect their observed differences.</div></div>`;
  }

  function renderComparisonOutput(alert, selectedIds) {
    const tokens = (alert.tokens || alert.representations || []).filter(token => selectedIds.includes(String(token.crypto_id)));
    if (tokens.length < 2) return 'Select two rows to inspect their observed differences.';
    if (tokens.length > 2) return 'Select only two rows for the side-by-side view.';
    const [left, right] = tokens;
    const observedField = (key, label, suffix = '') => {
      const rawValues = [left[key], right[key]];
      const values = rawValues.map(value => {
        const number = numericValue(value);
        return {
          present: number !== null && number >= 0,
          number: number === null ? 0 : number,
        };
      });
      const displayValue = (value, present) => present ? `${formatNumber(value)}${suffix}` : 'missing';
      if (!values.every(value => value.present)) return `<div><span>${label}</span><strong>Not comparable</strong><small>${displayValue(values[0].number, values[0].present)} vs ${displayValue(values[1].number, values[1].present)} · missing field is not treated as zero</small></div>`;
      const numericValues = values.map(value => value.number);
      const low = Math.min(...numericValues);
      const high = Math.max(...numericValues);
      const gap = low === 0 ? (numericValues[0] === 0 && numericValues[1] === 0 ? 'both zero' : 'zero / non-zero') : `${formatNumber(((high - low) / low) * 100)}% gap`;
      return `<div><span>${label}</span><strong>${gap}</strong><small>${displayValue(numericValues[0], true)} vs ${displayValue(numericValues[1], true)} · observed field only</small></div>`;
    };
    const observedDeltas = `<div class="comparison-deltas"><span class="comparison-deltas-label">OBSERVED FIELD DIFFERENCES</span><div class="comparison-delta-grid">${observedField('price', 'Price')}${observedField('market_cap', 'Market cap')}${observedField('volume_24h', '24h volume')}</div><small class="comparison-deltas-note">Differences are descriptive. Bell does not normalize units, backing, eligibility, liquidity or execution.</small></div>`;
    const cards = tokens.map(token => {
      const platforms = (token.platforms || []).map(platform => `${platform.name || 'unknown chain'} · ${platform.contract_address || 'no contract'}`).join(' / ') || 'not resolved';
      const website = externalURL(token.issuer_website);
      const issuer = website ? `<a href="${escapeHTML(website)}" target="_blank" rel="noopener">${escapeHTML(token.issuer_name || 'unlinked')} ↗</a>` : escapeHTML(token.issuer_name || 'unlinked');
      return `<div class="comparison-card"><strong>${escapeHTML(token.symbol || token.name || 'token')}</strong><span>${escapeHTML(token.name || 'N/A')}</span>${identityLine(token, alert.rwa_id)}<small>Issuer: ${issuer}</small><small>Chain / contract: ${escapeHTML(platforms)}</small><small>Observed price: ${formatNumber(token.price)} · MCap: ${formatNumber(token.market_cap)} · 24h volume: ${formatNumber(token.volume_24h)}</small>${sourceLinks(token)}</div>`;
    }).join('');
    const prefix = alert.state === 'do_not_compare'
      ? '<b>DO NOT SHORTLIST</b><span>A Bell critical rule fired for this reference. These facts are shown for investigation, not as equivalent exposure.</span>'
      : '<b>FACTS ONLY · NO WRAPPER RANKING</b><span>Observed quote fields are not normalized for unit, backing, eligibility or execution.</span>';
    return `<div class="comparison-verdict">${prefix}</div>${observedDeltas}<div class="comparison-cards">${cards}</div>`;
  }

  function briefButton(rwaId) {
    return `<button class="brief-button" type="button" data-brief-id="${escapeHTML(rwaId)}">Save decision brief</button>`;
  }

  function worksheetKey(rwaId) {
    return `bell-research-worksheet-${rwaId}`;
  }

  function capitalBudgetKey(rwaId) {
    return `bell-capital-budget-${rwaId}`;
  }

  function readCapitalBudget(rwaId) {
    try {
      const value = Number(localStorage.getItem(capitalBudgetKey(rwaId)) || 10000);
      return Number.isFinite(value) && value > 0 ? value : 10000;
    } catch {
      return 10000;
    }
  }

  function saveCapitalBudget(rwaId, value) {
    try {
      localStorage.setItem(capitalBudgetKey(rwaId), String(value));
    } catch {
      // The capital check remains useful when browser storage is unavailable.
    }
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
    return `<details class="research-worksheet"><summary>Open research worksheet</summary><p class="worksheet-note">Local handoff for your research process. These checks are your record, not Bell verification or investment approval.</p><div class="worksheet-checks">${checks}</div><textarea aria-label="Research note for ${escapeHTML(item.name || item.symbol || 'this reference')}" data-worksheet-note="${escapeHTML(item.rwa_id)}" placeholder="Add the one unresolved question or source you want to carry into the memo">${escapeHTML(worksheet.note)}</textarea><div class="worksheet-footer"><span data-worksheet-status="${escapeHTML(item.rwa_id)}">${escapeHTML(worksheetStateLabel(worksheet))}</span><button type="button" class="brief-button" data-save-worksheet="${escapeHTML(item.rwa_id)}">Save local worksheet</button></div></details>`;
  }

  function renderHandoff(item) {
    if (item.state === 'do_not_compare') {
      return '<div class="alert-handoff"><span>TO CLEAR THIS CASE</span><ol><li>Match the RWA ID to the token ID and issuer ID</li><li>Confirm the exact instrument and unit, then verify issuer and redemption terms</li><li>Obtain venue and execution evidence before comparing wrappers</li></ol></div>';
    }
    if (Number(item.token_count || 0) === 1) {
      return '<div class="alert-handoff"><span>SINGLE REPRESENTATION PATH</span><p>CMC returned one representation for this reference, so there is no wrapper ranking to perform. Verify the instrument, issuer, backing, redemption, eligibility, custody and executable liquidity before treating it as investable.</p></div>';
    }
    if (item.state === 'investigate') {
      return '<div class="alert-handoff"><span>TO MOVE FORWARD</span><p>Classify the representation, confirm the issuer and missing fields, then keep unresolved wrappers separate in the research memo.</p></div>';
    }
    return '<div class="alert-handoff"><span>FACTS OPEN PATH</span><p>No published Bell rule fired for this reference. You may inspect the observed rows, but run external checks for backing, eligibility, redemption, custody and executable liquidity before treating any wrapper as investable.</p></div>';
  }

  function renderCompactRoute(item) {
    const route = item.state === 'do_not_compare'
      ? 'Resolve identity, unit and market evidence'
      : Number(item.token_count || 0) === 1
        ? 'No comparison route; verify instrument and issuer terms'
        : item.state === 'investigate'
          ? 'Classify the representation and verify missing fields'
          : 'Complete external backing and execution checks';
    return `<div class="compact-route"><span>NEXT CHECK</span><p>${route}</p></div>`;
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
    const receiptLabel = publication ? `${publication.source === 'dated_static' ? 'DATED REPLAY' : 'LIVE RECEIPT'} · ${String(status).toUpperCase()}` : 'DATED RECEIPT';
    byId('receipt-status-label').textContent = receiptLabel;
    const heroProofStatus = document.querySelector('.proof-id');
    if (heroProofStatus) heroProofStatus.textContent = publication?.source === 'dated_static'
      ? 'DATED REPLAY'
      : `LIVE RECEIPT · ${String(status).toUpperCase()}`;
    const glossary = document.querySelector('.plain-words dl');
    if (glossary && !glossary.dataset.extended) {
      glossary.insertAdjacentHTML('beforeend', '<div><dt>HHI</dt><dd>A concentration index from 0 to 10,000; higher means reported value is held by fewer issuer labels</dd></div><div><dt>Effective issuer count</dt><dd>A simple equivalent count based only on positive reported market-cap shares, not a count of real issuers</dd></div>');
      glossary.dataset.extended = 'true';
    }
    byId('metric-references').textContent = universe.tokenised_references_scanned.toLocaleString();
    byId('metric-tokens').textContent = universe.tokens_scanned.toLocaleString();
    byId('metric-blocked').textContent = universe.states.do_not_compare.toLocaleString();
    byId('metric-unaddressable').textContent = receipt.catalogue_integrity.asset_list_rows_without_rwa_id.toLocaleString();
    if (receipt.method?.scan_status !== 'ready') byId('receipt-status-label').textContent += ' · INPUT INCOMPLETE';
  }

  function renderThesisStrip() {
    const copy = byId('thesis-copy');
    const proof = byId('thesis-proof');
    const metrics = byId('thesis-metrics');
    if (!copy || !proof || !metrics || !receipt) return;
    const states = receipt.universe?.states || {};
    const total = Number(receipt.universe?.tokenised_references_scanned || Object.values(states).reduce((sum, value) => sum + Number(value || 0), 0));
    if (!total) return;
    const blocked = Number(states.do_not_compare || 0);
    const investigate = Number(states.investigate || 0);
    const clear = Number(states.no_flags || 0);
    const unresolved = blocked + investigate;
    const share = (unresolved / total) * 100;
    copy.textContent = `${share.toFixed(1)}% of the scanned references need identity or market-data follow-up before a wrapper comparison. This routes the next question; it is not a safety score or an approval label`;
    const issuerValues = new Map();
    let positiveRows = 0;
    let nonPositiveRows = 0;
    (receipt.alert_index || []).flatMap(item => item.representations || []).forEach(token => {
      const cap = numericValue(token.market_cap);
      if (cap === null || cap <= 0) {
        nonPositiveRows += 1;
        return;
      }
      positiveRows += 1;
      const issuerKey = token.issuer_id || token.issuer_name || token.issuer_catalogue_name || 'unlinked issuer label';
      const current = issuerValues.get(issuerKey) || { value: 0, label: token.issuer_name || token.issuer_catalogue_name || 'unlinked issuer label' };
      current.value += cap;
      issuerValues.set(issuerKey, current);
    });
    const issuerTotals = [...issuerValues.values()].map(item => item.value);
    const reportedValue = issuerTotals.reduce((sum, value) => sum + value, 0);
    const topFive = issuerTotals.sort((a, b) => b - a).slice(0, 5).reduce((sum, value) => sum + value, 0);
    proof.textContent = reportedValue > 0
      ? `The top five issuer labels hold ${(topFive / reportedValue * 100).toFixed(1)}% of positive reported market cap across ${positiveRows.toLocaleString()} rows. ${nonPositiveRows.toLocaleString()} rows have no positive market-cap field`
      : 'No positive market-cap fields were available for the population concentration check';
    metrics.innerHTML = `<div class="thesis-metric blocked"><strong>${blocked.toLocaleString()}</strong><span>do not shortlist</span></div><div class="thesis-metric investigate"><strong>${investigate.toLocaleString()}</strong><span>investigate first</span></div><div class="thesis-metric clear"><strong>${clear.toLocaleString()}</strong><span>facts open</span></div>`;
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
    return evidence || '<li>No compact numerical evidence was published for this index row</li>';
  }

  function displayDecisionLabel(item, fallback = 'REVIEW') {
    if (item?.state === 'do_not_compare' || item?.decision?.state === 'blocked') return 'DO NOT SHORTLIST';
    if (item?.state === 'investigate') return 'INVESTIGATE';
    if (item?.state === 'no_flags' && Number(item?.token_count || 0) === 1) return 'SINGLE REPRESENTATION';
    if (item?.state === 'no_flags') return 'FACTS OPEN';
    return item?.decision?.label || fallback;
  }

  function capitalPanel(alert) {
    const assessment = window.BellCapitalImpact.assess(alert, readCapitalBudget(alert.rwa_id));
    const rangeMetrics = assessment.metrics?.ratio
      ? `<div><span>OBSERVED RANGE</span><strong>${formatNumber(assessment.metrics.ratio)}×</strong></div><div><span>UNITS AT LOW QUOTE</span><strong>${formatNumber(assessment.metrics.unitsAtLowQuote)}</strong></div><div><span>UNITS AT HIGH QUOTE</span><strong>${formatNumber(assessment.metrics.unitsAtHighQuote)}</strong></div>`
      : '';
    const volumeMetrics = assessment.metrics?.volume
      ? `<div><span>AMOUNT / REPORTED 24H VOLUME</span><strong>${formatNumber(assessment.metrics.volume.amountSharePercent)}%</strong></div>`
      : '';
    const metrics = rangeMetrics || volumeMetrics
      ? `<div class="capital-metrics">${rangeMetrics}${volumeMetrics}</div><small class="capital-metrics-note">Nominal quote units only. Reported 24h volume is a rolling field, not depth or executable exit capacity. Rows remain non-comparable until Bell's identity and unit checks are cleared.</small>`
      : '<div class="capital-metrics capital-metrics-empty"><span>No comparable quote range in this receipt.</span></div>';
    return `<section class="capital-panel capital-${assessment.mode}" data-capital-panel="${escapeHTML(alert.rwa_id || '')}">
      <div class="capital-panel-head"><span>CAPITAL CHECK</span><b>Make the financial consequence visible</b></div>
      <label class="capital-budget">Amount under consideration <span>$</span><input type="number" min="1" max="1000000000" step="100" value="${assessment.budget}" inputmode="decimal" data-capital-budget aria-label="Amount under consideration"></label>
      <strong data-capital-headline>${escapeHTML(assessment.headline)}</strong>
      <p data-capital-copy>${escapeHTML(assessment.copy)}</p>
      <div data-capital-metrics>${metrics}</div>
      <small data-capital-note>${escapeHTML(assessment.note)}</small>
    </section>`;
  }

  function observedQuoteEndpoints(item) {
    const tokens = item?.tokens || item?.representations || [];
    const band = window.BellCapitalImpact.quoteBand(tokens);
    if (!band) return '';
    const volume = row => row.volumeState === 'positive'
      ? formatNumber(row.volume)
      : row.volumeState === 'zero' ? '0 reported' : 'missing';
    const rows = band.rows.map(row => `<tr><th>${escapeHTML(row.token.symbol || row.token.name || 'unlabelled')}<small>${escapeHTML(row.token.name || '')}</small></th><td>${escapeHTML(row.token.issuer_name || row.token.issuer_catalogue_name || 'issuer not resolved')}</td><td>${formatNumber(row.price)}</td><td class="quote-band-delta">${row.deltaPercent >= 0 ? '+' : ''}${row.deltaPercent.toFixed(2)}%</td><td>${volume(row)}</td></tr>`).join('');
    return `<section class="search-evidence" data-search-evidence><div class="search-evidence-head"><span>OBSERVED QUOTE BAND</span><b>${formatNumber(band.ratio)}×</b></div><p class="search-evidence-lede">${band.rows.length} priced representations around a ${formatNumber(band.median)} median quote</p><div class="quote-band-scroll"><span class="quote-band-scroll-hint">SWIPE FOR QUOTE · MEDIAN GAP · VOLUME →</span><table class="quote-band-table"><thead><tr><th>Representation</th><th>Issuer</th><th>Quote</th><th>Vs median</th><th>24h volume</th></tr></thead><tbody>${rows}</tbody></table></div><small>CMC quote rows in this receipt · relative to the observed median only · not a ranking, discount, backing, liquidity or executable spread</small></section>`;
  }

  function referenceConcentrationPanel(alert) {
    const tokens = alert?.tokens || alert?.representations || [];
    if (tokens.length < 2) {
      return `<section class="reference-concentration-panel"><div class="reference-concentration-head"><span>ISSUER CONCENTRATION</span><b>SINGLE REPRESENTATION</b></div><p>This reference has one observed representation, so there is no issuer concentration comparison to make.</p><small>Check the instrument, issuer, backing, redemption and execution terms directly.</small></section>`;
    }
    const groups = new Map();
    let missing = 0;
    let zero = 0;
    let reportedValue = 0;
    tokens.forEach(token => {
      const hasValue = token?.market_cap !== null && token?.market_cap !== undefined && token?.market_cap !== '';
      const value = Number(token?.market_cap);
      if (!hasValue || !Number.isFinite(value)) {
        missing += 1;
        return;
      }
      if (!(value > 0)) {
        zero += 1;
        return;
      }
      const key = token.issuer_id || token.issuer_name || 'unresolved';
      const group = groups.get(key) || { name: token.issuer_name || 'Unresolved issuer', value: 0, rows: 0 };
      group.value += value;
      group.rows += 1;
      groups.set(key, group);
      reportedValue += value;
    });
    if (!(reportedValue > 0)) {
      return `<section class="reference-concentration-panel"><div class="reference-concentration-head"><span>ISSUER CONCENTRATION</span><b>NOT CALCULABLE</b></div><p>No positive token-level market-cap values were reported for this reference in the receipt.</p><small>${missing} missing rows · ${zero} zero rows</small></section>`;
    }
    const issuers = [...groups.values()].sort((a, b) => b.value - a.value);
    const shares = issuers.map(item => item.value / reportedValue);
    const hhi = shares.reduce((sum, share) => sum + (share * 100) ** 2, 0);
    const effective = 1 / shares.reduce((sum, share) => sum + share ** 2, 0);
    const top = issuers[0];
    const topShare = top.value / reportedValue;
    const concentrationRead = topShare >= 0.8
      ? 'Treat this reference as concentrated issuer exposure until the top issuer’s backing and redemption terms are checked'
      : topShare >= 0.5
        ? 'Keep issuer concentration separate from token count and verify whether the alternatives are genuinely independent'
        : 'Issuer exposure is distributed across the reported rows; continue with unit, venue and redemption checks';
    const money = value => value >= 1e9 ? `$${(value / 1e9).toFixed(2)}bn` : value >= 1e6 ? `$${(value / 1e6).toFixed(1)}m` : `$${Math.round(value).toLocaleString()}`;
    return `<section class="reference-concentration-panel"><div class="reference-concentration-head"><span>ISSUER CONCENTRATION · THIS REFERENCE</span><b>${(topShare * 100).toFixed(1)}% TOP ISSUER</b></div><h4>${escapeHTML(top.name)} carries ${(topShare * 100).toFixed(1)}% of positive reported value</h4><div class="reference-concentration-metrics"><div><strong>${hhi.toFixed(0)}</strong><span>HHI / 10,000</span></div><div><strong>${effective.toFixed(2)}</strong><span>EFFECTIVE ISSUERS</span></div><div><strong>${money(reportedValue)}</strong><span>REPORTED VALUE</span></div></div><p>${issuers.length} issuer labels across ${tokens.length} representations · ${missing} missing market-cap rows · ${zero} zero rows</p><p class="reference-concentration-action"><b>NEXT CHECK</b> ${escapeHTML(concentrationRead)}</p><small>Reported token-level market cap only. This is not legal issuer concentration, backing, reserves, redemption or investability.</small></section>`;
  }

  function resolutionRoute(alert) {
    const codes = new Set((alert?.signals || []).map(signal => signal.code).concat(alert?.signal_codes || []));
    const steps = [];
    if (codes.has('TOKEN_INFO_MISSING') || codes.has('SYMBOL_COLLISION')) {
      steps.push(['IDENTITY', 'Resolve crypto_id, issuer_id, chain and contract before treating two rows as the same instrument']);
    }
    if (codes.has('PRICE_DENOMINATION_BREAK')) {
      steps.push(['UNIT', 'Check denomination, decimals, share basis and quote currency; do not call the spread a discount yet']);
    }
    if (codes.has('DERIVATIVE_MIX')) {
      steps.push(['INSTRUMENT', 'Separate derivative-labelled rows from spot-like representations before comparing the group']);
    }
    if (codes.has('MARKET_FIELDS_MISSING') || codes.has('ZERO_MCAP_POSITIVE_VOLUME')) {
      steps.push(['MARKET DATA', 'Confirm price, market-cap and volume completeness and freshness; missing values stay unresolved']);
    }
    steps.push(['TERMS', 'Verify backing, redemption, eligibility, venue depth and size-specific execution with primary sources']);
    const visible = steps.slice(0, 4);
    return `<section class="resolution-route"><div class="resolution-route-head"><span>RESOLUTION ROUTE</span><b>${alert?.state === 'do_not_compare' ? 'WHAT TO CHECK BEFORE RE-RUNNING' : 'WHAT TO CHECK NEXT'}</b></div><div class="resolution-route-grid">${visible.map(([label, copy], index) => `<div><strong>${String(index + 1).padStart(2, '0')} · ${label}</strong><p>${escapeHTML(copy)}</p></div>`).join('')}</div><small>This route explains the next diligence step. It does not diagnose the cause or certify the instrument.</small></section>`;
  }

  function referenceActivityPanel(alert) {
    const tokens = alert?.tokens || alert?.representations || [];
    if (!tokens.length) return '';
    const rows = tokens.map(token => {
      const volume = numericValue(token.volume_24h);
      const state = volume === null || volume < 0 ? 'missing' : volume === 0 ? 'zero' : 'positive';
      return {
        symbol: token.symbol || token.name || 'row',
        state,
        volume: volume || 0,
      };
    });
    const active = rows.filter(row => row.state === 'positive');
    const missing = rows.filter(row => row.state === 'missing').length;
    const zero = rows.filter(row => row.state === 'zero').length;
    const total = active.reduce((sum, row) => sum + row.volume, 0);
    if (!(total > 0)) {
      return `<section class="reference-activity-panel"><div class="reference-activity-head"><span>OBSERVED ACTIVITY · TOKEN ROWS</span><b>NO REPORTED ACTIVITY</b></div><p>No positive 24h volume was reported for this reference in the receipt.</p><small>${missing} missing rows · ${zero} zero rows. This is not proof that the instrument cannot be traded.</small></section>`;
    }
    const top = [...active].sort((a, b) => b.volume - a.volume)[0];
    const topShare = top.volume / total;
    const coverage = active.length / rows.length;
    const activityRead = coverage < 0.5
      ? 'Most representations do not report positive activity. Do not treat the lowest quote as executable until venue and depth evidence is checked'
      : topShare >= 0.8
        ? `Reported activity is concentrated in ${top.symbol}. Treat the comparison as route-dependent until venue and depth evidence is checked`
        : 'Reported activity is spread across several rows, but 24h volume still is not order-book depth or executable size';
    const money = value => value >= 1e9 ? `$${(value / 1e9).toFixed(2)}bn` : value >= 1e6 ? `$${(value / 1e6).toFixed(1)}m` : `$${Math.round(value).toLocaleString()}`;
    return `<section class="reference-activity-panel"><div class="reference-activity-head"><span>OBSERVED ACTIVITY · TOKEN ROWS</span><b>${(topShare * 100).toFixed(1)}% TOP ROW</b></div><h4>${money(total)} reported 24h volume across ${active.length} of ${rows.length} rows</h4><div class="reference-activity-metrics"><div><strong>${(coverage * 100).toFixed(0)}%</strong><span>POSITIVE ACTIVITY COVERAGE</span></div><div><strong>${(topShare * 100).toFixed(1)}%</strong><span>TOP ROW SHARE</span></div><div><strong>${money(total)}</strong><span>REPORTED 24H VOLUME</span></div></div><p class="reference-activity-action"><b>NEXT CHECK</b> ${escapeHTML(activityRead)}</p><small>CMC token-row volume is a rolling 24h field. It is a routing clue, not venue depth, liquidity, price discovery or executable size. ${missing} missing rows · ${zero} zero rows.</small></section>`;
  }

  function refreshCapitalPanel(panel) {
    if (!panel || !receipt) return;
    const rwaId = panel.dataset.capitalPanel;
    const alert = (receipt.alerts || []).find(item => String(item.rwa_id) === String(rwaId))
      || (receipt.alert_index || []).find(item => String(item.rwa_id) === String(rwaId));
    if (!alert) return;
    const value = panel.querySelector('[data-capital-budget]')?.value;
    saveCapitalBudget(rwaId, value);
    const assessment = window.BellCapitalImpact.assess(alert, value);
    panel.className = `capital-panel capital-${assessment.mode}`;
    panel.querySelector('[data-capital-headline]').textContent = assessment.headline;
    panel.querySelector('[data-capital-copy]').textContent = assessment.copy;
    const metrics = assessment.metrics;
    const rangeMetrics = metrics?.ratio
      ? `<div><span>OBSERVED RANGE</span><strong>${formatNumber(metrics.ratio)}×</strong></div><div><span>UNITS AT LOW QUOTE</span><strong>${formatNumber(metrics.unitsAtLowQuote)}</strong></div><div><span>UNITS AT HIGH QUOTE</span><strong>${formatNumber(metrics.unitsAtHighQuote)}</strong></div>`
      : '';
    const volumeMetrics = metrics?.volume
      ? `<div><span>AMOUNT / REPORTED 24H VOLUME</span><strong>${formatNumber(metrics.volume.amountSharePercent)}%</strong></div>`
      : '';
    panel.querySelector('[data-capital-metrics]').innerHTML = metrics
      ? `<div class="capital-metrics">${rangeMetrics}${volumeMetrics}</div><small class="capital-metrics-note">Nominal unit counts only. Reported 24h volume is a rolling field, not depth or executable exit capacity. Rows remain non-comparable until Bell's identity and unit checks are cleared.</small>`
      : '<div class="capital-metrics capital-metrics-empty"><span>No comparable quote range in this receipt.</span></div>';
    panel.querySelector('[data-capital-note]').textContent = assessment.note;
  }

  function renderAlertRow(alert) {
      const labels = alert.signals.filter(signal => signal.severity !== 'info').map(signal => signalLabels[signal.code] || signal.code).slice(0, 3).join(' · ');
      const evidence = alert.signals.filter(signal => signal.severity !== 'info').map(signal => `<div class="evidence-rule"><b>${escapeHTML(signalLabels[signal.code] || signal.code)}</b><p>${escapeHTML(signal.message)}</p><ul>${renderEvidence(signal)}</ul></div>`).join('');
      const stateLabel = alert.state === 'no_flags' ? 'FACTS OPEN' : alert.state === 'do_not_compare' ? 'DO NOT SHORTLIST' : alert.state.replaceAll('_', ' ').toUpperCase();
      const decision = alert.decision || {};
      return `<article class="alert-row" data-rwa-id="${escapeHTML(alert.rwa_id)}"><div class="alert-name">${escapeHTML(alert.name)}<small>${escapeHTML(alert.symbol)} · ${escapeHTML(alert.asset_type)} · ${alert.issuer_count} issuers</small></div><div class="alert-state ${alert.state === 'investigate' ? 'investigate' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML(labels)}</div><div class="alert-tokens"><strong>${alert.token_count}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(displayDecisionLabel(alert))}</b><p>${escapeHTML(decision.consequence || '')}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(alert.next_action)}</div>${renderHandoff(alert)}<div class="alert-tools">${watchButton(alert)}${briefButton(alert.rwa_id)}</div><details class="alert-details"><summary>Inspect evidence</summary>${evidence}<h4>Representation rows</h4>${renderTokenTable(alert)}</details>${renderWorksheet(alert)}</article>`;
  }

  function renderIndexRow(item, detail) {
    if (detail) return renderAlertRow(detail);
    const stateLabel = item.state === 'no_flags' ? 'FACTS OPEN' : item.state === 'do_not_compare' ? 'DO NOT SHORTLIST' : String(item.state || '').replaceAll('_', ' ').toUpperCase();
    const decision = item.decision || {};
    return `<article class="alert-row compact-row" data-rwa-id="${escapeHTML(item.rwa_id)}"><div class="alert-name">${escapeHTML(item.name)}<small>${escapeHTML(item.symbol)} · ${escapeHTML(item.asset_type)} · ${item.issuer_count || 0} issuers · RWA ${escapeHTML(item.rwa_id)}</small></div><div class="alert-state ${item.state === 'investigate' ? 'investigate' : item.state === 'no_flags' ? 'clear' : ''}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML((item.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET').slice(0, 3).map(code => signalLabels[code] || code).join(' · ') || 'No published rule hit')}</div><div class="alert-tokens"><strong>${Number(item.token_count || 0).toLocaleString()}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(displayDecisionLabel(item, 'FACTS OPEN'))}</b><p>${escapeHTML(decision.consequence || '')}</p><p class="compact-observation"><span>OBSERVED</span> ${escapeHTML(compactObservation(item))}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(item.next_action || '')}</div>${renderCompactRoute(item)}<div class="alert-tools">${watchButton(item)}${briefButton(item.rwa_id)}</div><details class="alert-details"><summary>Inspect representations</summary><p class="compact-note">CMC quote rows observed in this receipt. Bell uses them to route research, not to certify backing, eligibility, liquidity or equivalence.</p><ul class="compact-evidence">${renderCompactEvidence(item)}</ul>${renderTokenTable(item)}</details>${renderWorksheet(item)}</article>`;
  }

  function markdownBrief(item) {
    const decision = item.decision || {};
    const capital = window.BellCapitalImpact.assess(item, readCapitalBudget(item.rwa_id));
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
      const tokenCell = cmcURL ? `[${token.symbol || 'N/A'}](${cmcURL})` : (token.symbol || 'N/A');
      const platforms = (token.platforms || []).map(platform => `${platform.name || 'unknown chain'}: ${platform.contract_address || 'no contract'}`).join('<br>') || 'not resolved';
      const sourceURLs = [token.cmc_url, token.issuer_website, token.project_url, ...(token.explorer_urls || []), ...(token.technical_doc_urls || [])].filter(Boolean);
      const sourceCells = sourceURLs.length ? sourceURLs.map(url => `[link](${url})`).join(' ') : 'none';
      return `| ${tokenCell} (${token.crypto_id || 'no id'}) | ${token.name || 'N/A'} | ${issuerCell} (${token.issuer_id || 'no id'}) | ${platforms} | ${formatNumber(token.price)} | ${formatNumber(token.market_cap)} | ${formatNumber(token.volume_24h)} | ${sourceCells} |`;
    }).join('\n');
    const worksheet = readWorksheet(item.rwa_id);
    const worksheetLines = worksheetChecks.map(([key, label]) => `- [${worksheet.checks[key] ? 'x' : ' '}] ${label}`).join('\n');
    return `# Bell decision brief: ${item.name || 'RWA reference'}

Generated from the credential-free Bell receipt. This is research triage, not investment advice.

## Decision

- Reference: ${item.name || 'N/A'} (${item.symbol || 'N/A'})
- RWA ID: ${item.rwa_id || 'N/A'}
- Asset type: ${item.asset_type || 'N/A'}
- State: ${displayDecisionLabel(item)}
- Published rule state: ${item.state === 'no_flags' ? 'FACTS OPEN' : String(item.state || '').replaceAll('_', ' ').toUpperCase()}
- Consequence: ${decision.consequence || 'No allocation status is produced by this monitor'}
- Observed: ${receipt.observed_at || 'N/A'}
- Published: ${receipt._publication?.published_at || 'N/A'}

## Evidence

${signalLines}

## Next action

${item.next_action || 'Continue external diligence before comparing or allocating.'}

## Capital check

- Amount under consideration: ${capital.budget.toLocaleString(undefined, { maximumFractionDigits: 0 })}
- Bell route: ${capital.headline}
- Financial interpretation: ${capital.copy}
- Observed range: ${capital.metrics ? `${formatNumber(capital.metrics.ratio)}× · ${formatNumber(capital.metrics.unitsAtLowQuote)} nominal units at the low quote vs ${formatNumber(capital.metrics.unitsAtHighQuote)} at the high quote` : 'Unavailable'}
- Boundary: ${capital.note}

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
    // A blocked or single-representation case completes the route by saving
    // its handoff; it must not force the user into an invalid pair comparison.
    completeInvestorTaskStep(3);
    completeInvestorTaskStep(4);
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function caseReceipt(item) {
    const publication = receipt?._publication || {};
    return {
      schema_version: 'bell.case-receipt.v1',
      observed_at: receipt?.observed_at || null,
      published_at: publication.published_at || null,
      source: '/api/integrity',
      credential_free: publication.credential_free === true,
      question: 'Do these representations deserve to be compared as if they represented the same investable thing?',
      reference: {
        rwa_id: item.rwa_id,
        name: item.name || null,
        symbol: item.symbol || null,
        asset_type: item.asset_type || null,
        token_count: item.token_count || (item.tokens || []).length,
        issuer_count: item.issuer_count || null,
        tradfi_market_count: item.tradfi_market_count ?? null,
      },
      decision: item.decision || null,
      next_action: item.next_action || null,
      signals: item.signals || [],
      tokens: item.tokens || item.representations || [],
      method: {
        join_key: receipt?.method?.join_key || 'rwa_id',
        token_join_key: receipt?.method?.token_join_key || 'crypto_id',
        rules: receipt?.method?.rules || [],
      },
      source_hashes: receipt?.source_hashes || {},
      limits: [
        'Observed CMC fields do not prove backing, redemption, custody, eligibility, solvency, liquidity or executable size',
        'The case is a research triage record, not an investment recommendation',
      ],
    };
  }

  function downloadCaseReceipt(rwaId) {
    const item = (receipt.alerts || []).find(alert => String(alert.rwa_id) === String(rwaId))
      || (receipt.alert_index || []).find(alert => String(alert.rwa_id) === String(rwaId));
    if (!item) return;
    const filename = `bell-${String(item.symbol || item.name || 'rwa').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}-case-receipt.json`;
    const blob = new Blob([JSON.stringify(caseReceipt(item), null, 2)], { type: 'application/json;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  async function copyCaseLink(rwaId, button) {
    const item = (receipt?.alerts || []).find(alert => String(alert.rwa_id) === String(rwaId))
      || (receipt?.alert_index || []).find(alert => String(alert.rwa_id) === String(rwaId));
    if (!item) return;
    const shareURL = new URL(window.location.href);
    shareURL.searchParams.set('reference', String(item.rwa_id));
    const text = shareURL.toString();
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const fallback = document.createElement('textarea');
      fallback.value = text;
      fallback.setAttribute('readonly', '');
      fallback.style.position = 'fixed';
      fallback.style.opacity = '0';
      document.body.appendChild(fallback);
      fallback.select();
      document.execCommand('copy');
      fallback.remove();
    }
    const original = button.textContent;
    button.textContent = 'Case link copied';
    window.setTimeout(() => { button.textContent = original; }, 1400);
  }

  function renderAlerts() {
    if (!receipt) return;
    const indexed = receipt.alert_index || receipt.alerts || [];
    const normalizedQuery = query.trim().toLowerCase();
    const details = new Map((receipt.alerts || []).map(alert => [String(alert.rwa_id), alert]));
    const candidates = indexed.filter(item => {
      const stateMatches = filter === 'all' || item.state === filter;
      const haystack = [item.name, item.symbol, item.asset_type, item.rwa_id].join(' ').toLowerCase();
      return stateMatches && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
    const exactMatches = normalizedQuery
      ? candidates.filter(item => [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery))
      : [];
    const matching = exactMatches.length ? exactMatches : candidates;
    const totalPages = Math.max(1, Math.ceil(matching.length / pageSize));
    pageNumber = Math.min(pageNumber, totalPages - 1);
    const start = pageNumber * pageSize;
    const visible = matching.slice(start, start + pageSize);
    const focusAction = normalizedQuery && matching.length ? ' <button type="button" class="focus-action" data-open-first-evidence>Open first evidence ↓</button>' : '';
    const range = matching.length ? `${start + 1}-${Math.min(start + pageSize, matching.length)}` : '0';
    byId('alert-count').innerHTML = `Showing <strong>${range}</strong> of <strong>${matching.length}</strong> matching references · ${indexed.length.toLocaleString()} references scanned · representation rows remain inspectable for each indexed reference.${focusAction}`;
    byId('alert-list').innerHTML = visible.map(item => renderIndexRow(item, details.get(String(item.rwa_id)))).join('') || '<p class="section-note">No references match this filter.</p>';
    const pagination = byId('alert-pagination');
    if (pagination) {
      pagination.innerHTML = matching.length > pageSize
        ? `<button type="button" data-page="${pageNumber - 1}" ${pageNumber === 0 ? 'disabled' : ''} aria-label="Previous population page">Previous</button><span>Page ${pageNumber + 1} of ${totalPages}</span><button type="button" data-page="${pageNumber + 1}" ${pageNumber === totalPages - 1 ? 'disabled' : ''} aria-label="Next population page">Next</button>`
        : '';
    }
    renderWatchlist();
  }

  function renderSearchResult() {
    const result = byId('search-result');
    if (!result) return;
    const normalizedQuery = query.trim().toLowerCase();
    if (!receipt || !normalizedQuery) {
      result.hidden = true;
      result.innerHTML = '';
      return;
    }
    const matches = searchMatches(normalizedQuery);
    const item = preferredSearchMatch(normalizedQuery);
    if (!item) {
      result.hidden = false;
      result.innerHTML = `<span>SEARCH RESULT</span><strong>No live case found for “${escapeHTML(query)}”</strong><p>This reference may still exist in the full CMC RWA map, even when Bell has not published a dossier for it yet.</p><a href="#explorer" data-open-map-query="${escapeHTML(query)}">Search the full RWA map ↓</a>`;
      return;
    }
    const state = displayDecisionLabel(item);
    const next = item.state === 'do_not_compare'
      ? 'Resolve the identity, unit and quote contradiction before comparing wrappers.'
      : item.state === 'investigate'
        ? 'Classify the representation and keep unresolved wrappers separate.'
        : Number(item.token_count || 0) === 1
          ? 'There is no wrapper ranking to perform; verify the instrument and issuer externally.'
          : 'Open the rows for a factual side-by-side, then complete external diligence.';
    result.hidden = false;
    const exact = [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery);
    const matchLabel = exact ? `${matches.filter(candidate => [candidate.name, candidate.symbol, candidate.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery)).length || 1} MATCH · EXACT MATCH` : `${matches.length} MATCH${matches.length === 1 ? '' : 'ES'} · SHOWING FIRST`;
    result.innerHTML = `<span>SEARCHED REFERENCE · ${matchLabel}</span><strong>${escapeHTML(item.name || item.symbol || 'Reference')} · ${escapeHTML(item.symbol || 'RWA')}</strong><p>${formatNumber(item.token_count || 0)} representations · ${formatNumber(item.issuer_count || 0)} issuers · <b>${state}</b></p><p>${escapeHTML(next)}</p>${capitalPanel(item)}${observedQuoteEndpoints(item)}<div class="search-result-actions"><a href="#monitor">Inspect this evidence ↓</a><a href="#explorer" data-open-map-query="${escapeHTML(item.rwa_id || item.name || item.symbol || '')}">Open live dossier context ↓</a></div>`;
  }

  function searchFromHero(event) {
    event.preventDefault();
    const input = byId('hero-search');
    query = input.value.trim();
    searchAttempted = true;
    const shareURL = new URL(window.location.href);
    if (query) shareURL.searchParams.set('reference', query);
    else shareURL.searchParams.delete('reference');
    window.history.replaceState({}, '', shareURL);
    pageNumber = 0;
    byId('alert-search').value = input.value;
    if (query) completeInvestorTaskStep(1);
    if (!receipt) return;
    filter = 'all';
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('selected', item.dataset.filter === 'all'));
    renderAlerts();
    renderSearchResult();
    renderDecisionStory();
    if (!query) {
      byId('search-result').hidden = false;
      byId('search-result').innerHTML = '<span>SEARCH RESULT</span><strong>Enter a reference to begin</strong><p>Try Silver, Gold, Tesla, SPY or an RWA ID.</p>';
      byId('hero-search').focus();
      return;
    }
    const target = window.matchMedia('(max-width: 900px)').matches ? byId('search-result') : byId('decision');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderSignals() {
    const signals = receipt.universe.signals;
    const cards = [
      ['PRICE_DENOMINATION_BREAK', 'groups above the 10× quote-ratio review threshold', 'A comparison may be mixing units or claim types.'],
      ['ZERO_MCAP_POSITIVE_VOLUME', 'volume with zero market cap', 'The quote surface needs investigation before it becomes a market claim.'],
      ['DERIVATIVE_MIX', 'groups mix derivatives', 'A derivative-labelled representation is not silently treated as spot.'],
      ['MARKET_FIELDS_MISSING', 'groups with missing fields', 'Absence stays visible. It is never converted into zero.'],
      ['TOKEN_INFO_MISSING', 'groups with missing token identity', 'A crypto ID without resolved chain or contract identity stays out of a clean shortlist.'],
    ];
    byId('signal-grid').innerHTML = cards.map(([code, title, copy]) => `<article class="signal-card"><strong>${signals[code] || 0}</strong><h3>${title}</h3><p>${copy}</p></article>`).join('');
    const chart = byId('signal-chart');
    if (chart) {
      const chartRows = cards.map(([code, title]) => ({ code, title, value: Number(signals[code] || 0) }));
      const maxValue = Math.max(...chartRows.map(row => row.value), 1);
      chart.innerHTML = `<div class="signal-chart-head"><div><span class="eyebrow">OBSERVED SIGNAL COUNTS</span><h3>Where the population needs a second look</h3></div><span class="chart-note">groups in this receipt</span></div><div class="signal-chart-axis"><span>0</span><span>${maxValue.toLocaleString()}</span></div><div class="signal-bars">${chartRows.map(row => `<div class="signal-bar-row"><span class="signal-bar-label">${escapeHTML(row.title)}</span><div class="signal-bar-track"><i style="width:${Math.max((row.value / maxValue) * 100, row.value ? 2 : 0)}%"></i></div><strong>${row.value.toLocaleString()}</strong></div>`).join('')}</div><p class="signal-chart-caption">Counts are groups flagged by each deterministic rule. A group may appear in more than one bar.</p>`;
    }
  }

  function renderPopulationVisual() {
    const target = byId('population-visual-grid');
    if (!target || !receipt) return;
    const states = receipt.universe?.states || {};
    const total = Object.values(states).reduce((sum, value) => sum + Number(value || 0), 0) || 1;
    const stateRows = [
      ['do_not_compare', 'DO NOT SHORTLIST', 'blocked', 'Critical rule fired'],
      ['investigate', 'INVESTIGATE', 'investigate', 'Keep wrappers separate'],
      ['no_flags', 'FACTS OPEN', 'clear', 'Descriptive only, still not approval'],
    ];
    const stateVisual = stateRows.map(([key, label, tone, note]) => {
      const value = Number(states[key] || 0);
      return `<div class="population-state"><div><span>${label}</span><strong>${value.toLocaleString()}</strong></div><small>${note}</small><div class="population-state-track"><i class="${tone}" style="width:${Math.max((value / total) * 100, value ? 1 : 0)}%"></i></div></div>`;
    }).join('');
    const bands = [
      ['&lt;2×', value => value < 2],
      ['2×–5×', value => value >= 2 && value < 5],
      ['5×–10×', value => value >= 5 && value < 10],
      ['10×+', value => value >= 10],
    ].map(([label, test]) => ({ label, test, value: 0 }));
    let pricedReferences = 0;
    (receipt.alert_index || []).forEach(item => {
      const prices = (item.representations || []).map(token => Number(token?.price)).filter(value => Number.isFinite(value) && value > 0);
      if (prices.length < 2) return;
      pricedReferences += 1;
      const ratio = Math.max(...prices) / Math.min(...prices);
      const band = bands.find(entry => entry.test(ratio));
      if (band) band.value += 1;
    });
    const maxBand = Math.max(...bands.map(band => band.value), 1);
    const spreadVisual = bands.map(band => `<div class="spread-row"><span>${band.label}</span><div class="spread-track"><i style="width:${Math.max((band.value / maxBand) * 100, band.value ? 2 : 0)}%"></i></div><strong>${band.value.toLocaleString()}</strong></div>`).join('');
    target.innerHTML = `<article class="population-chart-panel state-panel"><div class="population-chart-top"><span class="eyebrow">ROUTE BY STATE</span><strong>${total.toLocaleString()} references</strong></div><h3>Most references need investigation before comparison</h3><div class="population-states">${stateVisual}</div><div class="population-stacked" aria-label="Stacked population state bar">${stateRows.map(([key, label, tone]) => `<i class="${tone}" style="width:${Math.max((Number(states[key] || 0) / total) * 100, Number(states[key] || 0) ? 1 : 0)}%" title="${label}: ${Number(states[key] || 0).toLocaleString()}"></i>`).join('')}</div></article><article class="population-chart-panel spread-panel"><div class="population-chart-top"><span class="eyebrow">OBSERVED QUOTE SPREAD</span><strong>${pricedReferences.toLocaleString()} references</strong></div><h3>Where multiple priced representations diverge</h3><div class="spread-rows">${spreadVisual}</div><p class="population-chart-note">A band describes the largest observed quote divided by the smallest in one reference. It identifies a review route, not a fair-value gap.</p></article>`;
  }

  function renderConcentrationVisual() {
    const target = byId('concentration-visual-grid');
    if (!target || !receipt) return;
    const representations = (receipt.alert_index || []).flatMap(item => item.representations || []);
    const groups = new Map();
    let pricedTokens = 0;
    let missingTokens = 0;
    let zeroValueTokens = 0;
    let reportedValue = 0;
    representations.forEach(token => {
      const cap = Number(token?.market_cap);
      const hasCap = token?.market_cap !== null && token?.market_cap !== undefined && token?.market_cap !== '';
      if (!hasCap || !Number.isFinite(cap)) {
        missingTokens += 1;
        return;
      }
      if (!(cap > 0)) {
        zeroValueTokens += 1;
        return;
      }
      pricedTokens += 1;
      reportedValue += cap;
      const key = token.issuer_id || token.issuer_name || 'unlinked';
      const current = groups.get(key) || { name: token.issuer_name || 'Unresolved issuer', value: 0, tokens: 0 };
      current.value += cap;
      current.tokens += 1;
      groups.set(key, current);
    });
    const issuers = [...groups.values()].sort((a, b) => b.value - a.value);
    const topFive = issuers.slice(0, 5);
    const topFiveValue = topFive.reduce((sum, issuer) => sum + issuer.value, 0);
    const shares = issuers.map(issuer => issuer.value / (reportedValue || 1));
    const hhi = shares.reduce((sum, share) => sum + (share * 100) ** 2, 0);
    const effectiveIssuers = shares.length ? 1 / shares.reduce((sum, share) => sum + share ** 2, 0) : 0;
    const money = value => {
      if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}bn`;
      if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}m`;
      if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}k`;
      return `$${Math.round(value).toLocaleString()}`;
    };
    const maxValue = Math.max(...topFive.map(issuer => issuer.value), 1);
    const issuerBars = topFive.map(issuer => {
      const share = issuer.value / (reportedValue || 1);
      return `<div class="issuer-bar-row"><div class="issuer-bar-label"><span>${escapeHTML(issuer.name)}</span><strong>${(share * 100).toFixed(1)}%</strong></div><div class="issuer-bar-track"><i style="width:${Math.max((issuer.value / maxValue) * 100, 2)}%"></i></div><small>${money(issuer.value)} · ${issuer.tokens.toLocaleString()} priced token${issuer.tokens === 1 ? '' : 's'}</small></div>`;
    }).join('');
    const coverageTotal = representations.length || 1;
    const coverageRows = [
      ['Positive market cap', pricedTokens, 'positive-value token rows', 'priced'],
      ['Missing market cap', missingTokens, 'null or unavailable rows', 'missing'],
      ['Zero or no value', zeroValueTokens, 'explicit zero rows', 'zero'],
    ].map(([label, value, note, tone]) => `<div class="coverage-row"><div><span>${label}</span><strong>${value.toLocaleString()}</strong></div><small>${note}</small><div class="coverage-track"><i class="${tone}" style="width:${Math.max((value / coverageTotal) * 100, value ? 1 : 0)}%"></i></div></div>`).join('');
    target.innerHTML = `<article class="concentration-panel issuer-panel"><div class="concentration-panel-top"><span class="eyebrow">REPORTED VALUE BY ISSUER</span><strong>${money(reportedValue)}</strong></div><h3>Five issuer labels carry ${(topFiveValue / (reportedValue || 1) * 100).toFixed(1)}% of positive reported value</h3><div class="issuer-bars">${issuerBars}</div><p class="concentration-note">${issuers.length.toLocaleString()} issuer labels carry reported value · HHI ${hhi.toFixed(0)} / 10,000 · effective issuer count ${effectiveIssuers.toFixed(2)}</p><small class="concentration-definition">HHI rises as reported value concentrates. Effective issuer count is an equivalent-share estimate, not a count of legal issuers.</small></article><article class="concentration-panel coverage-panel"><div class="concentration-panel-top"><span class="eyebrow">DATA COVERAGE</span><strong>${representations.length.toLocaleString()} rows</strong></div><h3>${missingTokens.toLocaleString()} token rows do not report market cap in this receipt</h3><div class="coverage-rows">${coverageRows}</div><p class="concentration-note">Value shares use positive token-level market-cap fields only. The denominator is not the full tokenised-asset market.</p></article>`;
  }

  function readReceiptMemory() {
    try {
      const value = JSON.parse(localStorage.getItem(receiptMemoryKey) || 'null');
      return value && value.schema_version === 'bell.integrity.receipt-memory.v1' ? value : null;
    } catch {
      return null;
    }
  }

  function saveReceiptMemory() {
    try {
      localStorage.setItem(receiptMemoryKey, JSON.stringify({
        schema_version: 'bell.integrity.receipt-memory.v1',
        observed_at: receipt.observed_at || null,
        states: receipt.universe?.states || {},
        signals: receipt.universe?.signals || {},
        saved_at: new Date().toISOString(),
      }));
    } catch {
      // Browser memory is optional and never changes the receipt.
    }
  }

  function renderReceiptDelta() {
    const target = byId('receipt-delta');
    if (!target || !receipt) return;
    const previous = readReceiptMemory();
    if (!previous) {
      target.innerHTML = '<div class="receipt-delta-head"><span>RECEIPT MEMORY</span><small>LOCAL TO THIS BROWSER</small></div><strong>First visit has no prior receipt to compare</strong><p>Return after the next publication to see which signal counts changed. This memory is not an additional market-data source.</p>';
      saveReceiptMemory();
      return;
    }
    const changes = [];
    const labels = { do_not_compare: 'blocked groups', investigate: 'investigate groups', no_flags: 'clear groups' };
    const currentStates = receipt.universe?.states || {};
    Object.entries(labels).forEach(([key, label]) => {
      const delta = Number(currentStates[key] || 0) - Number(previous.states?.[key] || 0);
      if (delta) changes.push(`${label} ${delta > 0 ? '+' : ''}${delta.toLocaleString()}`);
    });
    const signalCodes = new Set([...Object.keys(previous.signals || {}), ...Object.keys(receipt.universe?.signals || {})]);
    signalCodes.forEach(code => {
      const delta = Number(receipt.universe?.signals?.[code] || 0) - Number(previous.signals?.[code] || 0);
      if (delta) changes.push(`${signalLabels[code] || code} ${delta > 0 ? '+' : ''}${delta.toLocaleString()}`);
    });
    const sameObservation = previous.observed_at === receipt.observed_at;
    const headline = sameObservation ? 'No new observation since the last visit' : changes.length ? 'The population changed since the last receipt' : 'A new receipt arrived with unchanged counts';
    const detail = sameObservation
      ? `This browser last saw the same observation at ${previous.observed_at || 'an unknown time'}.`
      : `Compared with the observation at ${previous.observed_at || 'an unknown time'}, using deterministic receipt counts only.`;
    target.innerHTML = `<div class="receipt-delta-head"><span>RECEIPT MEMORY</span><small>LOCAL TO THIS BROWSER</small></div><strong>${escapeHTML(headline)}</strong><p>${escapeHTML(detail)}</p>${changes.length ? `<ul>${changes.map(change => `<li>${escapeHTML(change)}</li>`).join('')}</ul>` : ''}`;
    saveReceiptMemory();
  }

  function renderPublicationHistory(history) {
    const target = byId('publication-history');
    const storedObservations = Array.isArray(history?.observations) ? history.observations : [];
    const liveObservation = receipt?.observed_at && receipt?.universe
      ? {
        observed_at: receipt.observed_at,
        tokenised_references_scanned: receipt.universe.tokenised_references_scanned,
        tokens_scanned: receipt.universe.tokens_scanned,
        states: receipt.universe.states || {},
        signals: receipt.universe.signals || {},
      }
      : null;
    const observations = liveObservation && storedObservations.at(-1)?.observed_at !== liveObservation.observed_at
      ? [...storedObservations, liveObservation]
      : storedObservations;
    const heroTrail = byId('hero-receipt-trail');
    if (heroTrail) {
      heroTrail.textContent = Array.isArray(observations) && observations.length
        ? `RECEIPT TRAIL · ${observations.length} dated observations · live receipt included`
        : 'RECEIPT TRAIL · no dated history available';
      if (!byId('hero-receipt-link')) {
        heroTrail.insertAdjacentHTML('afterend', '<a id="hero-receipt-link" class="hero-receipt-link" href="/api/integrity" target="_blank" rel="noopener">OPEN CREDENTIAL-FREE RECEIPT ↗</a>');
      }
    }
    if (!target || !Array.isArray(observations) || observations.length < 2) return;
    const previous = observations[observations.length - 2];
    const latest = observations[observations.length - 1];
    const delta = (key) => Number(latest.states?.[key] || 0) - Number(previous.states?.[key] || 0);
    const signed = (value) => `${value > 0 ? '+' : ''}${value.toLocaleString()}`;
    const visibleObservations = observations.slice(-9);
    const historyBars = visibleObservations.map(item => {
      const states = item.states || {};
      const total = Number(item.tokenised_references_scanned || 0) || 1;
      const stamp = String(item.observed_at || '').slice(5, 10);
      return `<div class="history-point" title="${escapeHTML(item.observed_at || '')}"><div class="history-stack"><i class="blocked" style="height:${Math.max((Number(states.do_not_compare || 0) / total) * 100, 1)}%"></i><i class="investigate" style="height:${Math.max((Number(states.investigate || 0) / total) * 100, 1)}%"></i><i class="clear" style="height:${Math.max((Number(states.no_flags || 0) / total) * 100, 1)}%"></i></div><small>${escapeHTML(stamp)}</small></div>`;
    }).join('');
    target.innerHTML = `<div class="publication-history-head"><div><span class="eyebrow">PUBLICATION HISTORY</span><h3>What changed between the two receipts</h3></div><span>${escapeHTML(previous.observed_at || 'prior')} → ${escapeHTML(latest.observed_at || 'latest')}</span></div><div class="publication-history-grid"><div><strong>${signed(delta('do_not_compare'))}</strong><small>blocked groups</small></div><div><strong>${signed(delta('investigate'))}</strong><small>investigate groups</small></div><div><strong>${signed(delta('no_flags'))}</strong><small>clear groups</small></div><div><strong>${signed(Number(latest.signals?.PRICE_DENOMINATION_BREAK || 0) - Number(previous.signals?.PRICE_DENOMINATION_BREAK || 0))}</strong><small>price spread signals</small></div></div><div class="history-chart" aria-label="State composition across published receipts"><div class="history-chart-label"><span>STATE COMPOSITION · LAST ${visibleObservations.length} OF ${observations.length} RECEIPTS</span><small>each column is one dated summary</small></div><div class="history-bars">${historyBars}</div></div><p>Counts are from the published summaries, not inferred market impact. The receipts cover ${Number(latest.tokenised_references_scanned || 0).toLocaleString()} tokenised references and ${Number(latest.tokens_scanned || 0).toLocaleString()} representations.</p>`;
  }

  async function loadPublicationHistory() {
    const target = byId('publication-history');
    if (!target || window.location.protocol === 'file:') return;
    try {
      const response = await fetch('proof/rwa-surface-integrity-history.json', { cache: 'no-store', headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      renderPublicationHistory(await response.json());
    } catch {
      target.innerHTML = '<p class="publication-history-unavailable">Publication history is available in the linked receipt file.</p>';
      const heroTrail = byId('hero-receipt-trail');
      if (heroTrail) {
        heroTrail.textContent = 'RECEIPT TRAIL · open the evidence index';
        if (!byId('hero-receipt-link')) heroTrail.insertAdjacentHTML('afterend', '<a id="hero-receipt-link" class="hero-receipt-link" href="proof/rwa-surface-integrity-replay-index.md" target="_blank" rel="noopener">OPEN EVIDENCE INDEX ↗</a>');
      }
    }
  }

  function renderIdentity() {
    const identity = receipt.identity_integrity || {};
    const catalogue = receipt.catalogue_integrity || {};
    const duplicateIds = Object.keys(catalogue.asset_list_duplicate_ids || {}).length;
    byId('identity-proof').innerHTML = `<div class="identity-proof-block"><span>IDENTITY JOIN CHECK</span><strong>${formatNumber(identity.info_unique_ids || 0)} / ${formatNumber(identity.tokenised_map_ids || 0)} tokenised references resolved through info</strong><small>${formatNumber(identity.issuer_catalogue_rows || 0)} issuer records · ${formatNumber(identity.quote_issuer_ids || 0)} issuer IDs seen in quotes · ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved issuer joins · ${formatNumber(identity.crypto_info_rows || 0)} token identity rows · ${formatNumber((identity.quote_crypto_ids_missing_from_info || []).length)} unresolved token joins</small></div><div class="identity-proof-block"><span>CMC SURFACE DRIFT</span><strong>${formatNumber(catalogue.map_rows || 0)} map rows · ${formatNumber(catalogue.asset_list_rows || 0)} asset-list rows</strong><small>${formatNumber(catalogue.asset_list_rows_without_rwa_id || 0)} rows without stable RWA ID · ${formatNumber(duplicateIds)} duplicate asset IDs · ${formatNumber((catalogue.map_ids_not_in_asset_list || []).length)} map IDs absent from asset list</small></div>`;
  }

  function renderDifferentiation() {
    const identity = receipt.identity_integrity || {};
    byId('differentiation').innerHTML = `<div class="diff-column"><span>CMC AND SCREENS SHOW THE CANDIDATES</span><strong>References, wrappers, issuers and latest quote fields</strong><p>That is the discovery and comparison layer. A row being grouped under one reference does not prove that its economic claim, unit or market data is equivalent.</p></div><div class="diff-arrow">→</div><div class="diff-column accent"><span>BELL STRESS-TESTS THE GROUPING</span><strong>A gate across the scanned references before a wrapper enters your shortlist</strong><p>${formatNumber(receipt.universe.states.do_not_compare)} blocked groups, ${formatNumber(receipt.universe.signals.PRICE_DENOMINATION_BREAK || 0)} denomination breaks and ${formatNumber((identity.quote_issuer_ids_missing_from_catalogue || []).length)} unresolved issuer joins in this receipt. This is an integrity decision, not a token ranking.</p></div>`;
  }

  function renderDecisionStory() {
    const normalizedQuery = query.trim().toLowerCase();
    const focused = normalizedQuery ? preferredSearchMatch(normalizedQuery) : null;
    const focusedDetail = focused && (receipt.alerts || []).find(item => String(item.rwa_id) === String(focused.rwa_id));
    const alert = focusedDetail || focused || (!normalizedQuery && !searchAttempted && (receipt.alerts.find(item => item.state === 'do_not_compare') || receipt.alerts.find(item => item.state === 'investigate')));
    const publication = receipt._publication || {};
    if (!alert) {
      byId('hero-case').textContent = normalizedQuery ? 'No reference found' : 'Search a reference';
      byId('hero-case-fact').textContent = normalizedQuery ? `Nothing in the published receipt matches “${query}”.` : 'Use the search above to open a published evidence case.';
      setHeroProofHeading(searchAttempted ? 'START HERE' : 'NO PUBLISHED CASE');
      byId('hero-proof-reason').textContent = 'Search a listed reference before reading the evidence card.';
      byId('hero-signal-list').innerHTML = '<div><span class="hero-signal-severity checked">NO MATCH</span><strong>No published case selected</strong><small>Try the asset name, ticker or RWA ID</small></div>';
      byId('hero-quote-contrast').hidden = true;
      byId('hero-token-count').textContent = '—';
      byId('hero-issuer-count').textContent = '—';
      byId('hero-signal-count').textContent = '—';
      byId('hero-identity-check').textContent = '—';
      byId('hero-unit-check').textContent = '—';
      byId('hero-market-check').textContent = '—';
      byId('hero-proof-output').textContent = 'NO MATCH';
      byId('hero-proof-hint').textContent = 'search a listed reference';
      byId('hero-proof-cta-label').textContent = 'Open searchable queue';
      byId('hero-proof-cta').hidden = false;
      byId('decision-hero').innerHTML = `<p class="eyebrow">SEARCH RESULT</p><h3>${normalizedQuery ? 'No matching reference' : 'Search a reference'}</h3><p>${normalizedQuery ? `Try the asset name, ticker or RWA ID again` : 'Try Silver, Gold, Tesla, SPY or an RWA ID'}</p>`;
      return;
    }
    const heroSearchInput = byId('hero-search');
    if (heroSearchInput) heroSearchInput.value = alert.name || alert.symbol || query;
    const decision = alert.decision || {};
    const significantSignals = alert.signals
      ? alert.signals.filter(signal => signal.severity !== 'info')
      : (alert.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET').map(code => ({ code, evidence: alert.signal_evidence?.[code] || {} }));
    const signals = significantSignals.slice(0, 2).map(signal => signalLabels[signal.code] || signal.code).join(' · ');
    const primaryEvidence = significantSignals[0]?.evidence || {};
    const caseFacts = [];
    if (alert.token_count) caseFacts.push(`${formatNumber(alert.token_count)} representations`);
    if (alert.issuer_count) caseFacts.push(`${formatNumber(alert.issuer_count)} issuers`);
    if (primaryEvidence.max_min_ratio) caseFacts.push(`${formatNumber(primaryEvidence.max_min_ratio)}× observed price spread`);
    byId('hero-case').textContent = alert.name || 'Current flagged case';
    byId('hero-case-fact').textContent = caseFacts.join(' · ') || signals || 'Published rule hit';
    const proofReason = byId('hero-proof-reason');
    const reasonPrefix = alert.state === 'do_not_compare' ? 'Unit or market compatibility needs review' : alert.state === 'investigate' ? 'Identity or market fields need review' : '';
    const reasonSignals = significantSignals.slice(0, 3).map(signal => signalLabels[signal.code] || signal.code).join(' · ');
    if (proofReason) proofReason.textContent = [reasonPrefix, reasonSignals].filter(Boolean).join(' · ') || 'No published contradiction in the current rule set';
    const signalList = byId('hero-signal-list');
    if (signalList) signalList.innerHTML = significantSignals.length
      ? significantSignals.slice(0, 3).map(signal => `<div><span class="hero-signal-severity ${signal.severity === 'critical' ? 'critical' : 'warning'}">${escapeHTML(String(signal.severity || 'signal').toUpperCase())}</span><strong>${escapeHTML(signalLabels[signal.code] || signal.code)}</strong><small>${escapeHTML(signalEvidenceSummary(signal))} · ${escapeHTML(signalSourceLabel(signal.code))}</small></div>`).join('')
      : '<div><span class="hero-signal-severity checked">CLEAR</span><strong>No published rule hit</strong><small>Observed fields remain descriptive and require external diligence</small></div>';
    const quoteContrast = byId('hero-quote-contrast');
    const capitalSignal = byId('hero-capital-signal');
    const pricedTokens = (alert.tokens || []).filter(token => typeof token.price === 'number').sort((a, b) => a.price - b.price);
    if (quoteContrast) {
      const hasRange = pricedTokens.length >= 2 && pricedTokens[0].price !== pricedTokens[pricedTokens.length - 1].price;
      quoteContrast.hidden = !hasRange;
      if (hasRange) {
        const low = pricedTokens[0];
        const high = pricedTokens[pricedTokens.length - 1];
        byId('hero-low-quote').textContent = formatNumber(low.price);
        byId('hero-low-symbol').textContent = low.symbol || 'LOW';
        byId('hero-high-quote').textContent = formatNumber(high.price);
        byId('hero-high-symbol').textContent = high.symbol || 'HIGH';
        byId('hero-low-issuer').textContent = low.issuer_name || 'Issuer not resolved';
        byId('hero-high-issuer').textContent = high.issuer_name || 'Issuer not resolved';
      }
    }
    if (capitalSignal) {
      const capital = window.BellCapitalImpact.assess(alert, 10000);
      capitalSignal.hidden = false;
      capitalSignal.className = `hero-capital-signal hero-capital-${capital.mode}`;
      const capitalHeadline = byId('hero-capital-headline');
      const capitalCopy = byId('hero-capital-copy');
      if (capitalHeadline) capitalHeadline.textContent = capital.headline;
      if (capitalCopy) capitalCopy.textContent = capital.note;
    }
    const tokenCount = byId('hero-token-count');
    const issuerCount = byId('hero-issuer-count');
    const signalCount = byId('hero-signal-count');
    if (tokenCount) tokenCount.textContent = formatNumber(alert.token_count || alert.tokens?.length || 0);
    if (issuerCount) issuerCount.textContent = formatNumber(alert.issuer_count || new Set((alert.tokens || []).map(token => token.issuer_id).filter(Boolean)).size || 0);
    if (signalCount) signalCount.textContent = formatNumber(significantSignals.length);
    const proofCTA = byId('hero-proof-cta-label');
    if (proofCTA) proofCTA.textContent = significantSignals.length ? `View ${significantSignals.length} supporting signals` : 'View evidence';
    const proofLink = byId('hero-proof-cta');
    if (proofLink) {
      proofLink.dataset.rwaId = String(alert.rwa_id || '');
      proofLink.hidden = false;
    }
    const isDatedReplay = receipt?._publication?.source === 'dated_static';
    setHeroProofHeading(normalizedQuery ? 'SEARCHED REFERENCE' : (isDatedReplay ? 'PUBLISHED REPLAY' : 'LIVE EXAMPLE'));
    const signalCodes = new Set(significantSignals.map(signal => signal.code));
    const setEvidenceCheck = (id, text, tone) => {
      const element = byId(id);
      if (!element) return;
      element.textContent = text;
      element.className = tone;
    };
    const identityNeedsReview = signalCodes.has('TOKEN_INFO_MISSING') || signalCodes.has('SYMBOL_COLLISION');
    setEvidenceCheck('hero-identity-check', identityNeedsReview ? 'REVIEW' : 'CHECKED', identityNeedsReview ? 'review' : 'checked');
    setEvidenceCheck('hero-unit-check', signalCodes.has('PRICE_DENOMINATION_BREAK') ? 'BLOCKED' : signalCodes.has('DERIVATIVE_MIX') ? 'REVIEW' : 'CHECKED', signalCodes.has('PRICE_DENOMINATION_BREAK') ? 'blocked' : signalCodes.has('DERIVATIVE_MIX') ? 'review' : 'checked');
    setEvidenceCheck('hero-market-check', signalCodes.has('ZERO_MCAP_POSITIVE_VOLUME') || signalCodes.has('MARKET_FIELDS_MISSING') ? 'REVIEW' : 'OBSERVED', signalCodes.has('ZERO_MCAP_POSITIVE_VOLUME') || signalCodes.has('MARKET_FIELDS_MISSING') ? 'review' : 'checked');
    byId('hero-example').textContent = `${isDatedReplay ? 'Published replay' : 'Live example'}: search ${alert.name || 'the reference'} → inspect ${caseFacts.join(' · ') || 'the evidence'} → ${displayDecisionLabel(alert, 'HOLD COMPARISON')} → verify the next action before ranking a wrapper.`;
    byId('hero-proof-output').textContent = displayDecisionLabel(alert, 'HOLD COMPARISON');
    const isClean = alert.state === 'no_flags';
    const hint = alert.state === 'do_not_compare' ? 'verify unit and market evidence' : alert.state === 'investigate' ? 'classify before shortlist' : Number(alert.token_count || 0) === 1 ? 'single representation · verify externally' : 'facts only · continue external diligence';
    const proofHint = byId('hero-proof-hint');
    if (proofHint) proofHint.textContent = hint;
    const decisionHeading = query.trim() ? 'SEARCHED REFERENCE' : (isClean ? 'CURRENT REFERENCE' : 'FLAGGED REFERENCE');
    const signalLabel = signals || (isClean ? 'no published rule hit' : 'published rule hit');
      byId('decision-hero').innerHTML = `<div class="decision-hero-top"><span class="eyebrow">${decisionHeading}</span><span class="decision-case">${escapeHTML(alert.symbol || 'RWA')}</span></div><h3>${escapeHTML(alert.name)}</h3><p class="decision-signal">${escapeHTML(signalLabel)}</p><div class="decision-outcome"><span>OUTPUT</span><strong>${escapeHTML(displayDecisionLabel(alert, 'HOLD COMPARISON'))}</strong><p>${escapeHTML(decision.consequence || alert.next_action || '')}</p><b class="allocation-gate">${escapeHTML(decision.allocation_effect || 'No allocation status is produced by this monitor')}</b></div><div class="decision-actions"><button class="brief-button" type="button" data-brief-id="${escapeHTML(alert.rwa_id)}">Save decision brief ↓</button><button class="brief-button" type="button" data-case-receipt="${escapeHTML(alert.rwa_id)}">Download case JSON ↓</button><button class="brief-button" type="button" data-copy-case="${escapeHTML(alert.rwa_id)}">Copy case link ↗</button>${watchButton(alert)}<a class="decision-action-link" href="#monitor">Inspect representation rows ↘</a></div>${capitalPanel(alert)}${temporalPanel(alert)}${referenceConcentrationPanel(alert)}${referenceActivityPanel(alert)}${resolutionRoute(alert)}<div class="decision-receipt"><span>${escapeHTML(publication.status ? String(publication.status).toUpperCase() : 'DATED')} · ${escapeHTML(publication.observed_at || receipt.observed_at || 'N/A')}</span><a href="/api/integrity" target="_blank" rel="noopener">Open credential-free receipt ↗</a></div>`;
      loadTemporalEvidence(alert);
  }

  async function boot() {
    try {
      const localHost = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
      const sources = localHost
        ? ['proof/rwa-surface-integrity-latest-replay-2026-09-21.json']
        : ['/api/integrity', 'proof/rwa-surface-integrity-latest-replay-2026-09-21.json'];
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
      byId('hero-search').value = query;
      byId('alert-search').value = query;
      renderMetrics();
      renderThesisStrip();
      renderInvestorTask();
      renderAlerts();
      renderSearchResult();
      renderSignals();
      renderPopulationVisual();
      renderConcentrationVisual();
      renderReceiptDelta();
      loadPublicationHistory();
      renderIdentity();
      renderDifferentiation();
      renderDecisionStory();
    } catch (error) {
      byId('alert-list').innerHTML = '<p class="section-note">The dated evidence receipt could not be loaded. Open the JSON receipt directly to inspect the source.</p>';
    }
  }

  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    pageNumber = 0;
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('selected', item === button));
    renderAlerts();
  }));
  byId('alert-search').addEventListener('input', event => {
    query = event.target.value;
    pageNumber = 0;
    byId('hero-search').value = event.target.value;
    renderAlerts();
    renderSearchResult();
    renderDecisionStory();
  });
  document.addEventListener('input', event => {
    const budgetInput = event.target.closest('[data-capital-budget]');
    if (!budgetInput) return;
    refreshCapitalPanel(budgetInput.closest('[data-capital-panel]'));
  });
  byId('alert-pagination').addEventListener('click', event => {
    const button = event.target.closest('[data-page]');
    if (!button || button.disabled) return;
    pageNumber = Math.max(0, Number(button.dataset.page) || 0);
    renderAlerts();
    byId('monitor').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  document.addEventListener('click', event => {
    const mapQueryLink = event.target.closest('[data-open-map-query]');
    if (mapQueryLink) {
      const mapInput = byId('explorer-search');
      const mapForm = byId('explorer-form');
      if (mapInput && mapForm) {
        mapInput.value = mapQueryLink.dataset.openMapQuery || '';
        const shareURL = new URL(window.location.href);
        shareURL.searchParams.set('map_reference', mapInput.value);
        window.history.replaceState({}, '', shareURL);
        mapForm.requestSubmit();
      }
      return;
    }
    const copyCaseButton = event.target.closest('[data-copy-case]');
    if (copyCaseButton) {
      copyCaseLink(copyCaseButton.dataset.copyCase, copyCaseButton);
      return;
    }
    const briefButtonElement = event.target.closest('[data-brief-id]');
    if (briefButtonElement) {
      downloadBrief(briefButtonElement.dataset.briefId);
      return;
    }
    const caseReceiptButton = event.target.closest('[data-case-receipt]');
    if (caseReceiptButton) {
      downloadCaseReceipt(caseReceiptButton.dataset.caseReceipt);
      return;
    }
    const removeButton = event.target.closest('[data-watch-remove]');
    if (removeButton) {
      saveWatchlist(readWatchlist().filter(entry => String(entry.rwa_id) !== String(removeButton.dataset.watchRemove)));
      renderWatchlist();
      renderAlerts();
      return;
    }
    const watchButtonElement = event.target.closest('[data-watch-id]');
    if (!watchButtonElement) return;
    const rwaId = String(watchButtonElement.dataset.watchId);
    const items = readWatchlist();
    const existing = items.findIndex(entry => String(entry.rwa_id) === rwaId);
    if (existing >= 0) {
      items.splice(existing, 1);
    } else {
      const item = (receipt?.alert_index || []).find(entry => String(entry.rwa_id) === rwaId);
      if (!item) return;
      items.unshift({ rwa_id: item.rwa_id, name: item.name, symbol: item.symbol, state: item.state, observed_at: receipt.observed_at });
    }
    saveWatchlist(items);
    renderWatchlist();
    renderAlerts();
  });
  byId('monitor').addEventListener('click', event => {
    if (!event.target.closest('[data-open-first-evidence]')) return;
    const details = byId('alert-list').querySelector('details.alert-details');
    if (!details) return;
    details.open = true;
    completeInvestorTaskStep(2);
    details.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  byId('alert-list').addEventListener('click', event => {
    if (event.target.closest('.alert-details summary')) completeInvestorTaskStep(2);
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
      completeInvestorTaskStep(3);
      completeInvestorTaskStep(4);
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
      if (selectedIds.length >= 2) completeInvestorTaskStep(3);
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
  byId('hero-proof-cta').addEventListener('click', event => {
    const rwaId = event.currentTarget.dataset.rwaId;
    if (!rwaId) return;
    window.setTimeout(() => {
      const row = byId('alert-list').querySelector(`[data-rwa-id="${CSS.escape(rwaId)}"]`);
      const details = row?.querySelector('details.alert-details');
      if (!details) return;
      details.open = true;
      details.scrollIntoView({ behavior: 'smooth', block: 'start' });
      completeInvestorTaskStep(2);
    }, 300);
  });
  document.querySelectorAll('[data-example-search]').forEach(button => button.addEventListener('click', () => {
    byId('hero-search').value = button.dataset.exampleSearch || '';
    byId('hero-search-form').requestSubmit();
  }));
  byId('task-reset').addEventListener('click', () => {
    try { localStorage.removeItem(investorTaskKey); } catch { /* optional local state */ }
    renderInvestorTask();
  });
  byId('refresh-receipt')?.addEventListener('click', event => {
    const button = event.currentTarget;
    button.disabled = true;
    button.textContent = 'Refreshing…';
    window.location.reload();
  });
  boot();
  window.setInterval(() => { if (receipt) renderMetrics(); }, 60000);
})();

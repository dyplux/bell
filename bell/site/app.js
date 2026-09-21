(() => {
  'use strict';
  const snapshot = window.BELL_SNAPSHOT;
  const wrappers = snapshot.wrappers;
  let focused = null;
  let metric = 'range';
  let goldMetric = 'range';
  let lastEvidenceTrigger = null;
  let toastTimer;
  const byId = id => document.getElementById(id);
  const percent = n => Number.isFinite(Number(n)) ? `${Number(n).toFixed(2)}%` : 'N/A';
  const relative = (w, session) => Number.isFinite(Number(w.range_pct[session])) && Number(w.range_pct.cash) > 0 ? Number(w.range_pct[session]) / Number(w.range_pct.cash) * 100 : null;
  const ratioLabel = value => Number.isFinite(Number(value)) ? `≈${Number(value).toFixed(0)}%` : 'Unavailable';
  const millions = n => `$${(n / 1e6).toFixed(1)}M`;
  const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

  const assets = window.BELL_CATALOGUE.assets;
  const auditSnapshots = window.BELL_AUDIT_SNAPSHOTS || {};
  const terminal = window.BELL_TERMINAL;
  const categories = ['All assets', ...new Set(assets.map(asset => asset.category))];
  const liveEnabled = Boolean(window.BELL_RUNTIME_ENDPOINT || window.BELL_LIVE_PUBLIC) || ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname);
  const directLiveEnabled = Boolean(window.BELL_RUNTIME_ENDPOINT) || ['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname);
  const publishedReview = asset => asset.analysis_id === 'tesla' ? snapshot : asset.analysis_id === 'gold' ? window.BELL_GOLD_SNAPSHOT : null;
  let currentBrief = null;
  let memoUrl = null;
  let liveDexRows = new Map();
  let liveReceiptSource = null;
  function renderInvestorBrief(asset, review) {
    currentBrief = review ? window.BELL_RESEARCH_BRIEF.build(review, asset.analysis_id) : null;
    byId('investor-brief').hidden = !currentBrief;
    if (!currentBrief) return;
    byId('brief-date').textContent = `${currentBrief.asset} / ${currentBrief.rows.length} entries / Observation ends ${currentBrief.end} / ${currentBrief.duration} hours / Saved snapshot, not a current quote`;
    for (const field of ['question', 'finding', 'limits', 'clock', 'provenance', 'decision']) {
      byId(`brief-${field}`).textContent = currentBrief[field];
    }
    byId('brief-diligence-list').innerHTML = currentBrief.diligence.map(item => `<li>${escapeHTML(item)}</li>`).join('');
    byId('brief-evidence').innerHTML = currentBrief.evidence.map(item => `<a class="text-button" href="${escapeHTML(item.path)}" target="_blank" rel="noopener noreferrer">${escapeHTML(item.label)} ↗</a>`).join('');
  }
  byId('download-research-memo').addEventListener('click', () => {
    if (!currentBrief) return;
    if (memoUrl) URL.revokeObjectURL(memoUrl);
    memoUrl = URL.createObjectURL(new Blob([window.BELL_RESEARCH_BRIEF.memo(currentBrief)], { type: 'text/markdown;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = memoUrl;
    link.download = `bell-${currentBrief.reviewId}-research-memo-${currentBrief.date}.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    const repeatLink = byId('research-memo-link');
    repeatLink.href = memoUrl;
    repeatLink.download = link.download;
    repeatLink.hidden = false;
    byId('download-status').textContent = 'Research memo download requested. Use “Download again” if your browser blocked it. Approval checks remain pending.';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { byId('download-status').textContent = ''; }, 4200);
  });
  const coverageLabel = asset => {
    const review = publishedReview(asset);
    const audit = auditSnapshots[asset.slug || asset.id];
    if (audit && review) return `Audit + session review · ${review.wrappers.length} wrappers`;
    if (audit) return `Surface audit available · ${audit.state.replaceAll('_', ' ')}`;
    return 'Map entry only · no published review';
  };
  let category = 'All assets';
  let cataloguePage = 1;
  const cataloguePageSize = 50;
  const normaliseSearch = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  function renderMapInsight() {
    const target = byId('map-insight');
    if (!target) return;
    const total = assets.length;
    const tokenised = assets.filter(asset => asset.has_tokens === true).length;
    const underlyingOnly = total - tokenised;
    const percent = value => total ? (value / total * 100).toFixed(1) : '0.0';
    const category = type => {
      const rows = assets.filter(asset => String(asset.category || '').toLowerCase() === type);
      const mapped = rows.filter(asset => asset.has_tokens === true).length;
      return { total: rows.length, mapped, rate: rows.length ? (mapped / rows.length * 100).toFixed(1) : '0.0' };
    };
    const stocks = category('stock');
    const etfs = category('etf');
    const commodities = category('commodity');
    target.innerHTML = `<div class="map-insight-lead"><small>MAP RESEARCH / DATED CMC INDEX</small><strong>Tokenisation is concentrated, not universal</strong><p>${tokenised.toLocaleString()} of ${total.toLocaleString()} references have a mapped token layer. Bell keeps the remaining ${underlyingOnly.toLocaleString()} in underlying-only mode.</p></div><div><small>Mapped references</small><strong>${percent(tokenised)}%</strong><p>${tokenised.toLocaleString()} assets with one or more token representations.</p></div><div><small>Stocks</small><strong>${stocks.rate}%</strong><p>${stocks.mapped} of ${stocks.total.toLocaleString()} mapped. The largest tokenised category in this snapshot.</p></div><div><small>ETFs / commodities</small><strong>${etfs.rate}% / ${commodities.rate}%</strong><p>${etfs.mapped} of ${etfs.total.toLocaleString()} ETFs and ${commodities.mapped} of ${commodities.total} commodities mapped.</p></div>`;
  }

  function renderCatalogue() {
    renderMapInsight();
    const query = normaliseSearch(byId('rwa-search').value);
    const matches = assets.filter(asset => (category === 'All assets' || asset.category === category) && normaliseSearch(`${asset.name} ${asset.symbol} ${asset.id} ${asset.category}`).includes(query));
    const pageCount = Math.max(1, Math.ceil(matches.length / cataloguePageSize));
    cataloguePage = Math.min(cataloguePage, pageCount);
    const pageAssets = matches.slice((cataloguePage - 1) * cataloguePageSize, cataloguePage * cataloguePageSize);
    byId('category-filters').innerHTML = categories.map(item => `<button type="button" data-category="${escapeHTML(item)}" aria-pressed="${category === item}">${escapeHTML(item)}</button>`).join('');
    byId('catalogue-body').innerHTML = pageAssets.map(asset => { const hasEvidence = Boolean(publishedReview(asset) || auditSnapshots[asset.slug || asset.id]); return `<tr><th scope="row"><a class="asset-name" href="#asset=${encodeURIComponent(asset.id)}"><span class="asset-monogram" aria-hidden="true">${escapeHTML(asset.symbol.slice(0, 2))}</span><span>${escapeHTML(asset.name)}<small>${escapeHTML(asset.symbol)}</small><small class="asset-coverage-mobile${hasEvidence ? ' has-analysis' : ''}">${coverageLabel(asset)}</small></span></a></th><td>${escapeHTML(asset.category)}</td><td><span class="coverage-label${hasEvidence ? ' has-analysis' : ''}">${coverageLabel(asset)}</span></td><td><a class="text-button" href="#asset=${encodeURIComponent(asset.id)}" aria-label="Open ${escapeHTML(asset.name)} details">${hasEvidence ? 'Open audit' : 'View map entry'} ↗</a></td></tr>`; }).join('');
    const from = matches.length ? (cataloguePage - 1) * cataloguePageSize + 1 : 0;
    const to = Math.min(cataloguePage * cataloguePageSize, matches.length);
    byId('catalogue-count').textContent = `${from}–${to} of ${matches.length} matching assets · ${window.BELL_CATALOGUE.total_size || assets.length} in map${category === 'All assets' ? '' : ` · ${category}`}${query ? ' · search applied' : ''}`;
    byId('catalogue-pagination').innerHTML = matches.length > cataloguePageSize ? `<button type="button" data-page="prev" ${cataloguePage === 1 ? 'disabled' : ''}>Previous</button><span>Page ${cataloguePage} of ${pageCount}</span><button type="button" data-page="next" ${cataloguePage === pageCount ? 'disabled' : ''}>Next</button>` : '';
    byId('catalogue-empty').hidden = matches.length > 0;
    document.querySelector('.catalogue-table-scroll').hidden = matches.length === 0;
    byId('clear-search').hidden = !byId('rwa-search').value;
  }
  byId('rwa-search').addEventListener('input', () => { cataloguePage = 1; renderCatalogue(); });
  byId('category-filters').addEventListener('click', event => {
    const button = event.target.closest('[data-category]');
    if (!button) return;
    category = button.dataset.category;
    cataloguePage = 1;
    renderCatalogue();
    Array.from(byId('category-filters').querySelectorAll('button')).find(item => item.dataset.category === category).focus({ preventScroll: true });
  });
  byId('catalogue-pagination').addEventListener('click', event => {
    const button = event.target.closest('[data-page]');
    if (!button || button.disabled) return;
    cataloguePage += button.dataset.page === 'next' ? 1 : -1;
    renderCatalogue();
    byId('catalogue').scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  byId('clear-search').addEventListener('click', () => { byId('rwa-search').value = ''; cataloguePage = 1; renderCatalogue(); byId('rwa-search').focus(); });
  byId('reset-catalogue').addEventListener('click', () => { category = 'All assets'; byId('rwa-search').value = ''; cataloguePage = 1; renderCatalogue(); byId('rwa-search').focus(); });

  function formatMoney(value) {
    if (value === null || value === undefined) return 'N/A';
    const number = Number(value);
    if (!Number.isFinite(number)) return 'N/A';
    return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(number);
  }
  function liveFingerprint(source) {
    return {
      observed_at: source.observed_at || source.provenance?.observed_at || null,
      tokens: (source.tokens || []).map(token => ({ crypto_id: token.crypto_id, symbol: token.symbol, issuer_id: token.issuer_id, issuer_name: token.issuer_name, price: token.price })),
      crypto_info: (source.crypto_info || []).map(info => ({ id: info.id, platform: info.platform?.slug || info.platform?.name || null, contract_address: info.contract_address || info.platform?.token_address || null })),
      dex_evidence: source.dex_evidence ? { covered_token_count: source.dex_evidence.covered_token_count || 0, contract_token_count: source.dex_evidence.contract_token_count || 0, tokens: (source.dex_evidence.tokens || []).map(row => ({ crypto_id: row.crypto_id, state: row.state, surfaces: row.surfaces || [] })) } : null
    };
  }
  function liveChangeNote(asset, source) {
    const key = `bell.live.receipt.${asset.slug || asset.rwa_id || asset.symbol || 'asset'}`;
    const current = liveFingerprint(source);
    let previous = null;
    try { previous = JSON.parse(window.localStorage.getItem(key) || 'null'); } catch (error) { previous = null; }
    try { window.localStorage.setItem(key, JSON.stringify(current)); } catch (error) { /* private browsing can disable storage */ }
    if (!previous) return '<div class="live-change-note"><span class="eyebrow">FIRST LOCAL OBSERVATION</span><p>No previous browser receipt exists for this asset. Save the evidence receipt to carry this observation into a research note.</p></div>';
    const previousIds = new Set((previous.tokens || []).map(token => String(token.crypto_id)));
    const currentIds = new Set((current.tokens || []).map(token => String(token.crypto_id)));
    const added = [...currentIds].filter(id => !previousIds.has(id)).length;
    const removed = [...previousIds].filter(id => !currentIds.has(id)).length;
    const issuers = rows => new Set(rows.map(token => token.issuer_id || token.issuer_name).filter(Boolean));
    const networks = rows => new Set(rows.map(info => info.platform).filter(Boolean));
    const priceValues = rows => rows.map(token => Number(token.price)).filter(value => Number.isFinite(value) && value > 0);
    const oldPrices = priceValues(previous.tokens || []);
    const newPrices = priceValues(current.tokens || []);
    const oldSpread = oldPrices.length > 1 ? Math.max(...oldPrices) / Math.min(...oldPrices) : null;
    const newSpread = newPrices.length > 1 ? Math.max(...newPrices) / Math.min(...newPrices) : null;
    const deltas = [`${current.tokens.length - previous.tokens.length >= 0 ? '+' : ''}${current.tokens.length - previous.tokens.length} wrapper(s)`, `${issuers(current.tokens).size - issuers(previous.tokens).size >= 0 ? '+' : ''}${issuers(current.tokens).size - issuers(previous.tokens).size} issuer(s)`, `${networks(current.crypto_info).size - networks(previous.crypto_info).size >= 0 ? '+' : ''}${networks(current.crypto_info).size - networks(previous.crypto_info).size} network(s)`];
    if (added || removed) deltas.push(`${added} added / ${removed} removed`);
    if (current.dex_evidence && previous.dex_evidence) deltas.push(`DEX coverage ${previous.dex_evidence.covered_token_count || 0} → ${current.dex_evidence.covered_token_count || 0}`);
    if (oldSpread && newSpread) deltas.push(`price spread ${oldSpread.toFixed(1)}x → ${newSpread.toFixed(1)}x`);
    const changed = current.tokens.length !== previous.tokens.length || issuers(current.tokens).size !== issuers(previous.tokens).size || networks(current.crypto_info).size !== networks(previous.crypto_info).size || added > 0 || removed > 0 || Boolean(current.dex_evidence && previous.dex_evidence && current.dex_evidence.covered_token_count !== previous.dex_evidence.covered_token_count) || Boolean(oldSpread && newSpread && Math.abs(oldSpread - newSpread) > 0.0001);
    return `<div class="live-change-note"><span class="eyebrow">SINCE LAST LOCAL RECEIPT</span><p>${changed ? deltas.map(escapeHTML).join(' · ') : 'No wrapper, issuer, network, price-spread or DEX-coverage changes observed.'}</p><small>Previous observation: ${escapeHTML(previous.observed_at || 'timestamp unavailable')} · current: ${escapeHTML(current.observed_at || 'timestamp unavailable')}</small></div>`;
  }
  function renderLiveDossier(dossier) {
    const audit = dossier.audit || null;
    const source = audit?.evidence || dossier;
    const asset = source.asset || dossier.asset || {};
    const tokens = Array.isArray(source.tokens) ? source.tokens : [];
    const cryptoInfo = Array.isArray(source.crypto_info) ? source.crypto_info : [];
    const dex = source.dex_evidence && typeof source.dex_evidence === 'object' ? source.dex_evidence : null;
    const dexById = new Map((dex?.tokens || []).map(item => [String(item.crypto_id), item]));
    liveDexRows = dexById;
    liveReceiptSource = source;
    const cryptoById = new Map(cryptoInfo.map(item => [String(item.id), item]));
    const tokenNetwork = token => {
      const info = cryptoById.get(String(token.crypto_id));
      const platform = info?.platform;
      const network = platform?.name || platform?.symbol || 'Unresolved';
      const contract = info?.contract_address || platform?.token_address;
      return `${network}${contract ? ` · ${String(contract).slice(0, 12)}…` : ''}`;
    };
    const dexStatus = token => {
      const row = dexById.get(String(token.crypto_id));
      if (!row) return 'NOT PROBED';
      if (row.state === 'no_contract') return 'NO CONTRACT';
      if (row.state === 'unavailable') return 'NOT RESOLVED';
      const surfaces = Array.isArray(row.surfaces) ? row.surfaces.length : 0;
      const pools = Array.isArray(row.pools) ? row.pools.length : 0;
      const holders = row.holders?.count == null ? 'N/A' : formatMoney(row.holders.count);
      return `LIVE · ${surfaces}/6 surfaces · ${pools} pools · ${holders} holders`;
    };
    const dexCell = token => {
      const row = dexById.get(String(token.crypto_id));
      if (!row) return `<span class="dex-status">${escapeHTML(dexStatus(token))}</span>`;
      return `<button class="dex-inspect-button" type="button" data-live-dex="${escapeHTML(token.crypto_id)}" aria-label="Inspect DEX evidence for ${escapeHTML(token.symbol || token.name || 'token')}">${escapeHTML(dexStatus(token))}<span aria-hidden="true">↗</span></button>`;
    };
    const coverageMark = (state, label) => `<span class="coverage-pill coverage-pill-${state}">${escapeHTML(label)}</span>`;
    const surfaceMark = (row, surface) => {
      if (!row) return coverageMark('not-loaded', 'NOT LOADED');
      if (row.state === 'no_contract') return coverageMark('not-applicable', 'N/A');
      return row.surfaces?.includes(surface) ? coverageMark('yes', 'YES') : coverageMark('missing', 'NO');
    };
    const coverageMatrix = tokens.length ? `<details class="coverage-matrix" open><summary><span><span class="eyebrow">EVIDENCE COVERAGE</span><strong>What Bell could resolve for each wrapper</strong></span><span class="coverage-summary">${dex ? `${dex.covered_token_count || 0}/${dex.contract_token_count || 0} DEX covered` : 'DEX not requested'} ↕</span></summary><div class="table-scroll"><table class="dossier-table"><thead><tr><th>Wrapper</th><th>CMC quote</th><th>Issuer</th><th>Contract</th><th>DEX detail</th><th>Pools</th><th>Security</th><th>Holders</th><th>Tag cohorts</th><th>OHLCV</th></tr></thead><tbody>${tokens.map(token => { const info = cryptoById.get(String(token.crypto_id)); const contract = info?.contract_address || info?.platform?.token_address; const row = dexById.get(String(token.crypto_id)); return `<tr><th>${escapeHTML(token.symbol || token.name || '—')}</th><td>${token.price == null ? coverageMark('missing', 'NO') : coverageMark('yes', 'YES')}</td><td>${token.issuer_id || token.issuer_name ? coverageMark('yes', 'YES') : coverageMark('missing', 'NO')}</td><td>${contract ? coverageMark('yes', 'YES') : coverageMark('missing', 'NO')}</td><td>${surfaceMark(row, 'detail')}</td><td>${surfaceMark(row, 'pools')}</td><td>${surfaceMark(row, 'security')}</td><td>${surfaceMark(row, 'holders')}</td><td>${surfaceMark(row, 'holder_tags')}</td><td>${coverageMark('not-loaded', 'NOT LOADED')}</td></tr>`; }).join('')}</tbody></table></div><p class="dossier-note">NOT LOADED means this dossier did not spend a historical OHLCV request. It is not evidence of missing history. NO means the requested surface returned no usable record or failed.</p></details>` : '';
    const terminalAsset = assets.find(item => item.id === String(asset.slug || asset.rwa_id || ''));
    const terminalDossier = audit ? { ...source, findings: audit.findings, conclusion: audit.conclusion } : dossier;
    if (terminal && terminalAsset) terminal.render(terminalAsset, terminalDossier);
    byId('detail-live-dossier').hidden = false;
    const findingMarkup = audit ? `<div class="live-audit-result"><div class="session-result-heading"><div><span class="eyebrow">TERMINAL AUDIT COMPLETE</span><p class="dossier-note">${escapeHTML(audit.conclusion || 'unknown')} · ${audit.findings?.length || 0} finding(s)</p></div><span class="audit-state">${escapeHTML(String(audit.conclusion || 'unknown').replaceAll('_', ' ').toUpperCase())}</span></div>${audit.findings?.length ? `<ul class="audit-findings">${audit.findings.map(item => `<li><strong>${escapeHTML(item.code)}</strong> — ${escapeHTML(item.message)}</li>`).join('')}</ul>` : '<p class="dossier-note">No deterministic findings returned.</p>'}</div>` : '<div id="live-audit-result"></div>';
    const marketPairLabel = source.market_pairs_error ? 'PLAN LIMITED' : source.market_pairs?.length ?? '—';
    const dexLabel = dex ? `${dex.covered_token_count || 0}/${dex.contract_token_count || 0}` : 'NOT REQUESTED';
    const observedAt = source.observed_at || source.provenance?.observed_at || 'timestamp unavailable';
    const changeNote = liveChangeNote(asset, source);
    const calls = Array.isArray(source.provenance?.calls) ? source.provenance.calls : [];
    const provenanceMarkup = `<details class="live-provenance"><summary><span><span class="eyebrow">LIVE API EVIDENCE</span><strong>${calls.length} recorded CMC request(s)</strong></span><span>↕</span></summary>${calls.length ? `<div class="table-scroll"><table class="dossier-table"><thead><tr><th>Endpoint</th><th>Status</th><th>Observed</th><th>CMC timestamp</th><th>Credits</th><th>Parameters</th></tr></thead><tbody>${calls.map(call => `<tr><th><code>${escapeHTML(call.endpoint || 'unknown')}</code></th><td>${escapeHTML(call.status ?? '—')}</td><td><code>${escapeHTML(call.observed_at || '—')}</code></td><td><code>${escapeHTML(call.api_timestamp || '—')}</code></td><td>${escapeHTML(call.credit_count ?? '—')}</td><td><code>${escapeHTML(JSON.stringify(call.params || {}))}</code></td></tr>`).join('')}</tbody></table></div>` : '<p class="dossier-note">No request log was returned by this publication.</p>'}<p class="dossier-note">The request log contains endpoint, status, timestamps, credits and parameters only. It does not include an API key or raw response body.</p></details>`;
    byId('detail-live-dossier').innerHTML = `<div class="dossier-heading"><div><span class="eyebrow">LIVE CMC TERMINAL DOSSIER</span><h3>${escapeHTML(asset.name || 'Selected RWA')}</h3><p class="dossier-asof">OBSERVED ${escapeHTML(observedAt)}</p></div><span class="snapshot-tag">${tokens.length} TOKENS</span></div><div class="dossier-stats"><span><small>Tokenized market cap</small><strong>$${formatMoney(asset.tokenized_market_cap)}</strong></span><span><small>24h tokenized volume</small><strong>$${formatMoney(asset.tokenized_volume_24h)}</strong></span><span><small>DEX coverage</small><strong>${escapeHTML(dexLabel)}</strong></span><span><small>CMC market pairs</small><strong>${escapeHTML(marketPairLabel)}</strong></span></div>${provenanceMarkup}${changeNote}${tokens.length ? `<div class="table-scroll"><table class="dossier-table"><thead><tr><th>Token</th><th>Issuer</th><th>Network / contract</th><th>DEX evidence</th><th>Price</th><th>Market cap</th><th>24h volume</th></tr></thead><tbody>${tokens.map(token => `<tr><th>${escapeHTML(token.symbol || token.name || '—')}<small>${escapeHTML(token.name || '')}</small></th><td>${escapeHTML(token.issuer_name || 'Unknown')}</td><td>${escapeHTML(tokenNetwork(token))}</td><td>${dexCell(token)}</td><td>${token.price == null ? '—' : `$${formatMoney(token.price)}`}</td><td>${token.market_cap == null ? '—' : `$${formatMoney(token.market_cap)}`}</td><td>${token.volume_24h == null ? '—' : `$${formatMoney(token.volume_24h)}`}</td></tr>`).join('')}</tbody></table></div>` : '<p class="dossier-empty">CMC returned no token wrappers for this reference.</p>'}${coverageMatrix}<div id="live-dex-inspector" class="live-dex-inspector" hidden></div><div class="live-dossier-actions"><button class="button button-outline live-receipt-button" type="button" data-live-receipt${tokens.length ? '' : ' disabled'}>Save evidence receipt ↓</button>${audit ? '' : `<button class="text-button live-audit-button" type="button" data-live-audit="${escapeHTML(asset.slug || '')}"${tokens.length ? '' : ' disabled'}>Run live terminal audit ↗</button>`}<button class="text-button live-session-button" type="button" data-live-session="${escapeHTML(asset.slug || '')}"${tokens.length ? '' : ' disabled'}>Run 7-day session review ↗</button></div>${findingMarkup}<div id="live-session-result"></div><p class="dossier-note">The terminal joins RWA identity, issuers, token metadata and DEX evidence. CMC market pairs may be unavailable on this API plan; that is separate from DEX coverage. It reports evidence and contradictions; it does not infer backing, rights, suitability or executable liquidity.</p>`;
    const liveProvenance = byId('detail-live-dossier').querySelector('.live-provenance');
    if (liveProvenance) liveProvenance.open = true;
    const publication = dossier._publication;
    if (publication) {
      const heading = byId('detail-live-dossier').querySelector('.dossier-heading .eyebrow');
      if (heading) heading.textContent = `PUBLISHED CMC DOSSIER · ${String(publication.status || 'STORED').toUpperCase()}`;
      const note = document.createElement('p');
      note.className = 'dossier-note';
      note.textContent = `Published ${publication.published_at || 'timestamp unavailable'} · observed ${publication.observed_at || 'timestamp unavailable'} · ${publication.status || 'stored'}`;
      byId('detail-live-dossier').prepend(note);
    }
  }

  async function loadPublishedDossier(asset) {
    if (!liveEnabled || !asset) return;
    try {
      const response = await fetch(`${window.BELL_PUBLISHED_ENDPOINT || '/api/published'}?slug=${encodeURIComponent(asset.id)}`, { headers: { Accept: 'application/json' } });
      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) return;
      const dossier = await response.json();
      if (response.status === 404 && dossier.status === 'map_only') {
        if (window.location.hash === `#asset=${encodeURIComponent(asset.id)}`) {
          byId('detail-availability').insertAdjacentHTML('beforeend', `<p class="dossier-note"><strong>Refresh queued.</strong> Bell will investigate this map entry server-side; this page will show the published dossier after the Mac mini publisher completes it.</p>`);
        }
        return;
      }
      if (!response.ok || window.location.hash !== `#asset=${encodeURIComponent(asset.id)}`) return;
      renderLiveDossier(dossier);
    } catch (error) {
      // The static fallback remains usable when no live origin is attached.
    }
  }

  async function loadHomepageDossier() {
    if (!liveEnabled || window.location.hash || !terminal) return;
    const asset = assets.find(item => item.id === 'gold');
    if (!asset) return;
    try {
      const response = await fetch(`${window.BELL_PUBLISHED_ENDPOINT || '/api/published'}?slug=gold`, { headers: { Accept: 'application/json' } });
      if (!response.ok || window.location.hash) return;
      const dossier = await response.json();
      const evidence = dossier?.audit?.evidence || dossier?.terminal;
      if (evidence) terminal.render(asset, { ...evidence, findings: dossier.audit?.findings || evidence.findings || [] });
    } catch (error) {
      // Keep the deterministic map brief if the publication edge is temporarily unavailable.
    }
  }

  function renderDexInspector(row) {
    const panel = byId('live-dex-inspector');
    if (!panel) return;
    if (!row) {
      panel.hidden = true;
      panel.innerHTML = '';
      return;
    }
    const detail = row.detail || {};
    const price = row.price || {};
    const security = row.security || {};
    const holders = row.holders || {};
    const pools = Array.isArray(row.pools) ? row.pools : [];
    const value = item => item == null || item === '' ? 'N/A' : `$${formatMoney(item)}`;
    const pair = pool => `${pool.base?.symbol || '?'} / ${pool.quote?.symbol || '?'}`;
    const state = row.state === 'available' ? 'DEX EVIDENCE AVAILABLE' : row.state === 'no_contract' ? 'NO CONTRACT / NO DEX LOOKUP' : 'DEX LOOKUP NOT RESOLVED';
    const errorNote = Array.isArray(row.errors) && row.errors.length ? `<p class="dossier-note">${row.errors.length} DEX request(s) failed for this wrapper. Bell keeps that as unavailable evidence, not zero activity.</p>` : '';
    panel.hidden = false;
    const tagRows = Array.isArray(row.holder_tags?.tags) ? row.holder_tags.tags : [];
    panel.innerHTML = `<div class="dex-inspector-head"><div><span class="eyebrow">WRAPPER EVIDENCE / ${escapeHTML(row.symbol || row.name || 'TOKEN')}</span><h3>${escapeHTML(row.name || row.symbol || 'Selected token')}</h3><p>${escapeHTML(row.network || 'Network unresolved')} · ${escapeHTML(row.contract_address || 'contract unavailable')}</p></div><div><span class="audit-state">${escapeHTML(state)}</span><button class="text-button" type="button" data-close-dex>Close ×</button></div></div><div class="dex-inspector-grid"><span><small>DEX price</small><strong>${value(price.price ?? detail.price)}</strong></span><span><small>Liquidity</small><strong>${value(price.liquidity_usd ?? detail.liquidity_usd)}</strong></span><span><small>Holders</small><strong>${holders.count == null ? '—' : formatMoney(holders.count)}</strong></span><span><small>Security</small><strong>${escapeHTML(security.security_level || '—')}</strong></span><span><small>Risk hits</small><strong>${security.hit_count == null ? '—' : security.hit_count}</strong></span><span><small>24h DEX volume</small><strong>${value(price.volume_24h ?? detail.volume_24h)}</strong></span></div>${pools.length ? `<div class="dex-pools"><div class="dex-inspector-subhead"><span class="eyebrow">TOP POOLS / ${pools.length}</span><span class="dossier-note">CMC DEX surface</span></div><div class="table-scroll"><table class="dossier-table"><thead><tr><th>Pair</th><th>Exchange</th><th>Liquidity</th><th>24h volume</th></tr></thead><tbody>${pools.map(pool => `<tr><th>${escapeHTML(pair(pool))}</th><td>${escapeHTML(pool.exchange || '—')}</td><td>${value(pool.liquidity_usd)}</td><td>${value(pool.volume_24h)}</td></tr>`).join('')}</tbody></table></div></div>` : '<p class="dossier-note">No pool rows were returned for this wrapper.</p>'}${tagRows.length ? `<div class="dex-pools"><div class="dex-inspector-subhead"><span class="eyebrow">HOLDER COHORTS / ${tagRows.length}</span><span class="dossier-note">Tagged wallet distribution</span></div><div class="table-scroll"><table class="dossier-table"><thead><tr><th>Tag</th><th>Holders</th><th>Holder ratio</th><th>Token balance</th></tr></thead><tbody>${tagRows.map(tag => `<tr><th>${escapeHTML(tag.tag || '—')}</th><td>${escapeHTML(tag.holder_count || '—')}</td><td>${escapeHTML(tag.holder_ratio || '—')}</td><td>${escapeHTML(tag.token_balance || '—')}</td></tr>`).join('')}</tbody></table></div></div>` : '<p class="dossier-note">No tagged holder cohorts were returned for this wrapper.</p>'}${security.tags?.length ? `<p class="dossier-note">Contract tags: ${security.tags.map(tag => escapeHTML(tag)).join(', ')}</p>` : ''}${errorNote}<p class="dossier-note">DEX evidence describes observable token and venue surfaces. It does not verify reserves, redemption rights, legal ownership or executable size.</p></div>`;
  }

  function downloadLiveReceipt() {
    if (!liveReceiptSource) return;
    const record = {
      schema_version: 'bell.live.receipt.v1',
      export_kind: 'normalized_live_rwa_evidence',
      exported_at: new Date().toISOString(),
      observed_at: liveReceiptSource.observed_at || liveReceiptSource.provenance?.observed_at || null,
      asset: liveReceiptSource.asset || {},
      metadata: liveReceiptSource.metadata || {},
      tokens: liveReceiptSource.tokens || [],
      issuers: liveReceiptSource.issuers || [],
      crypto_info: liveReceiptSource.crypto_info || [],
      market_pairs: liveReceiptSource.market_pairs || [],
      market_pairs_error: liveReceiptSource.market_pairs_error || null,
      dex_evidence: liveReceiptSource.dex_evidence || null,
      provenance: liveReceiptSource.provenance || {},
      note: 'Normalized evidence receipt. It contains no API key or raw HTTP response. It does not prove backing, redemption, legal rights or executable liquidity.'
    };
    const blob = new Blob([JSON.stringify(record, null, 2)], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bell-${record.asset.slug || record.asset.symbol || 'rwa'}-live-evidence-${record.observed_at ? record.observed_at.slice(0, 10) : 'receipt'}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  function renderAuditSnapshot(asset) {
    const audit = auditSnapshots[asset.slug || asset.id];
    const target = byId('detail-audit');
    target.hidden = !audit;
    if (!audit) {
      target.innerHTML = '';
      return;
    }
    const stateClass = audit.state.replaceAll('_', '-');
    target.innerHTML = `<div class="audit-snapshot-heading"><div><span class="eyebrow">CMC SURFACE AUDIT / ${escapeHTML(audit.observed_at)}</span><h3>${escapeHTML(audit.headline)}</h3></div><span class="audit-state audit-state-${escapeHTML(stateClass)}">${escapeHTML(audit.label)}</span></div><p class="audit-snapshot-summary">${escapeHTML(audit.summary)}</p><ul class="audit-findings">${audit.findings.map(finding => `<li>${escapeHTML(finding)}</li>`).join('')}</ul><div class="audit-next-action"><span class="eyebrow">NEXT EVIDENCE REQUIRED</span><p>${escapeHTML(audit.next_action || 'Collect more evidence before making a comparison.')}</p></div><p class="dossier-note">${escapeHTML(audit.source)}. Snapshot evidence is not a live quote and does not establish backing, redemption, eligibility or executable liquidity.</p>`;
  }
  byId('detail-availability').addEventListener('click', async event => {
    const button = event.target.closest('[data-live-asset]');
    if (!button) return;
    const slug = button.dataset.liveAsset;
    const original = button.textContent;
    button.disabled = true;
    button.textContent = 'Loading CMC dossier…';
    try {
      const publishedEndpoint = `${window.BELL_PUBLISHED_ENDPOINT || '/api/published'}?slug=${encodeURIComponent(slug)}`;
      let response = await fetch(publishedEndpoint, { headers: { Accept: 'application/json' } });
      let dossier = await response.json();
      // A scheduled Mac mini publication is preferred. If this asset has never
      // been published, fall back to a one-off live run and persist its result.
      if (response.status === 404 && directLiveEnabled) {
        const endpoint = `${window.BELL_RUNTIME_ENDPOINT || '/api/terminal'}?slug=${encodeURIComponent(slug)}`;
        response = await fetch(endpoint, { headers: { Accept: 'application/json' } });
        dossier = await response.json();
      }
      if (!response.ok) throw new Error(dossier.error || `HTTP ${response.status}`);
      renderLiveDossier(dossier);
    } catch (error) {
      byId('detail-live-dossier').hidden = false;
      byId('detail-live-dossier').innerHTML = '<p class="dossier-error"><strong>Live dossier unavailable.</strong> Start <code>python3 bell/server.py</code> with <code>CMC_API_KEY</code> on the server, or keep using this offline catalogue.</p>';
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  });
  function renderLiveSession(receipt) {
    const wrappers = Array.isArray(receipt.wrappers) ? receipt.wrappers : [];
    const value = (wrapper, session) => wrapper.sessions?.[session]?.median_range_pct == null ? 'N/A' : `${Number(wrapper.sessions[session].median_range_pct).toFixed(2)}%`;
    const warnings = Array.isArray(receipt.warnings) && receipt.warnings.length ? `<ul class="dossier-warnings">${receipt.warnings.map(warning => `<li>${escapeHTML(warning)}</li>`).join('')}</ul>` : '<p class="dossier-note">No coverage warnings returned for this run.</p>';
    byId('live-session-result').innerHTML = `<div class="session-result-heading"><div><span class="eyebrow">LIVE SESSION REVIEW COMPLETE</span><p class="dossier-note">${escapeHTML(receipt.window?.start_utc || 'Start not supplied')} to ${escapeHTML(receipt.window?.end_utc || 'end not supplied')} · ${escapeHTML(receipt.window?.duration_hours || 0)} hours · ${wrappers.length} wrappers</p></div><span class="snapshot-tag">${escapeHTML(receipt.state || 'unknown').toUpperCase()}</span></div><div class="table-scroll"><table class="dossier-table session-result-table"><thead><tr><th>Wrapper</th><th>Cash</th><th>After-hours</th><th>Weekend</th><th>Coverage</th></tr></thead><tbody>${wrappers.map(wrapper => `<tr><th>${escapeHTML(wrapper.symbol)}<small>${escapeHTML(wrapper.issuer || '')}</small></th><td>${value(wrapper, 'cash')}</td><td>${value(wrapper, 'after_hours')}</td><td>${value(wrapper, 'weekend')}</td><td>${escapeHTML(wrapper.state || 'unknown')}</td></tr>`).join('')}</tbody></table></div>${warnings}<p class="dossier-note">This is a new server-side CMC observation. It is not the dated public snapshot and does not measure liquidity, price discovery, eligibility or execution.</p>`;
  }
  byId('detail-live-dossier').addEventListener('click', async event => {
    const dexButton = event.target.closest('[data-live-dex]');
    if (dexButton) {
      renderDexInspector(liveDexRows.get(String(dexButton.dataset.liveDex)));
      return;
    }
    if (event.target.closest('[data-close-dex]')) {
      renderDexInspector(null);
      return;
    }
    const receiptButton = event.target.closest('[data-live-receipt]');
    if (receiptButton && !receiptButton.disabled) {
      downloadLiveReceipt();
      return;
    }
    const auditButton = event.target.closest('[data-live-audit]');
    if (auditButton && !auditButton.disabled) {
      const original = auditButton.textContent;
      auditButton.disabled = true;
      auditButton.textContent = 'Auditing CMC surfaces…';
      try {
        const endpoint = `${window.BELL_RUNTIME_ENDPOINT || '/api/audit'}?slug=${encodeURIComponent(auditButton.dataset.liveAudit)}`;
        const response = await fetch(endpoint, { headers: { Accept: 'application/json' } });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
        const findings = Array.isArray(result.findings) ? result.findings : [];
        const state = String(result.conclusion || 'unknown').replaceAll('_', ' ').toUpperCase();
        byId('live-audit-result').innerHTML = `<div class="live-audit-result"><div class="session-result-heading"><div><span class="eyebrow">LIVE INTEGRITY AUDIT COMPLETE</span><p class="dossier-note">${escapeHTML(result.asset?.name || auditButton.dataset.liveAudit)} · ${findings.length} finding(s)</p></div><span class="audit-state">${escapeHTML(state)}</span></div>${findings.length ? `<ul class="audit-findings">${findings.map(item => `<li><strong>${escapeHTML(item.code)}</strong> — ${escapeHTML(item.message)}</li>`).join('')}</ul>` : '<p class="dossier-note">No integrity findings were returned for this snapshot.</p>'}<p class="dossier-note">Deterministic rules ran server-side. Re-check denomination, legal claim and execution evidence separately.</p></div>`;
      } catch (error) {
        byId('live-audit-result').innerHTML = `<p class="dossier-error"><strong>Integrity audit unavailable.</strong> ${escapeHTML(error.message || 'The live server is not running.')}</p>`;
      } finally {
        auditButton.disabled = false;
        auditButton.textContent = original;
      }
      return;
    }
    const button = event.target.closest('[data-live-session]');
    if (!button || button.disabled) return;
    const original = button.textContent;
    button.disabled = true;
    button.textContent = 'Running 7-day review…';
    try {
      const endpoint = `${window.BELL_RUNTIME_ENDPOINT || '/api/session'}?slug=${encodeURIComponent(button.dataset.liveSession)}&days=7`;
      const response = await fetch(endpoint, { headers: { Accept: 'application/json' } });
      const receipt = await response.json();
      if (!response.ok) throw new Error(receipt.error || `HTTP ${response.status}`);
      renderLiveSession(receipt);
    } catch (error) {
      byId('live-session-result').innerHTML = `<p class="dossier-error"><strong>Session review unavailable.</strong> ${escapeHTML(error.message || 'The selected asset may have no hourly OHLCV, or the live server is not running.')} Try the published review, or start the local server with <code>CMC_API_KEY</code>.</p>`;
    } finally {
      button.disabled = false;
      button.textContent = original;
    }
  });

  function goldRelative(wrapper, session) {
    return Number.isFinite(Number(wrapper.range_pct[session])) && Number(wrapper.range_pct.cash) > 0 ? Number(wrapper.range_pct[session]) / Number(wrapper.range_pct.cash) * 100 : null;
  }
  function renderGoldAnalysis() {
    const gold = window.BELL_GOLD_SNAPSHOT;
    if (!gold) return;
    byId('gold-comparison-body').innerHTML = gold.wrappers.map(wrapper => {
      const cells = ['cash', 'after_hours', 'weekend'].map(session => {
        const value = goldMetric === 'range' ? percent(wrapper.range_pct[session]) : ratioLabel(goldRelative(wrapper, session));
        const width = goldMetric === 'range' ? (Number(wrapper.range_pct[session]) || 0) / 0.6 * 100 : (goldRelative(wrapper, session) || 0);
        return `<td${session === 'weekend' ? ' class="weekend-cell"' : ''}><span class="cell-value">${value}</span><span class="mini-track" aria-hidden="true"><span style="width:${Math.min(width, 100)}%"></span></span></td>`;
      }).join('');
      return `<tr><td><strong>${escapeHTML(wrapper.symbol)}</strong><span>${escapeHTML(wrapper.issuer)}</span></td>${cells}<td class="ratio-cell"><strong>≈${goldRelative(wrapper, 'weekend').toFixed(0)}%</strong><small>of comparison median range</small></td></tr>`;
    }).join('');
    byId('gold-table-caption').textContent = goldMetric === 'range' ? 'Median hourly range, as a percentage of each bar’s opening price.' : 'Bucket median relative to the weekday comparison median. Comparison = 100%; approximate ratios from rounded inputs.';
    byId('gold-metric-note').textContent = goldMetric === 'range' ? 'Range = (high − low) / open. A median of hourly ranges, not a return or a liquidity measure.' : 'Relative = bucket median / weekday comparison median × 100. These ratios describe movement; they do not measure market quality.';
    document.querySelectorAll('[data-gold-metric]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.goldMetric === goldMetric)));
  }
  document.querySelectorAll('[data-gold-metric]').forEach(button => button.addEventListener('click', () => { goldMetric = button.dataset.goldMetric; renderGoldAnalysis(); }));

  function renderAssetRoute(moveFocus = false, selectedId = null) {
    const match = /^#asset=([a-z0-9-]+)$/.exec(window.location.hash);
    const asset = (selectedId || match) ? assets.find(item => item.id === (selectedId || match[1])) : null;
    const review = asset ? publishedReview(asset) : null;
    renderInvestorBrief(asset, review);
    byId('asset-detail').hidden = !asset;
    byId('gold-analysis').hidden = !review || asset.analysis_id !== 'gold';
    byId('tesla-analysis').hidden = !review || asset.analysis_id !== 'tesla';
    if (!asset) {
      document.title = 'Bell | RWA Comparability Evidence | Dyplux';
      if (terminal) terminal.render(assets.find(item => item.id === 'gold') || assets[0]);
      loadHomepageDossier();
      if (match) {
        byId('catalogue-count').textContent = 'Asset unavailable in this demo. Browse the catalogue below.';
        byId('catalogue').scrollIntoView();
      }
      return;
    }
    if (terminal) terminal.render(asset);
    setFocus(null);
    byId('detail-title').textContent = `${asset.name} / ${asset.symbol}`;
    byId('detail-category').textContent = `REFERENCE ASSET / ${asset.category.toUpperCase()}`;
    const audit = auditSnapshots[asset.slug || asset.id];
    byId('detail-description').textContent = audit ? 'A dated CMC surface audit is available for this reference. Bell records what can be observed and where the grouping is not safe to compare.' : review ? asset.description : 'Reference identity and category from the catalogue. No wrapper dossier or session review is published for this asset in the static demo.';
    byId('detail-status').textContent = audit ? audit.label : review ? 'PUBLISHED SESSION REVIEW' : window.BELL_CATALOGUE.mode === 'live_map_snapshot' ? 'MAP ENTRY ONLY' : 'ILLUSTRATIVE MAP ENTRY ONLY';
    byId('detail-live-dossier').hidden = true;
    byId('detail-live-dossier').innerHTML = '';
    renderAuditSnapshot(asset);
    const liveCta = directLiveEnabled
      ? `<button class="text-button live-dossier-button" type="button" data-live-asset="${escapeHTML(asset.id)}">Load current CMC dossier ↗</button>`
      : liveEnabled
        ? '<p class="dossier-note">Live publication is enabled. Select this asset to request the latest published dossier; unexplored assets enter the server-side refresh queue.</p>'
        : '<p class="dossier-note">Public demo uses a dated, credential-free snapshot. Current CMC data is enabled in the local server mode.</p>';
    byId('detail-availability').innerHTML = review
      ? `<strong>${audit ? 'Comparability audit + session evidence' : 'Session review available'}</strong><p>${audit ? 'The surface audit is the primary result. The dated session review is secondary evidence about movement, not a quality score.' : '4 wrappers · 168 hours each · cash, after-hours and weekend comparisons · selected venue totals · downloadable Tesla evidence.'}</p><a class="text-button" href="#session-audit">Inspect the session comparison ↓</a>${liveCta}`
      : audit
        ? `<strong>Surface audit available</strong><p>CMC's RWA page already exposes the catalogue, issuers, tokens and markets. Bell records the contradictions that make a direct comparison unsafe or incomplete.</p>${liveCta}`
      : `<strong>Map entry only</strong><p>This asset was found in the catalogue, but no session review has been published for it. ${asset.has_tokens === false ? 'The map snapshot reports no token wrappers.' : 'Wrapper details and historical coverage have not been published for this entry; a map listing alone does not establish sufficient history.'} This is a catalogue result, not a failed analysis.</p><p>Session review is available only where published, and calculation requires sufficient hourly wrapper coverage. Explore a published example: <a class="text-button" href="#asset=gold">Gold ↗</a> or <a class="text-button" href="#asset=tesla">Tesla ↗</a>.</p>${liveEnabled ? '<p class="dossier-note">With the optional live server running, you can request current wrapper details and check historical coverage.</p>' : ''}${liveCta}`;
    if (review && asset.analysis_id === 'gold') {
      byId('detail-availability').innerHTML = `<strong>Comparability audit + session evidence</strong><p>The surface audit is the primary result. A dated Gold session receipt is secondary evidence about observed movement under a declared clock.</p><a class="text-button" href="#gold-analysis">Inspect the Gold session comparison ↓</a>${liveEnabled ? liveCta : '<p class="dossier-note">Public demo uses the dated Gold receipt. Current CMC data is enabled in the local server mode.</p>'}`;
      renderGoldAnalysis();
    }
    document.title = `${asset.name} · Bell RWA research`;
    byId('asset-detail').scrollIntoView({ behavior: 'auto', block: 'start' });
    loadPublishedDossier(asset);
    if (moveFocus) byId('detail-title').focus({ preventScroll: true });
  }
  // Keep in-page Tesla anchors open, while catalogue/back navigation closes
  // the deep dive. Hash routes work without a server, including file://.
  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#gold-analysis' && window.BELL_GOLD_SNAPSHOT) {
      renderAssetRoute(false, 'gold');
      byId('gold-analysis').scrollIntoView();
      return;
    }
    if (['#session-audit', '#venues', '#methodology'].includes(window.location.hash)) {
      renderAssetRoute(false, 'tesla');
      document.querySelector(window.location.hash).scrollIntoView();
      return;
    }
    renderAssetRoute(true);
  });

  byId('hero-bars').innerHTML = wrappers.map(w => `<div class="hero-bar-row"><span>${escapeHTML(w.symbol)}</span><div class="hero-bar-tracks"><div class="hero-bar-track"><span style="width:${w.range_pct.cash / 0.6 * 100}%"></span></div><div class="hero-bar-track weekend"><span style="width:${w.range_pct.weekend / 0.6 * 100}%"></span></div></div><strong>${percent(w.range_pct.weekend)}</strong></div>`).join('');

  function renderCards() {
    byId('wrapper-cards').innerHTML = wrappers.map((w, i) => `<button class="wrapper-card${focused && focused !== w.symbol ? ' is-dimmed' : ''}" data-wrapper="${escapeHTML(w.symbol)}" aria-pressed="${focused === w.symbol}" aria-label="${focused === w.symbol ? 'Clear focus on' : 'Focus'} ${escapeHTML(w.symbol)}, ${escapeHTML(w.issuer)}"><div class="wrapper-card-top"><span class="wrapper-monogram" aria-hidden="true">${['B', 'O', 'b', 'R'][i]}</span><span class="wrapper-focus">${focused === w.symbol ? 'FOCUSED −' : 'INSPECT ↗'}</span></div><h3>${escapeHTML(w.symbol)}</h3><p class="issuer">${escapeHTML(w.issuer)}</p><div class="wrapper-card-bottom"><span>168 HOURLY BARS</span><strong>SNAPSHOT</strong></div></button>`).join('');
    byId('reset-focus').hidden = !focused;
  }

  function renderComparison() {
    byId('comparison-body').innerHTML = wrappers.map(w => {
      const cells = ['cash', 'after_hours', 'weekend'].map(session => {
        const value = metric === 'range' ? percent(w.range_pct[session]) : ratioLabel(relative(w, session));
        const width = metric === 'range' ? (Number(w.range_pct[session]) || 0) / 0.6 * 100 : (relative(w, session) || 0);
        return `<td${session === 'weekend' ? ' class="weekend-cell"' : ''}><span class="cell-value">${value}</span><span class="mini-track" aria-hidden="true"><span style="width:${width}%"></span></span></td>`;
      }).join('');
      return `<tr class="${focused === w.symbol ? 'is-focused' : focused ? 'is-dimmed' : ''}"><td><strong>${escapeHTML(w.symbol)}</strong><span>${escapeHTML(w.issuer)}</span></td>${cells}<td class="ratio-cell"><strong>${ratioLabel(relative(w, 'weekend'))}</strong><small>of cash median range</small></td></tr>`;
    }).join('');
    byId('table-caption').textContent = metric === 'range' ? 'Median hourly range, as a percentage of each bar’s opening price.' : 'Session median range relative to the cash-session median. Cash = 100%; approximate ratios from rounded inputs.';
    byId('metric-note').textContent = metric === 'range' ? 'Range = (high − low) / open. A median of hourly ranges, not a return or a liquidity measure.' : 'Relative = session median / cash median × 100. These ratios describe movement; they do not measure market quality.';
    document.querySelectorAll('[data-metric]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.metric === metric)));
  }

  function renderVenues() {
    byId('venue-rows').innerHTML = wrappers.map(w => {
      const venue = w.venue_usd_24h;
      const rowClass = focused && focused !== w.symbol ? ' is-dimmed' : '';
      if (!venue) return `<div class="venue-row${rowClass}"><div class="venue-row-top"><strong>${escapeHTML(w.symbol)}<span>${escapeHTML(w.issuer)}</span></strong><span>NOT SUPPLIED</span></div><p class="venue-missing">No venue totals in this snapshot summary. Not zero; unknown.</p></div>`;
      const cexShare = venue.cex / (venue.cex + venue.dex) * 100;
      const label = `${w.symbol}: approximately ${cexShare.toFixed(1)}% CEX, ${(100 - cexShare).toFixed(1)}% DEX, from rounded 24-hour totals`;
      return `<div class="venue-row${rowClass}"><div class="venue-row-top"><strong>${escapeHTML(w.symbol)}<span>${escapeHTML(w.issuer)}</span></strong><span>≈${cexShare.toFixed(1)}% CEX / ${(100 - cexShare).toFixed(1)}% DEX</span></div><div class="venue-track" role="img" aria-label="${escapeHTML(label)}"><span class="cex" style="width:${cexShare}%"></span><span class="dex" style="width:${100 - cexShare}%"></span></div><div class="venue-amounts"><span>CEX ${millions(venue.cex)}</span><span>DEX ${millions(venue.dex)}</span></div></div>`;
    }).join('');
  }

  function renderEvidence() {
    const selected = focused ? wrappers.filter(w => w.symbol === focused) : wrappers;
    byId('focused-evidence-title').textContent = focused ? `Focused wrapper / ${focused}` : 'Wrapper evidence / all four';
    byId('focused-evidence').innerHTML = selected.map(w => `<div class="wrapper-evidence"><strong>${escapeHTML(w.symbol)} / ${escapeHTML(w.issuer)}</strong><p>Cash ${percent(w.range_pct.cash)} · After-hours ${percent(w.range_pct.after_hours)} · Weekend ${percent(w.range_pct.weekend)}<br>Weekend / cash ${ratioLabel(relative(w, 'weekend'))} · 168 bars<br>${w.venue_usd_24h ? `24h venue totals: CEX ${millions(w.venue_usd_24h.cex)} / DEX ${millions(w.venue_usd_24h.dex)} (receipt context)` : 'Venue totals: not supplied'}</p></div>`).join('');
  }

  function setFocus(symbol) {
    focused = symbol;
    renderCards();
    renderComparison();
    renderVenues();
    renderEvidence();
  }
  byId('wrapper-cards').addEventListener('click', event => {
    const button = event.target.closest('[data-wrapper]');
    if (!button) return;
    const symbol = button.dataset.wrapper;
    setFocus(focused === symbol ? null : symbol);
    // Cards are rebuilt; restore keyboard focus to the corresponding control.
    Array.from(document.querySelectorAll('[data-wrapper]')).find(b => b.dataset.wrapper === symbol).focus({ preventScroll: true });
  });
  byId('reset-focus').addEventListener('click', () => { setFocus(null); document.querySelector('[data-wrapper]').focus({ preventScroll: true }); });
  document.querySelectorAll('[data-metric]').forEach(button => button.addEventListener('click', () => { metric = button.dataset.metric; renderComparison(); }));

  const dialog = byId('evidence-dialog');
  document.querySelectorAll('[data-evidence]').forEach(button => button.addEventListener('click', () => {
    lastEvidenceTrigger = button;
    renderEvidence();
    dialog.showModal();
    document.body.style.overflow = 'hidden';
    byId('close-evidence').focus({ preventScroll: true });
  }));
  function closeEvidence() { dialog.close(); }
  byId('close-evidence').addEventListener('click', closeEvidence);
  byId('drawer-done').addEventListener('click', closeEvidence);
  dialog.addEventListener('click', event => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) closeEvidence();
  });
  dialog.addEventListener('close', () => {
    document.body.style.overflow = '';
    if (lastEvidenceTrigger) lastEvidenceTrigger.focus({ preventScroll: true });
  });

  function receipt() {
    // Export the complete snapshot even when the interface focuses one wrapper.
    return { ...snapshot, export_kind: 'offline_replayable_summary_receipt', export_scope: 'all_nine_entries', derived: wrappers.map(w => ({ symbol: w.symbol, relative_to_cash_pct: { cash: 100, after_hours: relative(w, 'after_hours'), weekend: relative(w, 'weekend') }, cex_share_pct: w.venue_usd_24h && (w.venue_usd_24h.cex + w.venue_usd_24h.dex) > 0 ? w.venue_usd_24h.cex / (w.venue_usd_24h.cex + w.venue_usd_24h.dex) * 100 : null })), exported_at: new Date().toISOString(), export_note: 'Export timestamp is the local save time, not a market fetch timestamp. Raw-normalised replay inputs are linked separately and the CMC receipt carries a dataset hash.' };
  }

  function legacyOfflineHTML(record) {
    const rows = wrappers.map(w => `<tr><th>${escapeHTML(w.symbol)}<small>${escapeHTML(w.issuer)}</small></th><td>${percent(w.range_pct.cash)}</td><td>${percent(w.range_pct.after_hours)}</td><td>${percent(w.range_pct.weekend)}</td><td>${ratioLabel(relative(w, 'weekend'))}</td><td>${w.venue_usd_24h ? `CEX ${millions(w.venue_usd_24h.cex)} / DEX ${millions(w.venue_usd_24h.dex)}` : 'Not supplied'}</td></tr>`).join('');
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bell · Tesla offline summary receipt</title><style>body{margin:0;background:#f4f1ea;color:#0a0e14;font:15px/1.7 Arial,sans-serif}main{max-width:1000px;margin:auto;padding:38px 24px}header{border-bottom:2px solid #0a0e14;padding-bottom:22px}h1{font-size:38px;line-height:1.1;letter-spacing:-1px;margin:12px 0}h2{font-size:22px;margin-top:32px}.tag{display:inline-block;background:#0a0e14;color:#ffcc00;padding:5px 10px;font-size:11px}p,li{max-width:850px}small{display:block;font-size:11px;font-weight:normal}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;white-space:nowrap;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:13px 10px;border-bottom:1px solid #ccc;font-size:12px}thead{background:#e8e3d7}code,pre{font-size:11px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e8e3d7;padding:18px}footer{border-top:1px solid #ccc;margin-top:30px;padding-top:16px;font-size:11px}@media print{main{padding:0}.scroll{overflow:visible}pre{font-size:9px}table{white-space:normal}}</style></head><body><main><header><span class="tag">BELL / DEMONSTRATION SNAPSHOT / SUMMARY RECEIPT</span><h1>What is still a market<br>after the bell?</h1><p>Tesla · Four wrappers · 168 hours ending 11 September 2026, 19:00 UTC.</p><small>Saved ${escapeHTML(record.exported_at)}. This is the local export time, not a market fetch timestamp.</small></header><h2>The observation</h2><p>Robinhood’s Tesla wrapper retains approximately 84% of its cash-session median hourly range at the weekend. Backed’s retains approximately 20%. This describes movement, not liquidity or price discovery.</p><div class="scroll"><table><caption>Median hourly ranges · dated summary · not live data</caption><thead><tr><th>Wrapper / issuer</th><th>Cash</th><th>After-hours*</th><th>Weekend</th><th>Weekend / cash</th><th>24h venue context</th></tr></thead><tbody>${rows}</tbody></table></div><p><small>*After-hours means all remaining weekday hours, including pre-market, post-market and overnight. Cash: 30 bars; weekday closed: 90; weekend: 48, per wrapper. Venue totals are rounded and dated 11 September 2026; exact fetch timestamp not supplied.</small></p><h2>Method</h2><p>Hourly range = ((high − low) / open) × 100. Aggregate = median by session. Assign bars by opening timestamp in America/New_York: weekdays 09:30–16:00 cash, remaining weekdays after-hours, Saturday/Sunday weekend. No exchange holiday calendar. Relative-to-cash and venue shares are derived from rounded summary values.</p><p>Hourly volume is not summed because the documented CMC field is rolling 24-hour volume.</p><h2>Provenance</h2><p>Summary documents: bell/JUDGE.md and research/rwa-session/notes.md in the Dyplux workspace. These documents and raw API responses are not bundled here.</p><ul>${snapshot.provenance.endpoints.map(endpoint => `<li><code>${escapeHTML(endpoint)}</code></li>`).join('')}</ul><p>No API requests, keys or external assets are required to open this receipt. Raw OHLCV bars, request IDs and response hashes are absent. The median ranges cannot be independently recalculated from this summary.</p><h2>Limits</h2><ul>${snapshot.limitations.map(limit => `<li>${escapeHTML(limit)}</li>`).join('')}</ul><h2>Disclosure</h2><p>${escapeHTML(snapshot.disclosure)}</p><details><summary>Complete machine-readable record</summary><pre>${escapeHTML(JSON.stringify(record, null, 2))}</pre></details><footer>Bell · An instrument by Dyplux, Lisbon. Research, not a trading signal.</footer></main></body></html>`;
  }

  function offlineHTML(record) {
    const rows = wrappers.map(wrapper => `<tr><th>${escapeHTML(wrapper.symbol)}<small>${escapeHTML(wrapper.issuer)}</small></th><td>${percent(wrapper.range_pct.cash)}</td><td>${percent(wrapper.range_pct.after_hours)}</td><td>${percent(wrapper.range_pct.weekend)}</td><td>${ratioLabel(relative(wrapper, 'weekend'))}</td><td>${wrapper.venue_usd_24h ? `CEX ${millions(wrapper.venue_usd_24h.cex)} / DEX ${millions(wrapper.venue_usd_24h.dex)}` : 'Not supplied'}</td></tr>`).join('');
    return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Bell · Tesla evidence receipt</title><style>body{margin:0;background:#f4f1ea;color:#0a0e14;font:15px/1.7 Arial,sans-serif}main{max-width:1000px;margin:auto;padding:38px 24px}header{border-bottom:2px solid #0a0e14;padding-bottom:22px}h1{font-size:38px;line-height:1.1;letter-spacing:-1px;margin:12px 0}h2{font-size:22px;margin-top:32px}.tag{display:inline-block;background:#0a0e14;color:#ffcc00;padding:5px 10px;font-size:11px}p,li{max-width:850px}small{display:block;font-size:11px;font-weight:normal}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;white-space:nowrap;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:13px 10px;border-bottom:1px solid #ccc;font-size:12px}thead{background:#e8e3d7}code,pre{font-size:11px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e8e3d7;padding:18px}footer{border-top:1px solid #ccc;margin-top:30px;padding-top:16px;font-size:11px}@media print{main{padding:0}.scroll{overflow:visible}pre{font-size:9px}table{white-space:normal}}</style></head><body><main><header><span class="tag">BELL / REPLAYABLE EVIDENCE RECEIPT</span><h1>Same asset.<br>Different clocks.</h1><p>Tesla · ${wrappers.length} entries · dated session summary.</p><small>Saved ${escapeHTML(record.exported_at)}. This is the local export time, not a market fetch timestamp.</small></header><h2>The observation</h2><p>The table preserves the nine-entry Tesla session snapshot and keeps any insufficient-data wrapper in the record. A session contrast describes observed movement; it does not establish liquidity, backing or price discovery.</p><div class="scroll"><table><caption>Median hourly ranges · dated summary</caption><thead><tr><th>Wrapper / issuer</th><th>Cash</th><th>After-hours</th><th>Weekend</th><th>Weekend / cash</th><th>24h venue context</th></tr></thead><tbody>${rows}</tbody></table></div><h2>Method and limits</h2><p>Hourly range = ((high − low) / open) × 100. Values are medians assigned by opening timestamp in America/New_York. The companion normalised payload is the replay input; no API key is included.</p><p>CMC fields do not prove denomination, legal claim, redemption, liquidity, executable size or suitability. Repeat the observation before treating a contrast as persistent.</p><h2>Provenance</h2><p>Export kind: ${escapeHTML(record.export_kind || 'offline_replayable_summary_receipt')}. The record binds the displayed values to the dated public snapshot and its evidence links.</p><details><summary>Complete machine-readable record</summary><pre>${escapeHTML(JSON.stringify(record, null, 2))}</pre></details><footer>Bell · RWA comparability evidence. Research, not a trading signal.</footer></main></body></html>`;
  }

  function download(kind) {
    const record = receipt();
    const isHTML = kind === 'html';
    const blob = new Blob([isHTML ? offlineHTML(record) : JSON.stringify(record, null, 2)], { type: isHTML ? 'text/html;charset=utf-8' : 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bell-tesla-2026-09-11-summary.${kind}`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
    byId('download-status').textContent = `${isHTML ? 'Offline HTML' : 'JSON'} summary receipt prepared. All four wrappers included.`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { byId('download-status').textContent = ''; }, 5000);
  }
  byId('download-html').addEventListener('click', () => download('html'));
  byId('download-json').addEventListener('click', () => download('json'));
  byId('drawer-download').addEventListener('click', () => download('html'));
  renderCards(); renderComparison(); renderVenues(); renderEvidence();
  renderCatalogue();
  renderAssetRoute();
  if (window.location.hash === '#gold-analysis' && window.BELL_GOLD_SNAPSHOT) {
    renderAssetRoute(false, 'gold');
    byId('gold-analysis').scrollIntoView();
  }
  if (['#session-audit', '#venues', '#methodology'].includes(window.location.hash)) {
    renderAssetRoute(false, 'tesla');
    document.querySelector(window.location.hash).scrollIntoView();
  }
})();

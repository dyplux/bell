/* Universal RWA terminal layer. It is intentionally deterministic: the brief explains
   the evidence available from the map/dossier and never pretends to be a recommendation. */
(() => {
  'use strict';

  const profiles = {
    gold: { observation: 'The saved CMC map contains token entries for Gold. Bell waits for the live dossier before asserting how many wrappers, issuers or networks are actually present.', desk: 'Load the live dossier before making a wrapper comparison. Then separate economic identity, issuer/network concentration and market access.', points: ['token entries are present in the saved map', 'live issuer and network coverage is required', 'comparison mode activates after evidence loads'] },
    silver: { observation: 'The saved CMC map contains token entries for Silver. Bell does not turn an offline catalogue flag into a wrapper count or an investment conclusion.', desk: 'Treat Silver as a discovery item until the live dossier resolves wrappers, denominations, issuers and venues.', points: ['token presence is known', 'wrapper count is not asserted offline', 'load the dossier for comparison evidence'] },
    tesla: { observation: 'The saved CMC map contains token entries for Tesla. Bell waits for current token, issuer and market evidence before comparing representations.', desk: 'Load current evidence, classify spot versus derivative representations and review issuer/network concentration before allocation review.', points: ['token presence is known', 'ticker collisions need live classification', 'market and metadata coverage are pending'] },
    spy: { observation: 'The saved CMC map says token representations exist for SPY. Bell does not assume that means one wrapper: the live dossier determines whether this is a single-token dossier or a comparison.', desk: 'Load the live dossier to resolve the representation count, issuer, chain, market access and holder evidence.', points: ['token presence is known', 'single versus multi-token state is unresolved offline', 'live dossier required'] }
  };

  let audience = 'normal';
  let latest = null;
  const byId = id => document.getElementById(id);
  const esc = value => String(value ?? '—').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
  const label = value => String(value || 'other').replace(/[_-]+/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  const compact = value => {
    if (value === null || value === undefined || value === '') return '—';
    const n = Number(value);
    if (!Number.isFinite(n)) return esc(value);
    return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(n);
  };

  function resolve(asset, dossier) {
    const known = profiles[asset?.id] || {};
    const tokens = Array.isArray(dossier?.tokens) ? dossier.tokens : [];
    const pairs = Array.isArray(dossier?.market_pairs) ? dossier.market_pairs : [];
    const issuerRows = Array.isArray(dossier?.issuers) ? dossier.issuers : [];
    const findings = Array.isArray(dossier?.findings) ? dossier.findings : [];
    const cryptoInfo = Array.isArray(dossier?.crypto_info) ? dossier.crypto_info : [];
    const dex = dossier?.dex_evidence && typeof dossier.dex_evidence === 'object' ? dossier.dex_evidence : null;
    const dexRows = Array.isArray(dex?.tokens) ? dex.tokens : [];
    const networks = new Set(cryptoInfo.map(item => item?.platform?.name || item?.platform?.symbol).filter(Boolean));
    const count = Array.isArray(dossier?.tokens) ? tokens.length : (asset?.has_tokens === false ? 0 : null);
    const state = asset?.has_tokens === false ? 'underlying-only' : dossier && Array.isArray(dossier.tokens) && count === 0 ? 'coverage-pending' : count === 0 ? 'underlying-only' : count === 1 ? 'single-token' : count > 1 ? 'multi-token' : 'coverage-pending';
    const tokenLabel = state === 'underlying-only' ? 'NO TOKEN MAPPED' : state === 'single-token' ? '1 TOKEN / DOSSIER' : state === 'multi-token' ? `${count} TOKENS / COMPARE` : 'TOKEN COVERAGE PENDING';
    const dexPoint = dex ? `DEX evidence: ${dex.covered_token_count || 0}/${dex.contract_token_count || 0} contract token(s) covered` : null;
    const livePoints = dossier ? [`${count} token representation(s) returned`, `${issuerRows.length || new Set(tokens.map(token => token.issuer_name).filter(Boolean)).size || '—'} issuer record(s) returned`, `${pairs.length} market pair(s) returned`, `${cryptoInfo.length} token metadata record(s); ${networks.size} network(s) resolved`, ...(dexPoint ? [dexPoint] : []), ...findings.slice(0, 2).map(item => `finding: ${item.code}`)] : null;
    const basePoints = livePoints || known.points || (state === 'underlying-only' ? ['no token representation in the CMC map', 'underlying research mode is active', 'token comparison is not applicable'] : ['live token count is not available in the offline map', 'load the CMC dossier for issuer and market evidence', 'do not infer absence from missing offline fields']);
    return { ...known, count, state, tokenLabel, tokens, pairs, issuerRows, findings, cryptoInfo, networks, dex, dexRows, points: basePoints, asset, dossier };
  }

  function render(asset, dossier = null) {
    if (!asset) return;
    latest = resolve(asset, dossier);
    const { state, tokenLabel, count, tokens } = latest;
    const name = asset.name || asset.id || 'Selected asset';
    const category = label(asset.category || asset.asset_type);
    const profile = latest;
    const normalBody = dossier
      ? `${name} returned ${count} token representation(s), ${latest.pairs.length} market pair(s), ${latest.issuerRows.length || 'unresolved'} issuer record(s) and ${latest.networks.size} resolved network(s). ${latest.dex ? `DEX evidence covers ${latest.dex.covered_token_count || 0} of ${latest.dex.contract_token_count || 0} wrappers with contracts.` : 'DEX evidence was not requested in this dossier.'} Bell keeps the raw observations visible and separates deterministic findings from the plain-language brief.`
      : state === 'underlying-only'
      ? `${name} has no token representation mapped in the current CMC map. Bell keeps this as underlying research: reference identity, category, historical coverage and future token availability.`
      : state === 'single-token'
        ? `${name} has one mapped token representation. There is no honest wrapper ranking to show; Bell opens a dossier for that token and tests identity, issuer, network, markets and evidence quality.`
        : state === 'multi-token'
          ? `${name} has multiple mapped representations. Bell turns the CMC token list into an exposure comparison: which entries can be compared, which need separation and what evidence is missing.`
          : `${name} is present in the CMC RWA map, but token coverage is not available in this offline view. Load the live dossier before drawing a conclusion.`;
    const deskBody = dossier
      ? `Live evidence for ${name}: ${count} token(s), ${latest.pairs.length} market pair(s), ${latest.issuerRows.length || 'unresolved'} issuer record(s), ${latest.networks.size} resolved network(s), ${latest.dex ? `${latest.dex.covered_token_count || 0}/${latest.dex.contract_token_count || 0} DEX-covered contract token(s)` : 'no DEX layer'} and ${latest.findings.length} deterministic finding(s). Use the findings as a research queue, not as a suitability decision.`
      : state === 'underlying-only'
      ? `No token layer is mapped for ${name}. Monitor the underlying and treat future tokenization as an event, not as a missing quote.`
      : state === 'single-token'
        ? `Single-representation exposure for ${name}. The desk should review the one issuer, network, market access and operational evidence rather than manufacture a peer comparison.`
        : state === 'multi-token'
          ? `${name} is a multi-representation exposure. The desk view should separate economic comparability from market access, issuer/network concentration and evidence quality.`
          : `Coverage is incomplete. This reference remains a discovery item until Bell receives token-level evidence.`;
    const observation = dossier ? (audience === 'desk' ? deskBody : normalBody) : (audience === 'desk' ? (profile.desk || deskBody) : (profile.observation || normalBody));
    const points = profile.points || [];
    latest.briefText = observation;
    byId('terminal-asset-name').textContent = name;
    byId('terminal-asset-meta').textContent = `${String(asset.symbol || '—').toUpperCase()} · ${category.toUpperCase()}`;
    byId('terminal-state').textContent = tokenLabel;
    byId('terminal-state').className = `audit-state terminal-state-${state}`;
    const liveAsset = dossier?.asset || {};
    const dexStat = latest.dex ? `${latest.dex.covered_token_count || 0}/${latest.dex.contract_token_count || 0}` : 'LOAD DOSSIER';
    const marketPairStat = dossier && dossier.market_pairs_error ? 'PLAN LIMITED' : dossier ? latest.pairs.length : 'LOAD DOSSIER';
    byId('terminal-asset-stats').innerHTML = `<span><small>Token layer</small><strong>${esc(tokenLabel)}</strong></span><span><small>DEX coverage</small><strong>${esc(dexStat)}</strong></span><span><small>Tokenized mcap</small><strong>${liveAsset.tokenized_market_cap == null ? 'MAP ONLY' : compact(liveAsset.tokenized_market_cap)}</strong></span><span><small>Market pairs</small><strong>${esc(marketPairStat)}</strong></span>`;
    byId('terminal-brief-kicker').textContent = audience === 'desk' ? 'DESK BRIEF / DETERMINISTIC' : 'PLAIN-LANGUAGE BRIEF / DETERMINISTIC';
    byId('terminal-brief-title').textContent = state === 'underlying-only' ? 'Underlying dossier' : state === 'single-token' ? 'Single representation' : state === 'multi-token' ? 'Exposure comparison' : 'Coverage pending';
    byId('terminal-brief-type').textContent = audience === 'desk' ? 'DESK NOTE' : 'RESEARCH NOTE';
    byId('terminal-brief-body').textContent = observation;
    byId('terminal-brief-points').innerHTML = points.map(point => `<li>${esc(point)}</li>`).join('');
    byId('terminal-brief-limit').textContent = dossier ? `Live dossier attached: ${tokens.length} token rows, ${latest.pairs.length} CMC market pairs and ${latest.dex ? `${latest.dex.covered_token_count || 0}/${latest.dex.contract_token_count || 0} DEX-covered contract tokens` : 'no DEX evidence'}. CMC fields are evidence; they do not prove backing, redemption or suitability.` : 'This brief is generated from the CMC map snapshot. Load a live dossier to add token, issuer, DEX and market evidence.';
    byId('terminal-flow-underlying').textContent = name;
    byId('terminal-flow-tokens').textContent = state === 'underlying-only' ? 'No token' : state === 'single-token' ? 'One token' : state === 'multi-token' ? `${count} tokens` : 'Pending';
    byId('terminal-flow-issuers').textContent = latest.issuerRows.length ? `${latest.issuerRows.length} issuer set` : tokens.length ? `${new Set(tokens.map(token => token.issuer_name).filter(Boolean)).size || '—'} issuer set` : 'Issuer set';
    byId('terminal-flow-output').textContent = state === 'multi-token' ? 'Compare' : state === 'single-token' ? 'Dossier' : state === 'underlying-only' ? 'Monitor' : 'Investigate';
    byId('terminal-source').textContent = dossier ? 'LIVE CMC DOSSIER' : 'OFFLINE MAP / DETERMINISTIC';
    document.querySelectorAll('[data-terminal-audience]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.terminalAudience === audience)));
  }

  function setAudience(next) {
    audience = next === 'desk' ? 'desk' : 'normal';
    if (latest) render(latest.asset, latest.dossier);
  }

  function briefMarkdown() {
    if (!latest) return '';
    const asset = latest.asset || {};
    const name = asset.name || asset.id || 'Selected asset';
    const body = latest.briefText || '';
    return `# Bell RWA brief: ${name}\n\nAudience: ${audience === 'desk' ? 'Institutional desk' : 'Normal user'}\nGenerated: ${new Date().toISOString()}\nStatus: ${latest.tokenLabel}\n\n## Question\n\nWhat does this RWA exposure represent, and what evidence is available before comparing or monitoring it?\n\n## Brief\n\n${body}\n\n## Evidence points\n\n${latest.points.map(point => `- ${point}`).join('\\n')}\n\n## Limits\n\nThis brief is deterministic and based on the CMC map${latest.dossier ? ' plus the selected live dossier' : ' snapshot'}. It does not prove backing, redemption, suitability, legal rights or executable liquidity.\n`;
  }

  byId('terminal-download-brief').addEventListener('click', () => {
    const blob = new Blob([briefMarkdown()], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bell-${latest?.asset?.id || 'rwa'}-brief.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  });

  document.addEventListener('click', event => {
    const button = event.target.closest('[data-terminal-audience]');
    if (button) setAudience(button.dataset.terminalAudience);
  });
  window.BELL_TERMINAL = { render, setAudience, profiles, briefMarkdown };
})();

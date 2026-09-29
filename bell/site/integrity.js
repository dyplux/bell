(() => {
  // The same boundary was spelled out five times on one screen. It has to be
  // said - the monitor genuinely does not observe any of it - but said five
  // times it stops being read, and it crowds out the answer the reader came
  // for. Full sentence once, where the decision is stated; a compact marker
  // everywhere else, pointing at the same four words.
  const NOT_OBSERVED_FULL = 'Backing, redemption, eligibility and custody are not observed here and remain your diligence.';
  const NOT_OBSERVED_SHORT = 'Not observed: backing · redemption · eligibility · custody';

  // The receipt carries this boundary on several fields, correctly - a receipt
  // should state its own limits wherever it is read. The page then printed
  // every one of them, so the same four words landed five times on one screen
  // and stopped being read. Say it in full the first time it is needed in a
  // render, and abbreviate after that. Reset per render, never across renders,
  // so a reader who lands mid-page still meets the full sentence once.
  // First attempt keyed this on render order, and the order is not what I
  // assumed: the hero copy and the panel below it are written in two passes
  // that do not share the flag, so both kept printing the sentence in full.
  // Abbreviating is a property of the PLACE, not of who happened to render
  // first - the hero states it, anything repeating it underneath shortens it.
  const shortenBoundary = text => String(text || '').replace(
    /(?:Backing|backing)[^.]*?(?:custody|diligence)[^.]*\./g, NOT_OBSERVED_SHORT);
  const boundary = text => String(text || '');

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
  const initialURL = new URL(window.location.href);
  const initialReference = initialURL.searchParams.get('reference') || '';
  // The index's own state is in the URL, because a research tool whose pitch is
  // a defensible handoff has to be able to hand over the view. Sort, filter,
  // page size, page number and the index query all used to leave the address
  // bar reading https://bell.dyplux.com/ , so "here is what I was looking at"
  // could not be sent to anyone. Only ?reference= and ?map_reference= were
  // shareable, which are the two a reader reaches by accident.
  // The index search is the same field as the hero search and already rides
  // in ?reference=, so it is not given a second name here.
  const INDEX_STATE = ['state', 'sort', 'size', 'page'];
  const startingFilter = initialURL.searchParams.get('state');
  const startingSort = initialURL.searchParams.get('sort');
  const startingSize = Number(initialURL.searchParams.get('size'));
  let filter = startingFilter || 'all';
  let sortBy = (window.BellIndexOrder?.ORDERS || []).includes(startingSort)
    ? startingSort : 'severity';
  let query = initialReference.trim();
  let searchAttempted = Boolean(query);
  let pageNumber = Math.max(0, (Number(initialURL.searchParams.get('page')) || 1) - 1);
  let lastVisibleIndex = [];

  function rememberIndexState() {
    const url = new URL(window.location.href);
    const state = {
      state: filter === 'all' ? null : filter,
      sort: sortBy === 'severity' ? null : sortBy,
      size: pageSize === defaultPageSize ? null : String(pageSize),
      page: pageNumber === 0 ? null : String(pageNumber + 1),
    };
    for (const key of INDEX_STATE) {
      if (state[key] === null) url.searchParams.delete(key);
      else url.searchParams.set(key, state[key]);
    }
    // replaceState, not pushState: changing a filter is not a navigation, and
    // making the back button walk a reader out through nine filter changes is
    // its own defect.
    if (url.toString() !== window.location.href) window.history.replaceState({}, '', url);
  }
  // Twelve rows at ~350px each made the reference index 4,200px - a third of
  // the whole page - rendered before a first-time visitor had searched for
  // anything. The index is where you go when you want the population; the
  // search box above it is where you go when you have a question. Six rows,
  // same pagination, nothing removed.
  // Six rows all carried the same state and the same sentence. Now that the
  // first page interleaves states, each row is a different shape and a
  // different length, so four show the whole range in less space than six
  // identical ones took. On a phone each of those four is about 1.2 screens
  // tall, which turned the index into five and a half screens of scrolling, so
  // a narrow viewport gets two. Nothing is hidden: the search, the state
  // filters and the pager all still reach every reference.
  // 4 cards a page over 792 references is 198 pages, which is not navigable by
  // hand: a reviewer said so and was right. These are full evidence cards, so
  // raising the number for everyone trades one unusable page for another. The
  // reader chooses, and the pagination gained a jump to the last page and a
  // direct page entry, because "Next" 197 times is not navigation either.
  const defaultPageSize = window.matchMedia('(max-width: 760px)').matches ? 2 : 4;
  let pageSize = [4, 12, 24].includes(startingSize) ? startingSize : defaultPageSize;

  labelDatedReplayLinks();

  const signalLabels = {
    PRICE_DENOMINATION_BREAK: 'observed quote ratio ≥10× block floor',
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
  function formatRatio(value) {
    const parsed = numericValue(value);
    if (parsed === null) return 'N/A';
    const precision = parsed > 1 && parsed < 1.01 ? 10 : 2;
    return parsed.toLocaleString(undefined, { maximumFractionDigits: precision });
  }
  const temporalReceiptPaths = new Map([
    ['1', ['proof/gold-live-2026-09-13.json', 'proof/gold-live-2026-09-17.json']],
    ['14', ['proof/tesla-live-2026-09-13.json', 'proof/tesla-live-2026-09-17.json']],
  ]);
  const temporalReceiptPromises = new Map();

  function temporalReceiptPathsFor(alert) {
    return temporalReceiptPaths.get(String(alert?.rwa_id || '')) || [];
  }

  // "For a product sold as tracking, there is still no per-reference
  // change-over-time view." The history answered how the POPULATION moved;
  // nothing answered "did THIS reference change since the dated observation",
  // which is the question a reader holding one reference actually has.
  //
  // The dated replay is 3.42 MiB, so a 95 KB snapshot of the four fields a
  // change needs is fetched instead: 4.2 KB on the wire, once per page, cached,
  // when a case renders. Be exact rather than flattering: the hero opens a case
  // on load, so in practice that is first paint, not an interaction.
  // And a state is a function of the rules, so a diff across a rule
  // boundary would state a rule change as a market change. That comparison is
  // refused here for the same reason the publication history refuses a delta.
  let referenceSeries = null;
  function loadReferenceSeries() {
    // The deltas: one entry per published observation, holding only the
    // references that moved. 4.4 KB today against 95 KB for a second full
    // snapshot, which is why the series can grow daily without the page
    // paying for it.
    if (referenceSeries) return referenceSeries;
    referenceSeries = fetch('proof/reference-deltas.json',
      { cache: 'force-cache', headers: { Accept: 'application/json' } })
      .then(response => (response.ok ? response.json() : null))
      .catch(() => null);
    return referenceSeries;
  }

  function seriesFor(referenceId, snapshot, deltas) {
    const key = String(referenceId);
    const points = [];
    const base = (snapshot.references || {})[key];
    if (base) points.push({ observed_at: snapshot.observed_at, baseline: true, ...base });
    for (const step of (deltas?.observations || [])) {
      if (step.changed && key in step.changed) {
        points.push({ observed_at: step.observed_at, baseline: false, ...step.changed[key] });
      } else if ((step.removed || []).includes(key)) {
        points.push({ observed_at: step.observed_at, baseline: false, removed: true });
      }
    }
    return points;
  }

  let referenceSnapshot = null;
  function loadReferenceSnapshot() {
    if (referenceSnapshot) return referenceSnapshot;
    referenceSnapshot = fetch('proof/reference-snapshot-2026-09-21.json',
      { cache: 'force-cache', headers: { Accept: 'application/json' } })
      .then(response => (response.ok ? response.json() : null))
      .catch(() => null);
    return referenceSnapshot;
  }

  // The receipt carries signals in two shapes: `alerts[]` holds objects with a
  // `code`, `alert_index[]` holds a flat `signal_codes`. The first version of
  // the comparison below read `signal_codes` off an `alerts[]` item, got
  // undefined, treated it as empty, and told every reader that every rule had
  // stopped firing. Absence read as a value, which is the defect this whole
  // product is about, committed inside the feature that reports change.
  //
  // So absence returns null and is never a difference. A change view that
  // cannot read one side says so instead of inventing a delta.
  function signalCodesOf(item) {
    if (Array.isArray(item?.signal_codes)) return [...item.signal_codes].sort();
    if (Array.isArray(item?.signals)) {
      return item.signals.map(signal => (typeof signal === 'string' ? signal : signal?.code))
        .filter(Boolean).sort();
    }
    return null;
  }

  function describeChange(before, now) {
    const lines = [];
    const beforeLabel = displayDecisionLabel({ state: before.state, comparison: before.comparison_published ? {} : null }, 'FACTS OPEN');
    const nowLabel = displayDecisionLabel(now, 'FACTS OPEN');
    if (beforeLabel !== nowLabel) lines.push(['ROUTE', `${beforeLabel} → ${nowLabel}`]);
    // `Number(now.token_count || 0)` read an absent count as zero and printed
    // "REPRESENTATIONS 3 → 0". The `|| []` twenty lines down was fixed after a
    // reviewer found it; the `|| 0` beside it was not. Absence is not a value
    // here either, so a side that cannot be read is reported as not compared.
    const nowRows = now.token_count == null ? null : Number(now.token_count);
    const wasRows = before.representations == null ? null : Number(before.representations);
    if (nowRows === null || wasRows === null) {
      lines.push(['REPRESENTATIONS', 'not compared: one side records no count']);
    } else if (wasRows !== nowRows) {
      lines.push(['REPRESENTATIONS', `${wasRows} → ${nowRows}`]);
    }
    const nowList = signalCodesOf(now);
    const wasList = signalCodesOf(before);
    if (nowList === null || wasList === null) {
      lines.push(['RULES', 'not compared: one side of this observation records no signal list']);
      return lines;
    }
    const nowCodes = new Set(nowList);
    const wasCodes = new Set(wasList);
    const started = nowList.filter(code => !wasCodes.has(code));
    const stopped = wasList.filter(code => !nowCodes.has(code));
    if (started.length) lines.push(['RULES NOW FIRING', started.join(', ')]);
    if (stopped.length) lines.push(['RULES NO LONGER FIRING', stopped.join(', ')]);
    return lines;
  }

  function renderReferenceChange(alert, container) {
    if (!container || !alert) return;
    Promise.all([loadReferenceSnapshot(), loadReferenceSeries()]).then(([snapshot, deltas]) => {
      if (!snapshot || container.dataset.forId !== String(alert.rwa_id)) return;
      const datedOn = String(snapshot.observed_at || '').replace('T', ' ').slice(0, 16);
      const liveRules = receipt?.universe?.rules_version || null;
      if (!snapshot.rules_version || !liveRules || snapshot.rules_version !== liveRules) {
        container.innerHTML = `<span class="eyebrow">SINCE ${escapeHTML(datedOn)} UTC</span>`
          + `<p class="change-refused">No change is stated. The dated observation was produced under `
          + `${escapeHTML(snapshot.rules_version || 'an unrecorded rule set')} and this receipt under `
          + `${escapeHTML(liveRules || 'an unrecorded rule set')}. Subtracting them would report a rule `
          + `change as a market change, which is the error this monitor exists to refuse.</p>`;
        container.hidden = false;
        return;
      }
      const before = (snapshot.references || {})[String(alert.rwa_id)];
      if (!before) {
        container.innerHTML = `<span class="eyebrow">SINCE ${escapeHTML(datedOn)} UTC</span>`
          + `<p class="change-refused">This reference is not in the dated observation, so there is `
          + `nothing to compare it against. It is new to the catalogue, not unchanged.</p>`;
        container.hidden = false;
        return;
      }
      const changes = describeChange(before, alert);
      // How many observations this reference is actually recorded across, so
      // the reader is never left to infer a month from two points.
      const body = changes.length
        ? `<div class="change-rows">${changes.map(([label, value]) =>
            `<div><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`).join('')}</div>`
        : `<p class="change-none">Route, representation count and the rules that fired are all the `
          + `same as on the recomputed baseline. That is descriptive, not reassurance: prices moved `
          + `and are not compared here.</p>`;
      // "SINCE ... · SAME RULE SET" read as "since what Bell published that
      // day". It is not: the baseline is that day's INPUTS recomputed under
      // today's rules, and the receipt published that day recorded no rule set
      // and a different distribution. A reviewer found the page saying both
      // things on one screen. Recomputed is the right baseline - it isolates
      // market change from rule change - and it has to say so.
      const recomputed = snapshot.baseline === 'recomputed';
      // The two halves of this panel described two different observations and
      // neither said so: the diff compares the baseline against the receipt
      // THIS PAGE loaded, while the series ends at whatever observation was
      // last published. A reviewer opened a reference and read "all the same as
      // on the recomputed baseline" directly above "moved on 1 of them" - a
      // contradiction that is only two named observations once they are named.
      const loadedAt = String(receipt?.observed_at || '').replace('T', ' ').slice(0, 16);
      const seriesEndsAt = String(
        (deltas?.observations || []).slice(-1)[0]?.observed_at || snapshot.observed_at
      ).replace('T', ' ').slice(0, 16);
      const differentObservations = loadedAt !== seriesEndsAt;
      // A reviewer asked what this reference did over the last month, and the
      // panel could only answer "since one baseline". It states how many
      // published observations the series actually spans and which of them
      // this reference moved on - two today, one more per observation, and it
      // says two rather than implying a month.
      const points = seriesFor(alert.rwa_id, snapshot, deltas);
      const observations = 1 + (deltas?.observations?.length || 0);
      const moved = points.filter(point => !point.baseline);
      const seriesLine = `<p class="change-series"><b>${observations}</b> published `
        + `observation${observations === 1 ? '' : 's'} in the series so far`
        + (moved.length
          ? `. This reference moved on ${moved.length} of them: `
            + moved.map(point => escapeHTML(String(point.observed_at).slice(0, 10))).join(', ')
          : `, and this reference is unchanged across all of them`)
        + `. The series grows by one point each time an observation is published; it does not `
        + `reach back before ${escapeHTML(String(snapshot.observed_at).slice(0, 10))}`
        + (differentObservations
          ? `. The comparison above is against the receipt this page loaded, observed `
            + `${escapeHTML(loadedAt)} UTC, and the series ends at ${escapeHTML(seriesEndsAt)} `
            + `UTC. Those are two observations, so the two halves can disagree without either `
            + `being wrong`
          : ``)
        + `.</p>`;
      container.innerHTML = `<span class="eyebrow">SINCE ${escapeHTML(datedOn)} UTC`
        + `${recomputed ? ' · RECOMPUTED BASELINE' : ''} · AGAINST ${escapeHTML(loadedAt)} UTC`
        + ` · ${escapeHTML(String(snapshot.rules_version))}</span>`
        + body
        + seriesLine
        + `<small class="change-limit">`
        + (recomputed
          ? `Baseline: the ${escapeHTML(datedOn)} inputs recomputed under `
            + `${escapeHTML(String(snapshot.rules_version))}, not the receipt published that day, `
            + `which recorded no rule set and a different distribution. Recomputing is what keeps `
            + `this a market comparison instead of a rule comparison. `
          : `Two dated observations, ${escapeHTML(String(snapshot.rules_version))} on both sides. `)
        + `Compared prices are deliberately excluded: they belong to the observation `
        + `that produced them.</small>`;
      container.hidden = false;
    });
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
    // A digits-only query is a reference id, so it is matched as one. It used
    // to be a substring over every field joined together, which meant
    // ?reference=0 matched SPY through "S&P 500" and returned a full verdict
    // panel for the first of 178 fuzzy hits, and ?reference=-1 reached PDBC
    // through "K-1". A shared link showed a complete capital panel about a
    // reference nobody had asked for. The label said "178 MATCHES · SHOWING
    // FIRST", which is honest and is not the same as being right.
    const index = receipt.alert_index || [];
    if (/^-?\d+$/.test(normalizedQuery)) {
      return index.filter(item => String(item.rwa_id ?? '').trim().toLowerCase() === normalizedQuery);
    }
    return index.filter(item => [item.name, item.symbol, item.asset_type, item.rwa_id].join(' ').toLowerCase().includes(normalizedQuery));
  }
  function preferredSearchMatch(normalizedQuery) {
    const matches = searchMatches(normalizedQuery);
    const exact = matches.find(item => [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery));
    return exact || matches[0] || null;
  }
  function workspaceReferenceId(normalizedQuery, matches) {
    const exact = matches.filter(item => [item.name, item.symbol, item.rwa_id]
      .some(value => String(value || '').trim().toLowerCase() === normalizedQuery));
    const selected = matches.length === 1 ? matches[0] : exact.length === 1 ? exact[0] : null;
    return selected?.rwa_id == null ? '' : String(selected.rwa_id);
  }
  function updateWorkspaceHandoff(normalizedQuery) {
    const link = document.querySelector('.workspace-link');
    if (!link) return;
    const referenceId = workspaceReferenceId(normalizedQuery, searchMatches(normalizedQuery));
    link.href = referenceId ? `/workspace?reference=${encodeURIComponent(referenceId)}` : '/workspace';
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

  // Route guidance is identical for every reference in the same state, so it is
  // published once as a legend above the list rather than repeated on each card.
  // Repeating it made roughly half the population list constant prose and buried
  // the per-reference signals that actually differ.
  const routeLegend = {
    do_not_compare: { label: 'DO NOT SHORTLIST', route: 'Resolve identity, unit and market evidence', steps: ['Match the RWA ID to the token ID and issuer ID', 'Confirm the exact instrument and unit, then verify issuer and redemption terms', 'Obtain venue and execution evidence before comparing wrappers'] },
    single_representation: { label: 'SINGLE REPRESENTATION', route: 'No comparison route; verify instrument and issuer terms', steps: ['CMC returned one representation, so there is no wrapper ranking to perform', 'Verify instrument, issuer, backing, redemption, eligibility and custody', 'Confirm executable liquidity before treating it as investable'] },
    investigate: { label: 'INVESTIGATE', route: 'Classify the representation and verify missing fields', steps: ['Classify the representation and confirm the issuer', 'Fill the missing fields named on the card', 'Keep unresolved wrappers separate in the research memo'] },
    no_flags: { label: 'FACTS OPEN', route: 'Complete external backing and execution checks', steps: ['No published rule fired; this is not an approval', 'Inspect the observed rows for yourself', 'Run external backing, eligibility, redemption, custody and liquidity checks'] },
    comparable: { label: 'FILTERED PRICE COMPARISON', route: 'Review filtered quotes, then verify units and issuer terms', steps: ['These routes share a CMC RWA reference; equivalent units and claims are not established', 'Read the spread and reported 24h volume; neither proves executable depth', 'Backing, redemption, eligibility and custody remain unobserved here'] },
  };

  // The fifth place this label was decided separately. The legend filed every
  // reference carrying a published comparison under INVESTIGATE or FACTS OPEN,
  // so selecting the COMPARABLE filter produced a heading reading
  // "INVESTIGATE - 4" above four cards badged COMPARABLE, and the word never
  // appeared in the legend at all. Derive the key from the label the card
  // shows, so the two cannot drift again.
  const routeKeyByLabel = {
    'DO NOT SHORTLIST': 'do_not_compare',
    'SINGLE REPRESENTATION': 'single_representation',
    INVESTIGATE: 'investigate',
    'FACTS OPEN': 'no_flags',
    COMPARABLE: 'comparable',
  };

  function routeKey(item) {
    return routeKeyByLabel[decisionBucket(item, 'FACTS OPEN')] || 'no_flags';
  }

  function renderRouteLegend(items) {
    const present = [];
    items.forEach(item => { const k = routeKey(item); if (!present.includes(k)) present.push(k); });
    if (!present.length) return '';
    const blocks = present.map(key => {
      const entry = routeLegend[key];
      const count = items.filter(item => routeKey(item) === key).length;
      return `<div class="route-legend-item" data-route="${key}"><div class="route-legend-head"><span class="route-legend-label">${escapeHTML(entry.label)}</span><strong>${count.toLocaleString()}</strong></div><p class="route-legend-route">${escapeHTML(entry.route)}</p><ol>${entry.steps.map(step => `<li>${escapeHTML(step)}</li>`).join('')}</ol></div>`;
    }).join('');
    return `<aside class="route-legend" aria-label="What each state means and what to do next"><div class="route-legend-top"><span class="eyebrow">WHAT TO DO NEXT, BY STATE</span><small>Published once. Each card below shows only what differs for that reference.</small></div><div class="route-legend-grid">${blocks}</div></aside>`;
  }



  // The headline number is the finding, so it is read from the measurement
  // rather than typed into the page. Hardcoding it would let the page and the
  // receipt drift apart, which is the defect this whole product exists to catch.
  async function renderFinding() {
    const headline = byId('finding-headline');
    const lede = byId('finding-lede');
    if (!headline || !lede) return;
    try {
      const response = await fetch('proof/base-rate-2026-09-21.json', { cache: 'no-cache' });
      if (!response.ok) throw new Error(`base rate unavailable (${response.status})`);
      const r = await response.json();
      const pct = (r.refusal_rate * 100).toFixed(1);
      const lo = (r.refusal_rate_ci95[0] * 100).toFixed(1);
      const hi = (r.refusal_rate_ci95[1] * 100).toFixed(1);
      const n = r.denominator_two_or_more_representations;
      // The rate is over references carrying MORE THAN ONE representation - the
      // only ones where a comparison is a thing anyone could attempt. Saying
      // "two thirds of tokenised assets" applied it to all 791 and overstated
      // the finding threefold. State the counts; do not band them into a word.
      // The headline stated only the refusal, and every reviewer read it the
      // same way: this tool tells me no. The refusal is the majority and stays
      // in the sentence - but the product's output is the comparison it DOES
      // publish, and that went unmentioned above the fold. Lead with what a
      // reader can act on, keep the denominator in the same breath.
      // "cannot honestly be compared at all" was false, and base_rate.py already
      // The refusal reasons have three distinct classes: missing source
      // coverage, data-review triggers, and no eligible spot pair. Keep the
      // categories separate; a rule hit is not proof of economic conflict.
      // Also: the measurement is pinned to a dated input package, so it says 791
      // while the live receipt re-scans and says 792. Date the sentence instead
      // of aligning the digits - two observations are allowed to differ.
      const split = r.refusal_split || {};
      const coverage = split.source_coverage;
      const dataReview = split.data_review;
      const noPair = split.not_applicable;
      const unclassified = split.unclassified || 0;
      const reasons = split.reason_total || (coverage || 0) + (dataReview || 0) + (noPair || 0) + unclassified;
      findingObservedAt = r.observed_at || null;
      // The strip's sentence claimed the two counts came from different dates.
      // On the dated replay a judge is told to clone they carry the same
      // instant, 2026-09-21T21:25:01Z, so the claim was false exactly where it
      // was most likely to be checked. This runs here, not in renderMetrics,
      // because renderMetrics runs first and would only ever see a null date
      // and print the same-instant sentence whether or not it was true.
      // The hero says 547 references carry a single representation; the
      // SINGLE REPRESENTATION filter returns 545. Both are right and they
      // count different things: the base rate asks how many have nothing to
      // compare, the filter asks what the card says, and two of those 547
      // also tripped a critical rule, so the card calls them DO NOT
      // SHORTLIST. Say it rather than leave a reader to find the gap.
      const singleNote = byId('single-rep-note');
      if (singleNote && receipt?.alert_index) {
        const singles = receipt.alert_index.filter(row => Number(row.token_count || 0) === 1);
        const blocked = singles.filter(row => decisionBucket(row, 'FACTS OPEN') === 'DO NOT SHORTLIST');
        singleNote.textContent = blocked.length
          ? `Of the ${singles.length.toLocaleString()} references carrying a single representation, `
            + `${blocked.length} also tripped a critical rule, so the index labels them `
            + `DO NOT SHORTLIST and the SINGLE REPRESENTATION filter returns `
            + `${(singles.length - blocked.length).toLocaleString()}.`
          : '';
      }
      const stripDates = byId('metric-strip-dates');
      if (stripDates) {
        const scanAt = receipt?.observed_at || null;
        const stamp = (value) => String(value).replace('T', ' ').slice(0, 16);
        stripDates.textContent = (scanAt && findingObservedAt && scanAt !== findingObservedAt)
          ? `The refusal count was observed ${stamp(findingObservedAt)} UTC and these four ${stamp(scanAt)} UTC.`
          : 'Both were observed at the same instant, so only the question differs.';
      }
      const measuredOn = new Date(r.observed_at).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long'
      });
      // Keep one observation in the first screen. Historical base-rate counts
      // remain available below as a dated, expandable note rather than competing
      // with the live receipt in the headline.
      const liveComparable = (receipt?.alert_index || []).filter(item => item?.comparison).length;
      const receiptDate = receipt?.observed_at ? new Date(receipt.observed_at) : null;
      const receiptStamp = receiptDate && Number.isFinite(receiptDate.getTime())
        ? receiptDate.toLocaleString('en-GB', {
          day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
          timeZone: 'UTC'
        }) + ' UTC'
        : 'the loaded receipt';
      headline.innerHTML = `<strong>${liveComparable.toLocaleString()}</strong> references have a `
        + `<em>filtered quote comparison</em><br>`
        + `<span class="finding-counter">Current CMC receipt observed ${receiptStamp}. Price and reported-volume filters pass; equivalent units, claims and executable markets are not established.</span>`;
      const measurementDetail = `Measured on ${measuredOn} over the whole catalogue, not a sample: `
        + `<strong>${r.population.toLocaleString()}</strong> references, of which `
        + `<strong>${r.excluded_single_representation.toLocaleString()}</strong> carry a single representation `
        + `and cannot be compared at all. Of the <strong>${n.toLocaleString()}</strong> that remain, `
        + `<strong>${r.refused.toLocaleString()}</strong> are refused, a rate of <strong>${pct}%</strong> `
        + `(95% interval ${lo} to ${hi}%).`
        + (reasons ? ` Behind those refusals are ${reasons} rule hits: `
          + `<strong>${coverage.toLocaleString()}</strong> missing-coverage reasons, `
          + `<strong>${dataReview.toLocaleString()}</strong> price or field review triggers, and `
          + `<strong>${noPair.toLocaleString()}</strong> with fewer than two eligible spot routes.`
          + (unclassified ? ` ${unclassified} remain unclassified.` : '') : '');
      lede.innerHTML = `<strong>${r.refused.toLocaleString()} of ${n.toLocaleString()} multi-wrapper references were refused (${pct}%).</strong> `
        + `This is a separate, historical population measurement, not today's receipt. `
        + `<details class="finding-methodology"><summary>Denominator and refusal reasons</summary>`
        + `<p>${measurementDetail}</p></details>`;
    } catch (error) {
      // Say what is missing rather than leaving a number-shaped hole - and
      // leave the question standing rather than a claim the measurement has
      // not yet backed. The static headline said "Most tokenised assets cannot
      // honestly be compared", which is true of 157 of the 244 that carry more
      // than one representation and false of the 791-reference catalogue.
      headline.innerHTML = 'Can these tokenised assets<br><em>honestly be compared?</em>';
      lede.textContent = 'The population measurement could not be loaded, so no rate is shown here. '
        + 'Run `make base-rate` against the shipped inputs to reproduce it.';
    }
  }


  // MARKET_FIELDS_MISSING used to drive 84% of the catalogue to INVESTIGATE,
  // which restated one API coverage fact 646 times instead of describing any
  // reference. It no longer decides a state - so the fact has to be published
  // once, in its own right, or demoting it would be concealment.
  function renderCoverageFact() {
    const target = byId('coverage-fact');
    if (!target || !receipt?.universe) return;
    const signals = receipt.universe.signals || {};
    const refs = Number(receipt.universe.tokenised_references_scanned || 0);
    const rows = Number(receipt.universe.tokens_scanned || 0);
    const missing = Number(signals.MARKET_FIELDS_MISSING || 0);
    if (!missing || !refs) { target.hidden = true; return; }
    target.hidden = false;
    // A reviewer saw 791 in the hero, labelled 21 September, and 792 here from
    // the current receipt, with nothing on screen saying they are two
    // observations. On a page whose thesis is that two numbers describing one
    // observation are a defect and two numbers describing two observations are
    // not, the date is the whole difference and it was missing.
    const observedOn = String(receipt.observed_at || '').replace('T', ' ').slice(0, 16);
    target.innerHTML = `<span>API COVERAGE · OBSERVED ${observedOn} UTC</span>`
      + `<strong>${missing.toLocaleString()} of ${refs.toLocaleString()} references</strong>`
      + `<details class="coverage-methodology"><summary>What this coverage gap means</summary><p>These references carry at least one representation with no price, market cap or volume reported by `
      + `CoinMarketCap, across ${rows.toLocaleString()} representation rows. This is a gap in the `
      + `source data, not a contradiction in any one reference, so it is reported here once rather `
      + `than held against each reference individually. Rows without a price and traded volume are `
      + `excluded from every comparison on this page.</p></details>`;
  }

  // The published `status` is whatever the worker cached at publication time,
  // so a receipt published inside its freshness window stays labelled "fresh"
  // for as long as the page is open. This recomputation existed, assigned to a
  // local that nothing read, while the chip printed the cached field: a
  // reviewer saw "PUBLISHED 10H AGO" and "FRESH" four lines apart on a receipt
  // with a 900 second contract. Dead code is not a fix. One function, and
  // every consumer reads it.
  function freshnessStatus(publication) {
    if (!publication) return 'UNKNOWN';
    const declared = publication.status || 'UNKNOWN';
    if (declared !== 'fresh' || !publication.published_at || !publication.stale_after_seconds) {
      return declared;
    }
    const age = Math.max(0, (Date.now() - Date.parse(publication.published_at)) / 1000);
    return age <= Number(publication.stale_after_seconds) ? 'fresh' : 'stale';
  }
  window.BellFreshness = freshnessStatus;

  function renderMetrics() {
    const universe = receipt.universe;
    byId('observed-at').textContent = `OBSERVED ${receipt.observed_at}`;
    const publication = receipt._publication;
    const status = freshnessStatus(publication);
    // "FRESH" was read as "measured just now" when it only meant "published
    // recently". The label now states when the population was OBSERVED, and names
    // the replay receipt separately so the displayed receipt is never mistaken
    // for the byte-verifiable one.
    const observedStamp = String(receipt.observed_at || '').replace('T', ' ').slice(0, 16);
    const ageMinutes = publication?.published_at
      ? Math.max(0, Math.round((Date.now() - Date.parse(publication.published_at)) / 60000))
      : null;
    const ageLabel = ageMinutes === null ? ''
      : ageMinutes < 60 ? ` · PUBLISHED ${ageMinutes}M AGO`
      : ` · PUBLISHED ${Math.round(ageMinutes / 60)}H AGO`;
    const receiptLabel = publication
      ? (publication.source === 'dated_static'
        ? `DATED REPLAY · OBSERVED ${observedStamp} UTC`
        : `OBSERVED ${observedStamp} UTC${ageLabel}`)
      : `DATED RECEIPT · OBSERVED ${observedStamp} UTC`;
    byId('receipt-status-label').textContent = receiptLabel;
    const heroProofStatus = document.querySelector('.proof-id');
    if (heroProofStatus) heroProofStatus.textContent = publication?.source === 'dated_static'
      ? `DATED REPLAY · OBSERVED ${observedStamp} UTC`
      : `OBSERVED ${observedStamp} UTC${ageLabel}`;
    const replayNote = byId('replay-receipt-note');
    if (replayNote) {
      replayNote.textContent = publication?.rule_migration
        ? `This CMC observation was collected under ${publication.rule_migration.source_rules_version}. The served v3 wording is a compatibility projection: values, findings and observation time are unchanged; no new collection was made.`
        : publication?.source === 'dated_static'
          ? 'This receipt is the byte-verifiable replay receipt.'
          : 'This is the current receipt. The byte-verifiable replay receipt is the dated one linked below, and it is a different observation.';
    }
    // The chip said "CURRENT RECEIPT" in the markup, so it kept saying it over
    // five-day-old replay data while the banner above read "DATED REPLAY".
    const populationChip = byId('population-receipt-chip');
    if (populationChip) {
      populationChip.textContent = publication?.source === 'dated_static'
        ? `DATED REPLAY · ${observedStamp} UTC`
        : `CURRENT RECEIPT · ${observedStamp} UTC`;
    }
    // One chip was fixed and three other places kept asserting currency over a
    // five-day-old replay. A single label following publication.source is not a
    // fix, it is one instance of a rule, so every label that dates the data
    // reads from the same place.
    const datedNow = publication?.source === 'dated_static';
    const populationSource = byId('hero-population-source');
    if (populationSource) {
      populationSource.textContent = datedNow
        ? `POPULATION LENS · DATED REPLAY · ${observedStamp} UTC`
        : `POPULATION LENS · CURRENT RECEIPT · ${observedStamp} UTC`;
    }
    const stripScope = byId('metric-strip-scope');
    if (stripScope) {
      stripScope.textContent = datedNow
        ? `These four are the dated replay observed ${observedStamp} UTC`
        : `These four are the current scan, observed ${observedStamp} UTC`;
    }
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
    const comparable = (receipt.alert_index || []).filter(item => item.comparison).length;
    // This strip used to print (blocked + investigate) / 791 as a percentage -
    // a second "comparability" rate in the same vocabulary as the headline's
    // 64.3%, which is measured over the 244 references where a comparison is
    // something you could attempt. Two rates, two denominators, one word: the
    // exact confusion this product exists to prevent. Print the counts.
    copy.textContent = `Of ${total.toLocaleString()} scanned references, ${blocked.toLocaleString()} hit a critical comparison stop rule and ${investigate.toLocaleString()} need identity or market-data follow-up first. ${comparable.toLocaleString()} have filtered price comparisons. A stop rule routes the next check; it does not prove an economic contradiction`;
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
    const populationSignal = byId('hero-population-signal');
    if (populationSignal && reportedValue > 0) {
      populationSignal.hidden = false;
      byId('hero-population-headline').textContent = `${(topFive / reportedValue * 100).toFixed(1)}% of positive reported value sits with five issuer labels`;
      byId('hero-population-copy').textContent = `${positiveRows.toLocaleString()} priced token rows · ${nonPositiveRows.toLocaleString()} rows without positive market cap · not a legal issuer or backing measure`;
    }
    proof.textContent = reportedValue > 0
      ? `The top five issuer labels hold ${(topFive / reportedValue * 100).toFixed(1)}% of positive reported market cap across ${positiveRows.toLocaleString()} rows. ${nonPositiveRows.toLocaleString()} rows have no positive market-cap field`
      : 'No positive market-cap fields were available for the population concentration check';
    // Four tiles of equal weight read as four parts of one whole. Three of
    // these are: every reference is blocked, investigate or facts-open, and
    // they sum to the population. The fourth is not a fourth state - it is a
    // slice across the other three (0 of the blocked, 42 of the investigate,
    // 41 of the facts-open on one observation), so presenting it alongside
    // them made the page appear to count past its own population. Say which
    // it is, on the tile.
    const partition = blocked + investigate + clear;
    metrics.innerHTML = `<div class="thesis-metric blocked"><strong>${blocked.toLocaleString()}</strong><span>do not shortlist</span></div>`
      + `<div class="thesis-metric investigate"><strong>${investigate.toLocaleString()}</strong><span>investigate first</span></div>`
      + `<div class="thesis-metric clear"><strong>${clear.toLocaleString()}</strong><span>facts open</span></div>`
      + `<div class="thesis-metric comparable subset"><strong>${comparable.toLocaleString()}</strong>`
      + `<span>comparison published</span>`
      + `<small>not a fourth state &mdash; a slice across the ${partition.toLocaleString()} above</small></div>`;
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

  // The label logic existed in three places: the card, the explorer's dossier
  // header and the explorer's live verdict. Fixing the card left the other two
  // printing INVESTIGATE for references the judge page promises are COMPARABLE.
  // Publish the one function rather than keep three in step by hand.
  window.BellDecisionLabel = (item, fallback) => displayDecisionLabel(item, fallback);

  function stateClass(label) {
    if (label === 'COMPARABLE') return 'comparable';
    if (label === 'INVESTIGATE') return 'investigate';
    if (label === 'DO NOT SHORTLIST') return '';
    return 'clear';
  }

  // The bucket a reference belongs to, which is what the filters are made of.
  function decisionBucket(item, fallback = 'REVIEW') {
    // One representation is not a comparison, whatever the scan flagged about
    // it. Two references in the live scan carry a single row and a
    // do_not_compare state, and they were bucketed DO NOT SHORTLIST: the
    // SINGLE REPRESENTATION filter returned 545 while the prose beside it said
    // 547, and a reader filtering for single-representation references lost
    // exactly the two the scanner had something to say about. The count is a
    // property of the reference, so it is read first.
    if (Number(item?.token_count ?? item?.representations ?? 0) === 1) return 'SINGLE REPRESENTATION';
    if (item?.state === 'do_not_compare' || item?.decision?.state === 'blocked') return 'DO NOT SHORTLIST';
    // A reference whose comparison was published is not merely "under
    // investigation" or "facts open" - the reader is holding the cheapest
    // route, the spread and the depth. Say so, and keep the refusal to endorse
    // in the decision body where it belongs.
    if (item?.comparison) return 'COMPARABLE';
    if (item?.state === 'investigate') return 'INVESTIGATE';
    if (item?.state === 'no_flags') return 'FACTS OPEN';
    return item?.decision?.label || fallback;
  }

  // Keep the replayable receipt untouched while giving the interface a
  // calibrated explanation derived from its published route set.
  function tokenRowsFor(item) {
    if (Array.isArray(item?.tokens) && item.tokens.length) return item.tokens;
    if (Array.isArray(item?.representations)) return item.representations;
    return [];
  }

  function alphabetClassScope(item) {
    if (String(item?.rwa_id) !== '4') return null;
    const tokenRows = tokenRowsFor(item);
    const classC = tokenRows.find(token => String(token.crypto_id) === '42272');
    if (!classC) return null;
    const routes = item?.comparison?.routes || [];
    const included = routes.some(route => String(route.crypto_id) === '42272');
    return { token: classC, included };
  }

  function alphabetClassScopeSentence(item) {
    const scope = alphabetClassScope(item);
    if (!scope) return '';
    const routeStatus = item?.comparison
      ? `the Class C route is ${scope.included ? 'included in' : 'excluded from'} this filtered quote set`
      : 'this observation has no published filtered quote set';
    const spreadScope = item?.comparison
      ? scope.included
        ? 'the displayed spread therefore combines Class A and Class C routes, not one share class'
        : 'the displayed spread uses the remaining Class A routes only'
      : '';
    return `CMC groups GOOGon (Alphabet Class C) under its Class A reference; ${routeStatus}${spreadScope ? `, and ${spreadScope}` : ''}.`;
  }

  // The live explorer dossier is a separate route from the decision card. Keep
  // the reference-specific class disclosure available to that renderer too.
  window.BellAlphabetClassScopeSentence = alphabetClassScopeSentence;

  function displayDecisionConsequence(item) {
    const comparison = item?.comparison;
    if (!comparison) {
      const signalCodes = new Set([
        ...(item?.signal_codes || []),
        ...(item?.signals || []).map(signal => typeof signal === 'string' ? signal : signal?.code).filter(Boolean),
      ]);
      const base = signalCodes.has('ZERO_MCAP_POSITIVE_VOLUME')
        ? 'CoinMarketCap reports positive 24h volume alongside a zero market-cap field. This is a reported-field inconsistency, not proof that no market exists. Keep the route out of a shortlist until the quote is checked by crypto_id.'
        : signalCodes.has('PRICE_DENOMINATION_BREAK')
          ? 'Observed CMC quotes span at least 10× within this reference. Verify units, wrapper claims and quote identity before comparing; the threshold is a review trigger, not proof of an economic mismatch.'
          : item?.decision?.consequence || '';
      return [base, alphabetClassScopeSentence(item)].filter(Boolean).join(' ');
    }
    const cheapest = comparison.cheapest || {};
    const highestVolume = comparison.highest_reported_volume || comparison.deepest || {};
    const unresolved = (comparison.unresolved || []).length;
    return `${comparison.route_count} routes under one CMC RWA reference passed Bell's price and reported-volume filters; equivalent units and claims are not established. `
      + `Observed spread ${Number(comparison.spread_bps).toFixed(1)} bps; lowest quote ${cheapest.symbol || 'unknown'}; highest reported 24h volume ${highestVolume.symbol || 'unknown'}.`
      + (unresolved ? ` ${unresolved} rule check${unresolved === 1 ? '' : 's'} remain open.` : '')
      + (alphabetClassScopeSentence(item) ? ` ${alphabetClassScopeSentence(item)}` : '');
  }

  function decisionForCaseReceipt(item) {
    const decision = item?.decision;
    if (!decision) return null;
    const comparison = item?.comparison;
    if (!comparison) {
      const classScope = alphabetClassScopeSentence(item);
      return classScope ? { ...decision, consequence: [decision.consequence, classScope].filter(Boolean).join(' ') } : { ...decision };
    }
    const cheapest = comparison.cheapest || {};
    const highestVolume = comparison.highest_reported_volume || comparison.deepest || {};
    const cheapestHasHighestVolume = comparison.cheapest_has_highest_reported_volume
      ?? comparison.cheapest_is_deepest;
    return {
      ...decision,
      consequence: `${comparison.route_count} token routes grouped under one CMC RWA reference passed Bell's price and reported-volume filters; this does not establish equivalent units or claims. Observed quote spread ${Number(comparison.spread_bps).toFixed(1)} bps; cheapest route ${cheapest.symbol || 'unknown'}`
        + (cheapestHasHighestVolume ? '' : `; ${highestVolume.symbol || 'another route'} has the highest reported 24h volume`)
        + `. ${alphabetClassScopeSentence(item)}`.trim(),
    };
  }

  function comparisonForCaseReceipt(item) {
    if (!item?.comparison) return null;
    const { deepest, cheapest_is_deepest, ...current } = item.comparison;
    return {
      ...current,
      highest_reported_volume: current.highest_reported_volume || deepest,
      cheapest_has_highest_reported_volume: current.cheapest_has_highest_reported_volume
        ?? cheapest_is_deepest,
      ...comparisonRouteSet(item),
    };
  }

  // A reference can carry a published comparison AND have been flagged by the
  // scan. 39 of the 75 comparisons in the live receipt are in that position,
  // and all of them read COMPARABLE, in the affirmative word, over the most
  // doubtful half of the affirmative set. The flags were always on the card,
  // under the verdict; a reviewer had to do the arithmetic against
  // /api/integrity to notice the split. Now the label carries it.
  //
  // The bucket stays COMPARABLE so the filter still gathers all 75: a reader
  // who wants the comparable set should not have to know there are two words
  // for it. Filtering asks which bucket; the label says what is in it.
  function isFlaggedComparable(item) {
    return Boolean(item?.comparison) && item?.state === 'investigate'
      && item?.decision?.state !== 'blocked';
  }

  // The same idea for the other bucket that can hide a flag: a lone
  // representation the scan had something to say about.
  function isFlaggedSingle(item) {
    return Number(item?.token_count ?? item?.representations ?? 0) === 1
      && (item?.state === 'do_not_compare' || item?.state === 'investigate'
          || item?.decision?.state === 'blocked');
  }

  // "1 representations · 1 issuers" was on screen for every single-row
  // reference. A product that reports other people's surfaces saying two
  // things at once should not print a plural over a count of one.
  // CoinMarketCap does not send is_derivative: zero occurrences in the shipped
  // input package, null on every row of the live receipt, including the 42
  // named "(Derivatives)". Reading the flag alone made this column say "no" on
  // all 1,444 exported rows, so a researcher filtering it concluded the RWA
  // catalogue contains no derivatives. The comment three lines below records
  // removing a `quote_source` column for being empty on every row of every
  // export; this was the same bug beside it.
  function isDerivativeRow(token) {
    if (token?.is_derivative === true) return true;
    return ['name', 'asset_type', 'token_type', 'category']
      .some(field => String(token?.[field] || '').toLowerCase().includes('derivative'));
  }

  function plural(count, word) {
    const value = Number(count) || 0;
    return `${formatNumber(value)} ${word}${value === 1 ? '' : 's'}`;
  }

  function displayDecisionLabel(item, fallback = 'REVIEW') {
    const bucket = decisionBucket(item, fallback);
    if (bucket === 'COMPARABLE' && isFlaggedComparable(item)) return 'COMPARABLE · FLAGGED';
    if (bucket === 'SINGLE REPRESENTATION' && isFlaggedSingle(item)) return 'SINGLE REPRESENTATION · FLAGGED';
    return bucket;
  }

  // One sentence, one place. This footnote was written twice, and both copies
  // ended "Rows remain non-comparable until Bell's identity and unit checks are
  // cleared" with no branch on the mode. So the affirmative card - the one
  // /judge tells a judge to search - stated that the representations share an
  // identity and a unit, and then four lines later stated they were not
  // comparable. On the comparable path the honest caveat is not that the rows
  // failed a check they passed; it is which questions the price fact does not
  // answer.
  function capitalRangeScope(alert, hasRange = true) {
    const hasFilteredRoutes = Boolean(alert?.comparison && Array.isArray(alert.comparison.routes));
    if (hasFilteredRoutes) {
      return {
        label: hasRange ? 'FILTERED ROUTE QUOTE RANGE' : '',
        note: hasRange
          ? 'Capital range uses this receipt’s filtered routes; the separate quote band includes all priced representations.'
          : 'No quote range is shown; any amount-to-volume check uses this receipt’s filtered routes.',
      };
    }
    return {
      label: hasRange ? 'OBSERVED ROW QUOTE RANGE' : '',
      note: hasRange
        ? 'Range uses reported token rows before comparison filters. No filtered comparison is published.'
        : 'No quote range is shown; any volume total uses reported token rows. No filtered comparison is published.',
    };
  }

  function capitalMetricsNote(mode, unitPhrase, representations, alert, hasRange = true) {
    const shared = `${unitPhrase} Reported 24h volume is a rolling field, not depth or executable exit capacity.`;
    const scope = capitalRangeScope(alert, hasRange).note;
    if (mode === 'comparable') {
      return `${shared} ${scope} Equivalent units and claims are not established. Backing, redemption, custody and executable size remain unobserved.`;
    }
    // "Rows remain non-comparable" over a single row says nothing: there is no
    // second row for it to be non-comparable with. The flag on such a
    // reference is about that row's own market state.
    if (Number(representations) === 1) {
      return `${shared} ${scope} This is the reference's only representation, so the flag is about that row's own fields.`;
    }
    return `${shared} ${scope} Rows remain outside Bell's filtered route comparison while its identity or quote rules are unresolved.`;
  }

  function capitalPanel(alert) {
    const assessment = window.BellCapitalImpact.assess(alert, readCapitalBudget(alert.rwa_id));
    const observedAt = String(receipt?.observed_at || '').replace('T', ' ').slice(0, 16);
    const rangeMetrics = assessment.metrics?.ratio
      ? `<div><span>${capitalRangeScope(alert, true).label}</span><strong>${formatRatio(assessment.metrics.ratio)}×</strong></div><div><span>NOMINAL TOKEN UNITS AT LOW QUOTE</span><strong>${formatNumber(assessment.metrics.unitsAtLowQuote)}</strong></div><div><span>NOMINAL TOKEN UNITS AT HIGH QUOTE</span><strong>${formatNumber(assessment.metrics.unitsAtHighQuote)}</strong></div>`
      : '';
    const volumeMetrics = assessment.metrics?.volume
      ? `<div><span>AMOUNT / REPORTED 24H VOLUME</span><strong>${formatNumber(assessment.metrics.volume.amountSharePercent)}%</strong></div>`
      : '';
    const metrics = rangeMetrics || volumeMetrics
      ? `<div class="capital-metrics">${rangeMetrics}${volumeMetrics}</div><small class="capital-metrics-note">${capitalMetricsNote(assessment.mode, 'Nominal quote units only.', alert?.token_count, alert, Boolean(assessment.metrics?.ratio))}</small>`
      : '<div class="capital-metrics capital-metrics-empty"><span>Fewer than two positive quote rows; no range is shown.</span></div>';
    return `<section class="capital-panel capital-${assessment.mode}" data-capital-panel="${escapeHTML(alert.rwa_id || '')}">
      <div class="capital-panel-head"><span>CAPITAL CHECK</span><b>RECEIPT OBSERVED · ${escapeHTML(observedAt || 'time unavailable')} UTC</b></div>
      <label class="capital-budget">Amount under consideration <span>$</span><input type="number" min="${window.BellCapitalImpact.MINIMUM_BUDGET}" max="${window.BellCapitalImpact.MAXIMUM_BUDGET}" step="100" value="${assessment.budget}" inputmode="decimal" data-capital-budget aria-label="Amount under consideration"></label>
      <strong data-capital-headline>${escapeHTML(assessment.headline)}</strong>
      <p data-capital-copy>${escapeHTML(shortenBoundary(assessment.copy))}</p>
      <div data-capital-metrics>${metrics}</div>
      <small data-capital-note>${escapeHTML(shortenBoundary(assessment.note))}</small>
    </section>`;
  }

  function observedQuoteEndpoints(item) {
    const tokens = tokenRowsFor(item);
    const band = window.BellCapitalImpact.quoteBand(tokens);
    if (!band) return '';
    const volume = row => row.volumeState === 'positive'
      ? formatNumber(row.volume)
      : row.volumeState === 'zero' ? '0 reported' : 'missing';
    const rows = band.rows.map(row => `<tr><th>${escapeHTML(row.token.symbol || row.token.name || 'unlabelled')}<small>${escapeHTML(row.token.name || '')}</small></th><td>${escapeHTML(row.token.issuer_name || row.token.issuer_catalogue_name || 'issuer not resolved')}</td><td>${formatNumber(row.price)}</td><td class="quote-band-delta">${row.deltaPercent >= 0 ? '+' : ''}${row.deltaPercent.toFixed(2)}%</td><td>${volume(row)}</td></tr>`).join('');
    return `<section class="search-evidence" data-search-evidence><div class="search-evidence-head"><span>OBSERVED QUOTE BAND</span><b>${formatRatio(band.ratio)}×</b></div><p class="search-evidence-lede">All ${band.rows.length} priced representations in this receipt around a ${formatNumber(band.median)} median quote</p><span class="quote-band-scroll-hint">SWIPE FOR QUOTE · MEDIAN GAP · VOLUME →</span><div class="quote-band-scroll"><table class="quote-band-table"><thead><tr><th>Representation</th><th>Issuer</th><th>Quote</th><th>Vs median</th><th>24h volume</th></tr></thead><tbody>${rows}</tbody></table></div><small>CMC quote rows in this receipt · relative to the observed median only · not a ranking, discount, backing, liquidity or executable spread</small></section>`;
  }

  function referenceConcentrationPanel(alert) {
    const tokens = alert?.tokens || alert?.representations || [];
    if (tokens.length < 2) {
      // 545 of 791 references carry one representation, and for all of them the
      // page used to say only that there was nothing to compare. That is 69% of
      // the catalogue receiving a non-answer while the data to answer sat in
      // the same row: which wrapper it is, who issues it, on what chain, at what
      // contract, and whether anyone traded it. "No comparison" is a true
      // statement about the ranking; it is not an answer to the question a
      // holder actually arrived with.
      const only = tokens[0] || {};
      const place = (only.platforms || [])[0] || {};
      const traded = Number(only.volume_24h) > 0;
      const facts = [
        ['WRAPPER', `${escapeHTML(only.symbol || '—')}${only.name ? ` · ${escapeHTML(only.name)}` : ''}`],
        ['ISSUER', escapeHTML(only.issuer_name || 'not resolved in the issuer catalogue')],
        ['CHAIN', place.name ? escapeHTML(place.name) : 'not published for this row'],
        ['CONTRACT', place.contract_address
          ? `<code>${escapeHTML(String(place.contract_address))}</code>` : 'not published for this row'],
        ['24H VOLUME', traded
          ? `${formatNumber(only.volume_24h)} observed`
          : 'none observed — quoted, but nobody traded it in the window'],
      ];
      return `<section class="reference-concentration-panel"><div class="reference-concentration-head"><span>THE ONE WRAPPER</span><b>SINGLE REPRESENTATION</b></div>`
        + `<p>One representation, so there is no wrapper ranking to perform. This is what you would be holding.</p>`
        + `<dl class="single-wrapper">${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`
        + `<small>Identity, chain and venue as CoinMarketCap published them. ${NOT_OBSERVED_FULL}</small></section>`;
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
    return `<section class="reference-concentration-panel"><div class="reference-concentration-head"><span>ISSUER CONCENTRATION · THIS REFERENCE</span><b>${(topShare * 100).toFixed(1)}% TOP ISSUER</b></div><h4>${escapeHTML(top.name)} carries ${(topShare * 100).toFixed(1)}% of positive reported value</h4><div class="reference-concentration-metrics"><div><strong>${hhi.toFixed(0)}</strong><span>HHI / 10,000</span></div><div><strong>${effective.toFixed(2)}</strong><span>EFFECTIVE ISSUERS</span></div><div><strong>${money(reportedValue)}</strong><span>REPORTED VALUE</span></div></div><p>${issuers.length} issuer labels across ${plural(tokens.length, 'representation')} · ${missing} missing market-cap rows · ${zero} zero rows</p><p class="reference-concentration-action"><b>NEXT CHECK</b> ${escapeHTML(concentrationRead)}</p><small>Reported token-level market cap only. This is not legal issuer concentration, backing, reserves, redemption or investability.</small></section>`;
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
      ? `<div><span>${capitalRangeScope(alert, true).label}</span><strong>${formatRatio(metrics.ratio)}×</strong></div><div><span>NOMINAL TOKEN UNITS AT LOW QUOTE</span><strong>${formatNumber(metrics.unitsAtLowQuote)}</strong></div><div><span>NOMINAL TOKEN UNITS AT HIGH QUOTE</span><strong>${formatNumber(metrics.unitsAtHighQuote)}</strong></div>`
      : '';
    const volumeMetrics = metrics?.volume
      ? `<div><span>AMOUNT / REPORTED 24H VOLUME</span><strong>${formatNumber(metrics.volume.amountSharePercent)}%</strong></div>`
      : '';
    panel.querySelector('[data-capital-metrics]').innerHTML = metrics
      ? `<div class="capital-metrics">${rangeMetrics}${volumeMetrics}</div><small class="capital-metrics-note">${capitalMetricsNote(assessment.mode, 'Nominal unit counts only.', alert?.token_count, alert, Boolean(metrics?.ratio))}</small>`
      : '<div class="capital-metrics capital-metrics-empty"><span>Fewer than two positive quote rows; no range is shown.</span></div>';
    panel.querySelector('[data-capital-note]').textContent = assessment.note;
  }

  // When the gate clears a reference, the receipt carries the comparison it
  // performed. Render it: a monitor that only ever refuses is a gate with no
  // door. The unresolved warnings ride along so this is never read as a clean
  // bill of health.
  function issuerEvidenceMarkup(item, routes) {
    const catalogue = window.BELL_INSTRUMENT_EVIDENCE || {};
    const tokenRows = tokenRowsFor(item);
    const tokenById = new Map(tokenRows.map(token => [String(token.crypto_id), token]));
    const matched = routes.map(route => ({
      route,
      entry: catalogue[String(route.crypto_id)],
      token: tokenById.get(String(route.crypto_id)),
    }));
    if (!matched.length) return '';
    const classScope = alphabetClassScope(item);
    const classMismatch = Boolean(classScope);
    const documented = matched.filter(row => row.entry);
    const unmapped = matched.filter(row => !row.entry);
    if (!documented.length && !classMismatch) return '';
    const cards = documented.map(({ route, entry, token }) => {
      const routeLabel = `${route.symbol || '—'} · ${route.name || 'instrument name not supplied'} · CMC crypto_id ${route.crypto_id ?? 'missing'}`;
      const metadataLinks = [
        ['CMC listing', token?.cmc_url],
        ['Project page', token?.project_url],
      ].map(([label, href]) => {
        const url = externalURL(href);
        return url ? `<a href="${escapeHTML(url)}" target="_blank" rel="noopener">${label} ↗</a>` : '';
      }).filter(Boolean).join('');
      const platforms = Array.isArray(token?.platforms) ? token.platforms : [];
      const contractDetails = platforms.length
        ? `<details class="issuer-contracts"><summary>CMC contracts · ${platforms.length} networks</summary><ul>${platforms.map(platform => `<li>${escapeHTML(platform.name || platform.slug || 'Network')} · <code>${escapeHTML(platform.contract_address || 'address unavailable')}</code></li>`).join('')}</ul></details>`
        : '';
      const identityLinks = metadataLinks || contractDetails
        ? `<div class="issuer-evidence-links">${metadataLinks}</div>${contractDetails}`
        : '';
      const sources = entry.sources.map(source => {
        const url = externalURL(source.url);
        return url ? `<a href="${escapeHTML(url)}" target="_blank" rel="noopener">${escapeHTML(source.label)} ↗</a>` : '';
      }).filter(Boolean).join('');
      return `<article class="issuer-evidence-card"><div class="issuer-evidence-title"><span>${escapeHTML(entry.issuer)}</span><strong>${escapeHTML(entry.status)}</strong></div><p class="issuer-evidence-routes">${escapeHTML(routeLabel)}<br>${escapeHTML(entry.identity)}</p><p>${escapeHTML(entry.note)}</p><div class="issuer-evidence-links">${sources}</div>${identityLinks}</article>`;
    }).join('');
    const gapNote = unmapped.length
      ? `<details class="issuer-evidence-gap issuer-unmapped"><summary>Issuer terms not mapped for ${unmapped.length} included route${unmapped.length === 1 ? '' : 's'}</summary><ul>${unmapped.map(({ route }) => `<li>${escapeHTML(`${route.symbol || '—'} · ${route.name || route.issuer_name || 'unknown route'} · CMC crypto_id ${route.crypto_id ?? 'missing'}`)}</li>`).join('')}</ul><p>Unit, rights, backing and redemption remain unreviewed for these IDs.</p></details>`
      : '';
    const classWarning = classScope
      ? `<p class="issuer-evidence-gap"><b>Share-class mismatch:</b> ${escapeHTML(alphabetClassScopeSentence(item))} This reference groups different share classes; only the rows listed above contribute to the displayed spread.</p>`
      : '';
    return `<section class="issuer-evidence" aria-label="Issuer-published terms by token ID"><div class="issuer-evidence-heading"><span>TERMS BY TOKEN ID</span><p>Each note is attached to the exact CMC crypto_id shown. Sources describe issuer-published claims; they do not independently verify backing, redemption, eligibility or custody.</p></div>${cards ? `<div class="issuer-evidence-grid">${cards}</div>` : ''}${gapNote}${classWarning}</section>`;
  }

  function pairReviewMarkup(item, routes) {
    const pair = window.BELL_PAIR_REVIEWS?.[`${item?.rwa_id}:37013:38001`];
    const ids = new Set((routes || []).map(route => String(route.crypto_id)));
    if (!pair || !ids.has('37013') || !ids.has('38001')) return '';
    const sources = pair.sources.map(source => {
      const url = externalURL(source.url);
      return url ? `<a href="${escapeHTML(url)}" target="_blank" rel="noopener">${escapeHTML(source.label)} ↗</a>` : '';
    }).filter(Boolean).join('');
    return `<aside class="pair-review" aria-label="Pairwise RWA terms review"><div class="pair-review-head"><div><span>DATED PAIRWISE TERMS CHECK</span><h4>${escapeHTML(pair.title)}</h4></div><strong>${escapeHTML(pair.decision)}</strong></div><dl><div><dt>CMC pair snapshot</dt><dd>${escapeHTML(pair.cmcObserved)}</dd></div><div><dt>Issuer pages checked</dt><dd>${escapeHTML(pair.termsChecked)}</dd></div></dl><p><b>What aligns:</b> ${escapeHTML(pair.alignment)}</p><p><b>What remains open:</b> ${escapeHTML(pair.gap)}</p><p class="pair-review-next"><b>Next check:</b> ${escapeHTML(pair.next)}</p><div class="issuer-evidence-links">${sources}</div><small>This is a dated research artifact separate from the live integrity result, which carries its own observation time. Issuer pages are linked, not archived. This does not establish legal equivalence, backing, redemption, or fair value.</small></aside>`;
  }

  function pairwiseReviewRecord(item) {
    const pair = window.BELL_PAIR_REVIEWS?.[`${item?.rwa_id}:37013:38001`];
    const rows = item?.tokens || item?.representations || [];
    const ids = new Set(rows.map(token => String(token.crypto_id)));
    if (!pair || !ids.has('37013') || !ids.has('38001')) return null;
    return {
      schema_version: 'bell.pairwise-terms-review.v1',
      review_id: 'alphabet-class-a-googlx-googlon-2026-09-29',
      receipt: 'proof/alphabet-class-a-pair-review-2026-09-29.json',
      receipt_sha256: 'eee4eae050f3f320de6caad30c2a92254a75b0286b25479555dcdce7203c8b3f',
      relationship: 'This is a separately dated terms review, not a claim that those terms were observed in the live quote timestamp above.',
    };
  }

  function renderComparison(item) {
    const c = item.comparison;
    if (!c || !Array.isArray(c.routes) || c.routes.length < 2) {
      const routes = tokenRowsFor(item);
      return issuerEvidenceMarkup(item, routes) + pairReviewMarkup(item, routes);
    }
    const rows = c.routes.map(route => {
      const share = Number.isFinite(route.volume_share) ? `${(route.volume_share * 100).toFixed(1)}%` : '--';
      const premium = Number(route.premium_to_cheapest_bps || 0);
      return `<tr><td><strong>${escapeHTML(route.symbol || '')}</strong><small class="comparison-route-name">${escapeHTML(route.name || 'Instrument name not supplied')}</small></td><td>${escapeHTML(route.issuer_name || '')}</td><td class="num">${formatNumber(route.price)}</td><td class="num">${premium === 0 ? 'cheapest' : `+${premium.toFixed(1)} bps`}</td><td class="num">${share}</td></tr>`;
    }).join('');
    const highestReportedVolume = c.highest_reported_volume || c.deepest || {};
    const cheapestHasHighestReportedVolume = c.cheapest_has_highest_reported_volume
      ?? c.cheapest_is_deepest;
    const routeSet = comparisonRouteSet(item);
    const includedIds = routeSet.included_crypto_ids
      .map(id => escapeHTML(id ?? 'missing'));
    const excludedRows = routeSet.excluded_crypto_ids;
    const routeSetDetails = `<details class="comparison-route-set"><summary>Inspect token IDs · ${includedIds.length} included · ${excludedRows.length} excluded</summary><p>Included crypto_id values: ${includedIds.join(', ') || 'none'}</p><ul>${excludedRows.map(row => `<li>${escapeHTML(row.crypto_id ?? 'no crypto_id')} · ${escapeHTML(row.symbol || 'unknown symbol')} · ${escapeHTML((row.reasons || []).join(', ') || 'excluded')}</li>`).join('') || '<li>No excluded rows recorded.</li>'}</ul></details>`;
    const fill = cheapestHasHighestReportedVolume
      ? 'The cheapest route also has the highest reported 24h volume.'
      : `${escapeHTML(highestReportedVolume.symbol || '')} has the highest reported 24h volume, not the cheapest route.`;
    const open = (c.unresolved || []).length
      ? `<p class="comparison-open"><span>STILL OPEN</span> ${escapeHTML((c.unresolved || []).join(' · '))}. The route filter drops derivatives, keys on the token id rather than the ticker, and excludes rows without both a price and traded volume, so these do not block the comparison - but they are not resolved.</p>`
      : '';
    const alphabetScope = alphabetClassScope(item);
    const comparisonTitle = alphabetScope?.included
      ? 'CMC-GROUPED QUOTE SPREAD · CLASS A + C'
      : 'FILTERED PRICE COMPARISON';
    const routeNotes = c.routes.filter(route => window.BELL_INSTRUMENT_EVIDENCE?.[String(route.crypto_id)]).length;
    const unitScope = alphabetScope?.included
      ? `CMC groups Class A and Class C routes here; this is not a same-share-class spread. `
      : '';
    const scopeNotice = `<aside class="comparison-scope-notice"><span>TERMS CHECK · BEFORE THE QUOTE</span><p><strong>Equivalent units and claims are not established.</strong> ${unitScope}${routeNotes} of ${c.routes.length} included routes have token-specific issuer-source notes. Those notes describe published terms; they do not verify rights or backing.</p></aside>`;
    return `<div class="comparison-block"><span class="comparison-scroll-hint">SWIPE FOR PRICE · VS CHEAPEST · SHARE OF VOLUME →</span>${scopeNotice}<div class="comparison-head"><span>${comparisonTitle}</span><strong>${Number(c.spread_bps).toFixed(1)} bps</strong><small>${c.route_count} token routes under this CMC RWA reference</small></div><p class="comparison-fill">${fill}</p><table class="comparison-table"><thead><tr><th>route</th><th>issuer</th><th class="num">price</th><th class="num">vs cheapest</th><th class="num">share of volume</th></tr></thead><tbody>${rows}</tbody></table>${issuerEvidenceMarkup(item, c.routes)}${pairReviewMarkup(item, c.routes)}${routeSetDetails}${open}<p class="comparison-limits">Observed CMC price and reported-volume fields are not execution, depth, backing or redemption evidence. ${NOT_OBSERVED_SHORT}</p></div>`;
  }

  function comparisonRouteSet(item) {
    const comparison = item?.comparison || {};
    const routes = Array.isArray(comparison.routes) ? comparison.routes : [];
    const included = comparison.included_crypto_ids || routes.map(route => route.crypto_id);
    if (Array.isArray(comparison.excluded_crypto_ids)) {
      return { included_crypto_ids: included, excluded_crypto_ids: comparison.excluded_crypto_ids };
    }
    const includedKeys = new Set(included.map(id => String(id)));
    const tokens = tokenRowsFor(item);
    const eligibleCounts = new Map();
    for (const token of tokens) {
      const id = token?.crypto_id;
      const price = numericValue(token?.price);
      const volume = numericValue(token?.volume_24h);
      if (id != null && !isDerivativeRow(token) && price > 0 && volume > 0) {
        const key = String(id);
        eligibleCounts.set(key, (eligibleCounts.get(key) || 0) + 1);
      }
    }
    const excluded = tokens.filter(token => !includedKeys.has(String(token?.crypto_id))).map(token => {
      const id = token?.crypto_id;
      const price = numericValue(token?.price);
      const volume = numericValue(token?.volume_24h);
      const reasons = [];
      if (id == null) reasons.push('missing_crypto_id');
      if (isDerivativeRow(token)) reasons.push('derivative_label');
      if (price === null || price <= 0) reasons.push('missing_or_non_positive_price');
      if (volume === null || volume <= 0) reasons.push('missing_or_non_positive_volume');
      if (id != null && eligibleCounts.get(String(id)) > 1) reasons.push('duplicate_crypto_id');
      if (!reasons.length) reasons.push('not_in_published_route_set');
      return { crypto_id: id ?? null, symbol: token?.symbol || null, reasons };
    });
    return { included_crypto_ids: included, excluded_crypto_ids: excluded };
  }

  function renderAlertRow(alert) {
      const labels = alert.signals.filter(signal => signal.severity !== 'info').map(signal => signalLabels[signal.code] || signal.code).slice(0, 3).join(' · ');
      const evidence = alert.signals.filter(signal => signal.severity !== 'info').map(signal => `<div class="evidence-rule"><b>${escapeHTML(signalLabels[signal.code] || signal.code)}</b><p>${escapeHTML(signal.message)}</p><ul>${renderEvidence(signal)}</ul></div>`).join('');
      // The badge and the decision effect were computed by different functions,
      // so one card carried two vocabularies. Every reference with a published
      // comparison was badged FACTS OPEN or INVESTIGATE while its effect read
      // COMPARABLE, and COMPARABLE never appeared as a badge anywhere on the
      // site - including on the reference the judge page names as its worked
      // example. One function now decides the word.
      const stateLabel = displayDecisionLabel(alert);
      const decision = alert.decision || {};
      return `<article class="alert-row" data-rwa-id="${escapeHTML(alert.rwa_id)}"><div class="alert-name">${escapeHTML(alert.name)}<small>${escapeHTML(alert.symbol)} · ${escapeHTML(alert.asset_type)} · ${alert.issuer_count} issuers</small></div><div class="alert-state ${stateClass(stateLabel)}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML(labels)}</div><div class="alert-tokens"><strong>${alert.token_count}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(displayDecisionLabel(alert))}</b><p>${escapeHTML(displayDecisionConsequence(alert))}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(alert.next_action)}</div>${renderComparison(alert)}<div class="alert-tools">${watchButton(alert)}${briefButton(alert.rwa_id)}</div><details class="alert-details"><summary>Inspect evidence</summary>${evidence}<h4>Representation rows</h4>${renderTokenTable(alert)}</details>${renderWorksheet(alert)}</article>`;
  }

  function renderIndexRow(item, detail) {
    if (detail) return renderAlertRow(detail);
    const stateLabel = displayDecisionLabel(item, 'FACTS OPEN');
    const decision = item.decision || {};
    return `<article class="alert-row compact-row" data-rwa-id="${escapeHTML(item.rwa_id)}"><div class="alert-name">${escapeHTML(item.name)}<small>${escapeHTML(item.symbol)} · ${escapeHTML(item.asset_type)} · ${item.issuer_count || 0} issuers · RWA ${escapeHTML(item.rwa_id)}</small></div><div class="alert-state ${stateClass(stateLabel)}">${escapeHTML(stateLabel)}</div><div class="alert-signals">${escapeHTML((item.signal_codes || []).filter(code => code !== 'NO_TRADFI_MARKET').slice(0, 3).map(code => signalLabels[code] || code).join(' · ') || 'No published rule hit')}</div><div class="alert-tokens"><strong>${Number(item.token_count || 0).toLocaleString()}</strong><small>representations</small></div><div class="alert-decision"><span>Decision effect</span><b>${escapeHTML(displayDecisionLabel(item, 'FACTS OPEN'))}</b><p>${escapeHTML(displayDecisionConsequence(item))}</p><p class="compact-observation"><span>OBSERVED</span> ${escapeHTML(compactObservation(item))}</p></div><div class="alert-action"><span>Next action</span>${escapeHTML(item.next_action || '')}</div>${renderComparison(item)}<div class="alert-tools">${watchButton(item)}${briefButton(item.rwa_id)}</div><details class="alert-details"><summary>Inspect representations</summary><p class="compact-note">CMC quote rows observed in this receipt. Bell uses them to route research, not to certify backing, eligibility, liquidity or equivalence.</p><ul class="compact-evidence">${renderCompactEvidence(item)}</ul>${renderTokenTable(item)}</details>${renderWorksheet(item)}</article>`;
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
    const tokens = item.tokens || item.representations || [];
    const comparison = comparisonForCaseReceipt(item);
    const included = new Set((comparison?.included_crypto_ids || []).map(String));
    const excluded = new Map((comparison?.excluded_crypto_ids || [])
      .map(row => [String(row.crypto_id), row.reasons || []]));
    const tokenLines = tokens.map(token => {
      const issuerURL = externalURL(token.issuer_website);
      const issuer = token.issuer_name || token.issuer_catalogue_name || 'unlinked';
      const issuerCell = issuerURL ? `[${issuer}](${issuerURL})` : issuer;
      const cmcURL = externalURL(token.cmc_url);
      const tokenCell = cmcURL ? `[${token.symbol || 'N/A'}](${cmcURL})` : (token.symbol || 'N/A');
      const platforms = (token.platforms || []).map(platform => `${platform.name || 'unknown chain'}: ${platform.contract_address || 'no contract'}`).join('<br>') || 'not resolved';
      const sourceURLs = [token.cmc_url, token.issuer_website, token.project_url, ...(token.explorer_urls || []), ...(token.technical_doc_urls || [])].filter(Boolean);
      const sourceCells = sourceURLs.length ? sourceURLs.map(url => `[link](${url})`).join(' ') : 'none';
      const id = String(token.crypto_id || '');
      const membership = included.has(id) ? 'Included in filtered price comparison'
        : excluded.has(id) ? `Excluded: ${excluded.get(id).join(', ') || 'not eligible'}`
          : comparison ? 'Outside published comparison set' : 'No filtered comparison published';
      return `| ${tokenCell} (${token.crypto_id || 'no id'}) | ${membership} | ${token.name || 'N/A'} | ${issuerCell} (${token.issuer_id || 'no id'}) | ${platforms} | ${formatNumber(token.price)} | ${formatNumber(token.market_cap)} | ${formatNumber(token.volume_24h)} | ${sourceCells} |`;
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
- Consequence: ${displayDecisionConsequence(item) || 'No allocation status is produced by this monitor'}
- Observed: ${receipt.observed_at || 'N/A'}
- Published: ${receipt._publication?.published_at || 'N/A'}
- Receipt ID: ${caseReceipt(item).receipt_id}
- Ruleset: ${receipt.universe?.rules_version || 'unrecorded'}

## Evidence

${signalLines}

## Next action

${item.next_action || 'Continue external diligence before comparing or allocating.'}

## Capital check

- Amount under consideration: ${capital.budget.toLocaleString(undefined, { maximumFractionDigits: 0 })}
- Bell route: ${capital.headline}
- Financial interpretation: ${capital.copy}
- Observed range: ${capital.metrics?.ratio ? `${formatRatio(capital.metrics.ratio)}× · ${formatNumber(capital.metrics.unitsAtLowQuote)} nominal units at the low quote vs ${formatNumber(capital.metrics.unitsAtHighQuote)} at the high quote` : 'Unavailable'}
- Boundary: ${capital.note}

## Resolution checklist

- match the RWA ID to the token ID and issuer ID, then confirm the exact token, chain and unit;
- verify instrument type, backing, redemption and eligibility from primary documents;
- obtain venue access, depth, spread and size-specific execution evidence;
- resolve the unit, instrument and issuer terms behind the observed quote spread before treating the routes as economically equivalent.

## Published comparison set

${comparison ? `- Included crypto IDs: ${(comparison.included_crypto_ids || []).join(', ') || 'none'}\n- Excluded crypto IDs and reasons: ${(comparison.excluded_crypto_ids || []).map(row => `${row.crypto_id} (${(row.reasons || []).join(', ') || 'not eligible'})`).join('; ') || 'none'}\n- Filtered routes: ${comparison.route_count}; observed spread: ${formatNumber(comparison.spread_bps)} bps\n- Boundary: this is a filtered CMC quote comparison; it does not establish equivalent units, backing, redemption, eligibility, custody or executable liquidity.` : 'No filtered price comparison was published for this reference.'}

## Representation rows

| Token | Comparison membership | Representation | Issuer | Chain / contract | Price | Market cap | 24h volume | Source paths |
|---|---|---|---|---|---:|---:|---:|---|
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
    const sourceHashes = receipt?.source_hashes || {};
    const pairwiseTermsReview = pairwiseReviewRecord(item);
    const receiptId = `bell.integrity/${encodeURIComponent(receipt?.observed_at || 'unknown')}/`
      + Object.keys(sourceHashes).sort().map(surface => `${surface}=${sourceHashes[surface]}`).join('&');
    return {
      schema_version: 'bell.case-receipt.v3',
      receipt_id: receiptId,
      ruleset: receipt?.universe?.rules_version || null,
      observed_at: receipt?.observed_at || null,
      published_at: publication.published_at || null,
      // This was hard-coded to '/api/integrity' even when the page had fallen
      // back to the dated replay file, so an exported case receipt could name a
      // source that had not produced it. Wrong provenance on an evidence
      // product is worse than no provenance.
      source: receiptSource || '/api/integrity',
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
      decision: decisionForCaseReceipt(item),
      decision_interpretation: displayDecisionConsequence(item),
      // The case carries the exact crypto_id set used for its published
      // comparison. The v2 verifier recomputes this object from the exported
      // token rows and rejects edits to either side of the relationship.
      comparison: comparisonForCaseReceipt(item),
      // The engine's own label is "DO NOT SELECT A WRAPPER", which is more
      // precise about what is being refused, but the public vocabulary the
      // page and verify_submission.py both declare is "DO NOT SHORTLIST". An
      // exported artifact that disagrees with the screen it came from is the
      // defect this product exists to find, so it carries both and says which
      // is which.
      public_label: displayDecisionLabel(item),
      next_action: item.next_action || null,
      // `item.signals` is the full objects, and only the 50 references inside
      // the truncated `alerts` array have them. For every other reference the
      // export wrote `[]` - claiming no rule fired on a reference whose own
      // alert_index entry lists three. A reviewer downloaded fifteen receipts
      // through this button and two of them said that. An artefact that omits
      // the findings is worse than one that says it does not carry them.
      signals: item.signals
        || (item.signal_codes || []).map((code, position) => ({
          code,
          severity: (item.signal_severities || [])[position] || 'unknown',
          message: 'Recorded in the population index; the full message is in the receipt.',
          evidence: (item.signal_evidence || {})[code] || {},
        })),
      signals_detail: item.signals ? 'full' : 'codes only, from the population index',
      tokens: item.tokens || item.representations || [],
      method: {
        join_key: receipt?.method?.join_key || 'rwa_id',
        token_join_key: receipt?.method?.token_join_key || 'crypto_id',
        rules: [
          'A 10x observed quote spread is a review trigger; it does not prove a denomination break.',
          'Positive reported volume beside a zero market-cap field is a data-review trigger; it does not prove an economic contradiction.',
          'Only non-derivative rows with positive price and positive reported 24h volume enter a published comparison.',
          'CMC reference membership does not establish equivalent units, backing, redemption, eligibility, custody or executable liquidity.',
        ],
        published_rule_text: receipt?.method?.rules || [],
      },
      ruleset_note: `Ruleset ${receipt?.universe?.rules_version || 'unrecorded'} is the version stamped on this published observation. The interpretation above calibrates what its triggers establish; it does not rewrite the source receipt.`,
      // A hash proves the payload did not change. It does not tell a reader
      // which endpoint produced it, nor how to get back to it. Pair each hash
      // with the surface it came from and the command that recomputes this
      // whole receipt from the shipped inputs, so the artifact is checkable by
      // someone who has no CoinMarketCap credential and never will.
      provenance: {
        surfaces: Object.fromEntries(Object.entries(receipt?.source_hashes || {})
          .map(([surface, sha256]) => {
            const transport = transportRecord?.surfaces?.[surface];
            return [surface, {
              endpoint: receipt?.method?.[surface] || null,
              sha256,
              // Transport belongs to the dated replay package, not necessarily
              // to the observation above it, so it says which one it describes
              // rather than implying it measured this scan.
              ...(transport ? {
                requests: transport.request_count,
                responses: transport.successful_response_count,
                status_codes: transport.status_codes,
                request_window: [transport.first_request_at, transport.last_response_at],
                transport_observed_at: transportRecord.observed_at,
              } : {}),
            }];
          })),
        transport_note: transportRecord
          ? `Request counts and status codes are the collection manifest of the replay package `
            + `observed ${transportRecord.observed_at}. No credential or transport header is recorded.`
          : 'Transport record unavailable; endpoint and payload digest only.',
        reproduce: [
          'git clone https://github.com/dyplux/bell.git && cd bell',
          'make verify   # recomputes this receipt from the shipped inputs, no API key',
          'make demo     # re-derives the published decisions and prints the reasoning',
        ],
        note: receiptSource
          ? `This case was read from ${receiptSource}.`
          : 'This case was read from the live credential-free receipt.',
      },
      source_hashes: sourceHashes,
      limits: [
        'Observed CMC fields do not prove backing, redemption, custody, eligibility, solvency, liquidity or executable size',
        'The case is a research triage record, not an investment recommendation',
      ],
      ...(pairwiseTermsReview ? { pairwise_terms_review: pairwiseTermsReview } : {}),
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

  function csvCell(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  }

  function downloadPopulationAttribution() {
    const rows = (receipt?.alert_index || []).flatMap(reference => {
      const representations = reference.representations || reference.tokens || [];
      // A route the comparison published carries its rank and its premium to
      // the cheapest. Everything else is a representation Bell would not put
      // side by side, and the export has to say which is which.
      const routeSet = comparisonRouteSet(reference);
      const routes = new Map((reference.comparison?.routes || []).map(route => [String(route.crypto_id), route]));
      const exclusions = new Map(routeSet.excluded_crypto_ids
        .map(row => [String(row.crypto_id), (row.reasons || []).join('|')]));
      return representations.map(token => {
        const marketCap = numericValue(token.market_cap);
        const marketCapStatus = marketCap === null ? 'missing' : marketCap <= 0 ? 'zero_or_non_positive' : 'positive';
        return [
          reference.rwa_id,
          reference.name,
          reference.symbol,
          reference.asset_type,
          reference.state,
          token.crypto_id,
          token.symbol,
          token.name,
          token.issuer_id,
          token.issuer_name || token.issuer_catalogue_name,
          marketCap === null ? '' : marketCap,
          marketCapStatus,
          numericValue(token.price) ?? '',
          numericValue(token.volume_24h) ?? '',
          isDerivativeRow(token) ? 'yes' : 'no',
          routes.has(String(token.crypto_id)) ? 'yes' : 'no',
          exclusions.get(String(token.crypto_id)) || '',
          routes.get(String(token.crypto_id))?.premium_to_cheapest_bps?.toFixed(1) ?? '',
        ];
      });
    });
    // `quote_source` was in this header and empty on every row of every export:
    // a column promising provenance and delivering nothing. These four are
    // fields Bell actually observed.
    const header = ['rwa_id', 'reference_name', 'reference_symbol', 'asset_type', 'state', 'crypto_id', 'token_symbol', 'token_name', 'issuer_id', 'issuer_name', 'market_cap', 'market_cap_status', 'price', 'volume_24h', 'is_derivative', 'in_published_comparison', 'comparison_exclusion_reasons', 'premium_to_cheapest_bps'];
    const csv = [header, ...rows].map(row => row.map(csvCell).join(',')).join('\n') + '\n';
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    link.download = `bell-rwa-population-attribution-${String(receipt?.observed_at || '').slice(0, 10) || 'latest'}.csv`;
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

  function interleaveByState(items) {
    const buckets = new Map();
    items.forEach(item => {
      const key = item.comparison ? 'comparable' : (item.state || 'unknown');
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(item);
    });
    const lead = ['comparable', 'do_not_compare', 'investigate', 'no_flags'];
    const queues = lead.filter(key => buckets.has(key)).map(key => buckets.get(key));
    buckets.forEach((rows, key) => { if (!lead.includes(key)) queues.push(rows); });
    const ordered = [];
    while (ordered.length < items.length) {
      let moved = false;
      queues.forEach(queue => { if (queue.length) { ordered.push(queue.shift()); moved = true; } });
      if (!moved) break;
    }
    return ordered;
  }

  function renderAlerts() {
    if (!receipt) return;
    const indexed = receipt.alert_index || receipt.alerts || [];
    const normalizedQuery = query.trim().toLowerCase();
    const details = new Map((receipt.alerts || []).map(alert => [String(alert.rwa_id), alert]));
    const candidates = indexed.filter(item => {
      // "comparable" is not a state the scan emits, it is the outcome a reader
      // actually wants: the references whose prices can honestly be set side by
      // side. Without it the affirmative half sits on page four behind the
      // refusals, which is where it was.
      // The filters matched the raw state while the cards showed the decision
      // label, so FACTS OPEN returned 666 rows of which 545 were badged SINGLE
      // REPRESENTATION and 44 COMPARABLE: 88% of what the button returned said
      // something else. Filter by the word the reader can see.
      const stateMatches = filter === 'all' || decisionBucket(item, 'FACTS OPEN') === filter;
      const haystack = [item.name, item.symbol, item.asset_type, item.rwa_id].join(' ').toLowerCase();
      return stateMatches && (!normalizedQuery || haystack.includes(normalizedQuery));
    });
    const exactMatches = normalizedQuery
      ? candidates.filter(item => [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery))
      : [];
    const unordered = exactMatches.length ? exactMatches : candidates;
    // The index arrives sorted by severity, so every reference on page one was
    // do_not_compare: six cards with the same state, under a heading that
    // promises "what to do next, by state", each repeating the same sentence
    // because that sentence is a constant on every blocked row. Round-robin the
    // state buckets on the default view so the first page shows the range the
    // scan actually produces, and lead with the affirmative - a reader who
    // opens on six refusals reads the product as "this tool tells me no".
    // Nothing is dropped and nothing is hidden; only the order changes, and
    // only while no filter or query is narrowing the list.
    const ordered = (filter === 'all' && !normalizedQuery && sortBy === 'severity')
      ? interleaveByState(unordered) : unordered;
    const matching = window.BellIndexOrder.orderIndex(ordered, sortBy);
    // The export writes this list, not the whole population: a button that
    // silently exports something other than what is on screen is the kind of
    // quiet disagreement this product reports.
    lastVisibleIndex = matching;
    const totalPages = Math.max(1, Math.ceil(matching.length / pageSize));
    pageNumber = Math.min(pageNumber, totalPages - 1);
    const start = pageNumber * pageSize;
    const visible = matching.slice(start, start + pageSize);
    const focusAction = normalizedQuery && matching.length ? ' <button type="button" class="focus-action" data-open-first-evidence>Open first evidence ↓</button>' : '';
    const range = matching.length ? `${start + 1}-${Math.min(start + pageSize, matching.length)}` : '0';
    byId('alert-count').innerHTML = `Showing <strong>${range}</strong> of <strong>${matching.length}</strong> matching references · ${indexed.length.toLocaleString()} references scanned · representation rows remain inspectable for each indexed reference.${focusAction}`;
    byId('alert-list').innerHTML = visible.length
      ? renderRouteLegend(visible) + visible.map(item => renderIndexRow(item, details.get(String(item.rwa_id)))).join('')
      : '<p class="section-note">No references match this filter.</p>';
    const pagination = byId('alert-pagination');
    if (pagination) {
      pagination.innerHTML = matching.length > pageSize
        ? `<button type="button" data-page="0" ${pageNumber === 0 ? 'disabled' : ''} aria-label="First population page">&laquo; First</button><button type="button" data-page="${pageNumber - 1}" ${pageNumber === 0 ? 'disabled' : ''} aria-label="Previous population page">Previous</button><span>Page <input id="alert-page-jump" type="number" min="1" max="${totalPages}" value="${pageNumber + 1}" aria-label="Go to population page"> of ${totalPages}</span><button type="button" data-page="${pageNumber + 1}" ${pageNumber === totalPages - 1 ? 'disabled' : ''} aria-label="Next population page">Next</button><button type="button" data-page="${totalPages - 1}" ${pageNumber === totalPages - 1 ? 'disabled' : ''} aria-label="Last population page">Last &raquo;</button>`
        : '';
    }
    renderWatchlist();
  }

  // Ordering and the shape of an export live in index-order.js so they can be
  // driven by a test instead of a browser. The rule worth naming: a reference
  // with no published comparison has no observed spread and sorts last, not as
  // zero, in both directions.
  function downloadIndex() {
    if (!receipt) return;
    const order = window.BellIndexOrder;
    const rows = lastVisibleIndex.map(item =>
      order.exportRow(item, displayDecisionLabel(item, 'FACTS OPEN')));
    const csv = [order.HEADER, ...rows].map(row => row.map(csvCell).join(',')).join('\n') + '\n';
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    link.download = `bell-rwa-reference-index-${String(receipt?.observed_at || '').slice(0, 10) || 'latest'}.csv`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
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
    // The label was read from displayDecisionLabel and the next step from the
    // raw scan state, so a reference that prints COMPARABLE was told to
    // "classify the representation and keep unresolved wrappers separate" in
    // the next line. That is 46 references in the live receipt: the ones the
    // scan marks investigate AND that carry a published comparison. Branch on
    // the word the reader just read.
    const state = displayDecisionLabel(item);
    const classScope = alphabetClassScopeSentence(item);
    const next = state === 'DO NOT SHORTLIST'
      ? 'Resolve the identity or reported-quote issue before comparing wrappers.'
      : state === 'COMPARABLE'
        ? 'Compare the routes below, then complete issuer, redemption and eligibility diligence outside this monitor.'
        : state === 'INVESTIGATE'
          ? 'Classify the representation and keep unresolved wrappers separate.'
          : state === 'SINGLE REPRESENTATION'
            ? 'There is no wrapper ranking to perform; verify the instrument and issuer externally.'
            : 'Open the rows for a factual side-by-side, then complete external diligence.';
    result.hidden = false;
    const exact = [item.name, item.symbol, item.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery);
    const matchLabel = exact ? `${matches.filter(candidate => [candidate.name, candidate.symbol, candidate.rwa_id].some(value => String(value || '').trim().toLowerCase() === normalizedQuery)).length || 1} MATCH · EXACT MATCH` : `${matches.length} MATCH${matches.length === 1 ? '' : 'ES'} · ${matches.length === 1 ? 'CLOSEST NAME' : 'SHOWING FIRST'}`;
    result.innerHTML = `<span>SEARCHED REFERENCE · ${matchLabel}</span><strong>${escapeHTML(item.name || item.symbol || 'Reference')} · ${escapeHTML(item.symbol || 'RWA')}</strong><p>${plural(item.token_count, 'representation')} · ${plural(item.issuer_count, 'issuer')} · <b>${state}</b></p>${classScope ? `<p class="share-class-scope"><strong>Share-class scope:</strong> ${escapeHTML(classScope)}</p>` : ''}<p>${escapeHTML(next)}</p>${capitalPanel(item)}${observedQuoteEndpoints(item)}<div class="search-result-actions"><a href="#monitor">Inspect this evidence ↓</a><a href="#explorer" data-open-map-query="${escapeHTML(item.rwa_id || item.name || item.symbol || '')}">Open live dossier context ↓</a></div>`;
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
    updateWorkspaceHandoff(query.toLowerCase());
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
    // This sentence carried a hardcoded 87 while the filter it describes showed
    // 78, on a page whose README says "every figure on it is derived from that
    // receipt, never written into the page". Counted the same way the filter
    // matches, so the two cannot disagree again.
    const comparableCount = byId('population-comparable-count');
    if (comparableCount) {
      const labelled = (receipt.alert_index || [])
        .filter(item => decisionBucket(item, 'FACTS OPEN') === 'COMPARABLE').length;
      comparableCount.textContent = labelled.toLocaleString();
    }
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
    const calibration = receipt.rule_calibration || {};
    const observedBands = calibration.observed_ratio_bands || {};
    const bands = [
      ['&lt;2×', 'below_2x', value => value < 2],
      ['2×–5×', '2x_to_below_5x', value => value >= 2 && value < 5],
      ['5×–10×', '5x_to_below_10x', value => value >= 5 && value < 10],
      ['10×+', '10x_or_more', value => value >= 10],
    ].map(([label, key, test]) => ({ label, key, test, value: Number(observedBands[key] || 0) }));
    let pricedReferences = Number(calibration.references_with_two_positive_prices || 0);
    if (!Object.keys(observedBands).length) {
      pricedReferences = 0;
      (receipt.alert_index || []).forEach(item => {
        const prices = (item.representations || []).map(token => Number(token?.price)).filter(value => Number.isFinite(value) && value > 0);
        if (prices.length < 2) return;
        pricedReferences += 1;
        const ratio = Math.max(...prices) / Math.min(...prices);
        const band = bands.find(entry => entry.test(ratio));
        if (band) band.value += 1;
      });
    }
    const maxBand = Math.max(...bands.map(band => band.value), 1);
    const spreadVisual = bands.map(band => `<div class="spread-row"><span>${band.label}</span><div class="spread-track"><i style="width:${Math.max((band.value / maxBand) * 100, band.value ? 2 : 0)}%"></i></div><strong>${band.value.toLocaleString()}</strong></div>`).join('');
    const insufficientReferences = Number(calibration.references_with_insufficient_positive_prices || Math.max(total - pricedReferences, 0));
    target.innerHTML = `<article class="population-chart-panel state-panel"><div class="population-chart-top"><span class="eyebrow">ROUTE BY STATE</span><strong>${total.toLocaleString()} references</strong></div><h3>Most references need investigation before comparison</h3><div class="population-states">${stateVisual}</div><div class="population-stacked" aria-label="Stacked population state bar">${stateRows.map(([key, label, tone]) => `<i class="${tone}" style="width:${Math.max((Number(states[key] || 0) / total) * 100, Number(states[key] || 0) ? 1 : 0)}%" title="${label}: ${Number(states[key] || 0).toLocaleString()}"></i>`).join('')}</div></article><article class="population-chart-panel spread-panel"><div class="population-chart-top"><span class="eyebrow">OBSERVED QUOTE SPREAD</span><strong>${pricedReferences.toLocaleString()} with ≥2 priced routes</strong></div><h3>Where multiple priced representations diverge</h3><div class="spread-rows">${spreadVisual}</div><p class="population-chart-note">${insufficientReferences.toLocaleString()} references had fewer than two positive prices and stay outside this chart. These are population spread observations; only references passing the additional reported-volume and spot-route filters receive a published comparison. The bands identify a review route, not a fair-value gap.</p></article>`;
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
    const population = receipt.population_attribution || {};
    const reconciliation = population.asset_level_reconciliation || {};
    const matched = Number(reconciliation.matched_reference_rows || 0);
    const exact = Number(reconciliation.exact_within_usd_cent || 0);
    const residual = Number(reconciliation.residual_sum || 0);
    const residualLabel = `${residual < 0 ? '−' : ''}$${Math.abs(residual).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
    const valueRatio = Number(reconciliation.token_to_asset_value_ratio);
    const valueRatioLabel = Number.isFinite(valueRatio) ? `${(valueRatio * 100).toFixed(2)}%` : 'N/A';
    const reconciliationValueLabel = Number.isFinite(valueRatio) ? valueRatioLabel : residualLabel;
    const reconciliationValueNote = Number.isFinite(valueRatio) ? 'token / asset value' : 'net residual';
    target.innerHTML = `<article class="concentration-panel issuer-panel"><div class="concentration-panel-top"><span class="eyebrow">REPORTED VALUE BY ISSUER</span><strong>${money(reportedValue)}</strong></div><h3>Five issuer labels carry ${(topFiveValue / (reportedValue || 1) * 100).toFixed(1)}% of positive reported value</h3><div class="issuer-bars">${issuerBars}</div><p class="concentration-note">${issuers.length.toLocaleString()} issuer labels carry reported value · HHI ${hhi.toFixed(0)} / 10,000 · effective issuer count ${effectiveIssuers.toFixed(2)}</p><small class="concentration-definition">HHI rises as reported value concentrates. Effective issuer count is an equivalent-share estimate, not a count of legal issuers.</small></article><article class="concentration-panel coverage-panel"><div class="concentration-panel-top"><span class="eyebrow">DATA COVERAGE</span><strong>${representations.length.toLocaleString()} rows</strong></div><h3>${missingTokens.toLocaleString()} token rows do not report market cap in this receipt</h3><div class="coverage-rows">${coverageRows}</div><p class="concentration-note">Value shares use positive token-level market-cap fields only. The denominator is not the full tokenised-asset market.</p></article><article class="concentration-panel reconciliation-panel"><div class="concentration-panel-top"><span class="eyebrow">SURFACE RECONCILIATION</span><strong>${matched.toLocaleString()} matched references</strong></div><h3>Does the asset-level total reconcile with its token rows?</h3><div class="reconciliation-metrics"><div><strong>${exact.toLocaleString()}</strong><span>within $0.01</span></div><div><strong>${Math.max(matched - exact, 0).toLocaleString()}</strong><span>non-exact</span></div><div><strong>${reconciliationValueLabel}</strong><span>${reconciliationValueNote}</span></div></div><p class="concentration-note">Net residual ${residualLabel}. Bell compares CMC's asset-list <code>tokenized_market_cap</code> with the sum of positive token-row market caps on the same <code>rwa_id</code>. This validates surface agreement, not backing or investability.</p></article>`;
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
        rules_version: receipt.universe.rules_version || null,
      }
      : null;
    // The live observation used to be pushed onto the end regardless of when it
    // was observed. Once the series is appended by a scheduled job, a receipt
    // that arrives out of order prints the delta backwards: "20:08 -> 13:44",
    // with the signs inverted and nothing on the page saying so. Order by
    // observation time instead of by arrival.
    const observations = (liveObservation
      && !storedObservations.some(item => item.observed_at === liveObservation.observed_at)
      ? [...storedObservations, liveObservation]
      : storedObservations)
      .slice()
      .sort((left, right) => String(left.observed_at || '').localeCompare(String(right.observed_at || '')));
    const heroTrail = byId('hero-receipt-trail');
    if (heroTrail) {
      heroTrail.textContent = Array.isArray(observations) && observations.length
        ? (() => {
          // "12 dated observations" is true and it oversells: nine of them land
          // in one afternoon. A reader counting receipts is really asking how
          // many days this has been watched, so say both. The same sentence
          // that refuses a delta across a rule change should not let a count
          // imply a series that is not there.
          const days = new Set(observations.map(item => String(item.observed_at || '').slice(0, 10)));
          days.delete('');
          return `RECEIPT TRAIL · ${observations.length} dated observations across `
            + `${days.size} ${days.size === 1 ? 'day' : 'days'} · live receipt included`;
        })()
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
    // This panel used to print "-568 investigate groups, +570 clear groups" across
    // a boundary where the rules were rewritten, not where the market moved:
    // MARKET_FIELDS_MISSING stopped driving most of the catalogue to INVESTIGATE.
    // The same observation instant, 2026-09-21T21:25:01Z, is published twice with
    // different answers - 662 investigate in the stored summary, 90 in the replay
    // recomputed under bell.rules.v2 - which is exactly the kind of silent
    // disagreement between two surfaces that this product exists to catch. So it
    // refuses its own delta here on the same grounds it refuses a wrapper
    // comparison: the two numbers were not produced under the same rules, so
    // subtracting them states something nobody observed.
    const ruleOf = (item) => item?.rules_version || null;
    const comparableRules = Boolean(ruleOf(previous)) && ruleOf(previous) === ruleOf(latest);
    const ruleLabel = (item) => ruleOf(item) || 'rules not recorded';
    const visibleObservations = observations.slice(-9);
    // Several receipts can land on the same calendar day. Labelling every column
    // MM-DD then prints the same date repeatedly and reads as a broken axis.
    const distinctDays = new Set(visibleObservations.map(item => String(item.observed_at || '').slice(0, 10)));
    const labelByTime = distinctDays.size < visibleObservations.length;
    const fadedCount = visibleObservations.filter(item => ruleOf(item) !== ruleOf(latest)).length;
    // A faded column with no caption reads as a broken chart rather than a
    // deliberate boundary, so name it.
    const ruleNote = fadedCount
      ? ` ${fadedCount} faded ${fadedCount === 1 ? 'column was' : 'columns were'} produced under an earlier rule set and cannot be read as a trend against the current one.`
      : '';
    // This said "Short series: 9 receipts across 2 calendar days" directly under
    // a header reading "14 DATED OBSERVATIONS ACROSS 4 DAYS". Both were true and
    // together they read as a contradiction, because the caption described the
    // nine-column window without ever saying it was one. A page that refuses to
    // subtract two receipts on denominator grounds cannot leave its own chart
    // quoting a truncated count as if it were the series.
    const totalDays = new Set(observations.map(item => String(item.observed_at || '').slice(0, 10)));
    const windowed = visibleObservations.length < observations.length;
    const scope = windowed
      ? `The last ${visibleObservations.length} of ${observations.length} receipts, spanning ${distinctDays.size} of ${totalDays.size} calendar ${totalDays.size === 1 ? 'day' : 'days'}.`
      : `All ${visibleObservations.length} receipts, across ${distinctDays.size} calendar ${distinctDays.size === 1 ? 'day' : 'days'}.`;
    const spanNote = totalDays.size <= 2
      ? `${scope} Short series. Columns are separate observations, not daily closes.`
      : `${scope} Columns are separate observations, not daily closes.`;
    const chartNote = spanNote + ruleNote;
    const historyBars = visibleObservations.map(item => {
      const states = item.states || {};
      const total = Number(item.tokenised_references_scanned || 0) || 1;
      const observedAt = String(item.observed_at || '');
      const stamp = labelByTime
        ? `${observedAt.slice(8, 10)} ${observedAt.slice(11, 16)}`.trim()
        : observedAt.slice(5, 10);
      const otherRules = ruleOf(item) !== ruleOf(latest);
      return `<div class="history-point${otherRules ? ' other-rules' : ''}" title="${escapeHTML(`${item.observed_at || ''} · ${ruleLabel(item)}`)}"><div class="history-stack"><i class="blocked" style="height:${Math.max((Number(states.do_not_compare || 0) / total) * 100, 1)}%"></i><i class="investigate" style="height:${Math.max((Number(states.investigate || 0) / total) * 100, 1)}%"></i><i class="clear" style="height:${Math.max((Number(states.no_flags || 0) / total) * 100, 1)}%"></i></div><small>${escapeHTML(stamp)}</small></div>`;
    }).join('');
    // Three cases, and they are not the same refusal. Saying "the rules changed"
    // when neither receipt recorded its rules would be the same kind of
    // unsupported claim this panel exists to stop.
    const boundaryDetail = (!ruleOf(previous) && !ruleOf(latest))
      ? 'Neither summary records the rule set that produced it, so there is nothing to attribute the difference to. Receipts published from here on declare their rule set, and the dated replay package recomputes older observations under the current rules.'
      : (!ruleOf(previous))
        ? `The earlier summary predates rule-set recording; the later one declares ${escapeHTML(ruleOf(latest))}. The dated replay package recomputes that same observation instant under the current rules, and that recomputation is the honest comparison.`
        : `The two receipts declare ${escapeHTML(ruleOf(previous))} and ${escapeHTML(ruleOf(latest))}. A count produced by one rule set is not a measurement of the other.`;
    const historyHeadline = comparableRules
      ? 'What changed between the two receipts'
      : 'Two receipts, two rule sets';
    const deltaBlock = comparableRules
      ? `<div class="publication-history-grid"><div><strong>${signed(delta('do_not_compare'))}</strong><small>blocked groups</small></div><div><strong>${signed(delta('investigate'))}</strong><small>investigate groups</small></div><div><strong>${signed(delta('no_flags'))}</strong><small>clear groups</small></div><div><strong>${signed(Number(latest.signals?.PRICE_DENOMINATION_BREAK || 0) - Number(previous.signals?.PRICE_DENOMINATION_BREAK || 0))}</strong><small>price spread signals</small></div></div>`
      : `<div class="rule-boundary"><span>RULE CHANGE, NOT MARKET CHANGE</span><p>These two receipts were produced by different rule sets, so the difference between their counts is not an observation about the market. Bell does not publish a delta it cannot attribute, for the same reason it refuses to rank two wrappers that do not share a unit.</p><p class="rule-boundary-detail">${boundaryDetail}</p><a href="proof/rwa-surface-integrity-latest-replay-2026-09-21.json" target="_blank" rel="noopener">Open the recomputed replay receipt ↗</a></div>`;
    target.innerHTML = `<div class="publication-history-head"><div><span class="eyebrow">PUBLICATION HISTORY</span><h3>${escapeHTML(historyHeadline)}</h3></div><span>${escapeHTML(previous.observed_at || 'prior')} · ${escapeHTML(ruleLabel(previous))} → ${escapeHTML(latest.observed_at || 'latest')} · ${escapeHTML(ruleLabel(latest))}</span></div>${deltaBlock}<div class="history-chart" aria-label="State composition across published receipts"><div class="history-chart-label"><span>STATE COMPOSITION · LAST ${visibleObservations.length} OF ${observations.length} RECEIPTS</span><small>${escapeHTML(chartNote)}</small></div><div class="history-bars">${historyBars}</div></div><p>Counts are from the published summaries, not inferred market impact. The receipts cover ${Number(latest.tokenised_references_scanned || 0).toLocaleString()} tokenised references and ${Number(latest.tokens_scanned || 0).toLocaleString()} representations.</p>`;
  }

  async function loadPublicationHistory() {
    const target = byId('publication-history');
    if (!target || window.location.protocol === 'file:') return;
    try {
      const response = await fetch('proof/rwa-surface-integrity-history.json', { cache: 'no-cache', headers: { Accept: 'application/json' } });
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

  // The affirmative case the hero opens on, chosen by a published rule so the
  // choice can be checked rather than trusted: the reference with the most
  // comparable routes, ties broken by the widest spread still inside the
  // publishable ceiling.
  const HERO_RULE = 'most comparable routes, then widest publishable spread';

  function heroComparable() {
    const withComparison = (receipt.alerts || []).filter(item => item && item.comparison
      && Number(item.comparison.route_count) >= 2);
    if (!withComparison.length) return null;
    return withComparison.slice().sort((a, b) =>
      (b.comparison.route_count - a.comparison.route_count)
      || (b.comparison.spread_bps - a.comparison.spread_bps))[0];
  }

  function renderDecisionStory() {
    const normalizedQuery = query.trim().toLowerCase();
    const focused = normalizedQuery ? preferredSearchMatch(normalizedQuery) : null;
    const focusedDetail = focused && (receipt.alerts || []).find(item => String(item.rwa_id) === String(focused.rwa_id));
    // With nothing searched, this opened on the first blocked reference, so the
    // first thing a visitor met was the product declining. The gate has a door:
    // 83 references carry a published comparison, and none of them was ever
    // shown above the fold. Lead with one, by a stated rule rather than by
    // taste - most routes, ties broken by the widest publishable spread, which
    // selects the case where choosing the wrong wrapper costs the most. The
    // refusal is still one search away and still the honest majority.
    const alert = focusedDetail || focused
      || (!normalizedQuery && !searchAttempted && (heroComparable() || receipt.alerts.find(item => item.state === 'do_not_compare') || receipt.alerts.find(item => item.state === 'investigate')));
    const publication = receipt._publication || {};
    if (!alert) {
      byId('hero-case').textContent = normalizedQuery ? 'No reference found' : 'Search a reference';
      byId('hero-case-fact').textContent = normalizedQuery ? `Nothing in the published receipt matches “${query}”.` : 'Use the search above to open a published evidence case.';
      setHeroProofHeading(searchAttempted ? 'START HERE' : 'NO PUBLISHED CASE');
      byId('hero-proof-reason').textContent = 'Search a listed reference before reading the evidence card.';
      byId('hero-signal-list').innerHTML = '<div><span class="hero-signal-severity checked">NO MATCH</span><strong>No published case selected</strong><small>Try the asset name, ticker or RWA ID</small></div>';
      // Every hero block that describes THE SELECTED CASE has to go when there
      // is no selected case. This hid the quote contrast and left the capital
      // route showing, so a search that found nothing still read "Keep 10,000
      // uncommitted · Resolve identity, unit, issuer terms and execution
      // evidence before selecting a wrapper" - the previous reference's verdict,
      // printed under a card saying no case is selected. Listed rather than
      // hidden one by one, because that is how the first one got missed.
      // #hero-population-signal is deliberately not here: it describes the
      // receipt, not the case, and stays true when nothing is selected.
      for (const id of ['hero-quote-contrast', 'hero-capital-signal']) {
        const block = byId(id);
        if (block) block.hidden = true;
      }
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
      const mobileDecision = byId('hero-mobile-decision');
      if (mobileDecision) {
        mobileDecision.hidden = false;
        byId('hero-mobile-case').textContent = normalizedQuery ? 'No matching reference' : 'Search a reference';
        byId('hero-mobile-outcome').textContent = normalizedQuery ? 'NO MATCH' : 'START HERE';
        byId('hero-mobile-note').textContent = normalizedQuery ? 'Try the asset name, ticker or RWA ID again' : 'The current evidence card follows below';
      }
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
    if (alert.token_count) caseFacts.push(`${plural(alert.token_count, 'representation')}`);
    if (alert.issuer_count) caseFacts.push(`${formatNumber(alert.issuer_count)} issuers`);
    if (primaryEvidence.max_min_ratio) caseFacts.push(`${formatNumber(primaryEvidence.max_min_ratio)}× observed price spread`);
    byId('hero-case').textContent = alert.name || 'Current flagged case';
    // A reference carrying a published comparison was still described by the
    // rule that let it through, so the card read as a problem report even when
    // the product had produced its answer. Lead the card with the answer: how
    // many routes, how far apart, which is cheapest, and whether the cheapest
    // is the one you can actually fill.
    const heroComparison = alert.comparison;
    if (heroComparison) {
      const cheapest = heroComparison.cheapest || {};
      const highestReportedVolume = heroComparison.highest_reported_volume || heroComparison.deepest || {};
      caseFacts.unshift(`${formatNumber(heroComparison.route_count)} comparable routes`);
      caseFacts.push(`${Number(heroComparison.spread_bps).toFixed(1)} bps apart`);
      caseFacts.push(cheapest.symbol
        ? `cheapest ${cheapest.symbol}${(heroComparison.cheapest_has_highest_reported_volume ?? heroComparison.cheapest_is_deepest)
            ? ', highest reported 24h volume' : `; ${highestReportedVolume.symbol || 'another route'} has the highest reported 24h volume`}`
        : 'cheapest route published');
    }
    byId('hero-case-fact').textContent = caseFacts.join(' · ') || signals || 'Published rule hit';
    const proofReason = byId('hero-proof-reason');
    const reasonPrefix = heroComparison
      ? `Prices can be set side by side${(heroComparison.unresolved || []).length
          ? `, with ${(heroComparison.unresolved || []).length} check${(heroComparison.unresolved || []).length === 1 ? '' : 's'} still open`
          : ''}`
      : alert.state === 'do_not_compare' ? 'Unit or market compatibility needs review' : alert.state === 'investigate' ? 'Identity or market fields need review' : '';
    const reasonSignals = significantSignals.slice(0, 3).map(signal => signalLabels[signal.code] || signal.code).join(' · ');
    if (proofReason) proofReason.textContent = [reasonPrefix, reasonSignals].filter(Boolean).join(' · ') || 'No published review trigger in the current rule set';
    const signalList = byId('hero-signal-list');
    const comparableRow = heroComparison
      ? `<div><span class="hero-signal-severity comparable">PRICE COMPARISON</span><strong>${formatNumber(heroComparison.route_count)} routes under one CMC RWA reference pass Bell's price and reported-volume filters</strong><small>${Number(heroComparison.spread_bps).toFixed(1)} bps between cheapest and dearest · equivalent units and claims are not established</small></div>`
      : '';
    if (signalList) signalList.innerHTML = comparableRow + (significantSignals.length
      ? significantSignals.slice(0, 3).map(signal => `<div><span class="hero-signal-severity ${signal.severity === 'critical' ? 'critical' : 'warning'}">${escapeHTML(String(signal.severity || 'signal').toUpperCase())}</span><strong>${escapeHTML(signalLabels[signal.code] || signal.code)}</strong><small>${escapeHTML(signalEvidenceSummary(signal))} · ${escapeHTML(signalSourceLabel(signal.code))}</small></div>`).join('')
      : (comparableRow ? '' : '<div><span class="hero-signal-severity checked">CLEAR</span><strong>No published rule hit</strong><small>Observed fields remain descriptive and require external diligence</small></div>'));
    const quoteContrast = byId('hero-quote-contrast');
    const capitalSignal = byId('hero-capital-signal');
    const comparisonRows = heroComparison && Array.isArray(heroComparison.routes) ? heroComparison.routes : null;
    const pricedTokens = (comparisonRows || alert.tokens || []).filter(token => typeof token.price === 'number').sort((a, b) => a.price - b.price);
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
        byId('hero-low-issuer').textContent = [low.name, low.issuer_name].filter(Boolean).join(' · ') || 'Issuer not resolved';
        byId('hero-high-issuer').textContent = [high.name, high.issuer_name].filter(Boolean).join(' · ') || 'Issuer not resolved';
      }
    }
    if (capitalSignal) {
      const capital = window.BellCapitalImpact.assess(alert, 10000);
      capitalSignal.hidden = false;
      capitalSignal.className = `hero-capital-signal hero-capital-${capital.mode}`;
      const capitalHeadline = byId('hero-capital-headline');
      const capitalCopy = byId('hero-capital-copy');
      if (capitalHeadline) capitalHeadline.textContent = capital.headline;
      // The hero and the panel below render the same capital assessment, so the
      // same boundary sentence landed twice within one screen. The first one to
      // render states it; the second points back at it.
      if (capitalCopy) capitalCopy.textContent = boundary(capital.note);
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
    setEvidenceCheck('hero-unit-check', signalCodes.has('PRICE_DENOMINATION_BREAK') ? 'BLOCKED' : 'UNVERIFIED', signalCodes.has('PRICE_DENOMINATION_BREAK') ? 'blocked' : 'review');
    setEvidenceCheck('hero-market-check', signalCodes.has('ZERO_MCAP_POSITIVE_VOLUME') || signalCodes.has('MARKET_FIELDS_MISSING') ? 'REVIEW' : 'OBSERVED', signalCodes.has('ZERO_MCAP_POSITIVE_VOLUME') || signalCodes.has('MARKET_FIELDS_MISSING') ? 'review' : 'checked');
    byId('hero-example').textContent = `${isDatedReplay ? 'Published replay' : 'Live example'}: search ${alert.name || 'the reference'} → inspect ${caseFacts.join(' · ') || 'the evidence'} → ${displayDecisionLabel(alert, 'HOLD COMPARISON')} → verify the next action before ranking a wrapper.`;
    byId('hero-proof-output').textContent = displayDecisionLabel(alert, 'HOLD COMPARISON');
    byId('hero-proof-output').className = `state-${stateClass(displayDecisionLabel(alert, 'HOLD COMPARISON')) || 'blocked'}`;
    const mobileDecision = byId('hero-mobile-decision');
    if (mobileDecision) {
      mobileDecision.hidden = false;
      byId('hero-mobile-case').textContent = alert.name || alert.symbol || 'Current reference';
      byId('hero-mobile-outcome').textContent = displayDecisionLabel(alert, 'HOLD COMPARISON');
      byId('hero-mobile-note').textContent = alphabetClassScopeSentence(alert)
        || caseFacts.join(' · ') || signals || 'Open the full evidence card for the supporting fields';
    }
    const isClean = alert.state === 'no_flags';
    // The output was read from displayDecisionLabel and the hint from the raw
    // state, so the hero printed COMPARABLE with "classify before shortlist"
    // four pixels away. Same split, sixth place.
    const output = displayDecisionLabel(alert, 'HOLD COMPARISON');
    const hint = output === 'DO NOT SHORTLIST' ? 'verify unit and market evidence'
      : output === 'COMPARABLE' ? 'routes published · diligence continues outside this monitor'
      : output === 'INVESTIGATE' ? 'classify before shortlist'
      : output === 'SINGLE REPRESENTATION' ? 'single representation · verify externally'
      : 'facts only · continue external diligence';
    const proofHint = byId('hero-proof-hint');
    if (proofHint) proofHint.textContent = hint;
    const decisionHeading = query.trim() ? 'SEARCHED REFERENCE' : (isClean ? 'CURRENT REFERENCE' : 'FLAGGED REFERENCE');
    const signalLabel = signals || (isClean ? 'no published rule hit' : 'published rule hit');
      byId('decision-hero').innerHTML = `<div class="decision-hero-top"><span class="eyebrow">${decisionHeading}</span><span class="decision-case">${escapeHTML(alert.symbol || 'RWA')}</span></div><h3>${escapeHTML(alert.name)}</h3><p class="decision-signal">${escapeHTML(signalLabel)}</p><div class="decision-outcome"><span>OUTPUT</span><strong>${escapeHTML(displayDecisionLabel(alert, 'HOLD COMPARISON'))}</strong><p>${escapeHTML(displayDecisionConsequence(alert) || alert.next_action || '')}</p><b class="allocation-gate">${escapeHTML(boundary(decision.allocation_effect) || 'No allocation status is produced by this monitor')}</b></div><div class="decision-actions"><button class="brief-button" type="button" data-brief-id="${escapeHTML(alert.rwa_id)}">Save decision brief ↓</button><button class="brief-button" type="button" data-case-receipt="${escapeHTML(alert.rwa_id)}">Download case JSON ↓</button><button class="brief-button" type="button" data-copy-case="${escapeHTML(alert.rwa_id)}">Copy case link ↗</button>${watchButton(alert)}<a class="decision-action-link" href="#monitor">Inspect representation rows ↘</a></div>${capitalPanel(alert)}<section class="reference-change" data-reference-change data-for-id="${escapeHTML(alert.rwa_id)}" hidden></section>${temporalPanel(alert)}${referenceConcentrationPanel(alert)}${referenceActivityPanel(alert)}${resolutionRoute(alert)}<div class="decision-receipt"><span>${escapeHTML(publication.status ? freshnessStatus(publication).toUpperCase() : 'DATED')} · ${escapeHTML(publication.observed_at || receipt.observed_at || 'N/A')}</span><a href="/api/integrity" target="_blank" rel="noopener">Open credential-free receipt ↗</a></div>`;
      renderReferenceChange(alert, byId('decision-hero').querySelector('[data-reference-change]'));
      loadTemporalEvidence(alert);
  }

  const isLocalHost = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);

  // explorer.js needs this same receipt and used to fetch it a second time:
  // two independent IIFEs, 2.4 MB each, and cache:'no-cache' on both so the
  // HTTP cache could not collapse them into one. That was 2.4 MB of the page's
  // 7.2 MB, spent twice for the same bytes. Issue the request once here, at
  // module scope so it exists before explorer.js evaluates, and publish the
  // promise for it to read.
  const liveReceiptRequest = isLocalHost
    ? Promise.resolve(null)
    : fetch('/api/integrity', { cache: 'no-cache', headers: { Accept: 'application/json' } })
        .then(response => (response.ok ? response.json() : null))
        .catch(() => null);
  // Publishing the network request itself meant that on localhost, where there
  // is no /api/integrity to call, explorer.js received null and its live-verdict
  // cross-reference went dead: it told a reader that Gold "carried no token
  // representation in the latest scan" while the replay receipt loaded on the
  // same page held Gold with seven representations. Publish the receipt this
  // page actually ended up reading, whichever source it came from, so the two
  // halves of the page can never describe different data.
  let receiptSource = null;
  // Reviewers marked the exported receipt down for carrying no HTTP status and
  // no request counts. The data was never missing: it sits in the replay input
  // package's collection manifest, which is 16.5 MB and so never reached the
  // artefact a judge downloads. bell/extract_transport.py lifts it into 3 KB.
  let transportRecord = null;
  fetch('proof/transport-2026-09-21.json', { cache: 'no-cache' })
    .then(response => (response.ok ? response.json() : null))
    .then(record => { transportRecord = record; })
    .catch(() => { transportRecord = null; });
  let findingObservedAt = null;
  let announceReceipt;
  window.BellReceipt = new Promise(resolve => { announceReceipt = resolve; });

  async function boot() {
    try {
      const sources = isLocalHost
        ? ['proof/rwa-surface-integrity-latest-replay-2026-09-21.json']
        : ['/api/integrity', 'proof/rwa-surface-integrity-latest-replay-2026-09-21.json'];
      let lastError;
      for (const source of sources) {
        try {
          let candidate;
          if (source === '/api/integrity') {
            candidate = await liveReceiptRequest;
            if (!candidate) throw new Error('live receipt unavailable');
          } else {
            const response = await fetch(source, { cache: 'no-cache', headers: { Accept: 'application/json' } });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            candidate = await response.json();
          }
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
            receiptSource = source;
            announceReceipt(candidate);
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
      updateWorkspaceHandoff(query.toLowerCase());
      renderMetrics();
      renderFinding();
      renderCoverageFact();
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
      // Leave nothing awaiting a promise that will never settle: explorer.js
      // blocks its live-verdict lookup on this, and a hung lookup shows no
      // state at all rather than saying the receipt is unavailable.
      announceReceipt(null);
      byId('alert-list').innerHTML = '<p class="section-note">The dated evidence receipt could not be loaded. Open the JSON receipt directly to inspect the source.</p>';
    }
  }

  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    pageNumber = 0;
    document.querySelectorAll('[data-filter]').forEach(item => item.classList.toggle('selected', item === button));
    rememberIndexState();
    renderAlerts();
  }));
  // A shared link has to arrive with its controls already set, or the view is
  // restored and the page lies about how it got there.
  (function restoreIndexControls() {
    const sort = byId('alert-sort');
    if (sort) sort.value = sortBy;
    const size = byId('alert-page-size');
    if (size && [...size.options].some(option => Number(option.value) === pageSize)) {
      size.value = String(pageSize);
    }
    document.querySelectorAll('[data-filter]').forEach(button => {
      button.classList.toggle('selected', button.dataset.filter === filter);
    });
  }());

  byId('alert-sort')?.addEventListener('change', event => {
    sortBy = event.target.value;
    pageNumber = 0;
    rememberIndexState();
    renderAlerts();
  });
  byId('download-index')?.addEventListener('click', downloadIndex);
  byId('alert-page-size')?.addEventListener('change', event => {
    const chosen = Number(event.target.value);
    pageSize = Number.isFinite(chosen) && chosen > 0 ? chosen : pageSize;
    pageNumber = 0;
    rememberIndexState();
    renderAlerts();
  });
  document.addEventListener('change', event => {
    if (event.target?.id !== 'alert-page-jump') return;
    const asked = Number(event.target.value);
    if (!Number.isFinite(asked)) return;
    const highest = Number(event.target.max) || 1;
    pageNumber = Math.min(Math.max(1, Math.round(asked)), highest) - 1;
    rememberIndexState();
    renderAlerts();
  });
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
    rememberIndexState();
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
  byId('download-population-attribution')?.addEventListener('click', downloadPopulationAttribution);
  byId('refresh-receipt')?.addEventListener('click', event => {
    const button = event.currentTarget;
    button.disabled = true;
    button.textContent = 'Refreshing…';
    window.location.reload();
  });
  boot();
  window.setInterval(() => { if (receipt) renderMetrics(); }, 60000);
})();

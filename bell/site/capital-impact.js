/* Small, deterministic decision-economics helpers. No market prediction or recommendation. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BellCapitalImpact = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  function finitePositive(value) {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : null;
  }

  function budget(value, fallback = 10000) {
    const number = finitePositive(value);
    return number && number <= 1000000000 ? number : fallback;
  }

  function quoteRange(tokens) {
    const prices = (tokens || []).map(token => finitePositive(token && token.price)).filter(Boolean);
    if (prices.length < 2) return null;
    const low = Math.min(...prices);
    const high = Math.max(...prices);
    return {
      low,
      high,
      ratio: high / low,
      gapPercent: ((high - low) / low) * 100,
      count: prices.length,
    };
  }

  function quoteBand(tokens) {
    const rows = (tokens || [])
      .map((token, index) => ({
        token,
        index,
        price: finitePositive(token && token.price),
        volume: token && token.volume_24h == null ? null : Number(token.volume_24h),
      }))
      .filter(row => row.price !== null);
    if (rows.length < 2) return null;
    const ordered = [...rows].sort((a, b) => a.price - b.price);
    const middle = Math.floor(ordered.length / 2);
    const median = ordered.length % 2 ? ordered[middle].price : (ordered[middle - 1].price + ordered[middle].price) / 2;
    const low = ordered[0].price;
    const high = ordered[ordered.length - 1].price;
    return {
      median,
      low,
      high,
      ratio: high / low,
      gapPercent: ((high - low) / low) * 100,
      rows: rows.map(row => ({
        ...row,
        deltaPercent: ((row.price / median) - 1) * 100,
        volumeState: row.volume === null || !Number.isFinite(row.volume) ? 'missing' : row.volume === 0 ? 'zero' : 'positive',
      })),
    };
  }

  function volumeMetrics(tokens, amount) {
    const rows = (tokens || []).map(token => Number(token && token.volume_24h)).filter(value => Number.isFinite(value) && value > 0);
    if (!rows.length) return null;
    const reportedVolume = rows.reduce((sum, value) => sum + value, 0);
    const value = budget(amount);
    return {
      reportedVolume,
      positiveRows: rows.length,
      amountSharePercent: (value / reportedVolume) * 100,
    };
  }

  function capitalMetrics(range, amount, tokens) {
    const value = budget(amount);
    const volume = volumeMetrics(tokens, value);
    if (!range && !volume) return null;
    return {
      ...(range ? {
        ratio: range.ratio,
        gapPercent: range.gapPercent,
        unitsAtLowQuote: value / range.low,
        unitsAtHighQuote: value / range.high,
        nominalUnitGap: value / range.low - value / range.high,
      } : {}),
      volume,
    };
  }

  function assess(alert, amount = 10000) {
    const value = budget(amount);
    const range = quoteRange(alert && (alert.tokens || alert.representations));
    const metrics = capitalMetrics(range, value, alert && (alert.tokens || alert.representations));
    const tokenCount = Number(alert && alert.token_count) || 0;
    const state = alert && alert.state;

    if (state === 'do_not_compare') {
      return {
        mode: 'hold',
        budget: value,
        metrics,
        headline: `Keep ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })} uncommitted`,
        copy: range
          ? `Bell observed a ${range.ratio.toFixed(2)}× quote range across ${range.count} rows. That is a capital-preservation gate, not a discount or a proven saving`
          : 'Bell found a critical integrity break. Keep the amount outside a wrapper decision until the evidence is resolved.',
        note: 'Resolve identity, unit, issuer terms and execution evidence before selecting a wrapper.',
      };
    }

    if (state === 'investigate') {
      return {
        mode: 'review',
        budget: value,
        metrics,
        headline: `Protect ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })} while you verify`,
        copy: 'The grouping is not ready for a clean shortlist. Keep the amount provisional while missing identity or market fields are checked.',
        note: 'This is a review queue, not a buy, sell or allocation instruction.',
      };
    }

    if (tokenCount === 1) {
      return {
        mode: 'single',
        budget: value,
        metrics,
        headline: `One wrapper for ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })} to diligence`,
        copy: 'There is no cross-wrapper price comparison. The financial question moves to backing, redemption, eligibility, custody and execution.',
        note: 'A single representation is not an approval.',
      };
    }

    return {
      mode: 'facts',
      budget: value,
      metrics,
      headline: `Review the quote before committing ${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`,
      copy: range
        ? `Observed quotes span ${range.gapPercent.toFixed(2)}%. Bell exposes the difference so you can verify units, venues and execution before treating it as an economic premium.`
        : 'Observed quote data is incomplete. Confirm the market fields and execution route before committing capital.',
      note: 'Observed quote difference is not an executable saving or an investment recommendation.',
    };
  }

  return { budget, quoteRange, quoteBand, volumeMetrics, capitalMetrics, assess };
});

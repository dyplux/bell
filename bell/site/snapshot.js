/* Published workspace summary. No network, API keys or synthetic price series. */
window.BELL_SNAPSHOT = {
  schema_version: "bell.summary.v2",
  mode: "replayable_snapshot",
  asset: { name: "Tesla", symbol: "TSLA", grouping_source: "CoinMarketCap RWA grouping, as documented in workspace research" },
  window: {
    end_utc: "2026-09-13T09:00:00Z",
    duration_hours: 168,
    start_utc: "2026-09-06T09:00:00Z",
    note: "Seven-day observation with a bundled nine-wrapper receipt and normalised OHLCV payload.",
    timezone: "America/New_York",
    bars_per_wrapper: 168,
    session_counts: { cash: 30, after_hours: 90, weekend: 48 }
  },
  venue_quote: { date: "2026-09-13", fetched_at: null, note: "Venue context is latest 24-hour evidence from the same dated run." },
  provenance: {
    kind: "dated_cmc_receipt",
    documents: ["bell/docs/proof/tesla-live-2026-09-13.json", "bell/docs/proof/tesla-live-2026-09-13.payload.json"],
    endpoints: ["/v5/real-world-assets/quotes/latest", "/v2/cryptocurrency/ohlcv/historical", "/v2/cryptocurrency/quotes/latest"],
    raw_responses_included: false,
    dataset_hash: "see linked receipt",
    raw_response_hashes: null,
    live_requests_made_by_site: false
  },
  methodology: {
    hourly_range_pct: "((high - low) / open) * 100",
    aggregate: "median of hourly ranges, grouped by session",
    session_assignment: "bar opening timestamp in America/New_York; hourly boundary intervals are flagged in the receipt",
    calendar_policy: "weekday clock only; no exchange holiday calendar",
    cash: "Monday-Friday, 09:30 <= opening time < 16:00 ET",
    after_hours: "All other weekday hours, including pre-market, post-market and overnight",
    weekend: "Saturday and Sunday",
    relative_to_cash: "session median / cash median * 100",
    venue_mix: "cex_volume_24h / (cex_volume_24h + dex_volume_24h) * 100",
    hourly_volume: "Not summed; documented field is rolling 24-hour volume"
  },
  wrappers: [
    { symbol: "TSLAX", issuer: "Backed Assets", label: "Tesla xStock", range_pct: { cash: 0.4384, after_hours: 0.2002, weekend: 0.0852 }, venue_usd_24h: { cex: 4246186, dex: 1851547 }, venue_status: "receipt_totals" },
    { symbol: "TSLA.D", issuer: "Dinari Assets", label: "Tesla wrapper", range_pct: { cash: null, after_hours: null, weekend: null }, venue_usd_24h: null, venue_status: "insufficient_data" },
    { symbol: "TSLAon", issuer: "Ondo Assets", label: "Tesla wrapper", range_pct: { cash: 0.3706, after_hours: 0.1965, weekend: 0.0973 }, venue_usd_24h: { cex: 2502384, dex: 82170 }, venue_status: "receipt_totals" },
    { symbol: "TSLA", issuer: "NA (Derivatives)", label: "Derivative representation", range_pct: { cash: 0.5033, after_hours: 0.2259, weekend: 0.0882 }, venue_usd_24h: { cex: 441588, dex: 0 }, venue_status: "receipt_totals" },
    { symbol: "TSLA", issuer: "Hyperliquid Assets", label: "Tesla representation", range_pct: { cash: 0, after_hours: 0, weekend: 0 }, venue_usd_24h: null, venue_status: "zero_denominator" },
    { symbol: "TSLAB", issuer: "bStocks", label: "Tesla wrapper", range_pct: { cash: 0.4686, after_hours: 0.2397, weekend: 0.1036 }, venue_usd_24h: { cex: 4742129, dex: 386747 }, venue_status: "receipt_totals" },
    { symbol: "rTSLA", issuer: "Reality", label: "Tesla wrapper", range_pct: { cash: 0.5319, after_hours: 0.2341, weekend: 0.0965 }, venue_usd_24h: { cex: 129359, dex: 0 }, venue_status: "receipt_totals" },
    { symbol: "TSLA", issuer: "Robinhood", label: "Tesla wrapper", range_pct: { cash: 0.5639, after_hours: 0.4047, weekend: 0.3897 }, venue_usd_24h: { cex: 0, dex: 4661024 }, venue_status: "receipt_totals" },
    { symbol: "WTSLAX", issuer: "Backed Assets", label: "Wrapped Tesla xStock", range_pct: { cash: 0.6583, after_hours: 0.4884, weekend: 0.4308 }, venue_usd_24h: { cex: 0, dex: 426474 }, venue_status: "receipt_totals" }
  ],
  limitations: [
    "Dated replayable receipt, not a live market feed",
    "Normalised hourly bars are bundled in the linked payload and the receipt carries a dataset hash",
    "One observation window, nine Tesla entries; not a general conclusion about all tokenised equities",
    "Range is not return, spread, depth or executable liquidity. One print can produce a wide range",
    "The weekday session clock does not exclude exchange holidays",
    "Hourly bars straddle 09:30 ET and are assigned by their opening timestamp",
    "Relative-to-cash values and venue shares use receipt values rounded for display",
    "Venue mix is 24-hour context, not session-specific flow or proof of causality",
    "Dinari has insufficient OHLCV coverage and the Hyperliquid row has no positive venue denominator",
    "No underlying Tesla stock price, redemption rights, trade counts or market-quality ranking"
  ],
};

/* Second live-validated case, published as a dated summary for the public demo. */
window.BELL_GOLD_SNAPSHOT = {
  schema_version: "bell.summary.v1",
  mode: "demonstration_snapshot",
  asset: { name: "Gold", symbol: "XAU", grouping_source: "CoinMarketCap RWA grouping" },
  window: { start_utc: "2026-09-06T10:00:00Z", end_utc: "2026-09-13T10:00:00Z", duration_hours: 168, timezone: "America/New_York", bars_per_wrapper: 168, session_counts: { cash: 30, after_hours: 90, weekend: 48 } },
  wrappers: [
    { symbol: "PAXG", issuer: "Paxos", range_pct: { cash: 0.2791, after_hours: 0.2382, weekend: 0.0336 }, cex_share_pct: 97.9 },
    { symbol: "XAUt", issuer: "Tether Holdings", range_pct: { cash: 0.2727, after_hours: 0.2251, weekend: 0.0330 }, cex_share_pct: 97.0 },
    { symbol: "XAUM", issuer: "Matrixdock", range_pct: { cash: 0.3655, after_hours: 0.3198, weekend: 0.1713 }, cex_share_pct: 99.6 },
    { symbol: "CGO", issuer: "Comtech Gold", range_pct: { cash: 0.5085, after_hours: 0.4908, weekend: 0.4708 }, cex_share_pct: 100.0 },
    { symbol: "VNXAU", issuer: "VNX", range_pct: { cash: 0.2497, after_hours: 0.2155, weekend: 0.1725 }, cex_share_pct: 0.0 },
    { symbol: "XAUT0", issuer: "Tether Holdings", range_pct: { cash: 0.3180, after_hours: 0.2723, weekend: 0.1534 }, cex_share_pct: 0.0 },
    { symbol: "XAU", issuer: "NA (Derivatives)", range_pct: { cash: 0.2943, after_hours: 0.2641, weekend: 0.0360 }, cex_share_pct: null }
  ],
  limitations: [
    "Dated seven-day live summary, not a current market feed",
    "Range is not return, spread, depth or executable liquidity",
    "Venue share is latest 24-hour context, not session-specific flow",
    "The CMC grouping does not establish identical legal rights or backing"
  ],
};

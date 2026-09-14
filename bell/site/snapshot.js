/* Published workspace summary. No network, API keys or synthetic price series. */
window.BELL_SNAPSHOT = {
  schema_version: "bell.summary.v1",
  mode: "demonstration_snapshot",
  asset: { name: "Tesla", symbol: "TSLA", grouping_source: "CoinMarketCap RWA grouping, as documented in workspace research" },
  window: {
    end_utc: "2026-09-11T19:00:00Z",
    duration_hours: 168,
    start_utc: null,
    note: "Seven-day observation spanning 04–11 September. Exact first bar timestamp is not supplied in the summary.",
    timezone: "America/New_York",
    bars_per_wrapper: 168,
    session_counts: { cash: 30, after_hours: 90, weekend: 48 }
  },
  venue_quote: { date: "2026-09-11", fetched_at: null, note: "Amounts rounded in the source notes; shares are approximate." },
  provenance: {
    kind: "workspace_research_summary",
    documents: ["bell/JUDGE.md", "research/rwa-session/notes.md"],
    endpoints: ["/v5/real-world-assets/quotes/latest", "/v2/cryptocurrency/ohlcv/historical", "/v2/cryptocurrency/quotes/latest"],
    raw_responses_included: false,
    request_ids: null,
    raw_response_hashes: null,
    live_requests_made_by_site: false
  },
  methodology: {
    hourly_range_pct: "((high - low) / open) * 100",
    aggregate: "median of hourly ranges, grouped by session",
    session_assignment: "bar opening timestamp in America/New_York",
    cash: "Monday–Friday, 09:30 <= opening time < 16:00 ET; no exchange holiday calendar",
    after_hours: "All other weekday hours, including pre-market, post-market and overnight",
    weekend: "Saturday and Sunday",
    relative_to_cash: "session median / cash median * 100, calculated from rounded published medians",
    venue_mix: "cex_volume_24h / (cex_volume_24h + dex_volume_24h) * 100, using rounded summary totals",
    hourly_volume: "Not summed; documented field is rolling 24-hour volume"
  },
  wrappers: [
    { symbol: "TSLAX", issuer: "Backed", label: "Tesla xStock", range_pct: { cash: 0.44, after_hours: 0.21, weekend: 0.09 }, venue_usd_24h: { cex: 15200000, dex: 1600000 }, venue_status: "rounded_source_totals" },
    { symbol: "TSLAon", issuer: "Ondo", label: "Tesla tokenised wrapper", range_pct: { cash: 0.37, after_hours: 0.20, weekend: 0.10 }, venue_usd_24h: null, venue_status: "not_supplied_in_summary" },
    { symbol: "TSLAB", issuer: "bStocks", label: "Tesla tokenised wrapper", range_pct: { cash: 0.47, after_hours: 0.25, weekend: 0.16 }, venue_usd_24h: null, venue_status: "not_supplied_in_summary" },
    { symbol: "TSLA", issuer: "Robinhood", label: "Tesla tokenised wrapper", range_pct: { cash: 0.56, after_hours: 0.42, weekend: 0.47 }, venue_usd_24h: { cex: 0, dex: 4600000 }, venue_status: "rounded_source_totals" }
  ],
  limitations: [
    "Dated demonstration summary, not a live market feed.",
    "Raw hourly bars are not bundled: medians cannot be independently recomputed from this receipt.",
    "One observation window, four Tesla wrappers; not a general conclusion about all tokenised equities.",
    "Range is not return, spread, depth or executable liquidity. One print can produce a wide range.",
    "The weekday session clock does not exclude exchange holidays.",
    "Hourly bars straddling 09:30 ET are assigned by their opening timestamp.",
    "Relative-to-cash values and venue shares use rounded published inputs.",
    "Venue mix is 24-hour context, not session-specific flow or proof of causality.",
    "Ondo and bStocks venue totals are not supplied.",
    "No underlying Tesla stock price, redemption rights, trade counts or market-quality ranking."
  ],
  disclosure: "Built by Dyplux, Lisbon. One builder works at CoinMarketCap. Source research was conducted outside that role on a personal hackathon key. Nothing here is written on behalf of CoinMarketCap. This static demo uses no keys and makes no API calls."
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
    "Dated seven-day live summary, not a current market feed.",
    "Range is not return, spread, depth or executable liquidity.",
    "Venue share is latest 24-hour context, not session-specific flow.",
    "The CMC grouping does not establish identical legal rights or backing."
  ],
  disclosure: "Built by Dyplux, Lisbon. Source research was conducted outside the contributor's CoinMarketCap role. Nothing here is written on behalf of CoinMarketCap."
};

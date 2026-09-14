/* Credential-free findings from the dated CMC RWA surface audit. These are
   deliberately separate from live quotes and must remain labelled snapshots. */
window.BELL_AUDIT_SNAPSHOTS = {
  gold: {
    observed_at: '2026-09-13',
    state: 'do_not_compare',
    label: 'DO NOT COMPARE YET',
    headline: 'One Gold reference, mixed token denominations',
    summary: 'CMC groups seven tokens under Gold, but prices span roughly 140 to 4,335 USD. That gap may be a different unit or claim, not a discount.',
    findings: [
      'Denomination unresolved: CGO and VNXAU sit far below the XAUt/PAXG price cluster.',
      'Derivative representation is present and must not be mixed with spot wrappers.',
      'The evidence does not establish physical backing, redemption or units per token.'
    ],
    source: 'CMC Gold RWA page · dated browser surface audit'
  },
  silver: {
    observed_at: '2026-09-13',
    state: 'do_not_compare',
    label: 'DO NOT COMPARE YET',
    headline: 'The apparent 38% Silver gap is not yet an opportunity',
    summary: 'CMC shows Silver near 63.92 USD and average tokenized price near 39.53 USD, while tokenized market cap is zero and the table mixes KAG, XAGX, GRAMS and a derivative.',
    findings: [
      'Denomination unresolved: GRAMS explicitly signals a unit difference.',
      'Positive volume with zero market cap makes the aggregate unsafe to interpret.',
      'A derivative entry is mixed with spot-like representations.'
    ],
    source: 'CMC Silver RWA page · dated browser surface audit'
  },
  tesla: {
    observed_at: '2026-09-13',
    state: 'investigate',
    label: 'INVESTIGATE',
    headline: 'Most Tesla wrappers cluster; the exceptions matter',
    summary: 'CMC shows most Tesla wrappers near the underlying price, but the same TSLA ticker is reused across issuers and one Hyperliquid representation is a large price outlier.',
    findings: [
      'Ticker collision: TSLA identifies different issuers and representations.',
      'Hyperliquid TSLA is far below the cluster and reports no 24h volume.',
      'A derivative reports volume with zero market cap; TSLA.D has missing values.'
    ],
    source: 'CMC Tesla RWA page · dated browser surface audit'
  }
};

// Product evidence is mapped to a CoinMarketCap crypto_id, never to an issuer
// name or ticker. A match means the cited page describes that route; it does
// not independently verify legal rights, custody, or backing.
window.BELL_INSTRUMENT_EVIDENCE = {
  '37013': {
    issuer: 'Backed / xStocks',
    identity: 'GOOGLX · Alphabet Class A tracker certificate',
    status: 'Product-specific page checked · 24 Sep 2026',
    note: 'Backed identifies this product as an Alphabet Class A tracker certificate. Its general xStocks material says dividends can be reinvested through a balance multiplier; this does not establish a permanently fixed token-to-share unit.',
    sources: [
      { label: 'Alphabet xStock product page', url: 'https://assets.backed.fi/products/alphabet-xstock' },
      { label: 'xStocks dividend and split mechanics', url: 'https://docs.xstocks.fi/docs/frequently-asked-questions' },
      { label: 'Backed legal documents', url: 'https://assets.backed.fi/legal-documentation' },
    ],
  },
  '37121': {
    issuer: 'Backed / xStocks',
    identity: 'WGOOGLX · CMC labels this a wrapped xStock',
    status: 'Wrapper relationship unresolved · 28 Sep 2026',
    note: 'CMC names this route as a wrapped GOOGLX token. The issuer materials checked here did not establish the wrapper contract, conversion ratio, or whether its current unit tracks the same legal claim as GOOGLX.',
    sources: [
      { label: 'Backed legal documents', url: 'https://assets.backed.fi/legal-documentation' },
    ],
  },
  '38001': {
    issuer: 'Ondo Global Markets',
    identity: 'GOOGLon · Alphabet Class A',
    status: 'Product page checked · 28 Sep 2026',
    note: 'The asset-specific Ondo page identifies Alphabet Class A. Its general documentation says token units and dividend treatment can differ from a direct share; consult the offering documents for instrument terms.',
    sources: [
      { label: 'GOOGLon asset page', url: 'https://app.ondo.finance/assets/googlon' },
      { label: 'Ondo Stocks overview', url: 'https://docs.ondo.finance/ondo-stocks/overview' },
    ],
  },
  '42272': {
    issuer: 'Ondo Global Markets',
    identity: 'GOOGon · Alphabet Class C',
    status: 'Product page checked · 28 Sep 2026',
    note: 'The asset-specific Ondo page identifies Alphabet Class C. CoinMarketCap groups this route under its Alphabet Class A reference (RWA 4), so this grouped price range is not a same-share-class comparison.',
    sources: [
      { label: 'GOOGon asset page', url: 'https://app.ondo.finance/assets/googon' },
      { label: 'Ondo Stocks overview', url: 'https://docs.ondo.finance/ondo-stocks/overview' },
    ],
  },
  '40757': {
    issuer: 'Robinhood Chain',
    identity: 'GOOGL · tokenised debt security linked to Alphabet Class A',
    status: 'Final Terms checked · 25 Jun 2026',
    note: 'The Robinhood Chain Final Terms identify a debt security linked to Alphabet Class A, issued by Robinhood Assets (Jersey) Limited. This is not the Robinhood Europe Classic Stock Token or direct ownership of the underlying share.',
    sources: [
      { label: 'Alphabet Class A Final Terms', url: 'https://cdn.robinhood.com/assets/robinhood/legal/rhj_final_terms_for_tokenised_debt_securities_linked_to_alphabet_class_a.pdf' },
      { label: 'Robinhood Chain stock token documentation', url: 'https://docs.robinhood.com/chain/stock-tokens/' },
      { label: 'Robinhood Chain token contracts', url: 'https://docs.robinhood.com/chain/contracts/' },
    ],
  },
  '40793': {
    issuer: 'bStocks',
    identity: 'GOOGLB · tokenised Alphabet exposure',
    status: 'Issuer framework checked · instrument terms incomplete',
    note: 'Issuer and public materials describe the bStocks structure, but the exact GOOGLB final terms were not confirmed in this review. Treat the share linkage, rights, unit and redemption terms as unresolved.',
    sources: [
      { label: 'bStocks product information', url: 'https://www.bstocks.finance/' },
    ],
  },
  '40613': {
    issuer: 'Reality',
    identity: 'rGOOGL · issuer terms not retrieved',
    status: 'Unresolved · 28 Sep 2026',
    note: 'The issuer product page was located but could not be read in this review. No claim about its unit, rights, backing or redemption is made here.',
    sources: [
      { label: 'Reality rGOOGL asset page', url: 'https://realityfinance.xyz/en/market/detail/GOOGL' },
    ],
  },
  '28634': {
    issuer: 'Dinari',
    identity: 'GOOGL.D · instrument terms not confirmed',
    status: 'Unresolved · 28 Sep 2026',
    note: 'The reviewed Dinari materials did not establish the exact public GOOGL.D contract and offering terms. No claim about its unit, rights, backing or redemption is made here.',
    sources: [
      { label: 'Dinari documentation', url: 'https://docs.dinari.com/' },
    ],
  },
  '39622': {
    issuer: 'Hyperliquid',
    identity: 'xyz:GOOGL · perpetual market',
    status: 'Market type checked · not a tokenised share',
    note: 'The official market metadata defines this as a perpetual with one Alphabet Class A share as its reference unit. A derivative contract is not an issuer token or a claim on the underlying share.',
    sources: [
      { label: 'Hyperliquid market', url: 'https://app.hyperliquid.xyz/trade/xyz:GOOGL' },
    ],
  },
};

// A focused example of the evidence Bell needs before treating two quotes as
// like-for-like. Dates distinguish the CMC observation from issuer-page review.
window.BELL_PAIR_REVIEWS = {
  '4:37013:38001': {
    title: 'Alphabet Class A · GOOGLX / GOOGLon',
    summary: 'Same Alphabet Class A reference, but quote units remain unresolved. Ondo displays 1 GOOGLon = 1.0025 GOOGL.',
    cmcObserved: '28 Sep 2026 · dated case snapshot',
    termsChecked: '29 Sep 2026',
    alignment: 'Both issuer product pages identify Alphabet Class A exposure.',
    gap: 'Ondo’s page currently displays 1 GOOGLon = 1.0025 GOOGL. xStocks documents balance adjustments for corporate actions and dividend reinvestment, but the checked sources do not establish GOOGLX’s effective unit or whether CMC quotes use raw token units or adjusted share units. Shared Alphabet Class A reference does not establish comparable quote units.',
    decision: 'DO NOT COMPARE AS LIKE-FOR-LIKE',
    next: 'Establish each token’s effective unit for the relevant chain and venue, then verify the CMC quote-unit basis before naming a cheaper route.',
    sources: [
      { label: 'CMC paired capture · 28 Sep', url: 'https://bell.dyplux.com/proof/rwa-surface-integrity-capture-2026-09-28.json' },
      { label: 'Open pair-review JSON receipt', url: 'https://bell.dyplux.com/proof/alphabet-class-a-pair-review-2026-09-29.json' },
      { label: 'Ondo page observation excerpt · 29 Sep', url: 'https://bell.dyplux.com/proof/ondo-googlon-page-capture-2026-09-29.txt' },
      { label: 'Backed · Alphabet xStock', url: 'https://assets.backed.fi/products/alphabet-xstock' },
      { label: 'xStocks · dividends and splits', url: 'https://docs.xstocks.fi/docs/dividends-and-stock-splits' },
      { label: 'Ondo · GOOGLon asset page', url: 'https://app.ondo.finance/assets/googlon' },
    ],
  },
};

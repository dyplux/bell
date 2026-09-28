// Issuer-published, product-level documentation surfaced beside CMC quote rows.
// These summaries are navigation aids, not independent verification or legal advice.
window.BELL_ISSUER_EVIDENCE = [
  {
    match: /backed assets/i,
    issuer: 'Backed Assets / xStocks',
    structure: 'Tracker certificate',
    facts: [
      'Issuer documentation describes 1:1 collateralization and no shareholder voting rights.',
      'Dividends are reinvested and reflected through a balance multiplier; one token need not remain equal to one share.',
    ],
    scope: 'Product-level documentation. Open the asset-specific Final Terms before treating this as the exact GOOGL instrument contract.',
    sources: [
      { label: 'Product legal overview', url: 'https://docs.xstocks.fi/docs/product-legal-overview' },
      { label: 'xStocks FAQ', url: 'https://docs.xstocks.fi/docs/frequently-asked-questions' },
      { label: 'Backed legal documents', url: 'https://assets.backed.fi/legal-documentation' },
    ],
  },
  {
    match: /ondo assets/i,
    issuer: 'Ondo Global Markets',
    structure: 'Total-return tracker',
    facts: [
      'Ondo says one token does not necessarily equal one share; reinvested dividends can change exposure per token and its displayed price.',
      'Ondo describes full backing, but says holders do not receive direct title, voting rights or statutory information rights in the underlying security.',
    ],
    scope: 'Platform-level overview. Ondo says each asset has its own prospectus and offering documents; those terms were not independently checked here.',
    sources: [
      { label: 'Ondo Stocks overview', url: 'https://docs.ondo.finance/ondo-stocks/overview' },
      { label: 'Ondo legal and offering documents', url: 'https://app.ondo.finance/' },
    ],
  },
  {
    match: /^robinhood$/i,
    issuer: 'Robinhood Europe',
    structure: 'Derivative contract',
    facts: [
      'Robinhood describes its GOOGL Classic Stock Token as a derivative contract and says holders do not own the underlying stock or receive its shareholder rights.',
      'Robinhood says Classic Stock Tokens cannot currently be sent to other wallets or platforms.',
    ],
    scope: 'Issuer GOOGL listing plus the Classic Stock Tokens FAQ. Check the current KID and customer agreement for account-specific terms.',
    sources: [
      { label: 'Alphabet Class A product page', url: 'https://robinhood.com/eu/en/crypto/GOOGL/' },
      { label: 'Classic Stock Tokens FAQ', url: 'https://robinhood.com/eu/en/support/articles/stock-tokens-faq/' },
    ],
  },
];

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ids = [
  'terminal-source', 'terminal-state', 'terminal-asset-name', 'terminal-asset-meta',
  'terminal-asset-stats', 'terminal-brief-kicker', 'terminal-brief-title',
  'terminal-brief-type', 'terminal-brief-body', 'terminal-brief-points',
  'terminal-brief-limit', 'terminal-download-brief', 'terminal-flow-underlying', 'terminal-flow-tokens',
  'terminal-flow-issuers', 'terminal-flow-output'
];
const nodes = Object.fromEntries(ids.map(id => [id, {
  textContent: '', innerHTML: '', className: '', addEventListener() {},
  setAttribute() {}
}]));
const context = vm.createContext({
  window: {},
  document: {
    addEventListener() {},
    querySelectorAll() { return []; },
    getElementById(id) { return nodes[id]; }
  }
});
vm.runInContext(fs.readFileSync(path.resolve(__dirname, '../site/terminal.js'), 'utf8'), context);

test('universal terminal treats a single token as a dossier', () => {
  context.window.BELL_TERMINAL.render({ id: 'spy', name: 'SPDR S&P 500 ETF Trust', symbol: 'SPY', category: 'Exchange Traded Funds', rank: 86, has_tokens: true, last_historical_data: '2026-09-11T23:55:00Z' }, {
    asset: { name: 'SPDR S&P 500 ETF Trust', symbol: 'SPY', has_tokens: true },
    tokens: [{ crypto_id: 1, symbol: 'SPYx', issuer_name: 'Example' }],
    issuers: [{ name: 'Example' }],
    market_pairs: []
  });
  assert.equal(nodes['terminal-state'].textContent, '1 TOKEN / DOSSIER');
  assert.equal(nodes['terminal-flow-output'].textContent, 'Dossier');
  assert.match(nodes['terminal-brief-body'].textContent, /returned 1 token representation/i);
});

test('universal terminal exposes multi-token comparison mode', () => {
  context.window.BELL_TERMINAL.render({ id: 'gold', name: 'Gold', symbol: 'GOLD', category: 'Commodities', rank: 1, has_tokens: true }, {
    asset: { name: 'Gold', symbol: 'GOLD', has_tokens: true },
    tokens: Array.from({ length: 7 }, (_, index) => ({ crypto_id: index + 1, symbol: `GOLD${index}`, issuer_name: `Issuer ${index}` })),
    issuers: Array.from({ length: 7 }, (_, index) => ({ name: `Issuer ${index}` })),
    market_pairs: []
  });
  assert.equal(nodes['terminal-state'].textContent, '7 TOKENS / COMPARE');
  assert.equal(nodes['terminal-flow-tokens'].textContent, '7 tokens');
  assert.equal(nodes['terminal-flow-output'].textContent, 'Compare');
  assert.match(nodes['terminal-brief-title'].textContent, /comparison/i);
});

test('universal terminal keeps no-token assets in underlying mode', () => {
  context.window.BELL_TERMINAL.render({ id: 'future-asset', name: 'Future Asset', symbol: 'FUT', category: 'Stocks', rank: 500, has_tokens: false });
  assert.equal(nodes['terminal-state'].textContent, 'NO TOKEN MAPPED');
  assert.equal(nodes['terminal-flow-output'].textContent, 'Monitor');
  assert.match(nodes['terminal-brief-body'].textContent, /no token representation/i);
});

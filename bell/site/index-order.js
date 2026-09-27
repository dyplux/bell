/* How the reference index is ordered, and what an export of it contains.

   Kept out of integrity.js so it can be driven by a test rather than by a
   browser. The rule that matters is the one about absence: a reference with no
   published comparison has no observed spread, and it sorts last rather than
   as zero. A missing measurement is not a tight one, which is the distinction
   this whole product exists to make. Sorting it as zero would have put every
   unmeasured reference at the top of "tightest spread first" and read as a
   clean bill of health for the rows Bell knows least about. */
(function (root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.BellIndexOrder = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  const ORDERS = ['severity', 'spread-desc', 'spread-asc', 'representations'];

  function spreadOf(item) {
    // Not Number(raw): Number(null) and Number('') are both 0, which is a
    // finite number, so an absent spread would have sorted as the tightest one
    // in the catalogue. The receipt writes this field as a JSON number or not
    // at all, so anything else is absence.
    const raw = item && item.comparison ? item.comparison.spread_bps : undefined;
    return typeof raw === 'number' && Number.isFinite(raw) ? raw : null;
  }

  function representationsOf(item) {
    const value = Number((item && (item.token_count ?? item.representations)) || 0);
    return Number.isFinite(value) ? value : 0;
  }

  function orderIndex(items, sortBy) {
    const list = Array.isArray(items) ? items.slice() : [];
    if (sortBy === 'representations') {
      return list.sort((a, b) => representationsOf(b) - representationsOf(a));
    }
    if (sortBy !== 'spread-desc' && sortBy !== 'spread-asc') return list;
    const direction = sortBy === 'spread-asc' ? 1 : -1;
    return list.sort((a, b) => {
      const left = spreadOf(a);
      const right = spreadOf(b);
      if (left === null && right === null) return 0;
      if (left === null) return 1;
      if (right === null) return -1;
      return (left - right) * direction;
    });
  }

  const HEADER = ['rwa_id', 'reference_name', 'reference_symbol', 'asset_type', 'route',
                  'representations', 'issuers', 'observed_spread_bps', 'cheapest_route_symbol',
                  'cheapest_route_issuer', 'cheapest_is_deepest', 'tradable_routes'];

  function exportRow(item, routeLabel) {
    const c = item && item.comparison;
    const routes = c && Array.isArray(c.routes) ? c.routes : [];
    const cheapest = routes.find(route => Number(route.premium_to_cheapest_bps || 0) === 0) || routes[0];
    const spread = spreadOf(item);
    return [
      item.rwa_id,
      item.name,
      item.symbol,
      item.asset_type,
      routeLabel,
      representationsOf(item) || '',
      Number(item.issuer_count || 0) || '',
      // Empty, not 0: the column says what was observed, and nothing was.
      spread === null ? '' : spread.toFixed(1),
      c && cheapest ? (cheapest.symbol || '') : '',
      c && cheapest ? (cheapest.issuer_name || '') : '',
      c ? (c.cheapest_is_deepest ? 'yes' : 'no') : '',
      c && c.route_count != null ? c.route_count : '',
    ];
  }

  return { ORDERS, HEADER, orderIndex, exportRow, spreadOf, representationsOf };
});

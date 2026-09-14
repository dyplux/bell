/* The generated map is a credential-free build artifact. Keep the illustrative fallback so
   index.html still works if catalogue-live.js has not been generated yet. */
(() => {
  const categoryLabel = value => String(value || 'other').replace(/[_-]+/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
  const live = window.BELL_CATALOGUE_LIVE;
  const fallback = [
    { id: 'tesla', name: 'Tesla', symbol: 'TSLA', category: 'Equities', analysis_id: 'tesla', description: 'Explore tokenised Tesla wrappers and compare their movement across the reference market clock.' },
    { id: 'gold', name: 'Gold', symbol: 'XAU', category: 'Commodities', analysis_id: 'gold', description: 'Compare seven tokenised Gold wrappers across the traditional market clock.' },
    { id: 'silver', name: 'Silver', symbol: 'XAG', category: 'Commodities', analysis_id: null, description: 'Select this reference to inspect its tokenised asset dossier. Session research is not bundled yet.' }
  ];
  const assets = live?.assets?.length
    ? live.assets.filter(asset => asset.slug || asset.rwa_id).map(asset => ({
      id: String(asset.slug || asset.rwa_id),
      name: asset.name || String(asset.slug || asset.rwa_id),
      symbol: asset.symbol || '—',
      category: categoryLabel(asset.asset_type),
      analysis_id: asset.slug === 'tesla' ? 'tesla' : asset.slug === 'gold' ? 'gold' : null,
      rwa_id: asset.rwa_id,
      has_tokens: asset.has_tokens,
      rank: asset.rwa_rank,
      description: asset.slug === 'tesla'
        ? 'Explore the Tesla wrapper grouping and the bundled seven-day session review.'
        : asset.slug === 'gold'
          ? 'Explore the Gold wrapper grouping and the bundled seven-day session review.'
          : 'CMC RWA catalogue entry. Open the dossier to see what is known and whether session research is available.'
    }))
    : fallback;
  window.BELL_CATALOGUE = {
    schema_version: 'bell.catalogue.v1',
    mode: live?.assets?.length ? 'live_map_snapshot' : 'illustrative_demo',
    total_size: live?.total_size || assets.length,
    assets
  };
})();

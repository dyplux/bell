# Bell public source map

This is the shortest route from the live product to the implementation and the
credential-free proof for a reviewer who wants to inspect the build quickly.

## User-facing route

- `site/index.html` contains the single public product page and its accessible controls
- `site/integrity.js` loads the dated `/api/integrity` receipt, renders decisions and exports the brief and `bell.case-receipt.v1`
- `site/integrity.js` also exports a row-level population attribution CSV with stable reference, token and issuer IDs; positive, missing and non-positive market-cap states stay distinct
- `site/capital-impact.js` contains the deterministic capital scenario calculation used by the blocked-case panel
- `site/catalogue.js` and `site/catalogue-live.js` contain the complete-map discovery path
- `site/research-brief.js` generates the downloadable research brief from the displayed snapshot

## Population receipt path

- `rwa_integrity.py` collects and joins the authenticated CMC surfaces
- `population_attribution()` reconciles positive token-level market caps with CMC's asset-level `tokenized_market_cap` field and computes issuer concentration without converting missing values to zero
- `rule_calibration()` publishes the observed population around Bell's 2x dispersion and 10x denomination boundaries, so the thresholds can be inspected rather than treated as unexplained constants
- `integrity_publisher.py` publishes only the normalized credential-free receipt
- `verify_integrity_receipt.py` recomputes the public population summary from committed normalized inputs
- `verify_catalogue_receipt.py` checks the complete-map catalogue refresh
- `verify_case_receipt.py` checks a case JSON downloaded from the public page

## Exact CMC surfaces

| Surface | Endpoint |
| --- | --- |
| Reference map | `/v5/real-world-assets/map` |
| Token asset list | `/v5/real-world-assets/assets/list` |
| Token information | `/v5/real-world-assets/info` |
| Latest RWA quotes | `/v5/real-world-assets/quotes/latest` |
| Issuer catalogue | `/v5/real-world-assets/issuers/list` |
| Market pairs, when used by the audit path | `/v5/real-world-assets/market-pairs/list` |
| Hourly movement context | `/v2/cryptocurrency/ohlcv/historical` |
| CEX and DEX quote context | `/v2/cryptocurrency/quotes/latest` |

The public page does not call CMC directly and never receives the API key.

The population attribution is descriptive rather than a score. It reports the
positive token rows, missing and zero rows, top issuer-label shares, HHI and
effective issuer count, then reconciles matched `rwa_id` rows across the quote
and asset-list surfaces. It does not prove backing, reserves, redemption,
legal liability, liquidity or execution.

The rule calibration is also descriptive. It counts references in observed price
bands around the two deterministic boundaries. It is not a statistical threshold
fit, a fair-value estimate or an execution measure.

## Reproduce the proof without credentials

From the repository root:

```sh
python3 bell/verify_integrity_receipt.py
python3 bell/verify_catalogue_receipt.py
python3 bell/verify_case_receipt.py /path/to/downloaded-case-receipt.json
python3 bell/verify_rule_boundaries.py
PYTHONPATH=bell python3 -m unittest discover -s bell/tests -p 'test_*.py' -q
```

The public page also exposes `Download attribution CSV` in the population lens. The
export is a convenience view over the published receipt, not a second data source;
its header records the same `rwa_id`, `crypto_id` and `issuer_id` joins used by the
deterministic population calculation.

The case verifier checks the receipt contract, stable join keys, token-row count,
source fingerprints and explicit limits. It does not certify backing, liquidity,
redemption, custody, eligibility or execution.

`verify_rule_boundaries.py` is a credential-free executable specification of the
critical decision edges. It proves that 9.99x remains an investigation warning,
that 10x is an inclusive comparison stop, that a single representation does not
produce a wrapper ranking, that missing or zero prices do not create a ratio, and
that unresolved versus resolved `crypto_id` joins remain visible, including
chain and contract fields.

## What is evidence and what is not

- `site/proof/` contains dated normalized receipts and replay inputs
- `site/proof/rule-boundary-verifier-2026-09-22.json` is the checked-in output of the credential-free rule harness
- `/api/integrity` is the current published population observation
- the browser and Python checks prove the public workflow and deterministic transformations
- upstream CMC correctness and real-world legal, custody or execution claims remain outside this build

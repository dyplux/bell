# Bell public source map

This is the shortest route from the live product to the implementation and the
credential-free proof for a reviewer who wants to inspect the build quickly.

## User-facing route

- `site/index.html` contains the single public product page and its accessible controls
- `site/integrity.js` loads the dated `/api/integrity` receipt, renders decisions and exports the brief and `bell.case-receipt.v1`
- `site/capital-impact.js` contains the deterministic capital scenario calculation used by the blocked-case panel
- `site/catalogue.js` and `site/catalogue-live.js` contain the complete-map discovery path
- `site/research-brief.js` generates the downloadable research brief from the displayed snapshot

## Population receipt path

- `rwa_integrity.py` collects and joins the authenticated CMC surfaces
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

## Reproduce the proof without credentials

From the repository root:

```sh
python3 bell/verify_integrity_receipt.py
python3 bell/verify_catalogue_receipt.py
python3 bell/verify_case_receipt.py /path/to/downloaded-case-receipt.json
PYTHONPATH=bell python3 -m unittest discover -s bell/tests -p 'test_*.py' -q
```

The case verifier checks the receipt contract, stable join keys, token-row count,
source fingerprints and explicit limits. It does not certify backing, liquidity,
redemption, custody, eligibility or execution.

## What is evidence and what is not

- `site/proof/` contains dated normalized receipts and replay inputs
- `/api/integrity` is the current published population observation
- the browser and Python checks prove the public workflow and deterministic transformations
- upstream CMC correctness and real-world legal, custody or execution claims remain outside this build

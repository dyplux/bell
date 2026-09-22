# Public submission gate

Run this before exporting or submitting the repository:

```sh
python3 bell/verify_submission.py
python3 bell/verify_doc_links.py
```

Run it from the clean public export or clone that will be submitted. The
private development workspace intentionally contains files that are not part
of the public repository, so the gate must inspect the export's Git index.

The gate checks the Git index, not just the files visible in the working tree.
It verifies that the public build contains the website, explorer, receipts,
verifiers, deployment adapter and judge path, while excluding private jury
material, competitor dossiers, credentials and internal identity disclosures.

It also checks that the public interface uses one decision vocabulary:

- `DO NOT SHORTLIST`
- `INVESTIGATE`
- `FACTS OPEN`
- `SINGLE REPRESENTATION`

This gate is complementary to the test suite and the live smoke check. It does
not claim that the product is an investment recommendation or that a public
receipt proves backing, liquidity, redemption or execution.

## Hackathon submission checklist

The public submission surface is the Real World Assets track and uses one
product URL:

- Demo: <https://bell.dyplux.com/>
- Repository: <https://github.com/dyplux/bell>
- Track: Real World Assets
- Video: upload the credential-free walkthrough produced by `bell/record_demo.py`
- DoraHacks submission: add the final public BUIDL URL before publishing
- X post: link the DoraHacks submission and the demo video, then include `#BuildwithCMC`

The build names the CoinMarketCap surfaces it uses in [JUDGE.md](JUDGE.md):

- `/v5/real-world-assets/map`
- `/v5/real-world-assets/assets/list`
- `/v5/real-world-assets/quotes/latest`
- `/v5/real-world-assets/info`
- `/v5/real-world-assets/issuers/list`
- `/v2/cryptocurrency/info`
- `/v2/cryptocurrency/ohlcv/historical`
- `/v2/cryptocurrency/quotes/latest`

The public page exposes the result of a real server-side CMC collection through
the live receipt, source fingerprints, collection note and credential-free
replay inputs. The API makes the RWA map, wrapper grouping, issuer joins and
quote fields available; its limits are preserved as visible unresolved states
when coverage, market pairs or legal and execution evidence are unavailable.

Suggested X copy after replacing the two bracketed links:

> Tokenised assets can share a reference and still move on different clocks. Bell checks identity, unit, coverage and market state before an investor compares wrappers, then turns live CMC RWA data into a dated decision and receipt. Demo: https://bell.dyplux.com/ Submission: [DoraHacks URL] Video: [demo video URL] #BuildwithCMC

Do not publish the copy until `[DoraHacks URL]` and `[demo video URL]` have been replaced with the final public links.

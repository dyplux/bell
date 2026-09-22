# Bell demo video

Target length: 100 to 110 seconds. This is a product demonstration, not a
promise that the browser can make arbitrary authenticated CMC calls. Show the
live integrity monitor, its freshness badge and the receipt link.

## Before capture

Run `python3 bell/prepare_demo.py --reference Silver` immediately before
recording. Use its observed timestamp, route, ratio and endpoint labels in the
shots below. Never carry values forward from an earlier receipt.

To create current visual frames for Hyperframe, run:

```bash
PYTHONPATH=bell python3 bell/capture_demo.py --output /tmp/bell-demo-capture
```

The output contains a `manifest.json` with the receipt timestamp and frame
labels. The capture fails if the browser emits console errors.

## Story

An investor finds several tokens under the same stock, ETF or commodity. The
first question is not which wrapper wins. It is whether the wrappers deserve a
fair comparison at all.

## Shot list

| Time | Screen / wireframe | Voice and on-screen message |
|---|---|---|
| 0 to 5s | Dark hero, Bell mark, `Before you compare, check the wrapper` | “CMC can show you the candidates. Bell checks whether the grouping is safe to compare.” |
| 5 to 14s | Hero search with `Silver` entered | “Start with the asset you are researching. No account and no trading signal.” |
| 14 to 28s | Silver result: `5 representations · 4 issuers · [current observed ratio]`, endpoint panel and compact capital route | “Silver has five representations from four issuers. Bell shows the lowest and highest observed quote rows, their issuers and the ratio that changes the research route. The capital route makes the immediate consequence clear: keep the example amount uncommitted until the contradiction is resolved.” |
| 28 to 42s | Outcome key and evidence drawer | “Bell changes the route to `DO NOT SHORTLIST`. It shows the affected rows, identity path, timestamp and contradiction.” |
| 42 to 54s | Next-action handoff | “The next step is explicit: resolve unit, wrapper claim and quote identity, then verify issuer, redemption and execution.” |
| 54 to 68s | Search `Marvell`, open factual rows | “When no critical Bell rule fires, the route is different. Marvell opens a facts-only comparison without declaring a winner.” |
| 68 to 78s | Decision brief and local worksheet | “The investor exports a brief containing the state, evidence, unresolved questions and next diligence step.” |
| 78 to 88s | Explore RWA, search `Gold`, open the published dossier | “The dossier makes the data boundary visible. It shows network identity, DEX contract coverage, resolved pools, security and holder surfaces, and whether CMC market pairs were available.” |
| 88 to 98s | Scroll to `POPULATION SHAPE` and `OBSERVED QUOTE SPREAD` | “Bell also shows the shape of the full scan. The published receipt separates comparable references from rows without two positive prices, then shows how many sit in each observed spread band.” |
| 98 to 105s | Search `Colgate` and open the reference-only map route | “A reference without a published token case is not treated as a failure. Bell routes it to the complete RWA map and keeps the reference-only result explicit.” |
| 105 to 110s | Receipt JSON, freshness badge and public URL | “Every result is tied to a dated receipt. Bell is an integrity gate around CMC data, not a replacement for CMC or a buy recommendation.” |

## Proof frames

- Show the live `FRESH` badge and observed timestamp
- Show the exact Silver state and the current observed ratio from the receipt
- Keep the `OBSERVED QUOTE ENDPOINTS` panel on screen long enough to read the low
  and high symbols, issuer labels and values
- Open an evidence drawer so the video proves this is not a static slogan
- Show Marvell as the contrasting `FACTS OPEN` route
- Show the exported brief or worksheet
- Show the Gold dossier's `EVIDENCE CONTEXT` panel and its market-pair boundary
- Show the population chart using the published calibration counts, including the
  references that remain outside the spread chart because they lack two positive prices
- Show the map-only handoff and its reloadable `map_reference` URL
- End on the public monitor and `/api/integrity` receipt

## Claims the narrator must not make

- Bell does not prove backing, redemption, custody, eligibility, solvency or executable liquidity
- `FACTS OPEN` is not approval and does not rank a wrapper
- The public monitor does not expose the CMC API key or promise arbitrary live queries for every asset
- Read the Silver ratio from the live receipt immediately before recording; never hardcode a value from an earlier capture
- Read the endpoint symbols and issuer labels from the live receipt immediately
  before recording; the values can change between publications
- The ratio is an observed surface contradiction, not proof of fraud or an investment loss

## Hyperframe production notes

Use large typography and real interface crops. Keep the first frame to one
sentence and one visual question. Use a split-screen only for the CMC versus
Bell distinction. Let the evidence and next action occupy the whole frame.
The final cut should work without sound by keeping state labels and next action
visible for at least two seconds.

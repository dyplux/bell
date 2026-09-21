# Bell through an investor's eyes

Assessment date: 13 September 2026. Based on the inspected Bell implementation, its saved Gold receipt and official issuer material linked below. This is a realistic hypothetical decision, not an interview, an actual client mandate or a completed investment recommendation. Monetary amounts and operating limits below are scenario assumptions.

## Verdict before the story

Bell today is a useful prototype for comparing reported wrapper price behaviour and preparing a reproducible research observation. It is not yet a complete investment product. I could use it to decide what to investigate next. I could not use it to approve a wrapper, choose an execution venue, or establish whether buying this weekend is preferable to waiting.

The strongest near-term customer hypothesis is an analyst who repeatedly prepares tokenised-asset reviews. A one-off investor may need eligibility, costs and a usable route more urgently than session statistics. That distinction should determine what we build next.

## One decision: can our desk obtain gold exposure this Sunday?

It is Sunday, 13 September 2026, at 12:00 UTC, after the saved Bell Gold observation window ends. I am the analyst at a small investment desk. My portfolio manager has provisionally approved investigating a USD 100,000 gold allocation. The allocation thesis comes from the manager; Bell has not established that gold will hedge the portfolio or rise in price.

The desk has USD-equivalent stablecoin funding and existing exchange and custody relationships. Its mandate permits fully backed tokenised gold subject to instrument approval, but excludes leveraged and synthetic exposure for this allocation. Existing accounts do not establish approval for any particular token, chain or route. The manager wants a research recommendation by 15:00 UTC and would prefer exposure before the next conventional trading opportunity if a suitable route exists. Waiting remains an acceptable outcome.

My question is:

> Can we obtain and later unwind USD 100,000 of permitted tokenised gold through an accessible route this weekend, at a defensible cost? Which candidates require investigation, and what evidence is still missing before we approve one?

The unit of comparison is the instrument, chain, venue and account route together. A token symbol by itself cannot answer that question.

This is a real operating distinction. Paxos's support page distinguishes its PAXG mint/redeem pricing route, subject to specified gold-market hours, from order-book trading under its Trade tab, which it describes as available 24/7. That does not prove my account has access, that a particular venue is operating normally, or that USD 100,000 can execute at an acceptable price. It shows why token trading availability and issuer conversion availability need separate fields. [Paxos price determination](https://support.paxos.com/articles/7818174259-pax-gold-price-determination)

## The decision walkthrough

### 1. Establish what I am allowed to buy

I need the instrument's legal claim, backing model, units per token, issuer, contract and chain, eligibility for my entity, custody compatibility, redemption conditions and approved venues. Unknown eligibility means unresolved, not eligible.

Today, Bell lets me search Gold and view seven entries in the CMC grouping. The public review supplies names, issuer labels and session metrics. It does not establish those seven entries as approved substitutes. The optional local dossier supplies additional CMC fields where available, but does not perform instrument due diligence.

The saved receipt labels one entry `XAU` with issuer `NA (Derivatives)`. That is enough to flag it for exclusion pending verification under this mandate; it is not an independent legal classification. I must also verify whether similarly named entries are native instruments, bridged representations or other exposures before comparing their suitability.

Unit differences are concrete: Paxos describes PAXG as representing one fine troy ounce, while ComTech's whitepaper describes CGO as representing one gram of gold. Bell's percentage range calculation avoids comparing raw token prices, but any future price or premium comparison must normalise the gold quantity and relevant specification. These are issuer descriptions, not Bell attestations of backing. [Paxos product description](https://www.paxos.com/pax-gold), [ComTech whitepaper](https://www.comtechgold.com/assets/pdf/cgo_whitepaper_v1.pdf)

**Decision effect:** the seven search results become a discovery list requiring classification. Bell does not yet supply an investable shortlist. If the desk cannot establish an approved route, the process stops here regardless of the chart.

### 2. Check whether Bell's observation applies to my decision

I open the published Gold review and its receipt. The saved window is 6 September 2026 at 10:00 UTC through 13 September at 10:00 UTC: 168 hourly bars per entry, with 30 assigned to `cash`, 90 to `after_hours`, and 48 to `weekend`.

This is a historical dataset ending two hours before my hypothetical review. It contains no current executable quote. The public website does not make new CMC calls when I search or open the page. An unrelated search such as IBKR returns a map entry if present, not a new public analysis.

Bell uses weekday 09:30 to 16:00 in `America/New_York` as its cash bucket. For Gold, this is a comparison clock, not a verified gold-market session. The after-hours bucket also contains overnight and pre-market hours. Weekend bars in this rolling window span portions of two calendar weekends, so the 48 observations are not two independent weekend experiments.

**Decision effect:** I can use this dataset as historical context. I cannot treat its labels as proof that the relevant market or issuer route was open or closed at each timestamp.

### 3. Examine the behavioural contrast

Bell calculates `(high - low) / open * 100` for each hourly bar, then takes the median within each bucket. Selected results from the saved receipt are:

| Entry | Weekday comparison-window median | Other weekday hours median | Weekend median | Weekend / weekday comparison median |
|---|---:|---:|---:|---:|
| PAXG | 0.2791% | 0.2382% | 0.0336% | 12.05% |
| XAUt | 0.2727% | 0.2251% | 0.0330% | 12.08% |
| XAUM | 0.3655% | 0.3198% | 0.1713% | 46.86% |
| CGO | 0.5085% | 0.4908% | 0.4708% | 92.59% |

Ratios above are calculated from unrounded receipt medians, then rounded to two decimals. The website uses rounded summary inputs and approximate ratios. Source: [Gold receipt](docs/proof/gold-live-2026-09-13.json), with [normalised replay inputs](docs/proof/gold-live-2026-09-13.payload.json).

CGO's larger reported weekend range prompts a venue and data-quality investigation. It does not prove worse tracking, greater risk, better liquidity or a trading opportunity. PAXG's narrower range could coexist with accessible trading, stale prices or sparse observations. These are alternative explanations requiring evidence, not findings of this run. Hourly coverage does not establish the number or quality of underlying trades.

The receipt also contains latest 24-hour CEX/DEX volume context. Those aggregates do not reveal which route I can use or what it costs to trade on Sunday. In particular, a small latest volume number is not a measured ceiling on executable depth.

**Decision effect:** if CGO is otherwise eligible, I prioritise checking its source venues and contemporaneous prices before treating it as interchangeable with another candidate. I do not promote PAXG or XAUt to an approved buy because their bars look quieter.

### 4. Ask what the order would actually cost

For each eligible route I need fresh bid and ask prices, depth or a size-specific quote for USD 100,000, trade and settlement fees, funding conversion costs, chain costs where applicable, quote expiry, and an exit route. A firm RFQ and an indicative order-book estimate must be distinguished.

I also need an appropriate gold reference, its timestamp and unit. When that reference is closed or stale, a difference from its last observation is a premium to a dated reference, not a proven mispricing or executable arbitrage. A Sunday token quote cannot reveal an unobserved live underlying fair value.

Bell currently supplies none of this execution comparison. Its range metric cannot estimate my purchase cost, loss on an immediate unwind or Monday tracking difference. For scale only, an assumed 50-basis-point all-in entry cost on USD 100,000 would be USD 500. That is arithmetic illustrating the missing decision variable, not a measured Bell quote or a recommended limit.

**Decision effect:** Bell cannot answer buy now versus wait. I request route-specific information through the desk's existing channels. If it remains unavailable, the investment recommendation remains pending. That outcome follows missing execution and approval evidence, not a Bell finding that weekend buying is unsuitable.

### 5. Write the decision record

The defensible memo today would say:

> No wrapper has been approved from this review alone. Bell's saved Gold dataset shows differences in median hourly ranges across CMC-grouped entries. We will investigate the CGO contrast if it passes instrument eligibility checks, verify the classification of the derivative-labelled XAU entry, and obtain size-specific entry and exit information for approved routes. The data does not establish a preferred wrapper or justify a weekend execution. Approval remains pending those checks.

The receipt and replay inputs can support the numerical observation. They cannot substantiate missing legal or venue conclusions. `ready` in the receipt means the calculation meets the current coverage rules; it does not mean ready to invest. XAU is `ready` for the calculation while its venue composition is unavailable, illustrating why those statuses need separation.

**What changed:** the research queue became more specific and the memo gained traceable evidence. The capital allocation did not change. An experienced analyst might already perform these checks without Bell; time saved and incremental insight remain unmeasured.

## Is that useful enough?

For the investment desk's full Sunday decision, no. Bell covers historical behavioural triage and part of the evidence trail. Instrument qualification, executable cost, benchmark interpretation and operational access dominate the approval decision and remain external.

For a researcher producing recurring wrapper comparisons, possibly. Gathering the grouping, aligning bars, documenting coverage and preserving inputs is repeatable work. Bell can package it, but two published examples and a local live server do not yet establish a recurring service or willingness to pay.

For an already approved buy-and-hold investor using one established route, the current session table may add little. If user testing shows that researchers also see the table as interesting but never reuse it, Bell should remain an internal Dyplux research instrument. A larger catalogue alone would not resolve that result.

The missing ingredient is not a more persuasive origin story. It is evidence that a defined user completes a worthwhile task better with Bell.

## Exact product changes, in order

These are proposed changes, not implemented features. Work should first make the narrow research task reliable, then test whether execution-oriented expansion is justified.

| Priority | Change | Required behaviour and completion check |
|---|---|---|
| P0 | Bind every visual to its evidence | Keep the current nine-entry Tesla session view and the population monitor bound to their declared dated receipts. Session visuals must link to a payload when bars are published; the population view must label its summary and source fingerprints clearly. Recomputing a session payload must reproduce the displayed values under declared rounding. |
| P0 | Separate identity from comparability | Add a reviewable record for CMC ID, contract/chain, issuer, instrument type, units, native/bridged relationship and primary-source links with checked dates. Keep unverified and derivative-labelled entries visible with explicit classification status. Do not silently include them in a physically backed shortlist. Eligibility must be route/entity specific, not inferred from a country label alone. |
| P0 | Make the clock accurate and visible | Rename Gold's current buckets as a New York comparison convention. Introduce versioned calendars for the chosen benchmark and issuer route, including holidays, maintenance and Sunday reopening. Keep token venue hours separate. Flag hourly bars crossing boundaries instead of presenting them as clean session measurements. Test boundary, holiday and daylight-saving examples against the chosen calendar. |
| P0 | Expose evidence adequacy | Distinguish calculation coverage, history availability, freshness, identity verification and execution availability. Show counts, gaps, invalid bars and absent venue information. Reject bars outside the requested window and flag inconsistent OHLC bounds before computing statistics. The current engine needs these checks; complete counts alone are insufficient validation. |
| P1 | Provide a repeatable public research run | Support an explicitly selected asset and window through a server-side service with a dated cache and budget limits. Return the completed receipt or a specific partial/unavailable/error state. Show cache age and retrieval time. A map-only asset must remain usable without implying missing history has been established. Validate Gold and at least one previously map-only asset end to end, retaining all unavailable wrappers. |
| P1 | Compare repeated windows and preserve the analyst's conclusion | Add selected-wrapper comparison, at least four non-overlapping complete weekends where data permits, matched weekday context, and per-window distributions, flat-bar diagnostics and coverage. Four weekends are a minimum exploration target, not statistical validation. Export a memo containing the question, observation, unresolved explanations, follow-up and exact evidence links. Never interpret flat bars alone as stale trading. |
| P2, conditional on demand | Add route and size evidence | Let the analyst specify notional, funding asset, chain and approved venue. Integrate a verified quote/depth or RFQ source for at least two eligible routes, with entry and exit cost estimates, timestamps, expiry and fee assumptions. Confirm source access, licensing and actual fields first; CMC aggregate OHLCV is insufficient for this feature. Missing data must yield `execution evidence unavailable`, not a score. |
| P2, conditional on demand | Add a unit-correct reference comparison | Obtain a licensed reference series, identify its instrument and market hours, normalise units and quote currencies, and align timestamps. When closed, label the comparison as against a last available reference and display its age. Suppress any claim of current fair value. Replay must reproduce the normalisation and premium calculation. |

Avoid adding an opaque wrapper quality score before these inputs exist. Its appearance of decisiveness would exceed the evidence. A broader investment product would also need continued instrument, custody and issuer diligence; adding a quote feed alone would not complete it.

## Testable user hypothesis

> Analysts who already prepare recurring tokenised-asset reviews can use Bell to produce an evidence-backed weekend wrapper triage memo at least 30% faster than their existing tools, without making more unsupported investment claims, and will voluntarily reuse it for another review within 14 days.

Recruit six analysts who have performed this work or a closely related instrument review. Use two comparable, unseen historical datasets and counterbalance the order: half start with Bell, half with their usual tools. Give both conditions equivalent source access and the same question, not just different interfaces with unequal evidence. Use a frozen, declared information cutoff and keep later observations out of both tasks.

Each participant must produce a short memo with a candidate classification, a numerical observation, the decision it supports, unresolved investment questions and reproducible sources. A reviewer blinded to the condition scores accuracy and usefulness. Record active completion time, requests for help, unsupported conclusions and a follow-up reuse event. Do not count a complimentary demo reaction as adoption.

### Acceptance criteria for a useful research product

1. At least five of six participants complete a correct memo within 15 minutes in the Bell condition without facilitator intervention. Across paired tasks, median time falls at least 30%, with accuracy no worse than baseline. These are proposed pilot thresholds, not measured results.
2. At least five of six correctly identify the dataset date, the Gold comparison-clock convention, an instrument-classification uncertainty and the missing execution information. All six avoid inferring liquidity, investment suitability or fair value solely from range. Any such inference triggers a copy/design revision and retest.
3. Every memo's displayed numerical claim links to the exact receipt and replay payload. A separate reviewer can reproduce all cited medians and ratios with the documented rounding, without credentials.
4. All participants encountering a map-only, missing-history or failed-request case can distinguish those outcomes. The interface never substitutes an example's numbers for the requested asset.
5. At least four of six voluntarily use Bell for a second work-relevant review within 14 days and can identify a research step it saved or a follow-up it changed. Record the resulting memo or work artifact with their consent, not just stated intention.
6. If time improves but repeat use fails, retain Bell for internal research and investigate frequency of need before broadening the feature set. If accuracy deteriorates or the apparent advantage comes only from withholding data in the baseline, the hypothesis has not passed.

### Additional gate before claiming investment-decision support

For the USD 100,000 scenario, an analyst must be able to document at least two verified eligible routes, dated instrument and account-access evidence, fresh size-specific entry and exit information, explicit fees, quote validity and the benchmark's actual status. The quote source must meet the desk's declared freshness policy; stale quotes automatically expire from the comparison.

An independent reviewer must reproduce the cost comparison and trace every assumption. Removing eligibility, quote or benchmark evidence must produce the appropriate unresolved state rather than a recommended trade. Validate that behaviour in a paper exercise without placing orders. This gate concerns decision support, not proof of profitable execution or a substitute for the desk's approval process.

## What this contributes to the Dyplux research desk

Bell can support a first research note framed as: **"What seven Gold-linked entries can and cannot tell us about weekend exposure."** Start with the investment question above, show the saved observation, explain the clock and instrument-comparability problem, and publish the exact evidence alongside the unresolved questions. Do not present this single window as a persistent weekend effect.

The next repeatable desk task is to classify those entries, collect independent windows, check the source venues behind the contrast, and record whether it survives. Every research cycle should yield a dated note or a documented null result. Bell earns a place in Dyplux if it makes that output faster and more reliable, even if it never becomes a standalone investment terminal.

This document specifies that path only. It does not launch desk operations, implement the proposed features, or publish a new investment claim.

## Evidence inspected

- [Current narrative](STORY.md), [README](README.md) and [judge guide](JUDGE.md): intended workflow and declared limitations.
- [Browser logic](site/app.js) and [published summaries](site/snapshot.js): what the current site renders, including its approximate ratios and static/live distinction.
- [Gold receipt](docs/proof/gold-live-2026-09-13.json) and [Gold payload](docs/proof/gold-live-2026-09-13.payload.json): exact observation window, medians, counts, grouping and warnings.
- [Deterministic engine](engine.py): session assignment, coverage rules, range formula and current validation boundaries.
- Official issuer pages cited at the relevant claims were retrieved for this assessment. They establish what the issuers describe, not independent verification of backing or eligibility for the hypothetical desk. No new CMC market run or investor interview was performed.

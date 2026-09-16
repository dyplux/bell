# Bell product thesis

Date: 16 September 2026

## The job to be done

An investor sees several tokens attached to the same real-world reference and
wants to know whether they can fairly compare them before spending time on a
shortlist.

Bell answers the first decision only:

> Can this reference support a fair token comparison, and what must be checked
> before an analyst treats the representations as interchangeable?

The output is deliberately operational:

- `DO NOT COMPARE`: stop the wrapper selection;
- `INVESTIGATE`: continue research, but keep the representations separate;
- `NO RULE HIT, NOT APPROVED`: no published contradiction was found, but no
  investment approval is produced.

## Why this is not another CMC table

CMC's RWA surface already provides the catalogue, stable `rwa_id`, tokenised
representations, issuers and quote fields. Bell consumes those surfaces and
checks whether they can be joined into a defensible comparison. It is not a
replacement catalogue, a safety score or an execution venue.

The current public differentiation is therefore a workflow boundary:

1. find the reference;
2. test identity, denomination and market-data consistency;
3. refuse or hold the comparison when the evidence conflicts;
4. hand the unresolved questions to issuer, eligibility, redemption, custody
   and execution diligence.

## Demand hypothesis

The first likely repeat user is an analyst or crypto investor who reviews the
same asset class more than once. A one-off user should still understand the
result in under a minute, but recurring research is the stronger commercial
signal.

Proposed pilot test:

- 6 participants with prior crypto or tokenised-asset research experience;
- one Gold, equity or ETF comparison question per participant;
- Bell and the participant's normal workflow, with equivalent evidence access;
- measure time, unsupported conclusions, help requests and a second use within
  14 days.

Success means at least 5 of 6 can explain the state, cite the receipt, identify
one missing investment input and avoid calling `NO RULE HIT` an approval.
Repeat use matters more than a positive demo reaction.

## Product invariants

Every feature must preserve these rules:

- no opaque wrapper-quality score;
- no buy, sell or allocation recommendation from CMC fields alone;
- missing data remains missing;
- a ticker is never used as identity when a stable ID exists;
- every numerical claim has a dated receipt or replay path;
- a plan limitation is visible rather than replaced by an invented liquidity
  conclusion.

## Competitive boundary checked on 16 September

The CMC RWA API documents the catalogue, issuer and quote surfaces. Public
tokenised-asset comparison products also exist, including structural comparison
and screener experiences. Bell's defensible space is narrower: a population-wide
pre-comparison gate with explicit stop/investigate states and credential-free
evidence, not a generic screener.

This claim must be rechecked before submission and before any public marketing.
It is a product hypothesis, not a claim that no adjacent product can ever add a
similar feature.

Sources checked on 16 September 2026:

- [CMC RWA API](https://coinmarketcap.com/api/real-world-assets-api/): catalogue,
  `rwa_id`, tokens, issuers, quotes and plan boundaries;
- [Asortino](https://asortino.com/): tokenised-stock and ETF screener with
  backing and custodian fields;
- [TokenizedXonChain](https://www.tokenizedxonchain.com/compare): structural
  side-by-side comparison of tokenised assets.

These products validate that discovery and structural comparison already exist.
They do not invalidate Bell's narrower pre-comparison gate, but they mean Bell
must keep proving that its population scan, stop states and receipts change a
real research decision.

## Highest-value next improvements

### P0: make the decision obvious

The public monitor now starts with an investor question, a direct asset search
and a three-part explanation of the returned decision: compare, understand the
failure, verify the next input.

### P1: prove the workflow in a browser

Add browser end-to-end coverage for search, filter, detail evidence, stale/live
state and receipt links. Publish a redacted input manifest sufficient to replay
the displayed population without the authenticated response.

### P1: make the handoff reusable

Let a user export a one-page decision brief for a reference containing the
state, evidence, timestamp, unresolved diligence questions and explicit limits.
The brief must never contain a buy recommendation.

Completed on 16 September: every indexed reference now exposes its observed
representation rows, issuer IDs and issuer website when the CMC issuer
catalogue provides one. The browser can open that evidence path and the brief
retains the wrapper rows. Single-token references use a separate handoff so the
absence of a wrapper comparison is not mistaken for approval.

The local research worksheet is the final handoff layer: it records identity,
issuer documents, backing/redemption, account eligibility/custody and execution
checks without changing Bell's deterministic state. This makes the next step
concrete while preserving the evidence boundary.

The live scan also joins each observed `crypto_id` to CMC
`/v2/cryptocurrency/info` when available. The public row can therefore expose
the CMC token page, issuer and project links, explorer paths, technical
documentation links when supplied, and chain and contract identity. Unresolved
token identity is a warning, not a clean result. These are investigation paths,
not evidence that the linked material is complete or that the contract
represents the underlying instrument.

### P2: add execution evidence only if demand and access justify it

Market pairs, venue depth, spread and size-specific costs require a plan and
source that actually provide those fields. Until then the monitor must keep
calling the gap `execution evidence unavailable`.

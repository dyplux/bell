# Bell public product brief

## The user journey

1. Search an exposure by name, symbol, slug or category.
2. Read the automatically generated plain-language or institutional brief.
3. Open the asset's evidence state: underlying-only, single-token dossier, multi-token comparison,
   or coverage pending.
4. Inspect issuer, network, contract, DEX and market-pair coverage.
5. Export a credential-free receipt with observation and publication timestamps.

## The useful difference

The CMC RWA catalogue is a strong discovery layer. Bell does not try to replace it with another
list. Bell answers the question that appears after discovery:

> Is this tokenized representation safe to compare with the other entries shown under the same
> reference asset?

The answer is produced by deterministic rules and visible evidence. Bell can say `DO NOT COMPARE`,
`INVESTIGATE`, `INSUFFICIENT EVIDENCE`, `DOSSIER` or `MONITOR`. It does not turn an empty optional
surface into zero liquidity and does not rank a single representation against imaginary peers.

## Live versus published

The public website never calls CMC directly. It reads the latest published dossier from
`/api/published?slug=<slug>`. A missing asset returns `map_only` and queues a server-side refresh.
The publisher collects current CMC evidence, runs the audit and posts a normalized dossier back to
the Cloudflare Worker. Every response exposes `observed_at`, `published_at`, freshness and source.

## Evidence boundary

CMC data can show mapped references, token rows, quotes, issuer records, market pairs, crypto
metadata and selected DEX surfaces. Bell reports those observations. It does not independently
verify reserves, legal rights, redemption, solvency, manipulation, suitability or executable size.
Those boundaries are part of the product, not a footnote.

## Public demo cases

- Gold demonstrates a multi-representation case where grouping conflicts make a direct comparison
  unsafe.
- Tesla demonstrates ticker and issuer ambiguity plus incomplete DEX coverage.

The public website labels these as dated evidence and keeps the data window visible. A public map
entry without a published dossier is never presented as a completed research case.

# Bell blind AI investor acceptance

Date: 16 September 2026

This is a usability probe, not a claim of human demand or investment
performance. The evaluator received only the public Bell page and the visible
state for a searched reference. It did not receive the product thesis, jury
reports, competitive notes or private implementation context.

## Protocol

- Model: local `qwen2.5:1.5b`, temperature `0`.
- Surface: `https://bell.dyplux.com/integrity`.
- Case: search `Silver`, open the first evidence disclosure, then answer four
  plain-language investor questions.
- Questions: what decision Bell helps with, what `COMPARISON WITHHELD` means,
  what to do next, and whether Bell says what to buy.

## Result

The evaluator correctly identified Bell as a pre-comparison gate, read
`COMPARISON WITHHELD` as a critical contradiction that stops comparison,
named identity, unit and quote resolution followed by issuer, redemption and
execution diligence, and confirmed that Bell does not recommend what to buy.

An earlier first-viewport probe inverted the meaning of `WITHHELD`. That
failure caused the public outcome key to be rewritten in explicit terms:
`COMPARISON WITHHELD = BLOCKED`, `FACTS OPEN = DESCRIPTIVE ONLY`, and
`SINGLE REPRESENTATION`. The rerun above passed after that change.

## Boundary

This result shows that the visible state language can be understood by a
small blind model. It does not prove that a human would use Bell repeatedly,
pay for it or make a better investment decision. Those questions remain in
the [human pilot protocol](HUMAN-PILOT-2026-09-16.md).

## First-viewport differentiation rerun

After the sentence `CMC shows the candidates. Bell checks whether the grouping
deserves a fair comparison.` was moved into the hero, the same blind model was
asked what CMC already does and what Bell adds. It identified CMC as the
discovery/candidate layer, Bell as the pre-comparison integrity gate, the asset
search as the first action, and the no-buy boundary. This is a comprehension
improvement against a specific CMC comparison failure mode, not a claim that
Bell replaces CMC discovery.

## Post-pagination browser check

After the complete population was made navigable in the main monitor, a fresh
Chrome check against the public page confirmed:

- page one reports `1–12 of 790` and `Page 1 of 66`;
- `Next` changes the first visible reference from Silver to SPDR Gold Trust;
- searching `Gold` renders all seven matching rows;
- the `INVESTIGATE` filter resets its matching set; and
- the 390px viewport has no horizontal overflow or browser errors.

The neutral queue remains an independent replay surface, not a required escape
hatch for browsing the rest of Bell's population.

## Fresh blind investor pass

On 16 September, the same local evaluator was given only the visible hero and
the Silver case, without the product dossier or the CMC/API research context.
It correctly identified:

- the problem as deciding whether tokenised representations can be compared;
- CMC as the candidate/discovery layer;
- Silver as `COMPARISON WITHHELD`, requiring the comparison to stop;
- identity, unit and quote resolution as the first action; and
- issuer, redemption and execution checks as the follow-up.

It also explicitly returned no buy recommendation. A second plain-language
pass on Marvell read `FACTUAL COMPARISON OPEN` as descriptive facts requiring
external diligence, not approval. These are usability signals from a small
local model, not evidence of human demand or investment performance.

# Bell financial decision gate

Date: 17 September 2026

## Product change

Bell now asks the user for the amount they are considering and translates the
integrity result into a capital consequence.

This is intentionally not a price target, a ranking or a recommendation. It
answers a more immediate investor question:

> Should this amount be allowed into a wrapper comparison yet?

The amount is saved only in the user's browser and is copied into the local
decision brief. No amount is sent to CMC, Dyplux or an issuer.

## Routes

### Comparison withheld

Bell says to keep the amount uncommitted while identity, denomination, issuer
terms and execution evidence are resolved. If there is an observed quote range,
Bell displays its size as an integrity warning. It explicitly does not call that
range a discount, premium or saving because the rows may not represent the same
unit or claim.

### Investigate before shortlist

Bell keeps the amount provisional while the unresolved representation or market
fields are classified. The user gets a queue, not a trade instruction.

### Single representation

There is no wrapper comparison. The financial work moves to backing, redemption,
eligibility, custody and execution checks for that one representation.

### Factual comparison open

Bell can expose the observed quote difference between selected rows. That number
is marked as descriptive and non-executable. It is a prompt to verify units,
venues, size-specific quotes and settlement costs before treating it as an
economic premium.

## Why this is a real benefit

CMC already helps users discover tokenised assets. Bell makes the cost of a bad
first decision visible: a user can see the amount that should remain outside an
unresolved wrapper choice, the contradiction blocking it and the exact evidence
needed to clear it.

The product therefore creates a financial benefit through capital preservation
and avoided false comparison, without pretending that CMC quote fields prove
liquidity, backing, redemption or executable savings.

## Proof and tests

- `capital-impact.js` contains the pure deterministic assessment functions;
- six Node tests cover missing prices, zero baselines, blocked/investigate/single/facts routes and budget bounds;
- the generated invariant test runs 2,000 cases and confirms that no invalid price becomes a ratio or recommendation;
- a Playwright browser run verified Silver, a `$25,000` input, the `31.08x` observed range, no horizontal overflow at 390px and no page or console errors;
- the decision brief carries the capital route and boundary so the financial interpretation cannot disappear during export.

## Deliberate limitations

The capital amount is a user-entered scenario, not a portfolio instruction. Bell
does not know the user's suitability, tax position, jurisdiction, account,
slippage, fees or execution venue. The feature must never be described as
guaranteed savings or financial advice.

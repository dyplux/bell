# Blind investor UX audit

Date: 16 September 2026

## Persona

I am a crypto investor who understands wallets, stablecoins and token prices,
but not CoinMarketCap's RWA API. I have found two or more tokens connected to
the same stock, commodity or ETF. I want to know whether they are reasonable
comparison candidates before I research the issuer or decide what belongs on a
shortlist.

## Black-box run

Starting from the public monitor, the intended path is now:

1. read the hero question;
2. search `Silver`, `Gold`, `Tesla` or `SPY` from the first screen;
3. read the returned state and decision effect;
4. inspect the evidence and next action;
5. open the receipt and check freshness;
6. distinguish “no rule hit” from “approved”;
7. export a decision brief for a research handoff.

The browser validation confirmed the live path for `Silver`: the search was
mirrored into the queue, the matching result appeared, the decision brief
downloaded, and no page or console errors occurred. The same page had no
horizontal overflow at 390, 768 or 1440 pixels.

## Questions a normal user is expected to ask

### “Does this tell me what to buy?”

No. Bell decides whether a comparison is defensible and routes the next
diligence step. It does not approve an asset or provide a trade signal.

### “Why are two tokens for the same asset not automatically comparable?”

The wrapper can differ in issuer, unit, derivative status, identity or
market-data fields. The underlying name is not enough.

### “What does `NO RULE HIT` mean?”

None of the published Bell rules fired in this scan. It is not an approval,
backing attestation or liquidity result.

### “Can I trade the one that passed?”

Not from Bell alone. Check eligibility, legal structure, custody, redemption,
venue access, depth, spread and size-specific execution.

## Red-team findings resolved

1. The old hero described a technical monitor before stating the investor's
   question. It now starts with the shortlist decision.
2. The old first screen hid the search field below the fold. Search is now in
   the hero and is connected to the queue.
3. “Integrity” could sound like a safety or backing claim. The copy repeats the
   no-buy-approval boundary.
4. The output now has a reusable decision brief rather than ending at a table.

## Boundary

This is a black-box browser audit and red-team persona simulation, not a pilot
with six real investors and not an official hackathon score. A fresh model-based
blind jury should be run with `XAI_API_KEY` supplied only through the process
environment. No credential is stored in this repository.

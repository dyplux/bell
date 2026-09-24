# CMC API feedback from the Bell surface

Six findings from building one RWA workflow against the CMC v5 real-world-asset
family, ordered by what they cost. Each one is reproducible from the
credential-free capture shipped in this repository, and each is pinned by a test
that fails if CMC changes the behaviour. None of them is a complaint about
coverage; they are places where the contract surprised a careful caller.

## 1. `status.error_code` changes type between endpoint families

`status.error_code` arrives as the **string** `"0"` on the RWA v5 family and as
the **integer** `0` on `/v1/key/info`.

```python
if status.get("error_code"):      # reads as "an error occurred"
    raise ApiError(status)
```

That is the obvious check, and it is wrong in the worst possible direction: the
integer `0` is falsy, so the key probe passes, and the string `"0"` is truthy,
so every subsequent data call is rejected as an error. The integration appears
to authenticate and then returns nothing, which sends you looking at your key
and your plan rather than at a type.

Four other entries in this hackathon hit it independently, which makes it a
contract problem rather than six people's bug. Pinned by
`bell/tests/test_upstream_contract.py::test_error_code_is_never_assumed_to_be_an_integer`,
verified to fail when the captured shape is mutated.

**Suggested fix:** emit `error_code` as an integer everywhere, or document the
string form in the RWA reference page.

## 2. `quotes[]` is a list, not a currency-keyed map

A quote block reads naturally as `quotes["USD"]`, and that works for as long as
one currency comes back. It is a list keyed by symbol, so the mapping read
breaks the first time two currencies are returned — in production, not in
development. The failure is silent because the wrong currency is still a number.

## 3. A missing market cap is `null`, and `null` is not `0`

646 of 791 tokenised references in the 21 September capture are missing at least
one market field. Coercing `null` to `0` turns "we do not know" into "it is
worthless", and every concentration, share and ranking figure downstream moves.

This is the single most consequential field behaviour in the RWA family, because
the absence is not rare — it is the majority case. Bell reports the gap as an
`info` signal on 646 references rather than letting it decide a verdict, and
says so on the page.

**Suggested fix:** nothing in the payload; document that absence is expected at
this scale so integrators do not read it as a zero.

## 4. Positive 24h volume alongside a zero market cap

32 references carry at least one representation reporting real traded volume and
a market cap of exactly `0` — not `null`, which would mean unknown, but zero.
Two fields on the same row contradict each other, and a consumer has no way to
tell which is authoritative.

Example from the capture: Kinesis Silver (`KAG`, crypto_id 24439) prints
`market_cap: 0` with `volume_24h: 109,159.66`.

Bell treats this as critical and refuses to compare through it, because ranking
a wrapper on a market cap that the volume field contradicts is exactly the
mistake the product exists to prevent.

## 5. One symbol, more than one instrument

60 references contain a symbol collision across their representations, and 119
mix a derivative with spot-like wrappers under the same reference. `is_derivative`
is present and correct, which is what makes the join possible at all — but a
caller who groups by symbol, as the natural reading of the map invites, silently
compares a perpetual against a spot wrapper.

4 references show a price denomination break: representations of the same
underlying differ by more than 10×, which is a unit difference (gram versus
ounce) rather than a market dislocation. There is no unit field to disambiguate
them, so the break can only be inferred from the prices.

**Suggested fix:** a unit or denomination field on the representation row would
let integrators separate a unit difference from a dispersion finding.

## 6. `market-pairs/list` is not available on the Startup plan

Venue-level liquidity is the natural next check after "can these be compared?",
and it is the one check this build cannot make. Bell records the limitation
rather than presenting absent venue data as zero liquidity — but it means the
comparability answer stops at price and reported volume, and cannot reach
executable size.

## The surfaces Bell reads, and what each one enables

| CMC surface | What Bell uses it for | User consequence |
|---|---|---|
| `/v5/real-world-assets/map` | discover the reference asset and stable RWA ID | search the complete stock, ETF and commodity map |
| `/v5/real-world-assets/assets/list` | reconcile the map with the asset list | expose missing or duplicate identity joins |
| `/v5/real-world-assets/quotes/latest` | read token rows, price, market cap, volume and issuer IDs | show the observed wrapper set without inventing equivalence |
| `/v5/real-world-assets/info` | read reference metadata and TradFi context | distinguish an underlying reference from its token layer |
| `/v5/real-world-assets/issuers/list` | resolve issuer catalogue records | show issuer labels and unresolved joins explicitly |
| `/v2/cryptocurrency/info` | resolve token identity, chain and contract fields | route incomplete identity to diligence before comparison |

The important step is the join. A quote row is not treated as a complete
instrument identity merely because it sits under a familiar reference name.

## What the dated receipt observed

Receipt of 21 September 2026: 791 tokenised references, 1,435 representations.

| Signal | References | Severity | Route |
|---|---:|---|---|
| Missing market fields | 646 | info | reported, does not decide a verdict |
| Derivative mixed with spot-like wrappers | 119 | warning | separate instrument types |
| Symbol collision | 60 | warning | resolve identity before using the ticker |
| Positive volume with zero market cap | 32 | critical | do not compare through the contradiction |
| No tracked TradFi market | 13 | info | underlying relationship left unresolved |
| Price denomination break | 4 | critical | check units, decimals and wrapper claims |
| Missing token information | 4 | warning | resolve chain and contract identity |
| Price dispersion | 4 | warning | the disagreement is the finding |

These are a dated observation, not a permanent property of CMC data.

## Reproduce every number above

No API key, no network:

```sh
make verify      # re-runs the scan and asserts the published receipt
make base-rate   # the population measurement, method stated above the number
make test        # includes the upstream contract suite that pins findings 1-3
```

The public browser reads published evidence and never receives the CMC key.

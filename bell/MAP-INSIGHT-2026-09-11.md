# RWA map coverage insight · dated CMC snapshot

## Finding

The dated CMC RWA map contains **7,811 references**. **790 have at least one
mapped token layer**, while **7,021 remain underlying-only** in this snapshot.
Tokenisation is therefore concentrated rather than universal.

| Reference type | Mapped token layer | Total references | Coverage |
|---|---:|---:|---:|
| Stocks | 688 | 4,686 | 14.7% |
| ETFs | 98 | 3,121 | 3.1% |
| Commodities | 4 | 4 | 100.0% |

## Method

This is a count of `has_tokens` in the credential-free
`/v5/real-world-assets/map` snapshot captured on 11 September 2026. It is not
a count of legal securities, circulating supply, backing, liquidity or
adoption. A true value is used for “mapped token layer”; a false value remains
underlying-only. The map is a discovery index and must not be read as a live
quote.

## Product consequence

Bell changes mode based on this evidence: underlying-only references stay in
underlying research, one mapped token opens a representation dossier, and
multiple mapped tokens unlock a comparison only after identity and data-quality
gates are checked. The website now surfaces this population finding above the
catalogue instead of presenting 7,811 rows as an undifferentiated list.

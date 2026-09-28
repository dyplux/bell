# What changed, 26 to 28 September 2026

83 commits between `6361946`, the last commit the live site served on 26
September, and `03fba0e`. This is the record of what was done and, where it
matters more, what was wrong before.

Everything below was measured. No figure here comes from an estimate.

## 28 September follow-up: instrument evidence is keyed to the token

The mobile decision preview now jumps to the rendered case itself, with the
sticky-header offset applied. Issuer notes are mapped by CMC `crypto_id`, not
issuer name; the cards expose the CMC-reported networks and contract addresses
behind each token ID, while unreviewed issuer terms remain explicit. The
Robinhood GOOGL row now points to the Robinhood Chain debt-security Final Terms
instead of Robinhood Europe's separate derivative product. The Alphabet page
also marks that CMC groups Ondo's Class C `GOOGon` under its Class A reference,
and says whether that route is in the filtered quote table. When included, the
comparison heading now names the CMC-grouped Class A + C quote spread and says
beside the value that it is not a same-share-class spread. The same caveat is
present in the mobile preview, post-search summary and decision consequence.
The separate live explorer verdict now carries that same class-scope sentence
beside its spread, so following the dossier link does not drop the caveat. The
comparison table renders every included route, so its rows match the published
route count and evidence IDs. The deployed-browser gate now follows that link
and checks the warning in the separate dossier as well.

The complete offline gate passes (428 Python, 104 JavaScript and 18 Worker
tests, plus receipt, catalogue, capture and submission checks). A local
Chromium check renders the mobile caveat without page errors. Blind RWA
follow-up scores were 87–90.5; competitors were not re-scored on the same cut,
so these scores do not establish a current rank.

---

## The one that mattered most: the site was a week behind the repository

The deployed site served `main` from 26 September while the work sat on a
branch nobody could see. `/judge` answered **404**, and five surfaces had
drifted. Five independent blind evaluations scored the live site between 62 and
73 while scoring the same code between 77 and 87, so the gap was the deploy and
nothing else.

Published on 27 September. The live score went from **66 to 90** in the next
evaluation. Everything after that is refinement.

Measured now: `verify_deployment_matches.py` reports 5 surfaces byte-identical
to the commit, the browser audit against production exits 0, and CI is green on
the commit that is deployed.

---

## Defects found and closed

Each of these was a published claim that was not true. They are listed with the
evidence, because the list is the point.

### CoinMarketCap does not send `is_derivative`

The field appears **zero times** in the 16.5 MB credential-free input package
this repository ships, and is null on all 312 token rows of the live receipt,
including the 42 whose name ends in "(Derivatives)". The route filter read that
key alone, so it never excluded anything, while every published comparison
carried a basis string reading "Observed CMC quotes for the non-derivative
representations".

The working detector was fifteen lines below in the same file, which is how
`DERIVATIVE_MIX` correctly finds 121 groups. Two answers to one question, and
the affirmative output read the wrong one.

The headline is unmoved: 244 comparable-looking, 157 refused, 87 published,
64.3%. The reason split moves from **120 coverage / 38 contradictions to
107 / 51**. The scanner's own harvest was a third larger than it was claiming.
`API-FEEDBACK.md` had told CoinMarketCap the field "is present and correct";
it now says what was measured.

### `/judge` redirected to itself

The asset layer answers `/judge.html` with a 307 to `/judge`, and the worker
returned that redirect from the path it names. The page went from 404 to an
infinite loop, live. The local harness serves the file off disk and never runs
the worker, so every audit passed throughout, and the worker's own test used a
double that answered 200 to everything.

### The coverage receipt described one file as if it were five

`proof/guard-coverage.json` said "41 guards mutated, 17 survived". All
seventeen were in one file: a `make mutate ONLY=` run had overwritten the whole
receipt. The real figure was 123 and 38. The receipt now carries a record per
file with its own digests, and `complete` is false while anything is missing.

### The verifier's safe mode was not the default

A reviewer took a real case receipt, changed the reference to "Acme Bullion
Trust / ACME / 999999", ran the documented command and got **exit 0** with a
printed verdict about an asset that does not exist. Binding is required now and
`--allow-unbound` has to be asked for by name.

### The runtime band was one machine written as several

The page said the gate runs "between 11.0 and 15.1 seconds across the machines
it has been measured on". The receipt held one machine and 12.48 to 12.61, and
the test only asked whether the published band *contained* every measurement,
which any wide enough invention satisfies. The sentence is generated from the
clock's own file now, the band must equal the fastest and slowest in it, and
the page says plainly that it is a record of the machines it ran on and not a
bound on yours.

### One representation described as representations that must not be ranked

Two references carry a single row and were told "a research desk must not rank
or substitute these representations". There is one row. The same bug made the
SINGLE REPRESENTATION filter return 545 beside prose saying 547, so a reader
filtering for them lost exactly the two the scanner had something to say about.

### The tests wrote the artefact they exist to protect

Three tests forged the dated history by writing into the published file and
restoring it in a `finally`. `make mutate` runs the gate 140 times in a row;
after one sweep the shipped series was found rewritten in the working tree,
every digest after observation four re-linked, one `git add -A` from being
committed. A test may read a published artefact. It may not write one.

### The weekly secret scan had been failing every Monday

5,334 findings, all `generic-api-key`, every one a public on-chain identifier
inside the credential-free package: 3,285 EVM addresses, 466 Solana addresses,
94 SHA-256 digests. Not flaky, two scopes: push runs scan the push and the
weekly run scans the whole history. The allowance is written against the shape
of a public identifier rather than a filename, because silencing a path hides a
key committed into that path forever.

---

## What is measured now that was not

| | before | now |
|---|---|---|
| Tests | 244 | **535** |
| Evidence guards with a test that notices them | never measured | **140 of 140** |
| Gate runtime | quoted from one run | timed on 2 machines, generated from the file |
| Dated series | 11 observations, 9 on one day | **18 across 6 days**, appended by the scheduled job |
| Security headers on the root | none | five, and a test ties the worker's copy to the asset layer's |

Four commands were added because a claim nobody can check is a claim:

- `make mutate` neuters every refusal in the evidence path and the engine, one
  at a time, runs the full offline gate after each, and reports the ones no
  test notices. Three reviewers had been doing this by hand.
- `make time-gate` runs the gate against a clock and writes what it saw.
- `make audit-tests` fails any test that reached the end having asserted
  nothing, and any test that leaks a file handle.
- `make sync-counts` rewrites every count the documents state from a real
  measurement, so a hand-corrected number cannot drift.

---

## What these tools caught that people did not

Worth recording separately, because it is the argument for having them.

- A test written to defend a guard that **could not fail**: its fixture matched
  the fallback as well as the branch, so the guard reported as defended with
  the branch removed. `make mutate` said so.
- A malformed-evidence table that accepted any exception, so deleting a guard
  still crashed further along and the row passed. Nine of its own new rows were
  undefended.
- A second copy of the labelling rule inside the deployed-interface audit,
  which disagreed with the page the moment the rule changed.
- `isinstance(True, int)` is True, so a boolean passed a count check and failed
  two lines later with the wrong message.
- An engine change that stopped the shipped replay re-deriving, which is that
  receipt's whole contract, caught by the gate on the commit that made it.

---

## What is still open

- **No demo video is published.** The cut exists, 2:17 at 1920x1080, built from
  the capture manifest by `bell/demo_cards.py` and `bell/demo_assemble.py`, and
  the 12.9 MB file is deliberately not committed. It is the one field the
  submission is missing.
- `base_rate.py` is pinned to the 21 September input package and cannot be
  recomputed against a current one without an `--inputs` flag.
- The evidence chain does not defeat a whole-file rewrite, and says so in its
  own docstring and on `/judge`.
- Eleven of the seventeen CoinMarketCap endpoints sit in a key-gated audit path
  a reader cannot exercise.

## How it scored while this was happening

Fourteen independent blind evaluations, each by a fresh reviewer who was not
told whose project it was, on the official RWA rubric. The live site: 62, 70,
62, 73, 66 before the deploy, then **90, 90, 89, 83** after it. The 83 is the
one that found the `is_derivative` defect, and it was right to.

The competitors, on the same rubric: Investor Intel 93, Shelfware 90,
UnderScope 89, Backstop 86.

# Public submission gate

Run this before exporting or submitting the repository:

```sh
python3 bell/verify_submission.py
```

Run it from the clean public export or clone that will be submitted. The
private development workspace intentionally contains files that are not part
of the public repository, so the gate must inspect the export's Git index.

The gate checks the Git index, not just the files visible in the working tree.
It verifies that the public build contains the website, explorer, receipts,
verifiers, deployment adapter and judge path, while excluding private jury
material, competitor dossiers, credentials and internal identity disclosures.

It also checks that the public interface uses one decision vocabulary:

- `DO NOT SHORTLIST`
- `INVESTIGATE`
- `FACTS OPEN`
- `SINGLE REPRESENTATION`

This gate is complementary to the test suite and the live smoke check. It does
not claim that the product is an investment recommendation or that a public
receipt proves backing, liquidity, redemption or execution.

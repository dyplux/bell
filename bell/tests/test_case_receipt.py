"""The receipt a judge downloads must be checked for its verdict, not its shape.

A reviewer took a real Silver case receipt from the running site, flipped
`decision.state` from `blocked` to `comparable`, relabelled it `COMPARABLE, NOT
ENDORSED`, emptied all six signals, wrote "Proceed to shortlist" as the next
action and set every source fingerprint to sixty-four `f`s. The verifier
printed "valid public case receipt" and exited 0, with the five Silver rows and
their 31.24x quote range still in the file.

The fixture here was a hand-written stub: one token with no price, a
`source_hashes` of `{"map": "abc"}`, and a `decision` that was a bare string.
Nothing in it could have exercised a verdict check, which is part of why there
was not one. It is built from the shipped replay receipt now, so these tests
run against evidence the product actually produced.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from verify_case_receipt import ROW_DERIVED_SIGNALS, verify  # noqa: E402

REPLAY = json.loads((HERE.parent / "site" / "proof"
                     / "rwa-surface-integrity-latest-replay-2026-09-21.json")
                    .read_text(encoding="utf-8"))


def receipt_for(alert: dict) -> dict:
    """The exported case shape, built from a real alert in the shipped receipt."""
    return {
        "schema_version": "bell.case-receipt.v1",
        "observed_at": REPLAY["observed_at"],
        "published_at": REPLAY["observed_at"],
        "source": "/api/integrity",
        "credential_free": True,
        "question": "Can these representations be compared?",
        "reference": {
            "rwa_id": alert["rwa_id"], "name": alert["name"], "symbol": alert["symbol"],
            "asset_type": alert.get("asset_type"), "token_count": len(alert["tokens"]),
            "issuer_count": alert.get("issuer_count") or 1,
            "tradfi_market_count": alert.get("tradfi_market_count") or 0,
        },
        "decision": copy.deepcopy(alert["decision"]),
        "next_action": alert.get("next_action") or "continue external diligence",
        "signals": copy.deepcopy(alert["signals"]),
        "tokens": copy.deepcopy(alert["tokens"]),
        "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
        # The published digests, because the receipt now binds to the
        # published scan and a made-up fingerprint is exactly what that
        # binding exists to refuse.
        "source_hashes": copy.deepcopy(REPLAY["source_hashes"]),
        "limits": ["Observed fields do not prove liquidity"],
    }


def blocked_alert() -> dict:
    for alert in REPLAY["alerts"]:
        if alert.get("state") == "do_not_compare" and alert.get("tokens"):
            return alert
    raise AssertionError("the shipped receipt carries no blocked case to test with")


class CaseReceiptTests(unittest.TestCase):
    def setUp(self):
        self.alert = blocked_alert()

    def test_valid_receipt(self):
        result = verify(receipt_for(self.alert))
        self.assertEqual(result["status"], "valid public case receipt")
        self.assertEqual(result["token_rows"], len(self.alert["tokens"]))
        self.assertEqual(result["verdict_rederived_from_rows"], self.alert["decision"]["state"])

    def test_every_shipped_case_verifies(self):
        # Without this the refusals below prove nothing: a verifier that refuses
        # everything also refuses every forgery. All 50 published cases, not a
        # sample, because the re-derivation is the new claim.
        checked = 0
        for alert in REPLAY["alerts"]:
            if not alert.get("tokens"):
                continue
            verify(receipt_for(alert))
            checked += 1
        self.assertGreaterEqual(checked, 40,
                                f"only {checked} shipped cases were exercised")

    def test_token_count_must_match_rows(self):
        payload = receipt_for(self.alert)
        payload["reference"]["token_count"] = len(payload["tokens"]) + 1
        with self.assertRaisesRegex(ValueError, "token_count"):
            verify(payload)

    def test_credentials_are_not_accepted(self):
        payload = receipt_for(self.alert)
        payload["credential_free"] = False
        with self.assertRaisesRegex(ValueError, "credential_free"):
            verify(payload)

    def test_a_verdict_that_does_not_follow_from_the_rows_is_refused(self):
        payload = receipt_for(self.alert)
        payload["decision"] = {"state": "comparable", "label": "COMPARABLE, NOT ENDORSED",
                               "consequence": "Prices can be set side by side.",
                               "allocation_effect": "Wrapper selection permitted."}
        with self.assertRaisesRegex(ValueError, "does not follow from the evidence"):
            verify(payload)

    def test_relabelling_the_verdict_is_refused_too(self):
        # The state is only half the verdict; the label is what a reader sees.
        payload = receipt_for(self.alert)
        payload["decision"]["label"] = "COMPARABLE, NOT ENDORSED"
        with self.assertRaisesRegex(ValueError, "decision.label"):
            verify(payload)

    def test_deleting_the_findings_does_not_delete_them_from_the_rows(self):
        payload = receipt_for(self.alert)
        payload["signals"] = []
        with self.assertRaisesRegex(ValueError, "rows produce"):
            verify(payload)

    def test_an_invented_finding_is_refused(self):
        payload = receipt_for(self.alert)
        payload["signals"].append({"code": "TOTALLY_MADE_UP", "severity": "critical",
                                   "message": "x", "evidence": {}})
        with self.assertRaisesRegex(ValueError, "TOTALLY_MADE_UP"):
            verify(payload)

    def test_a_placeholder_fingerprint_is_refused(self):
        # The integrity verifier has refused this since a reviewer found it
        # there. This file accepted sixty-four f's six times over.
        payload = receipt_for(self.alert)
        payload["source_hashes"] = {"map": "f" * 64}
        with self.assertRaisesRegex(ValueError, "placeholder"):
            verify(payload)

    def test_the_two_context_signals_are_named_rather_than_silently_skipped(self):
        # They answer to the whole catalogue and cannot be recomputed from one
        # case. Saying so is the difference between a limit and a hole.
        result = verify(receipt_for(self.alert))
        self.assertEqual(result["signals_not_rederived"],
                         ["NO_TRADFI_MARKET", "TOKEN_INFO_MISSING"])
        self.assertTrue(set(result["signals_rederived"]) <= ROW_DERIVED_SIGNALS)
        self.assertNotIn("NO_TRADFI_MARKET", ROW_DERIVED_SIGNALS)

    def test_deleting_rows_is_refused_even_when_the_verdict_follows_from_what_is_left(self):
        # Re-deriving the verdict from the rows proves it follows from THOSE
        # rows. A reviewer deleted three of Silver's five representations, let
        # the engine re-derive honestly, and got COMPARABLE on the reference
        # this product's headline example blocks. Deleting evidence changed the
        # answer to the wrong question, so the rows are bound to the published
        # scan.
        from rwa_integrity import asset_scan
        payload = receipt_for(self.alert)
        payload["tokens"] = payload["tokens"][:2]
        payload["reference"]["token_count"] = 2
        # Let the verdict and the signals follow honestly from what is left, so
        # only the binding to the published scan can catch this. Anything less
        # is caught by the signal check and proves nothing about the binding.
        honest = asset_scan({**payload["reference"], "tokens": payload["tokens"]},
                            crypto_info_checked=True)
        payload["decision"] = honest["decision"]
        payload["signals"] = honest["signals"]
        payload["next_action"] = honest["next_action"]
        with self.assertRaises(ValueError) as raised:
            verify(payload)
        # Refused either by the subject check (token_count) or by the row set;
        # both are the binding doing its job, and the message names which.
        self.assertRegex(str(raised.exception), "token_count|representations")

    def test_an_edited_row_is_refused(self):
        payload = receipt_for(self.alert)
        payload["tokens"][0] = dict(payload["tokens"][0], price=1.0)
        with self.assertRaisesRegex(ValueError, "price"):
            verify(payload)

    def test_a_relabelled_row_is_refused(self):
        payload = receipt_for(self.alert)
        payload["tokens"][0] = dict(payload["tokens"][0], symbol="TSLA")
        with self.assertRaisesRegex(ValueError, "symbol"):
            verify(payload)

    def test_a_receipt_bound_to_nothing_says_so_instead_of_claiming_valid(self):
        # A case exported from the live endpoint has no receipt in this
        # repository to bind to. It used to print "valid public case receipt"
        # anyway. The status has to say which of the two questions was answered.
        payload = receipt_for(self.alert)
        # A live export is unbound because BOTH halves differ: it carries the
        # live scan's fingerprints and names an observation this repository
        # does not ship. Changing only the digests is now a contradiction, not
        # an unbinding - the receipt names a shipped observation while claiming
        # fingerprints that observation did not have, and that is refused by
        # name rather than softened to "not bound".
        payload["source_hashes"] = {key: "0123456789abcdef" * 4
                                    for key in payload["source_hashes"]}
        payload["observed_at"] = "2099-01-01T00:00:00Z"
        payload["published_at"] = "2099-01-01T00:00:00Z"
        result = verify(payload)
        self.assertEqual(result["status"],
                         "internally consistent; rows not bound to a published receipt")
        self.assertIn("not bound", result["rows_binding"])

    def test_a_bound_receipt_says_what_it_is_bound_to(self):
        result = verify(receipt_for(self.alert))
        self.assertTrue(result["rows_binding"].startswith("bound to "), result["rows_binding"])
        self.assertIn("rwa-surface-integrity-latest-replay-2026-09-21.json", result["rows_binding"])

    def test_every_reference_in_the_index_exports_a_receipt_that_verifies(self):
        # A reviewer downloaded fifteen receipts through the documented button
        # and two failed: Marvell, which is the COMPARABLE example judge.html
        # names, and Rivian. The documented verification command rejecting the
        # product's own unmodified output is worse than no command.
        #
        # Two causes, both mine. `verify_case_receipt` re-ran the engine over
        # rows that were already normalised, and `token_summary` recomputes
        # `crypto_info_resolved` from a lookup it did not have, so a resolved
        # row came back unresolved. And `next_action` was compared outright
        # although it is chosen from a signal set that includes two codes a
        # single case cannot reproduce.
        from rwa_integrity import asset_scan
        checked = 0
        for row in REPLAY["alert_index"][:60]:
            full = next((item for item in REPLAY["alerts"]
                         if str(item.get("rwa_id")) == str(row.get("rwa_id"))), None)
            if full is None or not full.get("tokens"):
                continue
            verify(receipt_for(full))
            checked += 1
        self.assertGreater(checked, 20, f"only {checked} references were exercised")

    def test_a_row_that_recorded_its_identity_as_resolved_stays_resolved(self):
        # The exact mechanism: re-normalising a normalised row lost the flag.
        payload = receipt_for(self.alert)
        resolved = [token for token in payload["tokens"]
                    if token.get("crypto_info_resolved") is True]
        if not resolved:
            self.skipTest("this reference records no resolved identity to preserve")
        result = verify(payload)
        self.assertEqual(result["status"], "valid public case receipt")
        self.assertNotIn("TOKEN_INFO_MISSING", result["signals_rederived"],
                         "a row that recorded a resolved identity came back unresolved")

    def test_the_verifier_says_whether_it_checked_the_next_action(self):
        # Scoped rather than silent: where the context signals differ, the
        # sentence cannot be required, and the reader is told which case it is.
        result = verify(receipt_for(self.alert))
        self.assertIn("next_action_checked", result)
        self.assertIsInstance(result["next_action_checked"], bool)

    def test_a_receipt_naming_a_shipped_observation_with_wrong_digests_is_refused(self):
        # `find_published` used to select the receipt BY the fingerprints and
        # `bind` then asserted the same equality, so through the CLI that check
        # could never fail. A reviewer counted seven guards in this file that
        # could be deleted with the suite green, and this was one. Selection
        # falls back to the timestamp now, so a receipt claiming a shipped
        # observation with the wrong fingerprints is refused instead of
        # falling through to the softer unbound status.
        payload = receipt_for(self.alert)
        payload["source_hashes"] = {key: "0123456789abcdef" * 4
                                    for key in payload["source_hashes"]}
        with self.assertRaisesRegex(ValueError, "source fingerprints"):
            verify(payload)

    def test_a_case_can_be_bound_against_a_receipt_the_reader_supplies(self):
        # Every case a real visitor downloads is unbindable, because the live
        # scan's inputs are not shipped - and a reviewer showed that relabelling
        # the subject on one of those is accepted. The live receipt is
        # credential-free, so the reader who has the URL can supply it and get
        # the whole check. Exercised here with a local receipt, because a gate
        # must not talk to a server it did not start.
        payload = receipt_for(self.alert)
        result = verify(payload, against=(REPLAY, "supplied.json"))
        self.assertEqual(result["rows_binding"], "bound to supplied.json")
        self.assertEqual(result["status"], "valid public case receipt")

    def test_a_supplied_receipt_of_another_observation_says_so(self):
        payload = receipt_for(self.alert)
        other = dict(REPLAY, observed_at="2099-01-01T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "A live endpoint moves on"):
            verify(payload, against=(other, "supplied.json"))

    def test_binding_against_a_supplied_receipt_still_refuses_a_forgery(self):
        # The control that makes the flag worth having: supplying a receipt
        # must not become a way to be believed.
        payload = receipt_for(self.alert)
        payload["reference"]["name"] = "Something Else"
        with self.assertRaisesRegex(ValueError, "wrong subject"):
            verify(payload, against=(REPLAY, "supplied.json"))

    def test_a_field_the_old_comparison_ignored_is_refused(self):
        # bind() compared four named fields of twenty-one. A reviewer rewrote
        # is_derivative, token_type, category, asset_type, name, issuer_id,
        # issuer_name and crypto_info_resolved, re-ran the engine to make the
        # verdict follow honestly, and eleven forged receipts passed
        # --require-binding: the cheapest route moved, the spread moved, and
        # DERIVATIVE_MIX vanished from thirteen of them. One case per field,
        # because a list of names is exactly what failed.
        from rwa_integrity import asset_scan
        fields = ("is_derivative", "token_type", "category", "asset_type", "name",
                  "issuer_id", "issuer_name", "crypto_info_resolved", "crypto_slug")
        for field in fields:
            payload = receipt_for(self.alert)
            published = payload["tokens"][0].get(field)
            # A value that really differs from the published one, whatever it
            # is: the first version used literals and two of them happened to
            # equal what was already there, so two of the eight proved nothing.
            forged = (not published) if isinstance(published, bool) else (
                "forged-value" if published != "forged-value" else "other-value")
            payload["tokens"][0] = dict(payload["tokens"][0], **{field: forged})
            # Let the verdict follow honestly from the rewritten rows, so only
            # the row comparison can catch it.
            resolved = {str(row["crypto_id"]): {"slug": row.get("crypto_slug"), "urls": {},
                                                "contract_address": []}
                        for row in payload["tokens"] if row.get("crypto_info_resolved")}
            honest = asset_scan({**payload["reference"], "tokens": payload["tokens"]},
                                crypto_lookup=resolved, crypto_info_checked=True)
            payload["decision"] = honest["decision"]
            payload["signals"] = honest["signals"]
            payload["next_action"] = honest["next_action"]
            with self.subTest(field=field), self.assertRaises(ValueError) as raised:
                verify(payload)
            self.assertIn(field, str(raised.exception),
                          f"rewriting {field} was accepted, or refused without naming it")


class TheDocumentedCommandRefusesAnUnboundSubject(unittest.TestCase):
    """The safe mode has to be the one you get by typing the command.

    A reviewer took a real exported receipt, changed the reference to "Acme
    Bullion Trust / ACME / 999999", and ran the command this repository's own
    documentation gives. Exit 0, and a printed verdict about an asset that does
    not exist. Everything the verifier checked was true: those rows do produce
    that state. It was not checking whether the rows were anybody's, and the
    flag that would have checked was opt-in.

    Binding is the default now. These tests are at the command line rather than
    at `verify()`, because the defect was never in `verify()` - it reported the
    unbound status correctly the whole time. The defect was the exit code.
    """

    def setUp(self):
        import subprocess
        import tempfile
        self.subprocess = subprocess
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        replay = json.loads((HERE.parent / "site" / "proof"
                             / "rwa-surface-integrity-latest-replay-2026-09-21.json")
                            .read_text(encoding="utf-8"))
        alert = next(item for item in replay["alerts"] if item.get("tokens"))
        self.case = {
            "schema_version": "bell.case-receipt.v1",
            "observed_at": replay["observed_at"], "published_at": replay["observed_at"],
            "source": "proof/rwa-surface-integrity-latest-replay-2026-09-21.json",
            "credential_free": True,
            "question": "Can these representations be compared?",
            "reference": {"rwa_id": alert["rwa_id"], "name": alert["name"],
                          "symbol": alert["symbol"], "asset_type": alert.get("asset_type"),
                          "token_count": len(alert["tokens"]),
                          "issuer_count": alert.get("issuer_count") or 1,
                          "tradfi_market_count": alert.get("tradfi_market_count") or 0},
            "decision": alert["decision"], "next_action": alert.get("next_action"),
            "signals": alert["signals"], "tokens": alert["tokens"],
            "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
            "source_hashes": replay["source_hashes"],
            "limits": ["Observed fields do not prove liquidity"],
        }

    def run_cli(self, payload: dict, *flags: str):
        path = self.root / "case.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return self.subprocess.run(
            [sys.executable, str(HERE.parent / "verify_case_receipt.py"), str(path), *flags],
            capture_output=True, text=True,
            env={"PYTHONPATH": str(HERE.parent), "PATH": "/usr/bin:/bin:/usr/local/bin"})

    def test_a_relabelled_subject_fails_the_bare_command(self):
        forged = copy.deepcopy(self.case)
        forged["reference"].update({"name": "Acme Bullion Trust", "symbol": "ACME",
                                    "rwa_id": 999999})
        result = self.run_cli(forged)
        self.assertEqual(result.returncode, 1,
                         "the documented command blessed an asset that does not exist")
        self.assertIn("not bound", result.stderr)

    def test_the_honest_case_still_passes_the_bare_command(self):
        # The fix must not be "refuse everything", which is the cheapest way to
        # pass the test above.
        result = self.run_cli(self.case)
        self.assertEqual(result.returncode, 0, result.stderr[-400:])
        self.assertIn("bound to", result.stdout)

    def test_unbound_is_still_reachable_by_asking_for_it(self):
        forged = copy.deepcopy(self.case)
        forged["reference"].update({"name": "Acme Bullion Trust", "symbol": "ACME",
                                    "rwa_id": 999999})
        result = self.run_cli(forged, "--allow-unbound")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--allow-unbound", result.stderr)

    def test_the_refusal_says_how_to_bind_a_live_export(self):
        # "not bound" covers a forged subject and an honest export from a scan
        # this repository does not ship. A reader who hits the second must not
        # have to guess.
        forged = copy.deepcopy(self.case)
        forged["reference"]["rwa_id"] = 999999
        result = self.run_cli(forged)
        self.assertIn("--against https://bell.dyplux.com/api/integrity", result.stderr)


if __name__ == "__main__":
    unittest.main()

"""Feed the verifiers malformed evidence and require a refusal for each shape.

`make mutate` neuters every guard in the evidence path and reports the ones no
test notices. On the first full sweep, 68 of 123 survived - and most of them
were shape checks: `if not isinstance(states, dict)`, `if field not in
observation`, `if not SHA256.fullmatch(digest)`. Real refusals, each one
written deliberately, none of them exercised, because every test in the suite
fed the verifiers well-formed evidence.

Three reviewers found the shape of this problem by hand before the tool
existed. Writing fifty-seven tests by hand is how it stays unwritten, so this
is a table: one row per malformation, driven at the function that refuses it.

A row here is not decoration. Each was confirmed to fail when its guard is
neutered, by running `make mutate` before and after.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

PROOF = HERE.parent / "site" / "proof"
HISTORY = json.loads((PROOF / "rwa-surface-integrity-history.json").read_text(encoding="utf-8"))
DATED = json.loads(
    (PROOF / "rwa-surface-integrity-2026-09-15.json").read_text(encoding="utf-8"))
REPLAY = json.loads(
    (PROOF / "rwa-surface-integrity-latest-replay-2026-09-21.json").read_text(encoding="utf-8"))


def observation_for(receipt: dict) -> dict:
    for item in HISTORY["observations"]:
        if item["observed_at"] == receipt["observed_at"]:
            return copy.deepcopy(item)
    raise AssertionError("the shipped history does not describe that receipt")


def case_for(alert: dict) -> dict:
    return {
        "schema_version": "bell.case-receipt.v1",
        "observed_at": REPLAY["observed_at"], "published_at": REPLAY["observed_at"],
        "source": "/api/integrity", "credential_free": True,
        "question": "Can these representations be compared?",
        "reference": {"rwa_id": alert["rwa_id"], "name": alert["name"],
                      "symbol": alert["symbol"], "asset_type": alert.get("asset_type"),
                      "token_count": len(alert["tokens"]),
                      "issuer_count": alert.get("issuer_count") or 1,
                      "tradfi_market_count": alert.get("tradfi_market_count") or 0},
        "decision": copy.deepcopy(alert["decision"]),
        "next_action": alert.get("next_action"),
        "signals": copy.deepcopy(alert["signals"]),
        "tokens": copy.deepcopy(alert["tokens"]),
        "method": {"join_key": "rwa_id", "token_join_key": "crypto_id", "rules": []},
        "source_hashes": copy.deepcopy(REPLAY["source_hashes"]),
        "limits": ["Observed fields do not prove liquidity"],
    }


class TheIntegrityVerifierRefusesMalformedEvidence(unittest.TestCase):
    """One row per shape the observation verifier refuses."""

    def setUp(self):
        from verify_integrity_receipt import verify_observation, verify_observation_shape
        self.verify_observation = verify_observation
        self.verify_shape = verify_observation_shape

    def test_a_receipt_of_the_wrong_shape_is_refused(self):
        # Each row names the message its own guard raises. This accepted
        # `(ValueError, KeyError)` and any message, so neutering `if not
        # isinstance(states, dict)` left the comparison two lines below to
        # raise a ValueError of its own and the row passed anyway. Four of the
        # guards this table exists to defend survived `make mutate` because of
        # it - the same defect as the rest of the table, in the rows written to
        # fix the rest of the table.
        cases = {
            "universe missing": (lambda r: r.pop("universe"),
                                 r"\.universe is missing"),
            "universe not an object": (lambda r: r.__setitem__("universe", []),
                                       r"\.universe is missing"),
            "states not an object": (lambda r: r["universe"].__setitem__("states", []),
                                     r"\.universe\.states is missing"),
            "signals not an object": (lambda r: r["universe"].__setitem__("signals", []),
                                      r"\.universe\.signals is missing"),
            "receipt carries no source_hashes": (lambda r: r.__setitem__("source_hashes", {}),
                                                 r"carries no source_hashes to compare"),
            "receipt source_hashes not an object": (
                lambda r: r.__setitem__("source_hashes", []),
                r"carries no source_hashes to compare"),
        }
        for label, (break_it, expected) in cases.items():
            receipt = copy.deepcopy(DATED)
            break_it(receipt)
            with self.subTest(case=label), self.assertRaisesRegex(ValueError, expected):
                self.verify_observation(observation_for(DATED), receipt, label)

    def test_a_record_that_carries_no_source_hashes_is_refused(self):
        # The observation side of the same comparison. Its shape check lives in
        # a different function, so this guard was reached by no test at all.
        for value in ({}, [], "", None):
            observation = observation_for(DATED)
            observation["source_hashes"] = value
            with self.subTest(value=repr(value)), \
                    self.assertRaisesRegex(ValueError, r"\.source_hashes is missing"):
                self.verify_observation(observation, copy.deepcopy(DATED), "record")

    def test_an_observation_of_the_wrong_shape_is_refused(self):
        required = ("observed_at", "tokenised_references_scanned", "tokens_scanned",
                    "states", "signals")
        for field in required:
            observation = observation_for(DATED)
            observation.pop(field, None)
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.verify_shape(observation, f"missing {field}")

    def test_a_state_total_that_does_not_equal_the_population_is_refused(self):
        observation = observation_for(DATED)
        key = sorted(observation["states"])[0]
        observation["states"][key] += 1
        with self.assertRaisesRegex(ValueError, "state total"):
            self.verify_shape(observation, "wrong total")

    def test_a_fingerprint_that_is_not_a_fingerprint_is_refused(self):
        for bad in ("", "abc", "z" * 64, "0123456789abcdef" * 3):
            observation = observation_for(DATED)
            observation["source_hashes"][sorted(observation["source_hashes"])[0]] = bad
            with self.subTest(digest=bad[:12]), self.assertRaises(ValueError):
                self.verify_shape(observation, "bad digest")

    def test_source_hashes_that_are_not_an_object_are_refused(self):
        for value in ([], "", 0, None):
            observation = observation_for(DATED)
            observation["source_hashes"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.verify_shape(observation, "bad source_hashes")


class TheCaseVerifierRefusesMalformedEvidence(unittest.TestCase):
    """One row per shape the case receipt verifier refuses."""

    def setUp(self):
        from verify_case_receipt import verify
        self.verify = verify
        self.alert = next(item for item in REPLAY["alerts"] if item.get("tokens"))

    def test_a_payload_of_the_wrong_type_is_refused(self):
        for value in ([], "receipt", 7, None):
            with self.subTest(value=repr(value)), self.assertRaisesRegex(ValueError, "JSON object"):
                self.verify(value)

    def test_a_missing_top_level_field_is_named(self):
        from verify_case_receipt import REQUIRED_TOP_LEVEL
        for field in sorted(REQUIRED_TOP_LEVEL):
            payload = case_for(self.alert)
            payload.pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception),
                          f"removing {field} was refused without naming it")

    def test_a_wrong_schema_version_is_refused(self):
        payload = case_for(self.alert)
        payload["schema_version"] = "bell.case-receipt.v99"
        with self.assertRaisesRegex(ValueError, "schema_version"):
            self.verify(payload)

    def test_a_missing_reference_field_is_named(self):
        from verify_case_receipt import REQUIRED_REFERENCE
        for field in sorted(REQUIRED_REFERENCE):
            payload = case_for(self.alert)
            payload["reference"].pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception))

    def test_a_missing_method_field_is_named(self):
        from verify_case_receipt import REQUIRED_METHOD
        for field in sorted(REQUIRED_METHOD):
            payload = case_for(self.alert)
            payload["method"].pop(field)
            with self.subTest(missing=field), self.assertRaises(ValueError) as raised:
                self.verify(payload)
            self.assertIn(field, str(raised.exception))

    def test_a_join_key_the_product_does_not_use_is_refused(self):
        for field, value in (("join_key", "symbol"), ("token_join_key", "ticker")):
            payload = case_for(self.alert)
            payload["method"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                self.verify(payload)

    def test_the_collection_of_wrong_types_is_refused(self):
        # Two rounds of the same defect. The first version accepted
        # (ValueError, TypeError, AttributeError), so removing a guard still
        # blew up further along and the row passed: nine were undefended. The
        # second asserted the field NAME appeared in the message, and four of
        # these still survived, because `tokens must be an array` and
        # `reference.token_count does not match tokens length` both contain the
        # word "tokens". The guard below it was answering for it.
        #
        # So each row names the message of its own guard and nothing else.
        cases = {
            "tokens not an array": ("tokens", {}, r"^tokens must be an array$"),
            "signals not an array": ("signals", {}, r"^signals must be an array$"),
            "source_hashes not an object": ("source_hashes", [],
                                            r"^source_hashes must be an object$"),
            "limits empty": ("limits", [], r"^limits must be a non-empty array$"),
            "limits not an array": ("limits", "none", r"^limits must be a non-empty array$"),
            "method not an object": ("method", [], r"^method must be an object$"),
            "reference not an object": ("reference", [], r"^reference must be an object$"),
            "question empty": ("question", "   ", r"^question must be a non-empty string$"),
            "question not a string": ("question", 7, r"^question must be a non-empty string$"),
        }
        for label, (field, value, expected) in cases.items():
            payload = case_for(self.alert)
            payload[field] = value
            with self.subTest(case=label), self.assertRaisesRegex(ValueError, expected):
                self.verify(payload)

    def test_a_rule_list_that_is_not_a_list_is_refused(self):
        for value in ({}, "rule", 1, None):
            payload = case_for(self.alert)
            payload["method"]["rules"] = value
            with self.subTest(value=repr(value)), \
                    self.assertRaisesRegex(ValueError, r"^method\.rules must be an array$"):
                self.verify(payload)

    def test_a_token_count_that_is_not_a_positive_integer_is_refused(self):
        for value in (0, -1, True, "5", None):
            payload = case_for(self.alert)
            payload["reference"]["token_count"] = value
            with self.subTest(value=repr(value)), self.assertRaisesRegex(
                    ValueError, r"^reference\.token_count must be a positive integer$"):
                self.verify(payload)
        # And a count that is a valid positive integer and still wrong, which
        # is a different guard from the type check above and has its own
        # message: asserting only "token_count" let either one answer for both.
        payload = case_for(self.alert)
        payload["reference"]["token_count"] = len(payload["tokens"]) + 3
        with self.assertRaisesRegex(
                ValueError, r"^reference\.token_count does not match tokens length$"):
            self.verify(payload)

    def test_a_source_hash_that_is_not_a_fingerprint_is_refused(self):
        for bad in ("", "abc", "0" * 63, "0" * 65, 64, None, ["a" * 64]):
            payload = case_for(self.alert)
            name = sorted(payload["source_hashes"])[0]
            payload["source_hashes"][name] = bad
            with self.subTest(value=repr(bad)[:16]), self.assertRaisesRegex(
                    ValueError, rf"^source_hashes\.{name} is not a SHA-256 fingerprint$"):
                self.verify(payload)

    def test_a_decision_that_is_not_an_object_is_refused(self):
        for value in ("comparable", [], None, {}):
            payload = case_for(self.alert)
            payload["decision"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                self.verify(payload)

    def test_a_receipt_this_repository_does_not_ship_is_refused(self):
        payload = case_for(self.alert)
        payload["source"] = "proof/rwa-surface-integrity-1999-01-01.json"
        with self.assertRaisesRegex(ValueError, "does not ship"):
            self.verify(payload)


class ReadingAReceiptToBindAgainstRefusesWhatItCannotRead(unittest.TestCase):
    """`--against` takes a URL or a path, and both branches were undefended."""

    def test_a_path_that_does_not_exist_is_refused_by_name(self):
        from verify_case_receipt import fetch_receipt
        with self.assertRaisesRegex(ValueError, "not a URL and not a file"):
            fetch_receipt("/tmp/a-receipt-that-is-not-here-1234.json")

    def test_a_path_that_exists_is_read_and_named(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(REPLAY), encoding="utf-8")
            document, name = fetch_receipt_local(str(path))
            self.assertEqual(name, "receipt.json")
            self.assertEqual(document["observed_at"], REPLAY["observed_at"])


def fetch_receipt_local(source: str):
    from verify_case_receipt import fetch_receipt
    return fetch_receipt(source)


class BindingRefusesWhatItCannotMatch(unittest.TestCase):
    def setUp(self):
        from verify_case_receipt import bind
        self.bind = bind
        self.alert = next(item for item in REPLAY["alerts"] if item.get("tokens"))

    def test_a_reference_the_published_receipt_does_not_carry_in_full_is_named(self):
        payload = case_for(self.alert)
        payload["reference"]["rwa_id"] = "9999999"
        with self.assertRaises(LookupError) as raised:
            self.bind(payload, REPLAY, "receipt")
        self.assertIn("not carried in full", str(raised.exception))

    def test_a_receipt_describing_another_observation_is_named(self):
        payload = case_for(self.alert)
        other = dict(REPLAY, observed_at="2099-01-01T00:00:00Z")
        with self.assertRaisesRegex(ValueError, "moves on"):
            self.bind(payload, other, "receipt")


class TheInputPackageIsRefusedWhenItIsMalformed(unittest.TestCase):
    """The provenance and package guards, driven at the functions that refuse.

    `make mutate` reported twenty-four refusals in verify_integrity_receipt.py
    that nothing noticed. Most are shape checks on the 16.5 MB input package
    and its collection manifest: every test in the suite handed them a
    well-formed package, so the branch that refuses a malformed one had never
    run. The surfaces are parsed once and only the manifest is copied, because
    re-reading 16.5 MB per row is how a useful test becomes one nobody runs.
    """

    @classmethod
    def setUpClass(cls):
        from verify_integrity_receipt import load, verify_collection_manifest
        cls.verify_manifest = staticmethod(verify_collection_manifest)
        package = load(PROOF / "rwa-surface-integrity-inputs-2026-09-21.json")
        cls.surfaces = package["surfaces"]
        cls.manifest = package["collection_manifest"]
        cls.names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")

    def manifest_copy(self):
        return copy.deepcopy(self.manifest)

    def test_a_manifest_that_is_not_a_server_side_collection_is_refused(self):
        for value in ({}, [], None, {"mode": "client_side"}, {"mode": None}):
            with self.subTest(value=repr(value)[:24]), \
                    self.assertRaisesRegex(ValueError, "collection manifest"):
                self.verify_manifest(self.surfaces, value, self.names)

    def test_a_surface_whose_digest_does_not_match_its_payload_is_named(self):
        manifest = self.manifest_copy()
        manifest["surfaces"]["map"]["payload_sha256"] = "0123456789abcdef" * 4
        with self.assertRaisesRegex(ValueError, "map"):
            self.verify_manifest(self.surfaces, manifest, self.names)

    def test_a_surface_that_is_not_an_object_is_named(self):
        manifest = self.manifest_copy()
        manifest["surfaces"]["quotes"] = []
        with self.assertRaisesRegex(ValueError, "quotes"):
            self.verify_manifest(self.surfaces, manifest, self.names)

    def test_a_request_count_that_is_not_a_positive_integer_is_refused(self):
        for value in (0, -3, "8", None, True):
            manifest = self.manifest_copy()
            manifest["surfaces"]["map"]["request_count"] = value
            with self.subTest(value=repr(value)), \
                    self.assertRaisesRegex(ValueError, "request count"):
                self.verify_manifest(self.surfaces, manifest, self.names)

    def test_a_successful_count_outside_the_request_count_is_refused(self):
        manifest = self.manifest_copy()
        manifest["surfaces"]["map"]["successful_response_count"] = \
            manifest["surfaces"]["map"]["request_count"] + 1
        with self.assertRaisesRegex(ValueError, "successful response count"):
            self.verify_manifest(self.surfaces, manifest, self.names)

    def test_response_digests_that_do_not_match_the_count_are_refused(self):
        manifest = self.manifest_copy()
        manifest["surfaces"]["map"]["response_sha256"] = \
            manifest["surfaces"]["map"]["response_sha256"][:-1]
        with self.assertRaisesRegex(ValueError, "response hashes"):
            self.verify_manifest(self.surfaces, manifest, self.names)

    def test_status_codes_that_do_not_match_the_request_count_are_refused(self):
        for broken in (lambda codes: codes[:-1], lambda codes: codes + ["200"]):
            manifest = self.manifest_copy()
            manifest["surfaces"]["map"]["status_codes"] = broken(
                list(manifest["surfaces"]["map"]["status_codes"]))
            with self.subTest(case=str(broken)), \
                    self.assertRaisesRegex(ValueError, "status codes"):
                self.verify_manifest(self.surfaces, manifest, self.names)

    def test_the_untouched_manifest_passes(self):
        # The control: a function that refuses everything proves nothing.
        try:
            self.verify_manifest(self.surfaces, self.manifest_copy(), self.names)
        except ValueError as refusal:
            self.fail(f"the shipped manifest was refused: {refusal}")
        self.assertTrue(True, "the shipped manifest passes the function the rows above break")


class TheHistoryFileIsRefusedWhenItIsMalformed(unittest.TestCase):
    """The history's own shape, which nothing exercised either."""

    def run_verifier(self, history: dict):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text(json.dumps(history), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(HERE.parent / "verify_integrity_receipt.py"),
                 "--history", str(path)],
                capture_output=True, text=True,
                env={"PYTHONPATH": str(HERE.parent), "PATH": "/usr/bin:/bin:/usr/local/bin"})

    def test_a_history_of_the_wrong_schema_is_refused(self):
        history = copy.deepcopy(HISTORY)
        history["schema_version"] = "bell.something.v9"
        result = self.run_verifier(history)
        self.assertEqual(result.returncode, 1)
        self.assertIn("history schema", result.stderr)

    def test_a_history_that_hides_what_it_does_not_contain_is_refused(self):
        # The purpose field has to disclose that raw authenticated responses
        # are absent. Deleting the disclosure is the cheapest overclaim there
        # is, and nothing caught it.
        history = copy.deepcopy(HISTORY)
        history["purpose"] = "A dated series of observations."
        result = self.run_verifier(history)
        self.assertEqual(result.returncode, 1)
        self.assertIn("raw responses", result.stderr)

    def test_a_history_with_fewer_than_two_observations_is_refused(self):
        history = copy.deepcopy(HISTORY)
        history["observations"] = history["observations"][:1]
        result = self.run_verifier(history)
        self.assertEqual(result.returncode, 1)
        self.assertIn("at least two", result.stderr)


class ThePackageHeaderIsRefusedBeforeAnythingIsRecomputed(unittest.TestCase):
    """The four guards at the top of verify_public_inputs, and two beside them.

    All four refuse before `scan` is reached, so each row is a pair of small
    files rather than a copy of the 16.5 MB package: the point is the refusal,
    and a test that has to read sixteen megabytes to assert one message is a
    test that gets deleted.

    Their shape is worth naming. Three of them - the schema version, the
    credential-free declaration, the six required surfaces - decide whether a
    package is the thing it says it is, and the fourth binds it to the receipt
    it claims to recompute. Without that fourth, a real package from one day
    recomputes a receipt from another and the mismatch reads as a rules change.
    """

    def setUp(self):
        import tempfile
        from verify_integrity_receipt import load, verify_public_inputs
        self.load = load
        self.verify = verify_public_inputs
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, name: str, value) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def check(self, package, expected, receipt=None):
        package_path = self.write("inputs.json", package)
        receipt_path = self.write("receipt.json", receipt or {"observed_at": "2026-09-21"})
        with self.assertRaisesRegex(ValueError, expected):
            self.verify(package_path, receipt_path)

    def test_a_package_of_another_schema_is_refused(self):
        for version in (None, "", "bell.rwa_surface_integrity.inputs.v2", "anything"):
            with self.subTest(version=repr(version)):
                self.check({"schema_version": version}, "unexpected public input package schema")

    def test_a_package_that_does_not_declare_itself_credential_free_is_refused(self):
        # `is not True` and not a truthy test: "credential_free": "yes" is a
        # string someone wrote, not a declaration the verifier can act on.
        for value in (None, False, "true", 1, {}):
            with self.subTest(value=repr(value)):
                self.check({"schema_version": "bell.rwa_surface_integrity.inputs.v1",
                            "credential_free": value},
                           "must be credential-free")

    def test_a_package_missing_any_required_surface_is_refused(self):
        names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
        header = {"schema_version": "bell.rwa_surface_integrity.inputs.v1",
                  "credential_free": True}
        for dropped in names:
            surfaces = {name: {} for name in names if name != dropped}
            with self.subTest(missing=dropped):
                self.check({**header, "surfaces": surfaces}, "missing a required surface")
        for value in (None, [], "", 0):
            with self.subTest(surfaces=repr(value)):
                self.check({**header, "surfaces": value}, "missing a required surface")

    def test_a_package_describing_another_observation_is_refused(self):
        names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
        package = {"schema_version": "bell.rwa_surface_integrity.inputs.v1",
                   "credential_free": True,
                   "surfaces": {name: {} for name in names},
                   "observed_at": "2026-09-20"}
        self.check(package, "timestamp does not match",
                   receipt={"observed_at": "2026-09-21"})

    def test_a_package_with_no_observation_binds_to_no_receipt(self):
        # Writing the row above found this: the guard was a bare `!=`, so two
        # absences agreed with each other and a package with no observed_at
        # passed the only check that ties it to an observation.
        names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
        package = {"schema_version": "bell.rwa_surface_integrity.inputs.v1",
                   "credential_free": True,
                   "surfaces": {name: {} for name in names}}
        for value in (None, "", 0, {}):
            with self.subTest(value=repr(value)):
                self.check({**package, "observed_at": value},
                           "carries no observed_at", receipt={"other": 1})
        self.check(package, "carries no observed_at", receipt={"other": 1})

    def test_a_file_whose_top_level_is_not_an_object_is_refused(self):
        for value in ([], "text", 3, None, True):
            path = self.write("thing.json", value)
            with self.subTest(value=repr(value)), \
                    self.assertRaisesRegex(ValueError, "is not a JSON object"):
                self.load(path)

    def test_a_bundled_receipt_with_no_observation_is_refused(self):
        from verify_integrity_receipt import bundle
        with self.assertRaisesRegex(ValueError, "carries no observed_at"):
            bundle([({"observed_at": "2026-09-21"}, "dated"), ({}, "latest")])


class AnEndpointThatDoesNotAnswerIsNotEvidence(unittest.TestCase):
    """The two loaders that can read a URL, driven without touching a network.

    Both were undefended, in both files, and for the same reason: every test in
    the suite passes a path. The HTTP branch and the status check are the only
    place either tool trusts something it did not ship, which makes them the
    branches most worth a test and the ones easiest to leave without one.

    `urlopen` is replaced, not called. The rule this repository already has for
    its browser audits - never talk to a server you did not start - applies
    just as well to a test that would otherwise depend on somebody's uptime.
    """

    class Response:
        def __init__(self, status, body):
            self.status = status
            self._body = body

        def read(self):
            return json.dumps(self._body).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def answering(self, status, body=None):
        from unittest import mock
        return mock.patch.object(self.module, self.opener,
                                 lambda *_args, **_kwargs: self.Response(status, body or {}))

    def test_the_case_verifier_refuses_an_endpoint_that_does_not_answer_200(self):
        import verify_case_receipt
        import urllib.request
        self.module, self.opener = urllib.request, "urlopen"
        for status in (404, 500, 301, 204):
            with self.subTest(status=status), self.answering(status), \
                    self.assertRaisesRegex(ValueError, f"answered HTTP {status}"):
                verify_case_receipt.fetch_receipt("https://bell.dyplux.com/api/published")

    def test_the_case_verifier_reads_a_url_as_a_url(self):
        # Neuter the `startswith("http")` dispatch and this source becomes a
        # filename, which is the only way to notice the dispatch is gone.
        import verify_case_receipt
        import urllib.request
        self.module, self.opener = urllib.request, "urlopen"
        with self.answering(200, {"observed_at": "2026-09-21"}):
            payload, name = verify_case_receipt.fetch_receipt("https://bell.dyplux.com/x.json")
        self.assertEqual(payload["observed_at"], "2026-09-21")
        self.assertEqual(name, "https://bell.dyplux.com/x.json")

    def test_the_history_job_refuses_an_endpoint_that_does_not_answer_200(self):
        import append_history
        self.module, self.opener = append_history, "urlopen"
        for status in (404, 500, 503):
            with self.subTest(status=status), self.answering(status), \
                    self.assertRaisesRegex(SystemExit, f"returned HTTP {status}"):
                append_history.load_receipt("https://bell.dyplux.com/api/integrity")

    def test_the_history_job_reads_a_url_as_a_url(self):
        import append_history
        self.module, self.opener = append_history, "urlopen"
        with self.answering(200, {"observed_at": "2026-09-21"}):
            receipt = append_history.load_receipt("https://bell.dyplux.com/api/integrity")
        self.assertEqual(receipt["observed_at"], "2026-09-21")


if __name__ == "__main__":
    unittest.main()

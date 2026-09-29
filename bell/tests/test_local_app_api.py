from __future__ import annotations

from functools import partial
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import BellHandler


ROOT = Path(__file__).resolve().parents[1]


class LocalAppApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(BellHandler, directory=str(ROOT / "site"))
        )
        cls.httpd.session_api_key = None
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def request_json(self, path: str, method: str = "GET", payload: dict | None = None,
                     headers: dict | None = None) -> tuple[int, dict]:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(self.base + path, data=body, method=method, headers=headers or {})
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_agent_manifest_describes_no_key_and_live_routes(self) -> None:
        status, manifest = self.request_json("/api/agent")
        self.assertEqual(status, 200)
        self.assertEqual(manifest["schema_version"], "bell.agent-manifest.v1")
        tools = {tool["name"]: tool for tool in manifest["tools"]}
        self.assertIn("bell_live_audit", tools)
        self.assertIn("may consume plan quota", tools["bell_live_audit"]["description"])
        self.assertIn("bell_search_catalogue", tools)

    def test_catalogue_search_is_credential_free_and_dated(self) -> None:
        status, result = self.request_json("/api/catalog?q=tesla&limit=5")
        self.assertEqual(status, 200)
        self.assertFalse(result["live_cmc_call"])
        self.assertTrue(result["credential_free"])
        self.assertTrue(result["results"])
        self.assertEqual(result["results"][0]["slug"], "tesla")

    def test_dated_receipt_works_without_a_key_and_is_labelled(self) -> None:
        status, receipt = self.request_json("/api/integrity")
        self.assertEqual(status, 200)
        self.assertTrue(receipt["alert_index"])
        self.assertEqual(receipt["_publication"]["status"], "dated replay")
        self.assertTrue(receipt["_publication"]["credential_free"])

    def test_key_is_held_in_memory_and_never_returned(self) -> None:
        key = "unit-test-secret-do-not-persist"
        status, result = self.request_json(
            "/api/key", "POST", {"api_key": key}, {"Content-Type": "application/json"}
        )
        self.assertEqual(status, 200)
        self.assertTrue(result["configured"])
        self.assertNotIn(key, json.dumps(result))
        self.assertEqual(self.httpd.session_api_key, key)
        status, state = self.request_json("/api/key")
        self.assertEqual(status, 200)
        self.assertTrue(state["configured"])
        self.assertNotIn(key, json.dumps(state))
        status, _ = self.request_json("/api/key", "DELETE")
        self.assertEqual(status, 200)
        self.assertIsNone(self.httpd.session_api_key)

    def test_key_mutation_rejects_non_local_host_header(self) -> None:
        status, result = self.request_json(
            "/api/key", "POST", {"api_key": "must-not-be-accepted"},
            {"Content-Type": "application/json", "Host": "attacker.example"},
        )
        self.assertEqual(status, 403)
        self.assertEqual(self.httpd.session_api_key, None)
        self.assertIn("local machine", result["error"])

    def test_live_route_without_key_fails_before_any_cmc_request(self) -> None:
        status, result = self.request_json("/api/audit?slug=tesla")
        self.assertEqual(status, 503)
        self.assertIn("set CMC_API_KEY", result["error"])


if __name__ == "__main__":
    unittest.main()

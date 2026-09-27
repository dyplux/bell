"""An outage is not a failing commit, and drift is not an outage.

The deployed site fell a whole redesign behind this repository - /judge
answered 404, the outcome key omitted a published state, an example chip
stated the wrong verdict - and every gate stayed green, because the only job
that touched the deployed site ran on a schedule and no job compared its bytes
to the repository's.

The stated reason for keeping it off pushes was that a site outage must not
redden a commit that is fine. That is true of an outage and false of drift, so
the two are separated. These tests hold that separation, against a local
server rather than the network: a gate that talks to a server it did not start
is a gate that fails for reasons that are not about the code.
"""

from __future__ import annotations

import http.server
from pathlib import Path
import socketserver
import sys
import threading
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from verify_deployment_matches import main  # noqa: E402

SITE = HERE.parent / "site"


class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves the repository's own site, with per-test distortions."""

    status_override: dict = {}
    body_override: dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, *args):
        pass

    def do_GET(self):
        route = self.path.split("?")[0]
        if route in self.status_override:
            self.send_response(self.status_override[route])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if route in self.body_override:
            body = self.body_override[route]
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if route == "/judge":
            self.path = "/judge.html"
        return super().do_GET()


class DeploymentDrift(unittest.TestCase):
    def setUp(self):
        Handler.status_override = {}
        Handler.body_override = {}
        socketserver.TCPServer.allow_reuse_address = True
        self.server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        # poll_interval, not the default 0.5s: shutdown() waits for the next
        # poll, so six tests cost three seconds of doing nothing and pushed the
        # whole gate past the runtime this repository publishes.
        self.thread = threading.Thread(
            target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def test_a_site_serving_this_commit_passes(self):
        self.assertEqual(main(["--base", self.base]), 0)

    def test_a_route_that_404s_is_drift_not_an_outage(self):
        # The exact shape of the defect a reviewer found: /judge existed in the
        # repository and answered 404 in production.
        Handler.status_override = {"/judge": 404}
        self.assertEqual(main(["--base", self.base]), 1)

    def test_a_surface_serving_different_bytes_fails(self):
        Handler.body_override = {"/integrity.js": b"// an older build\n"}
        self.assertEqual(main(["--base", self.base]), 1)

    def test_a_server_that_is_down_is_skipped_rather_than_failed(self):
        # This is the case the original reasoning was protecting, and it still
        # has to hold or the check cannot live on a push trigger.
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertEqual(main(["--base", self.base, "--timeout", "2"]), 0)

    def test_a_five_hundred_is_an_outage_not_drift(self):
        Handler.status_override = {"/": 503}
        self.assertEqual(main(["--base", self.base, "--timeout", "5"]), 0)

    def test_it_checks_the_routes_a_judge_actually_reads(self):
        from verify_deployment_matches import SURFACES
        routes = {route for route, _ in SURFACES}
        self.assertIn("/", routes)
        self.assertIn("/judge", routes, "the submitted demo URL is not being compared")
        for _, filename in SURFACES:
            self.assertTrue((SITE / filename).exists(), f"{filename} is not in the repository")


if __name__ == "__main__":
    unittest.main()

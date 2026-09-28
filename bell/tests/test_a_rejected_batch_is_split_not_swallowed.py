"""CMC rejects a whole batch of unknown ids, so the collector retries one by one.

The retry has to tell two things apart: an id this catalogue does not carry,
which is recorded as an unresolved gap, and any other HTTP failure, which must
stop the scan. `if item_error.code != 400: raise` is that distinction, and it
was the last guard in the mutated set that nothing noticed - because it lives
in the live collection path, which needs a CoinMarketCap key and a network, so
no test in the suite had ever been near it.

It does not need either. `api_get` is a module-level function, so the sequence
of responses can be handed to the collector directly.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import rwa_integrity  # noqa: E402


def page(rows=None, has_more=False, key="rwa_assets"):
    return {"data": {key: rows or [], "has_more": has_more}}


def http_error(code: int) -> HTTPError:
    return HTTPError("https://pro-api.coinmarketcap.com/v2/cryptocurrency/info",
                     code, "rejected", {}, None)


class ARejectedBatchIsSplitAndTheGapIsRecorded(unittest.TestCase):
    """The collector is driven with responses rather than a network."""

    def collect(self, per_id):
        """Run collect_live with one quoted token, and `per_id` deciding the retry."""
        calls = []

        # Two ids, so the batch request carries a comma. With one, the batch
        # and the single retry are the same string, the OUTER guard fires and
        # the inner one is never reached - which is how the first version of
        # this test passed while leaving the guard it was written for
        # undefended. `make mutate` said so.
        asset = {"rwa_id": 1, "name": "Acme", "symbol": "ACME", "has_tokens": True,
                 "tokens": [{"crypto_id": 77, "symbol": "ACME"},
                            {"crypto_id": 78, "symbol": "ACMEB"}]}

        def fake_api_get(path, params, key, surface=None, surface_times=None):
            calls.append((path, dict(params)))
            # The map decides which references are asked for quotes, so it has
            # to carry the reference and say it has tokens.
            if path == "/v5/real-world-assets/map":
                return page([asset])
            if path in ("/v5/real-world-assets/quotes/latest", "/v5/real-world-assets/info"):
                return page([asset])
            if path == "/v2/cryptocurrency/info":
                return per_id(params["id"])
            if path == "/v5/real-world-assets/issuers/list":
                return page(key="issuers")
            return page()

        original = rwa_integrity.api_get
        rwa_integrity.api_get = fake_api_get
        try:
            return rwa_integrity.collect_live("a-key", {}), calls
        finally:
            rwa_integrity.api_get = original

    def test_an_unknown_id_is_recorded_rather_than_hidden(self):
        def per_id(ids):
            # The batch is refused, and so is the single id inside it.
            raise http_error(400)

        (_, _, _, _, _, crypto_info), calls = self.collect(per_id)
        invalid = crypto_info["unresolved_ids"]
        self.assertIn("77", invalid,
                      "an id CMC does not carry was dropped instead of recorded")
        singles = [params for path, params in calls
                   if path == "/v2/cryptocurrency/info" and params["id"] == "77"]
        self.assertTrue(singles, "the failing batch was never split")

    def test_any_other_failure_stops_the_scan(self):
        # The guard. A 500, a 401 or a 429 on a single id is not "this asset
        # does not exist"; swallowing it would publish a scan with a silent
        # hole and call the id unresolved.
        for code in (401, 403, 429, 500, 503):
            def per_id(ids, code=code):
                raise http_error(400 if "," in ids else code)

            with self.subTest(code=code):
                with self.assertRaises(HTTPError) as raised:
                    self.collect(per_id)
                self.assertEqual(raised.exception.code, code,
                                 f"HTTP {code} was recorded as an unknown id")

    def test_a_batch_that_answers_is_never_split(self):
        def per_id(ids):
            return {"data": {"77": {"id": 77, "slug": "acme"}}}

        (_, _, _, _, _, crypto_info), calls = self.collect(per_id)
        self.assertEqual(crypto_info["unresolved_ids"], [], "a batch that answered produced an unresolved id")
        singles = [params for path, params in calls
                   if path == "/v2/cryptocurrency/info" and "," not in str(params["id"])]
        self.assertEqual(singles, [], "a batch that answered was split anyway")


if __name__ == "__main__":
    unittest.main()

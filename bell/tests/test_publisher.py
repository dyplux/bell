"""These tests never ran: pytest-style functions in a unittest-collected gate."""

import json
import sys
from pathlib import Path
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import publisher


class Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"jobs": []}).encode()


class ThePublisher(unittest.TestCase):
    def setUp(self):
        for name, value in (("BELL_JOBS_URL", "https://example.test/internal/jobs"),
                            ("PUBLISHER_TOKEN", "test-token")):
            patcher = mock.patch.dict("os.environ", {name: value})
            patcher.start()
            self.addCleanup(patcher.stop)
        self.captured = {}

        def fake_urlopen(request, timeout=None):
            self.captured["request"] = request
            self.captured["timeout"] = timeout
            return Response()

        patcher = mock.patch.object(publisher, "urlopen", fake_urlopen)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_remote_queue_uses_stable_user_agent(self):
        self.assertEqual(publisher.pull_remote_jobs(5), [])
        self.assertEqual(self.captured["request"].headers["User-agent"],
                         publisher.PUBLISHER_USER_AGENT)

    def test_failed_job_is_reported_to_the_worker(self):
        result = publisher.mark_remote_job_failed({"id": 7, "slug": "marvell"}, "CMC HTTP 400")
        self.assertIs(result["remote_failure_recorded"], True)
        self.assertEqual(self.captured["request"].full_url, "https://example.test/internal/fail")
        self.assertEqual(json.loads(self.captured["request"].data),
                         {"id": 7, "slug": "marvell", "error": "CMC HTTP 400"})


if __name__ == "__main__":
    unittest.main()

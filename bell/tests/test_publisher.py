import json
import sys
from pathlib import Path

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


def test_remote_queue_uses_stable_user_agent(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("BELL_JOBS_URL", "https://example.test/internal/jobs")
    monkeypatch.setenv("PUBLISHER_TOKEN", "test-token")
    monkeypatch.setattr(publisher, "urlopen", fake_urlopen)

    assert publisher.pull_remote_jobs(5) == []
    assert captured["request"].headers["User-agent"] == publisher.PUBLISHER_USER_AGENT

import json
import tempfile
import unittest
from pathlib import Path

from verify_demo_manifest import verify


class DemoManifestTests(unittest.TestCase):
    def test_long_manifest_binds_receipt_steps_and_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "demo.webm"
            video.write_bytes(b"video")
            steps = [
                {"id": step, "route": "/", "selector": "#step"}
                for step in (
                    "hero",
                    "silver-search",
                    "silver-evidence",
                    "population-shape",
                    "population-concentration",
                    "facts-open",
                    "gold-repeat-window",
                    "map-only",
                    "receipt",
                )
            ]
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "bell.demo-video.v1",
                "mode": "long",
                "base": "https://bell.dyplux.com",
                "captured_at": "2026-09-22T07:50:17Z",
                "receipt": {
                    "status": "fresh",
                    "observed_at": "2026-09-22T07:39:11Z",
                    "published_at": "2026-09-22T07:39:32Z",
                    "tokenised_references": 791,
                    "representations": 1435,
                },
                "steps": steps,
                "console_errors": [],
                "video": video.name,
            }), encoding="utf-8")
            result = verify(manifest)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["steps"], 9)


if __name__ == "__main__":
    unittest.main()

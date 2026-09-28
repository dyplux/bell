"""The live publisher's credential-free marker must reproduce from public inputs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from verify_integrity_receipt import verify_public_inputs  # noqa: E402

PROOF = HERE.parent / "site" / "proof"
INPUTS = PROOF / "rwa-surface-integrity-inputs-2026-09-21.json"
RECEIPT = PROOF / "rwa-surface-integrity-latest-replay-2026-09-21.json"

PROVENANCE = {
    "mode": "server_side_authenticated_collection",
    "credential_free": True,
    "api_key_published": False,
    "transport_headers_published": False,
    "replay_index_url": "/proof/rwa-surface-integrity-replay-index.md",
    "replay_package_note": "The live receipt is current; the linked replay package is a dated credential-free recomputation artifact.",
}


class LiveCollectionProvenanceTests(unittest.TestCase):
    def test_publisher_envelope_recomputes_from_the_public_input_package(self):
        published = json.loads(RECEIPT.read_text(encoding="utf-8"))
        published["collection_provenance"] = copy.deepcopy(PROVENANCE)
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipt.json"
            receipt_path.write_text(json.dumps(published), encoding="utf-8")
            self.assertIsNone(verify_public_inputs(INPUTS, receipt_path))

    def test_unrecognized_provenance_is_refused(self):
        published = json.loads(RECEIPT.read_text(encoding="utf-8"))
        published["collection_provenance"] = {**PROVENANCE, "api_key_published": True}
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "receipt.json"
            receipt_path.write_text(json.dumps(published), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "credential-free marker"):
                verify_public_inputs(INPUTS, receipt_path)


if __name__ == "__main__":
    unittest.main()

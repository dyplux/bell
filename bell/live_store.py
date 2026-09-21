"""Small credential-free store for the latest Bell research outputs.

The store is intentionally boring: JSON files, atomic replacement and no API key.
It is the Mac mini adapter for the eventual Cloudflare D1/KV publication layer.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


SAFE_SLUG = re.compile(r"^[a-z0-9-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LiveStore:
    def __init__(self, root: Path | None = None) -> None:
        configured = os.environ.get("BELL_STORE_DIR")
        self.root = root or Path(configured or Path(__file__).resolve().parent / "runtime")

    def _path(self, kind: str, slug: str) -> Path:
        if not SAFE_SLUG.fullmatch(slug):
            raise ValueError("invalid RWA slug")
        if not SAFE_SLUG.fullmatch(kind):
            raise ValueError("invalid store kind")
        return self.root / kind / f"{slug}.json"

    def read(self, kind: str, slug: str) -> dict[str, Any] | None:
        path = self._path(kind, slug)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None

    def write(self, kind: str, slug: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = self._path(kind, slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": "bell.live.store.v1",
            "kind": kind,
            "slug": slug,
            "published_at": utc_now(),
            "observed_at": payload.get("observed_at") or payload.get("provenance", {}).get("observed_at"),
            "credential_free": True,
            "cache_policy": {
                "public_max_age_seconds": int(os.environ.get("BELL_PUBLIC_MAX_AGE_SECONDS", "30")),
                "stale_after_seconds": int(os.environ.get("BELL_FRESHNESS_SECONDS", "3600")),
                "stale_serving": True,
            },
            "payload": payload,
        }
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        temporary.replace(path)
        return record

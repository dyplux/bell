#!/usr/bin/env python3
"""Small optional server for Bell's on-demand live RWA terminal.

Static files remain safe and work without this server. The server exposes the credential-free
published cache at /api/published?slug=tesla. When started with CMC_API_KEY, it can also collect
one selected asset at /api/rwa?slug=tesla, load the full deterministic terminal dossier at
/api/terminal?slug=tesla, run a comparability audit at /api/audit?slug=tesla, or run a session
review at /api/session?slug=tesla&days=7. The key stays server-side and is never returned.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from functools import partial
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bell import BellDataError, CMCClient, fetch_live_asset, fetch_live_dataset
from engine import analyse_dataset
from rwa_audit import audit_rwa_evidence, collect_rwa_evidence
from terminal import build_terminal_summary
from live_store import LiveStore


ROOT = Path(__file__).resolve().parent
STORE = LiveStore()


def publication_status(record: dict) -> dict:
    published_at = record.get("published_at")
    age_seconds = None
    if published_at:
        try:
            age_seconds = max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(published_at)).total_seconds())
        except ValueError:
            pass
    try:
        fresh_seconds = max(60, int(os.environ.get("BELL_FRESHNESS_SECONDS", "3600")))
    except ValueError:
        fresh_seconds = 3600
    return {
        "status": "fresh" if age_seconds is not None and age_seconds <= fresh_seconds else "stale",
        "age_seconds": round(age_seconds) if age_seconds is not None else None,
        "stale_after_seconds": fresh_seconds,
        "refresh_queued": False,
    }


class BellHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path not in ("/api/rwa", "/api/session", "/api/audit", "/api/terminal", "/api/published"):
            super().do_GET()
            return
        slug = parse_qs(parsed.query).get("slug", [""])[0].strip().lower()
        if not slug or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in slug):
            self._json(400, {"error": "a valid RWA slug is required"})
            return
        if parsed.path == "/api/published":
            record = STORE.read("terminal", slug)
            if not record:
                self._json(404, {"status": "missing", "error": "no published dossier exists for this RWA yet"})
                return
            payload = dict(record.get("payload", {}))
            payload["_publication"] = {
                "source": "bell.live.store",
                "published_at": record.get("published_at"),
                "observed_at": record.get("observed_at"),
                "credential_free": True,
                **publication_status(record),
            }
            self._json(200, payload, cache_control="public, max-age=30, stale-while-revalidate=300")
            return
        api_key = os.environ.get("CMC_API_KEY")
        if not api_key:
            self._json(503, {"error": "live dossier unavailable; set CMC_API_KEY on the server"})
            return
        try:
            client = CMCClient(api_key)
            if parsed.path in ("/api/audit", "/api/terminal"):
                evidence = collect_rwa_evidence(client, slug)
                audit = audit_rwa_evidence(evidence)
                if parsed.path == "/api/terminal":
                    terminal_evidence = {**evidence, "findings": audit["findings"]}
                    dossier = {"terminal": build_terminal_summary(terminal_evidence), "audit": audit}
                else:
                    dossier = audit
            elif parsed.path == "/api/session":
                try:
                    days = int(parse_qs(parsed.query).get("days", ["7"])[0])
                except ValueError:
                    self._json(400, {"error": "days must be an integer"})
                    return
                if days < 1 or days > 30:
                    self._json(400, {"error": "days must be between 1 and 30"})
                    return
                payload = fetch_live_dataset(client, slug, days)
                dossier = analyse_dataset(payload, min_bars_per_session=3)
            else:
                dossier = fetch_live_asset(client, slug)
            if parsed.path == "/api/terminal":
                STORE.write("terminal", slug, dossier)
            elif parsed.path == "/api/audit":
                STORE.write("audit", slug, dossier)
        except BellDataError as exc:
            self._json(502, {"error": str(exc)})
            return
        self._json(200, dossier)

    def _json(self, status: int, payload: dict, cache_control: str = "no-store") -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Bell's offline site with an optional live RWA dossier endpoint")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    handler = partial(BellHandler, directory=str(ROOT / "site"))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Bell listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

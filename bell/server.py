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
import ipaddress
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
INTEGRITY_CAPTURE = ROOT / "site" / "proof" / "rwa-surface-integrity-capture-2026-09-28.json"


AGENT_MANIFEST = {
    "schema_version": "bell.agent-manifest.v1",
    "name": "Bell RWA Research API",
    "description": "Local, evidence-first CMC RWA research. Returns raw reported fields and deterministic Bell analysis, not investment advice.",
    "authentication": {
        "setup": "POST /api/key with JSON {\"api_key\": \"...\"}; key is held in local server memory only until restart or DELETE /api/key.",
        "environment": "CMC_API_KEY may instead be set in the server process environment.",
        "transport": "CMC requests are made server-side; the browser and agent API responses never receive the key.",
    },
    "tools": [
        {"name": "bell_catalogue_receipt", "method": "GET", "path": "/api/integrity", "description": "Read the committed, dated, credential-free population receipt; no CMC call."},
        {"name": "bell_search_catalogue", "method": "GET", "path": "/api/catalog?q={query}&limit=10", "description": "Search the committed 7,811-entry CMC RWA map snapshot without credentials or a live request."},
        {"name": "bell_agent_manifest", "method": "GET", "path": "/api/agent", "description": "Read this tool manifest."},
        {"name": "bell_live_asset", "method": "GET", "path": "/api/rwa?slug={rwa_slug}", "description": "Fetch one CMC RWA quote dossier; makes a live CMC request and may consume plan quota."},
        {"name": "bell_live_terminal", "method": "GET", "path": "/api/terminal?slug={rwa_slug}", "description": "Fetch one RWA evidence dossier and deterministic terminal summary; live CMC requests may consume plan quota."},
        {"name": "bell_live_audit", "method": "GET", "path": "/api/audit?slug={rwa_slug}", "description": "Run one comparability audit from live CMC evidence; live CMC requests may consume plan quota."},
        {"name": "bell_live_session", "method": "GET", "path": "/api/session?slug={rwa_slug}&days=7", "description": "Fetch one hourly session review (1–30 days); live CMC requests may consume plan quota."},
        {"name": "bell_key_status", "method": "GET", "path": "/api/key", "description": "Check whether this local server has a CMC key configured; never returns the key."},
    ],
}


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
    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if urlparse(self.path).path != "/api/key":
            self._json(404, {"error": "unknown local API route"})
            return
        if not self._is_loopback_request():
            self._json(403, {"error": "key setup is available only from this local machine"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 8192:
                raise ValueError("request body must be between 1 and 8192 bytes")
            body = json.loads(self.rfile.read(length))
            api_key = body.get("api_key") if isinstance(body, dict) else None
            if (not isinstance(api_key, str) or not api_key.strip() or len(api_key) > 4096
                    or any(ord(char) < 32 for char in api_key)):
                raise ValueError("enter a valid CMC API key")
        except (ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
            return
        self.server.session_api_key = api_key.strip()
        self._json(200, {"configured": True, "storage": "server memory only", "key_returned": False})

    def do_DELETE(self) -> None:  # noqa: N802 - stdlib handler API
        if urlparse(self.path).path != "/api/key":
            self._json(404, {"error": "unknown local API route"})
            return
        if not self._is_loopback_request():
            self._json(403, {"error": "key management is available only from this local machine"})
            return
        self.server.session_api_key = None
        self._json(200, {"configured": bool(os.environ.get("CMC_API_KEY")), "cleared_from_memory": True})

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path == "/api/agent":
            self._json(200, AGENT_MANIFEST)
            return
        if parsed.path == "/api/catalog":
            query = parse_qs(parsed.query).get("q", [""])[0].strip().lower()
            if not query or len(query) > 120:
                self._json(400, {"error": "a query between 1 and 120 characters is required"})
                return
            try:
                catalogue = json.loads((ROOT / "site" / "catalog.json").read_text(encoding="utf-8"))
                limit = min(25, max(1, int(parse_qs(parsed.query).get("limit", ["10"])[0])))
            except (OSError, json.JSONDecodeError, ValueError):
                self._json(503, {"error": "the dated RWA catalogue is unavailable"})
                return
            words = query.split()
            ranked = []
            for asset in catalogue.get("assets", []):
                name = str(asset.get("name", "")).lower()
                symbol = str(asset.get("symbol", "")).lower()
                slug = str(asset.get("slug", "")).lower()
                rwa_id = str(asset.get("rwa_id", ""))
                searchable = f"{name} {symbol} {slug} {rwa_id} {asset.get('asset_type', '')}".lower()
                if query.isdigit() and rwa_id == query:
                    score = 0
                elif name == query or symbol == query or slug == query:
                    score = 1
                elif name.startswith(query) or symbol.startswith(query) or slug.startswith(query):
                    score = 2
                elif all(word in searchable for word in words):
                    score = 3
                else:
                    continue
                ranked.append((score, name, asset))
            ranked.sort(key=lambda item: (item[0], item[1]))
            self._json(200, {
                "schema_version": "bell.catalog-search.v1",
                "source": "committed dated CMC RWA map snapshot",
                "observed_at": catalogue.get("observed_at"),
                "query": query,
                "total_matches": len(ranked),
                "results": [item[2] for item in ranked[:limit]],
                "credential_free": True,
                "live_cmc_call": False,
            })
            return
        if parsed.path == "/api/key":
            self._json(200, {"configured": bool(getattr(self.server, "session_api_key", None) or os.environ.get("CMC_API_KEY")), "storage": "server memory only"})
            return
        if parsed.path == "/api/integrity":
            try:
                payload = json.loads(INTEGRITY_CAPTURE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self._json(503, {"error": "the dated integrity receipt is unavailable"})
                return
            payload["_publication"] = {
                "source": "bell.site.proof dated capture",
                "observed_at": payload.get("observed_at"),
                "status": "dated replay",
                "credential_free": True,
            }
            self._json(200, payload, cache_control="no-store")
            return
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
        api_key = getattr(self.server, "session_api_key", None) or os.environ.get("CMC_API_KEY")
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

    def _is_loopback_request(self) -> bool:
        try:
            peer = ipaddress.ip_address(self.client_address[0]).is_loopback
            host = urlparse("//" + self.headers.get("Host", "")).hostname
            host_ok = host in {"localhost", "127.0.0.1", "::1"}
            origin = self.headers.get("Origin")
            origin_ok = origin is None or urlparse(origin).hostname in {"localhost", "127.0.0.1", "::1"}
            return peer and host_ok and origin_ok
        except ValueError:
            return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve Bell's offline site with an optional live RWA dossier endpoint")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    handler = partial(BellHandler, directory=str(ROOT / "site"))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    server.session_api_key = None
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

#!/usr/bin/env python3
"""Publish a fresh Bell dossier into the local credential-free live store.

This is the process a Mac mini launchd job can run on a schedule. The public
website reads the resulting store through Bell's HTTP API; it never receives
the CMC key.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bell import BellDataError, CMCClient
from live_store import LiveStore
from rwa_audit import audit_rwa_evidence, collect_rwa_evidence
from terminal import build_terminal_summary


PUBLISHER_USER_AGENT = "Dyplux-Bell-Publisher/1.0"


def publish(slug: str, store: LiveStore, client: CMCClient) -> dict:
    evidence = collect_rwa_evidence(client, slug)
    audit = audit_rwa_evidence(evidence)
    dossier = {
        "terminal": build_terminal_summary({**evidence, "findings": audit["findings"]}),
        "audit": audit,
    }
    record = store.write("terminal", slug, dossier)
    store.write("audit", slug, audit)
    remote_status = publish_remote(slug, dossier, evidence, record)
    return {
        "slug": slug,
        "conclusion": audit.get("conclusion"),
        "token_count": len(evidence.get("tokens", [])),
        "observed_at": evidence.get("observed_at"),
        "published_at": record.get("published_at"),
        "store": str(store.root),
        **remote_status,
    }


def publish_remote(slug: str, dossier: dict, evidence: dict, record: dict) -> dict:
    endpoint = os.environ.get("BELL_PUBLICATION_URL")
    token = os.environ.get("PUBLISHER_TOKEN")
    if not endpoint:
        return {"remote_published": False, "remote": "not_configured"}
    if not token:
        raise BellDataError("BELL_PUBLICATION_URL is set but PUBLISHER_TOKEN is missing")
    body = json.dumps({
        "slug": slug,
        "dossier": dossier,
        "observed_at": evidence.get("observed_at"),
        "published_at": record.get("published_at"),
    }).encode("utf-8")
    request = Request(endpoint, data=body, method="POST", headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": PUBLISHER_USER_AGENT,
    })
    try:
        with urlopen(request, timeout=30) as response:
            if response.status < 200 or response.status >= 300:
                raise BellDataError(f"remote publication returned HTTP {response.status}")
    except HTTPError as exc:
        raise BellDataError(f"remote publication returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise BellDataError(f"remote publication failed: {exc.reason}") from exc
    return {"remote_published": True, "remote": endpoint}


def pull_remote_jobs(limit: int) -> list[dict]:
    endpoint = os.environ.get("BELL_JOBS_URL")
    token = os.environ.get("PUBLISHER_TOKEN")
    if not endpoint:
        raise BellDataError("--pull-queue requires BELL_JOBS_URL")
    if not token:
        raise BellDataError("--pull-queue requires PUBLISHER_TOKEN")
    separator = "&" if "?" in endpoint else "?"
    request = Request(f"{endpoint}{separator}limit={max(1, min(limit, 20))}", headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": PUBLISHER_USER_AGENT,
    })
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise BellDataError(f"job queue returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise BellDataError(f"job queue failed: {exc.reason}") from exc
    return [item for item in payload.get("jobs", []) if isinstance(item, dict) and item.get("slug")]


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish current CMC RWA dossiers into Bell's live store")
    parser.add_argument("slugs", nargs="*", help="CMC RWA slugs to refresh")
    parser.add_argument("--pull-queue", action="store_true", help="lease refresh jobs from BELL_JOBS_URL")
    parser.add_argument("--limit", type=int, default=5, help="maximum queued jobs to lease")
    args = parser.parse_args()
    api_key = os.environ.get("CMC_API_KEY")
    if not api_key:
        parser.error("CMC_API_KEY must be set on the publisher machine")
    client = CMCClient(api_key)
    store = LiveStore()
    queued = pull_remote_jobs(args.limit) if args.pull_queue else []
    slugs = list(args.slugs) + [job["slug"] for job in queued]
    if not slugs:
        if args.pull_queue:
            print(json.dumps({"schema_version": "bell.publisher.run.v1", "results": []}, indent=2))
            return 0
        parser.error("provide at least one slug or use --pull-queue")
    results = []
    for slug in dict.fromkeys(slugs):
        try:
            result = publish(slug.strip().lower(), store, client)
            matching_job = next((job for job in queued if job["slug"] == slug), None)
            if matching_job:
                result["job_id"] = matching_job.get("id")
            results.append(result)
        except BellDataError as exc:
            results.append({"slug": slug, "error": str(exc)})
    print(json.dumps({"schema_version": "bell.publisher.run.v1", "results": results}, indent=2))
    return 1 if any("error" in result for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify that the checked-in Bell surface is safe and complete to submit.

This is a deterministic release gate. It deliberately inspects the Git index
and the public-facing files, rather than treating the presence of a local
working file as evidence that it will be included in the public repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "bell/README.md",
    "bell/JUDGE.md",
    "bell/USER-GUIDE.md",
    "bell/VIDEO-DEMO-SCRIPT.md",
    "bell/site/index.html",
    "bell/site/integrity.js",
    "bell/site/explorer.js",
    "bell/site/catalog.json",
    "bell/site/proof/rwa-surface-integrity-latest-replay-2026-09-21.json",
    "bell/site/proof/rwa-surface-integrity-inputs-2026-09-21.json",
    "bell/verify_integrity_receipt.py",
    "bell/verify_public_surface.py",
    "cloudflare/src/index.js",
    "cloudflare/wrangler.toml",
)

FORBIDDEN_PATH_PARTS = (
    "/jury/",
    "/reference/competitors-cmc-hackathon/",
    "/research/hackathon-2026/",
)

FORBIDDEN_BASENAMES = {
    "AGENT-ACCESS.md",
    ".env",
    ".dev.vars",
}

PUBLIC_TEXT_FILES = (
    "README.md",
    "bell/README.md",
    "bell/JUDGE.md",
    "bell/USER-GUIDE.md",
    "bell/VIDEO-DEMO-SCRIPT.md",
    "bell/site/index.html",
    "bell/site/integrity.js",
    "bell/site/explorer.js",
    "docs/PRODUCT.md",
    "docs/ARCHITECTURE.md",
)

FORBIDDEN_PUBLIC_TEXT = (
    re.compile(r"macro\s*bombastic", re.IGNORECASE),
    re.compile(r"works\s+at\s+coinmarketcap", re.IGNORECASE),
    re.compile(r"coinmarketcap\s+employee", re.IGNORECASE),
    re.compile(r"personal\s+hackathon", re.IGNORECASE),
    re.compile(r"xai-[A-Za-z0-9_-]{16,}"),
    re.compile(r"CMC_DYPLUX_API_KEY\s*=", re.IGNORECASE),
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [item for item in result.stdout.decode().split("\0") if item]


def fail(messages: list[str]) -> int:
    for message in messages:
        print(f"FAIL: {message}")
    return 1


def main() -> int:
    failures: list[str] = []
    files = tracked_files()
    tracked = set(files)

    for relative in REQUIRED_FILES:
        if relative not in tracked or not (ROOT / relative).is_file():
            failures.append(f"required public file is not tracked: {relative}")

    for relative in files:
        normalized_path = relative.replace("\\", "/")
        normalized = f"/{normalized_path}"
        if any(part in normalized for part in FORBIDDEN_PATH_PARTS):
            failures.append(f"private path is tracked: {relative}")
        if Path(relative).name in FORBIDDEN_BASENAMES:
            failures.append(f"secret-bearing filename is tracked: {relative}")

    for relative in PUBLIC_TEXT_FILES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_PUBLIC_TEXT:
            if pattern.search(text):
                failures.append(f"identity or credential disclosure in public file: {relative}")
        if "FACTUAL COMPARISON OPEN" in text or "INVESTIGATE BEFORE SHORTLIST" in text:
            failures.append(f"stale public state vocabulary: {relative}")
        if relative.endswith(("index.html", "integrity.js", "explorer.js")):
            if "FACTS OPEN" not in text:
                failures.append(f"public state vocabulary missing FACTS OPEN: {relative}")

    index_text = (ROOT / "bell/site/index.html").read_text(encoding="utf-8")
    if 'data-filter="no_flags">FACTS OPEN</button>' not in index_text:
        failures.append("public population filter is not labelled FACTS OPEN")
    if 'href="#explorer"' not in index_text or 'id="explorer"' not in index_text:
        failures.append("single-URL explorer route is missing")
    for marker in ('property="og:title"', 'property="og:description"', 'name="twitter:card"'):
        if marker not in index_text:
            failures.append(f"share preview metadata is missing: {marker}")

    if failures:
        return fail(failures)

    print(f"submission gate: ok ({len(files)} tracked files inspected)")
    print("public state vocabulary: FACTS OPEN / INVESTIGATE / DO NOT SHORTLIST / SINGLE REPRESENTATION")
    print("private paths and identity disclosures: none found in the public surface")
    return 0


if __name__ == "__main__":
    sys.exit(main())

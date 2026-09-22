#!/usr/bin/env python3
"""Check that relative Markdown links in the public Bell docs resolve."""

from __future__ import annotations

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^]]+\]\(([^)]+)\)")


def main() -> int:
    failures: list[str] = []
    for path in sorted((ROOT / "bell").rglob("*.md")):
        for link in LINK_RE.findall(path.read_text(errors="ignore")):
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = link.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: {link}")
    if failures:
        print("broken documentation links:")
        print("\n".join(failures))
        return 1
    print("documentation links: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

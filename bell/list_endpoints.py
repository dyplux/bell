#!/usr/bin/env python3
"""The CMC endpoints this repository calls, read out of the source.

Four documents listed these by hand and gave four different answers: the judge
page said 7 RWA and 17 total and was right; ARCHITECTURE.md listed 5 and omitted
`cryptocurrency/info`, whose digest ships in every receipt's `source_hashes`;
JUDGE.md listed 7 and omitted the same one; SOURCE-MAP.md, titled "Exact CMC
surfaces", listed 8 and omitted `cryptocurrency/info`, the singular `issuers`,
`key/info` and all six `/v1/dex/*` while including two the population scan never
calls. A reviewer found all four.

"17 endpoints" was also doing more work than it should. Every one has a real
call site, so the number is not invented, but the published product's scan calls
six of them; the rest live in a key-gated per-asset audit path a judge cannot
exercise, and one of those the Startup plan refuses outright. This prints the
breakdown that sentence needs, so the documents can state what the product does
rather than what the repository contains.

    PYTHONPATH=bell python3 bell/list_endpoints.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ENDPOINT = re.compile(r'["\'](/v\d+/[a-z0-9/_-]+)["\']')

# The module that performs the published population scan. Everything it calls is
# something a judge can exercise from the shipped receipt; everything else needs
# a credential and the per-asset audit path.
SCAN_MODULE = "rwa_integrity.py"
RWA_FAMILY = "/v5/real-world-assets/"
# Refused on the Startup plan. Recorded in words by the receipt rather than
# filled with a zero, which is the point, but it has never returned data.
PLAN_REFUSED = "/v5/real-world-assets/market-pairs/list"


def endpoints_by_module() -> dict:
    found: dict = {}
    for path in sorted(HERE.glob("*.py")):
        # A trailing slash is a base path the code concatenates onto, not an
        # endpoint. Counting it gave 18 and 8, one more than the judge page,
        # which was the generator being wrong rather than the page.
        hits = sorted({endpoint for endpoint in ENDPOINT.findall(path.read_text(encoding="utf-8"))
                       if not endpoint.endswith("/")})
        if hits:
            found[path.name] = hits
    return found


def summarise() -> dict:
    by_module = endpoints_by_module()
    every = sorted({endpoint for hits in by_module.values() for endpoint in hits})
    scanned = sorted(set(by_module.get(SCAN_MODULE, [])))
    family = sorted(endpoint for endpoint in every if endpoint.startswith(RWA_FAMILY))
    return {
        "total": len(every),
        "endpoints": every,
        "published_scan": scanned,
        "published_scan_count": len(scanned),
        "rwa_family": family,
        "rwa_family_count": len(family),
        "plan_refused": [PLAN_REFUSED] if PLAN_REFUSED in every else [],
        "key_gated_audit_path": sorted(set(every) - set(scanned)),
        "by_module": by_module,
    }


def sentence(summary: dict) -> str:
    """The one sentence every document should carry, generated once."""
    return (f"{summary['published_scan_count']} endpoints in the published scan, "
            f"{len(summary['key_gated_audit_path'])} more in a key-gated audit path, "
            f"{summary['total']} distinct in total, of which "
            f"{summary['rwa_family_count']} are the dedicated RWA family and "
            f"{len(summary['plan_refused'])} is refused on the Startup plan")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    summary = summarise()
    if args.json:
        print(json.dumps(summary, indent=2))
        return 0
    print(sentence(summary))
    print()
    print(f"published scan ({summary['published_scan_count']}), in {SCAN_MODULE}:")
    for endpoint in summary["published_scan"]:
        print(f"  {endpoint}")
    print(f"\nkey-gated audit path ({len(summary['key_gated_audit_path'])}):")
    for endpoint in summary["key_gated_audit_path"]:
        note = "  (Startup plan refuses this)" if endpoint in summary["plan_refused"] else ""
        print(f"  {endpoint}{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

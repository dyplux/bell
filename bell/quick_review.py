#!/usr/bin/env python3
"""The 30-second Bell path: one RWA, one evidence gate, one next action.

Offline is the default and reads a dated, credential-free CMC audit. ``--live``
uses CMC_API_KEY only in the process and emits the same deterministic shape.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from engine import canonical_digest


ROOT = Path(__file__).resolve().parent
FIXTURES = {
    "gold": ROOT / "docs/proof/gold-rwa-audit-2026-09-14.json",
    "tesla": ROOT / "docs/proof/tesla-rwa-audit-2026-09-14.json",
}


def load_review(asset: str, live: bool) -> dict:
    if live:
        from rwa_audit import run_live
        result = run_live(asset)
        result["run_mode"] = "live_cmc"
        return result
    path = FIXTURES.get(asset)
    if not path or not path.exists():
        raise ValueError(f"no bundled review for {asset}; choose gold or tesla, or use --live")
    result = json.loads(path.read_text(encoding="utf-8"))
    result["run_mode"] = "dated_offline_receipt"
    result["source_file"] = str(path.relative_to(ROOT))
    return result


def render(result: dict) -> str:
    asset = result.get("asset", {})
    findings = result.get("findings", [])
    conclusion = result.get("conclusion", "unknown")
    evidence = result.get("evidence", {})
    tokens = evidence.get("tokens", []) if isinstance(evidence, dict) else []
    next_action = {
        "do_not_compare": "Resolve denomination, representation and market-data contradictions before comparing prices or ranking wrappers.",
        "investigate": "Separate issuer, ticker, derivative and venue evidence before treating the wrappers as peers.",
        "provisionally_comparable": "Run the session review and repeat it across four independent windows before making a persistence claim.",
        "insufficient_evidence": "Load the missing token, issuer or market evidence; do not convert absence into zero.",
    }.get(conclusion, "Collect more evidence before making a comparison.")
    lines = [
        "BELL / RWA COMPARABILITY REVIEW",
        "=" * 32,
        f"Reference: {asset.get('name', 'unknown')} ({asset.get('symbol', '—')})",
        f"CMC token layer: {len(tokens)} representation(s)",
        f"Verdict: {conclusion.replace('_', ' ').upper()}",
        "",
        "Question:",
        "Can the representations grouped under this CMC reference be compared as if they were the same exposure?",
        "",
        "Findings:",
    ]
    if findings:
        lines.extend(f"[{item.get('severity', 'unknown').upper()}] {str(item.get('code') or 'finding').upper()}: {item.get('message')}" for item in findings)
    else:
        lines.append("No deterministic contradiction was returned.")
    lines += ["", "Next action:", next_action, "", "Execution boundary:", "CMC evidence can expose quoted price, volume and venue surfaces when returned. It does not provide a size-specific executable quote, depth guarantee or settlement route.", "", "Evidence rule:", "CMC fields are observations. This review does not prove backing, redemption, legal eligibility, liquidity or suitability."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Bell's 30-second RWA comparability review")
    parser.add_argument("--asset", default="gold", choices=sorted(FIXTURES))
    parser.add_argument("--live", action="store_true", help="fetch CMC evidence with CMC_API_KEY from the process")
    parser.add_argument("--output", type=Path, help="write the credential-free JSON review")
    args = parser.parse_args(argv)
    try:
        result = load_review(args.asset, args.live)
    except Exception as exc:
        print(f"bell-quick-review: {exc}", file=sys.stderr)
        return 2
    result["observed_or_loaded_at"] = datetime.now(timezone.utc).isoformat()
    result["evidence_hash"] = canonical_digest(result.get("evidence", result))
    print(render(result), end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

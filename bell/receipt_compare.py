#!/usr/bin/env python3
"""Compare two credential-free Bell session receipts and their payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def flat_bar_stats(payload: dict[str, Any]) -> dict[str, Any]:
    bars = [bar for wrapper in payload.get("wrappers", []) for bar in wrapper.get("bars", []) if isinstance(bar, dict)]
    flat = [bar for bar in bars if float(bar.get("high", 0)) == float(bar.get("low", 0))]
    return {
        "bars": len(bars),
        "flat_bars": len(flat),
        "flat_pct": round(len(flat) / len(bars) * 100, 4) if bars else None,
    }


def compare(before: dict[str, Any], after: dict[str, Any], before_payload: dict[str, Any] | None = None, after_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    old = {row["symbol"]: row for row in before.get("wrappers", [])}
    new = {row["symbol"]: row for row in after.get("wrappers", [])}
    rows = []
    for symbol in sorted(set(old) | set(new)):
        old_row = old.get(symbol)
        new_row = new.get(symbol)
        sessions = {}
        for name in ("cash", "after_hours", "weekend"):
            old_value = (old_row or {}).get("sessions", {}).get(name, {}).get("median_range_pct")
            new_value = (new_row or {}).get("sessions", {}).get(name, {}).get("median_range_pct")
            sessions[name] = {
                "before": old_value,
                "after": new_value,
                "delta": round(new_value - old_value, 8) if old_value is not None and new_value is not None else None,
            }
        rows.append({
            "symbol": symbol,
            "issuer_before": (old_row or {}).get("issuer"),
            "issuer_after": (new_row or {}).get("issuer"),
            "state_before": (old_row or {}).get("state"),
            "state_after": (new_row or {}).get("state"),
            "sessions": sessions,
        })
    result = {
        "schema_version": "bell.receipt-comparison.v1",
        "asset_before": before.get("asset", {}),
        "asset_after": after.get("asset", {}),
        "window_before": before.get("window", {}),
        "window_after": after.get("window", {}),
        "wrappers": rows,
        "flat_bar_diagnostics": {
            "before": flat_bar_stats(before_payload) if before_payload else None,
            "after": flat_bar_stats(after_payload) if after_payload else None,
        },
        "limitations": [
            "A delta describes two observed windows; it does not establish causality or persistence.",
            "Flat bars are a data-quality diagnostic, not proof of a closed market or zero liquidity.",
            "The comparison preserves each receipt's timezone, coverage and warnings rather than silently normalising them.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two Bell session receipts")
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--before-payload")
    parser.add_argument("--after-payload")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = compare(load(args.before), load(args.after), load(args.before_payload) if args.before_payload else None, load(args.after_payload) if args.after_payload else None)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

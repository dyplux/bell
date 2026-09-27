#!/usr/bin/env python3
"""Neuter each guard in the evidence path and report the ones no test notices.

Three reviewers in a row did this by hand and found eight, then sixty-eight. It
is the single most productive thing anyone has done to this repository, and it
was entirely manual: edit a condition to `if False:`, run the gate, write down
whether anything went red, put it back.

So it is a command now. For every `if` in the guarded files it rewrites the
condition to a constant that makes the body unreachable, runs the offline gate,
and records whether the gate noticed. A guard nothing notices is not defended,
whatever its docstring says.

It is slow by construction - one full gate run per guard, about twelve seconds
each - so it is not part of `make check-offline` and never will be. It is what
you run before claiming a guard is covered.

    make mutate            # every guard, slow
    make mutate ONLY=append_history.py
    PYTHONPATH=bell python3 bell/mutate_the_guards.py --limit 10

The repository is restored after every mutation, including on interrupt.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

GUARDED = (
    "verify_integrity_receipt.py",
    "verify_case_receipt.py",
    "reference_series.py",
    "append_history.py",
    "history_chain.py",
)


def guards(path: Path) -> list:
    """Every `if` whose body raises or returns: the shape of a refusal."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        refuses = any(isinstance(inner, (ast.Raise, ast.Return))
                      for inner in ast.walk(node) if inner is not node)
        if refuses and node.test.col_offset >= 0:
            found.append((node.lineno, node.test.col_offset, node.end_lineno))
    return sorted(set(found))


def neuter(path: Path, lineno: int) -> str:
    """Rewrite one `if` condition so its body cannot run. Returns the original text."""
    original = path.read_text(encoding="utf-8")
    lines = original.split("\n")
    line = lines[lineno - 1]
    stripped = line.lstrip()
    if not stripped.startswith("if ") and not stripped.startswith("elif "):
        return ""
    indent = line[:len(line) - len(stripped)]
    keyword = "elif" if stripped.startswith("elif ") else "if"
    # Multi-line conditions: replace through to the line ending in a colon.
    end = lineno - 1
    while end < len(lines) and not lines[end].rstrip().endswith(":"):
        end += 1
    lines[lineno - 1:end + 1] = [f"{indent}{keyword} False:"]
    path.write_text("\n".join(lines), encoding="utf-8")
    return original


def gate_notices() -> bool:
    result = subprocess.run(["make", "check-offline"], cwd=str(ROOT),
                            capture_output=True, text=True)
    return result.returncode != 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="one filename from the guarded list")
    parser.add_argument("--limit", type=int, help="stop after this many guards")
    parser.add_argument("--output", default=str(HERE / "site" / "proof" / "guard-coverage.json"))
    args = parser.parse_args(argv)

    targets = [name for name in GUARDED if not args.only or name == args.only]
    if not targets:
        raise SystemExit(f"{args.only} is not one of {', '.join(GUARDED)}")

    survivors, checked = [], 0
    for name in targets:
        path = ROOT / "bell" / name
        if not path.exists():
            continue
        for lineno, _, _ in guards(path):
            if args.limit and checked >= args.limit:
                break
            original = neuter(path, lineno)
            if not original:
                continue
            checked += 1
            try:
                noticed = gate_notices()
            finally:
                path.write_text(original, encoding="utf-8")
            mark = "caught" if noticed else "SURVIVED"
            print(f"  {name}:{lineno} {mark}")
            if not noticed:
                survivors.append({"file": name, "line": lineno})

    receipt = {
        "schema_version": "bell.guard_coverage.v1",
        "guards_mutated": checked,
        "survivors": survivors,
        "note": ("Each guard's condition was rewritten so its body cannot run, and the offline "
                 "gate was run. A survivor is a refusal no test notices, whatever its docstring "
                 "says. Three reviewers found these by hand before this existed."),
    }
    Path(args.output).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    print(f"\n{checked} guards mutated, {len(survivors)} survived")
    if survivors:
        print("these refusals are defended by nothing:", file=sys.stderr)
        for entry in survivors:
            print(f"  {entry['file']}:{entry['line']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

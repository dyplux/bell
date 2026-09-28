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
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCHEMA = "bell.guard_coverage.v2"

GUARDED = (
    "verify_integrity_receipt.py",
    "verify_case_receipt.py",
    "reference_series.py",
    "append_history.py",
    "history_chain.py",
    # The engine and the measurement were outside this list, so "122 mutated, 0
    # survive" was a statement about the evidence chain and not about the files
    # that produce every published number. A reviewer found a filter in
    # rwa_integrity that had never excluded anything, because it read a field
    # CoinMarketCap does not send, and no sweep could have reported it: the
    # file was not in scope.
    "rwa_integrity.py",
    "base_rate.py",
)


# Guards that change no behaviour when neutered, each with the reason written
# down. A sweep cannot catch these by definition, and leaving them in the
# survivor list makes the number mean two different things at once: "nobody
# tested this" and "nothing could". They are counted separately and the reason
# ships in the receipt, so a reader can disagree with the argument rather than
# take the number on trust.
#
# Nothing goes in here because it was inconvenient. Each entry was neutered and
# the suite stayed green, and then the code was read to find out why.
STATED_EXCEPTIONS = {
    ("rwa_integrity.py", 89):
        "number() rejects None and bool before parsing. Decimal(str(True)) and "
        "Decimal(str(None)) both raise InvalidOperation, which the except below "
        "already turns into None, so removing this changes no result. It states the "
        "intent and saves a raise; it does not decide anything.",
    ("base_rate.py", 182):
        "The single-representation lens sorts every row through if/elif/elif/else, "
        "so its four parts always sum to the total and this can never fire today. It "
        "is a guard against a future edit that removes the catch-all, which is the "
        "change that would silently drop references from the partition. It replaced "
        "a bare assert that vanished under python3 -O.",
}


def guards(path: Path) -> list:
    """Every `if` whose body raises or returns: the shape of a refusal."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or is_entrypoint(node):
            continue
        refuses = any(isinstance(inner, (ast.Raise, ast.Return))
                      for inner in ast.walk(node) if inner is not node)
        if refuses and node.test.col_offset >= 0:
            found.append((node.lineno, node.test.col_offset, node.end_lineno))
    return sorted(set(found))


def is_entrypoint(node: ast.If) -> bool:
    """`if __name__ == "__main__": raise SystemExit(main())` is not a refusal.

    It was counted as one, because its body contains a `raise`, and no test can
    ever defend it: neutering it stops the file being runnable as a script and
    the offline gate does not run it as a script. So it survived every sweep
    and will survive every future one, holding the number one higher than the
    truth for a reason that has nothing to do with coverage. One file writes it
    with `raise SystemExit` and three with `sys.exit`, which is why only one of
    the five ever showed up: the count was measuring a style difference.
    """
    test = node.test
    return (isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name) and test.left.id == "__name__"
            and any(isinstance(value, ast.Constant) and value.value == "__main__"
                    for value in test.comparators))


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


def digest_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_digest() -> str:
    """One digest over the suite, because a survivor is a statement about it.

    "This guard is defended" is never a property of the guard alone: it means
    some test in this suite goes red when the guard stops refusing. Delete that
    test and the sentence becomes false while the guarded file, and therefore
    its digest, is untouched. That is the shape this repository keeps finding -
    a guard that vanishes when the evidence is removed - and the coverage
    receipt had it too.

    So a record is current only while both sources are: the file it mutated and
    the suite that judged it.
    """
    digest = hashlib.sha256()
    for path in sorted((HERE / "tests").rglob("*.py")):
        digest.update(path.relative_to(HERE).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def assemble(measured: dict) -> dict:
    """Build the receipt from the per-file records, and say what it did not measure.

    `make mutate ONLY=one_file.py` used to overwrite the whole receipt with one
    file's numbers, under a note that reads as a sweep of the repository. The
    version committed before this change said "41 guards mutated, 17 survived"
    and every one of those seventeen was in `verify_case_receipt.py`: the other
    four guarded files were not in that run at all. The published figure was
    three times better than the real one, and nothing read the file, so nothing
    disagreed.

    A partial run is the useful run - one file's guards take four minutes where
    the sweep takes twenty - so the fix is not to forbid it. It is to merge it
    into what is already known, keep each file's own count beside its own
    digest, and refuse to call the total a sweep while a file is missing.

    `complete` says what this receipt covers, not whether it is still current.
    The first version conflated the two and deadlocked the repository inside an
    hour: editing a test changed the suite digest, which made the stored
    `complete: true` a lie, which turned the gate red, and `make mutate`
    refuses to start on a red gate. A twenty-minute sweep cannot be the price
    of editing a test. So the receipt stores the facts that decide currency -
    the digest of each file it mutated and of the suite that judged it - and
    leaves the comparison against today to whoever reads it, which the tool
    does out loud on every run.
    """
    files = dict(sorted(measured.items()))
    missing = [name for name in GUARDED
               if (ROOT / "bell" / name).exists() and name not in files]
    survivors = sorted(
        ({"file": name, "line": line}
         for name, record in files.items() for line in record["survivors"]),
        key=lambda entry: (entry["file"], entry["line"]))
    complete = not missing
    scope = ("every guarded file" if complete else
             "part of the guarded set: " + ", ".join(missing) + " not measured")
    return {
        "schema_version": SCHEMA,
        "complete": complete,
        "scope": scope,
        "guards_mutated": sum(record["guards_mutated"] for record in files.values()),
        "files": files,
        "files_not_measured": missing,
        "survivors": survivors,
        "note": ("Each guard's condition was rewritten so its body cannot run, and the offline "
                 "gate was run. A survivor is a refusal no test notices, whatever its docstring "
                 "says. Three reviewers found these by hand before this existed. The totals are "
                 "the sum of the per-file records below and cover exactly the files listed "
                 "there, which is why `scope` and `complete` are in the receipt: one file's run "
                 "is not the repository's coverage. `complete` is about what was measured, not "
                 "about when. Whether a record still describes this tree is decided by its two "
                 "digests: source_digest is the file it mutated, suite_digest is the suite that "
                 "judged it, because 'this guard is defended' means a test in that suite goes "
                 "red when the guard stops refusing. Recompute both and you know."),
    }


def outdated(files: dict) -> list:
    """Records whose source or suite has moved since they were measured."""
    suite = suite_digest()
    return sorted(name for name, record in files.items()
                  if ((ROOT / "bell" / name).exists()
                      and record.get("source_digest") != digest_of(ROOT / "bell" / name))
                  or record.get("suite_digest") != suite)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="one filename from the guarded list")
    parser.add_argument("--limit", type=int, help="stop after this many guards")
    parser.add_argument("--output", default=str(HERE / "site" / "proof" / "guard-coverage.json"))
    parser.add_argument(
        "--rescope", action="store_true",
        help=("rewrite the receipt's scope from the current guarded set without measuring "
              "anything. Adding a file to GUARDED makes an existing receipt incomplete, which "
              "is true the moment the list changes and has nothing to do with running the "
              "gate: scope is a function of the list, measurement is not. Without this the "
              "repository deadlocks, because the receipt can only be corrected by a sweep and "
              "a sweep refuses to start on the red gate the stale receipt caused."))
    args = parser.parse_args(argv)

    if args.rescope:
        out = Path(args.output)
        measured = json.loads(out.read_text(encoding="utf-8")).get("files", {}) if out.exists() else {}
        receipt = assemble(measured)
        out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"rescoped: {receipt['scope']}")
        return 0

    targets = [name for name in GUARDED if not args.only or name == args.only]
    if not targets:
        raise SystemExit(f"{args.only} is not one of {', '.join(GUARDED)}")

    out = Path(args.output)
    measured = {}
    if out.exists():
        try:
            measured = json.loads(out.read_text(encoding="utf-8")).get("files", {})
        except json.JSONDecodeError:
            measured = {}
    # A partial run replaces the file it measured and leaves the rest of the
    # record alone. A --limit run measures no file to the end, so it is allowed
    # to print but never to claim a file's coverage.
    keep = args.limit is None

    # A survivor is read off a green gate going red. If the gate is already red
    # for some unrelated reason, every mutation reads as caught and this writes
    # a receipt saying every guard in the repository is defended - the exact
    # inversion of what the tool is for, and it would have been believed,
    # because a receipt full of zeroes is the result everyone is hoping for.
    if gate_notices():
        raise SystemExit("the gate is red before any guard was touched, so every mutation "
                         "would read as caught; fix `make check-offline` first")

    checked = 0
    for name in targets:
        path = ROOT / "bell" / name
        if not path.exists():
            continue
        found, here, excepted = guards(path), [], []
        for lineno, _, _ in found:
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
            stated = (name, lineno) in STATED_EXCEPTIONS
            mark = "caught" if noticed else ("stated" if stated else "SURVIVED")
            print(f"  {name}:{lineno} {mark}")
            if not noticed and not stated:
                here.append(lineno)
            elif not noticed and stated:
                excepted.append(lineno)
        if keep:
            measured[name] = {
                "guards_mutated": len(found),
                "survivors": sorted(here),
                "stated_exceptions": [
                    {"line": line, "reason": STATED_EXCEPTIONS[(name, line)]}
                    for line in sorted(excepted)],
                "source_digest": digest_of(path),
                "suite_digest": suite_digest(),
                "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

    receipt = assemble(measured)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    survivors = receipt["survivors"]
    print(f"\n{checked} guards mutated this run; "
          f"receipt covers {receipt['guards_mutated']} across "
          f"{len(receipt['files'])} file(s), {len(survivors)} survived")
    if not receipt["complete"]:
        print(f"this receipt is not a sweep: {receipt['scope']}", file=sys.stderr)
    behind = outdated(receipt["files"])
    if behind:
        print(f"measured against a source or a suite that has since changed, so these numbers "
              f"no longer describe this tree: {', '.join(behind)}", file=sys.stderr)
    if survivors:
        print("these refusals are defended by nothing:", file=sys.stderr)
        for entry in survivors:
            print(f"  {entry['file']}:{entry['line']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Reproduce the original 21 September observation with its frozen rule code.

The current-rule replay is kept separately as a dated comparison. This tool
replays the original distribution from the same six credential-free inputs and
checks the recovered publisher receipt and immutable history entry.
"""

from __future__ import annotations

import copy
import hashlib
import json
from types import ModuleType
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROOF = HERE / "site" / "proof"
SCANNER = HERE / "rwa_integrity_legacy_2026_09_21.py.txt"
RECEIPT = PROOF / "rwa-surface-integrity-original-2026-09-21.json"
INPUTS = PROOF / "rwa-surface-integrity-inputs-2026-09-21.json"
HISTORY = PROOF / "rwa-surface-integrity-history.json"

EXPECTED_SCANNER_SHA256 = "6bc17c2b4403f6c15eb149fec76297de71b7c2d47a4237407fecdfa6c13c5324"
EXPECTED_RECEIPT_SHA256 = "a878f175d9144dfbbc0e57771cf2183c3f8d2fe647a37a41f73b04cab468ea2b"
OBSERVED_AT = "2026-09-21T21:25:01Z"
KNOWN_POST_OBSERVATION_FIELDS = ("population_attribution", "rule_calibration")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must be a JSON object")
    return value


def load_scanner():
    module = ModuleType("bell_legacy_2026_09_21")
    source = SCANNER.read_text(encoding="utf-8")
    exec(compile(source, str(SCANNER), "exec"), module.__dict__)
    return module


def legacy_projection(value: dict) -> dict:
    """Remove only fields introduced after the original receipt was written."""
    result = copy.deepcopy(value)
    for field in KNOWN_POST_OBSERVATION_FIELDS:
        if field not in result:
            raise ValueError(f"frozen replay did not produce expected later field {field!r}")
        result.pop(field)
    return result


def verify() -> tuple[dict, dict]:
    scanner_hash = sha256(SCANNER)
    if scanner_hash != EXPECTED_SCANNER_SHA256:
        raise ValueError(f"frozen scanner SHA-256 changed: {scanner_hash}")
    receipt_hash = sha256(RECEIPT)
    if receipt_hash != EXPECTED_RECEIPT_SHA256:
        raise ValueError(f"original receipt SHA-256 changed: {receipt_hash}")

    original = read_json(RECEIPT)
    package = read_json(INPUTS)
    if original.get("observed_at") != OBSERVED_AT or package.get("observed_at") != OBSERVED_AT:
        raise ValueError("receipt and inputs must both describe 2026-09-21T21:25:01Z")
    if package.get("credential_free") is not True:
        raise ValueError("the replay inputs are not marked credential-free")
    surfaces = package.get("surfaces")
    names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
    if not isinstance(surfaces, dict) or any(name not in surfaces for name in names):
        raise ValueError("the 21 September package does not contain all six input surfaces")

    scanner = load_scanner()
    recomputed = scanner.scan(
        surfaces["map"], surfaces["asset_list"], surfaces["quotes"],
        surfaces["info"], surfaces["issuers"], observed_at=OBSERVED_AT,
        crypto_info_payload=surfaces["crypto_info"],
    )
    if legacy_projection(recomputed) != original:
        raise ValueError("frozen scanner output does not reproduce the recovered original receipt")

    history = read_json(HISTORY)
    matches = [item for item in history.get("observations", [])
               if item.get("observed_at") == OBSERVED_AT]
    if len(matches) != 1:
        raise ValueError("history must contain exactly one observation at the replay timestamp")
    observation = matches[0]
    universe = original.get("universe") or {}
    for field in ("tokenised_references_scanned", "tokens_scanned", "states", "signals"):
        if observation.get(field) != universe.get(field):
            raise ValueError(f"historical summary {field!r} does not match the original receipt")
    if observation.get("source_hashes") != original.get("source_hashes"):
        raise ValueError("historical source hashes do not match the original receipt")
    if observation.get("rules_version_recorded") is not False or observation.get("rules_version"):
        raise ValueError("the history no longer identifies this as a pre-versioned rule observation")
    return original, recomputed


def main() -> int:
    original, _ = verify()
    states = (original.get("universe") or {}).get("states") or {}
    print("legacy replay: verified (six shipped inputs, frozen scanner, original receipt, history)")
    print("observed_at: " + OBSERVED_AT)
    print("states: " + json.dumps(states, sort_keys=True))
    print("scanner sha256: " + EXPECTED_SCANNER_SHA256)
    print("receipt sha256: " + EXPECTED_RECEIPT_SHA256)
    print("provenance: receipt recovered from the local publisher runtime on 2026-09-29")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"legacy replay verification failed: {error}", file=sys.stderr)
        raise SystemExit(1)

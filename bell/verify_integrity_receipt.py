#!/usr/bin/env python3
"""Check the public shape and summary counts of Bell integrity receipts.

This verifier checks that the published history agrees with the bundled receipts
and that a credential-free normalized input package recomputes the latest
deterministic receipt. It does not recreate authenticated HTTP transport or
prove that the upstream source data is correct.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rwa_integrity import digest, scan

DEFAULT_HISTORY = ROOT / "site/proof/rwa-surface-integrity-history.json"
DEFAULT_RECEIPT = ROOT / "site/proof/rwa-surface-integrity-2026-09-15.json"
DEFAULT_LATEST = ROOT / "site/proof/rwa-surface-integrity-latest-replay-2026-09-21.json"
DEFAULT_INPUTS = ROOT / "site/proof/rwa-surface-integrity-inputs-2026-09-21.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def assert_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def verify_observation(observation: dict, receipt: dict, label: str) -> None:
    assert_equal(f"{label}.observed_at", receipt.get("observed_at"), observation["observed_at"])
    universe = receipt.get("universe")
    if not isinstance(universe, dict):
        raise ValueError(f"{label}.universe is missing")

    for field in ("tokenised_references_scanned", "tokens_scanned"):
        assert_equal(f"{label}.{field}", universe.get(field), observation[field])

    states = universe.get("states")
    if not isinstance(states, dict):
        raise ValueError(f"{label}.universe.states is missing")
    # A state is a function of the rules, so two receipts over the same
    # observation are only comparable when the same rules produced them. When
    # the rules change, the distribution changes without the catalogue moving -
    # reconciling that silently by overwriting the history would erase the fact
    # that it was the rules. Report it instead, and compare only within a
    # version.
    recorded_rules = observation.get("rules_version")
    current_rules = universe.get("rules_version")
    # An observation recorded before rule versioning existed carries no version.
    # That is itself a different version from the one running now, so it is
    # reported rather than compared.
    rules_differ = bool(current_rules) and recorded_rules != current_rules
    if rules_differ:
        recorded_rules = recorded_rules or "an unversioned rule set"
        print(
            f"{label}: recorded under {recorded_rules}, recomputed under {current_rules}; "
            f"states {observation['states']} -> {{{', '.join(f'{k!r}: {states.get(k)}' for k in observation['states'])}}}. "
            "State counts are not compared across rule versions."
        )
    else:
        assert_equal(
            f"{label}.states",
            {key: states.get(key) for key in observation["states"]},
            observation["states"],
        )
    if not rules_differ:
        assert_equal(f"{label}.state total", sum(observation["states"].values()), observation["tokenised_references_scanned"])

    signals = universe.get("signals")
    if not isinstance(signals, dict):
        raise ValueError(f"{label}.universe.signals is missing")
    assert_equal(
        f"{label}.signals",
        {key: signals.get(key) for key in observation["signals"]},
        observation["signals"],
    )

    verify_observation_shape(observation, label)


def verify_observation_shape(observation: dict, label: str) -> None:
    """Validate fields that remain checkable when the raw receipt is remote."""
    required = ("observed_at", "tokenised_references_scanned", "tokens_scanned", "states", "signals")
    for field in required:
        if field not in observation:
            raise ValueError(f"{label}.{field} is missing")
    if sum(observation["states"].values()) != observation["tokenised_references_scanned"]:
        raise ValueError(f"{label}.state total does not equal the scanned population")
    source_hashes = observation.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise ValueError(f"{label}.source_hashes is missing")
    for name, digest in source_hashes.items():
        if not SHA256.fullmatch(digest):
            raise ValueError(f"{label}.source_hashes.{name} is not a SHA-256 fingerprint")


def verify_public_inputs(inputs_path: Path, receipt_path: Path) -> None:
    package = load(inputs_path)
    receipt = load(receipt_path)
    if package.get("schema_version") != "bell.rwa_surface_integrity.inputs.v1":
        raise ValueError("unexpected public input package schema")
    if package.get("credential_free") is not True:
        raise ValueError("public input package must be credential-free")
    surfaces = package.get("surfaces")
    names = ("map", "asset_list", "quotes", "info", "issuers", "crypto_info")
    if not isinstance(surfaces, dict) or any(name not in surfaces for name in names):
        raise ValueError("public input package is missing a required surface")
    if package.get("observed_at") != receipt.get("observed_at"):
        raise ValueError("public input timestamp does not match the receipt")
    manifest = package.get("collection_manifest")
    if not isinstance(manifest, dict) or manifest.get("mode") != "server_side_authenticated_collection":
        raise ValueError("public input collection manifest is missing")
    for name in names:
        surface_manifest = manifest.get("surfaces", {}).get(name)
        if not isinstance(surface_manifest, dict) or surface_manifest.get("payload_sha256") != digest(surfaces[name]):
            raise ValueError(f"public input manifest hash does not match {name}")
        request_count = surface_manifest.get("request_count")
        successful_count = surface_manifest.get("successful_response_count")
        response_hashes = surface_manifest.get("response_sha256")
        status_codes = surface_manifest.get("status_codes")
        if request_count is not None or successful_count is not None or response_hashes is not None or status_codes is not None:
            if not isinstance(request_count, int) or request_count < 1:
                raise ValueError(f"invalid request count for {name}")
            if not isinstance(successful_count, int) or successful_count < 1 or successful_count > request_count:
                raise ValueError(f"invalid successful response count for {name}")
            if not isinstance(response_hashes, list) or len(response_hashes) != successful_count or any(not isinstance(value, str) or len(value) != 64 for value in response_hashes):
                raise ValueError(f"response hashes do not match response count for {name}")
            if not isinstance(status_codes, list) or len(status_codes) != request_count or any(not isinstance(value, int) for value in status_codes):
                raise ValueError(f"status codes do not match request count for {name}")
    recomputed = scan(
        surfaces["map"], surfaces["asset_list"], surfaces["quotes"],
        surfaces["info"], surfaces["issuers"],
        observed_at=package["observed_at"], crypto_info_payload=surfaces["crypto_info"],
    )
    if recomputed != receipt:
        raise ValueError("public input package does not recompute the bundled receipt")
    print(f"public inputs: verified ({inputs_path.stat().st_size:,} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--latest", type=Path, default=DEFAULT_LATEST)
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    args = parser.parse_args()

    history = load(args.history)
    if history.get("schema_version") != "bell.rwa_surface_integrity.history.v1":
        raise ValueError("unexpected history schema")
    if "raw authenticated responses" not in history.get("purpose", "").lower():
        raise ValueError("history purpose must disclose that raw responses are absent")
    observations = history.get("observations")
    if not isinstance(observations, list) or len(observations) < 2:
        raise ValueError("history must contain at least two published observations")

    dated_receipt = load(args.receipt)
    latest_receipt = load(args.latest)
    if not args.inputs.exists():
        raise ValueError(f"public input package is missing: {args.inputs}")
    verify_public_inputs(args.inputs, args.latest)
    bundled = {dated_receipt.get("observed_at"): (dated_receipt, "dated receipt"), latest_receipt.get("observed_at"): (latest_receipt, "latest receipt")}
    bundled_matches = 0
    for index, observation in enumerate(observations):
        label = f"history observation {index + 1}"
        verify_observation_shape(observation, label)
        match = bundled.get(observation["observed_at"])
        if match:
            verify_observation(observation, match[0], match[1])
            bundled_matches += 1
    if bundled_matches != len(bundled):
        raise ValueError("history is missing a bundled receipt observation")
    print(f"integrity receipt verification: ok ({len(observations)} observations)")
    print(f"bundled cross-checks: {bundled_matches}; remaining observations are public summaries")
    print(f"history sha256: {hashlib.sha256(args.history.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

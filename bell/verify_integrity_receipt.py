#!/usr/bin/env python3
"""Check the public shape and summary counts of Bell integrity receipts.

This verifier checks that the published history agrees with the bundled receipts
and that a credential-free normalized input package recomputes the latest
deterministic receipt. It does not recreate authenticated HTTP transport or
prove that the upstream source data is correct.
"""

from __future__ import annotations
from history_chain import verify as verify_chain

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rwa_integrity import RULES_VERSION, digest, scan

# What a bundled receipt is allowed to declare: the rule set the publisher
# stamps today, or nothing, which is what receipts written before versioning
# existed carry. Nothing else.
#
# The first version of this allowlist also admitted "bell.rules.v1", on the
# reasoning that it is a set this repository really published. That reasoning
# closed the hole for a version we never shipped and left it open for one we
# did: a reviewer added `"rules_version": "bell.rules.v1"` to a receipt whose
# history record carries none, which made the versions "differ", skipped the
# state comparison, and let a completely rewritten distribution through a green
# 306-test gate. Fixing one value of a field is not fixing the field.
#
# No code in this tree stamps v1. `integrity_publisher` writes RULES_VERSION,
# and receipts older than the field have it absent. A bundled receipt carrying
# any other value was edited after it was written.
ALLOWED_RULES_VERSIONS = frozenset({RULES_VERSION})

DEFAULT_HISTORY = ROOT / "site/proof/rwa-surface-integrity-history.json"
DEFAULT_RECEIPT = ROOT / "site/proof/rwa-surface-integrity-2026-09-15.json"
DEFAULT_LATEST = ROOT / "site/proof/rwa-surface-integrity-latest-replay-2026-09-21.json"
DEFAULT_INPUTS = ROOT / "site/proof/rwa-surface-integrity-inputs-2026-09-21.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")

# `verify_observation` required only "a non-empty dict" for source_hashes, and
# the comparison against the receipt is symmetric, so shrinking BOTH sides to
# one fingerprint agreed with itself and the gate went green over four deleted
# source digests.
#
# The floor is five, not six: `crypto_info` was added to the scan after the two
# oldest observations were published, and they really do record five. Demanding
# six would refuse honest history, which is the opposite failure and just as
# bad. Anything outside this vocabulary is a surface this code does not read.
REQUIRED_SOURCE_SURFACES = frozenset({"map", "asset_list", "quotes", "info", "issuers"})
KNOWN_SOURCE_SURFACES = REQUIRED_SOURCE_SURFACES | {"crypto_info"}


def load(path: Path) -> dict:
    # A truncated or corrupted file raised JSONDecodeError and printed a raw
    # traceback. A verifier exists to say what is wrong with the evidence, so
    # a reader who feeds it a half-written file should be told that, not shown
    # a stack. The exit code was already correct; the message was not.
    if not path.exists():
        raise ValueError(f"{path} is missing")
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{path} is not readable JSON: {error.msg.rstrip(' at')} at line {error.lineno}, column {error.colno}. "
            "A truncated or edited file fails here rather than being partly trusted.") from None
    except UnicodeDecodeError as error:
        raise ValueError(f"{path} is not valid UTF-8: {error.reason}") from None
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
    # The escape hatch this closes: the skip below is decided by a field inside
    # the file being audited, so an attacker who wants the state comparison
    # switched off just writes a different version into the receipt.
    if current_rules and current_rules not in ALLOWED_RULES_VERSIONS:
        raise ValueError(
            f"{label}: the bundled receipt declares rule set {current_rules!r}. The publisher in "
            f"this tree stamps {RULES_VERSION}, and receipts older than the field carry none, so "
            "this one was edited after it was written. Declaring a rule set is not a way to "
            "opt out of being checked.")
    # The third escape hatch, and the one that was open in the shipped
    # repository: a MISSING `rules_version` on the history record was read as
    # "a different version", so deleting the key switched the state comparison
    # off. A reviewer rewrote observation 11 to 791 blocked, re-linked the chain
    # and the anchor, and the gate returned ok.
    #
    # Absence no longer grants the skip. A record that predates the field says
    # so, in a field of its own, which a forger has to add rather than remove -
    # and adding it re-links every digest after it. Eleven records carry that
    # declaration, written once by declare_unversioned_observations.py.
    declared = observation.get("rules_version_recorded")
    if declared is None:
        raise ValueError(
            f"{label} does not say whether it recorded a rule set. A record whose rule set is "
            "simply missing cannot be told from one whose rule set was removed, and the state "
            "comparison is skipped on exactly that basis. Run "
            "bell/declare_unversioned_observations.py.")
    if declared and not recorded_rules:
        raise ValueError(
            f"{label} declares it recorded a rule set and carries none")
    if not declared and recorded_rules:
        raise ValueError(
            f"{label} declares it recorded no rule set and carries {recorded_rules!r}")
    # Two records under one unversioned rule set are comparable; the boundary is
    # only real when the two sides name different rule sets, or when one
    # genuinely predates the field and the other does not.
    rules_differ = (bool(current_rules) != bool(recorded_rules)) or \
        (bool(current_rules) and recorded_rules != current_rules)
    if rules_differ:
        recorded_rules = recorded_rules or "an unversioned rule set"
        print(
            f"{label}: recorded under {recorded_rules}, recomputed under {current_rules}; "
            f"states {observation['states']} -> {{{', '.join(f'{k!r}: {states.get(k)}' for k in observation['states'])}}}. "
            "State counts are not compared across rule versions."
        )
    else:
        # Found by the pattern test rather than by a reviewer, which is the
        # first time that has happened here: the same projection as `signals`,
        # two lines apart, unnoticed through three review rounds. A state the
        # receipt carries and the record does not is a disagreement, so the
        # whole dicts are compared.
        assert_equal(f"{label}.states", states, observation["states"])
    if not rules_differ:
        assert_equal(f"{label}.state total", sum(observation["states"].values()), observation["tokenised_references_scanned"])

    signals = universe.get("signals")
    if not isinstance(signals, dict):
        raise ValueError(f"{label}.universe.signals is missing")
    # This compared {key: signals.get(key) for key in observation["signals"]}
    # against observation["signals"] - a projection of the receipt onto the
    # keys the HISTORY RECORD claims. An empty claim therefore compared nothing
    # and passed, so a reviewer emptied the record's signals, zeroed every
    # signal in the receipt, rebuilt the chain and the anchor, and the gate went
    # green while printing that signals were compared. Every contradiction the
    # product exists to find, erased by a check driven by the forger's own dict.
    #
    # Seventeen lines below, source_hashes already compares whole dicts. Same
    # file, same function, one form safe and one not. Compare whole dicts, which
    # also catches a signal the receipt carries and the record does not.
    assert_equal(f"{label}.signals", signals, observation["signals"])

    # The source digests were shape-checked and never compared to the receipt,
    # so all six could be replaced with zeroes on an observation this gate calls
    # cross-checked and it still returned ok. A digest of an input payload does
    # not depend on the rules that read it, so unlike the state counts these are
    # comparable across every rule version and there is no reason to skip them.
    recorded_hashes = observation.get("source_hashes")
    receipt_hashes = receipt.get("source_hashes")
    if not isinstance(recorded_hashes, dict) or not recorded_hashes:
        raise ValueError(f"{label}.source_hashes is missing")
    if not isinstance(receipt_hashes, dict) or not receipt_hashes:
        raise ValueError(f"{label}: the bundled receipt carries no source_hashes to compare")
    # The comparison below is symmetric, so shrinking BOTH sides to one
    # fingerprint agreed with itself and the gate went green over four deleted
    # source digests. Same shape as the emptied `signals`, fixed there and left
    # here. Seventeen lines from `verify_public_inputs`, which has always
    # required all six named surfaces. Require them here too, so a receipt
    # cannot claim fewer sources than the scan reads.
    missing = REQUIRED_SOURCE_SURFACES - recorded_hashes.keys()
    if missing:
        raise ValueError(
            f"{label}.source_hashes is missing {', '.join(sorted(missing))}. Every published scan "
            "reads those five surfaces, so a record that fingerprints fewer of them is a record "
            "with sources removed.")
    unknown = recorded_hashes.keys() - KNOWN_SOURCE_SURFACES
    if unknown:
        raise ValueError(
            f"{label}.source_hashes names {', '.join(sorted(unknown))}, which this code does not "
            "read")
    assert_equal(f"{label}.source_hashes", receipt_hashes, recorded_hashes)

    verify_observation_shape(observation, label)
    return not rules_differ


def verify_observation_shape(observation: dict, label: str) -> None:
    """Validate fields that remain checkable when the raw receipt is remote."""
    required = ("observed_at", "tokenised_references_scanned", "tokens_scanned", "states", "signals")
    for field in required:
        if field not in observation:
            raise ValueError(f"{label}.{field} is missing")
    # `states` was protected by the sum-total check below; `signals` had no
    # equivalent, so an empty dict satisfied "the key exists". A scan that
    # returned no signal at all over 791 references is not an observation this
    # repository has ever published, and an empty one is how the comparison
    # above was made to compare nothing.
    if not isinstance(observation["signals"], dict) or not observation["signals"]:
        raise ValueError(
            f"{label}.signals is empty. An observation that records no signal over the whole "
            "population is not a scan result; it is a deleted one.")
    if sum(observation["states"].values()) != observation["tokenised_references_scanned"]:
        raise ValueError(f"{label}.state total does not equal the scanned population")
    source_hashes = observation.get("source_hashes")
    if not isinstance(source_hashes, dict) or not source_hashes:
        raise ValueError(f"{label}.source_hashes is missing")
    for name, digest in source_hashes.items():
        if not SHA256.fullmatch(digest):
            raise ValueError(f"{label}.source_hashes.{name} is not a SHA-256 fingerprint")
        # Sixty-four zeroes match the pattern above. On the two observations
        # that ship their payload the receipt comparison catches it; on the
        # summary-only records nothing did, so a placeholder was accepted as a
        # fingerprint of something. Be exact about what this buys: it rejects a
        # digest that is obviously not a digest of anything, and it does not
        # tell a real digest from a digest of the wrong bytes. That question is
        # what shipping the payload answers, and only two records do.
        if len(set(digest)) == 1:
            raise ValueError(
                f"{label}.source_hashes.{name} is {digest[0] * 4}...: a single repeated character "
                "is a placeholder, not the fingerprint of a payload")


def verify_collection_manifest(surfaces: dict, manifest: dict, names: tuple) -> None:
    """Check the per-surface provenance against the payloads it describes.

    Split out of `verify_public_inputs` so it can be checked without reparsing
    16.5 MB for every forgery: a test holds the surfaces once and mutates the
    manifest, which is a few kilobytes.
    """
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
        # This whole block used to be optional: "if any of the four is
        # present". Deleting all four from all six surfaces made the check
        # vanish and the verifier still printed "public inputs: verified" over
        # a package 5.9 MB lighter. A guard the forger can remove by removing
        # the evidence it guards is not a guard. The manifest already declares
        # `mode: server_side_authenticated_collection`, so the provenance it
        # implies is required, not optional.
        if True:
            if not isinstance(request_count, int) or request_count < 1:
                raise ValueError(f"invalid request count for {name}")
            if not isinstance(successful_count, int) or successful_count < 1 or successful_count > request_count:
                raise ValueError(f"invalid successful response count for {name}")
            if not isinstance(response_hashes, list) or len(response_hashes) != successful_count or any(not isinstance(value, str) or len(value) != 64 for value in response_hashes):
                raise ValueError(f"response hashes do not match response count for {name}")
            # Checked for length and compared to nothing. Every response
            # fingerprint in all six surfaces could be set to sixty-four zeroes
            # and the whole suite stayed green, while the page renders these as
            # transport evidence. Thirty lines away the same placeholder is
            # already refused for `source_hashes`; the rule was fixed in one
            # place and left alone in the other, which is this repository's
            # most repeated defect. Same rule, both places.
            placeholders = [value for value in response_hashes if len(set(value)) == 1]
            if placeholders:
                raise ValueError(
                    f"{len(placeholders)} of {name}'s response fingerprints are a single repeated "
                    f"character ({placeholders[0][:8]}...): a placeholder is not the digest of a "
                    "response")
            if not isinstance(status_codes, list) or len(status_codes) != request_count or any(not isinstance(value, int) for value in status_codes):
                raise ValueError(f"status codes do not match request count for {name}")


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
    verify_collection_manifest(surfaces, manifest, names)
    recomputed = scan(
        surfaces["map"], surfaces["asset_list"], surfaces["quotes"],
        surfaces["info"], surfaces["issuers"],
        observed_at=package["observed_at"], crypto_info_payload=surfaces["crypto_info"],
    )
    if recomputed != receipt:
        raise ValueError("public input package does not recompute the bundled receipt")
    print(f"public inputs: verified ({inputs_path.stat().st_size:,} bytes)")


def bundle(receipts: list) -> dict:
    """Index the bundled receipts by observation, refusing a collision.

    This was a dict literal keyed on the receipts' own timestamps, built inside
    `main`. Relabel the dated receipt's observed_at to match the latest and one
    entry silently overwrote the other, so a receipt was never compared to
    anything and the `bundled_matches != len(bundled)` guard could not see it,
    because both sides shrank together. The forger chose the key.

    Lifted out of `main` so it can be checked: a reviewer pointed out that the
    escape-hatch suite exercised two helpers and never the function where this
    one lived.
    """
    stamps = [receipt.get("observed_at") for receipt, _ in receipts]
    if len(set(stamps)) != len(receipts):
        raise ValueError(
            f"the bundled receipts claim the same observation ({stamps}). Two receipts of one "
            "observation is either a duplicate or an edit, and it hides one of them from every "
            "comparison below.")
    if any(stamp is None for stamp in stamps):
        raise ValueError("a bundled receipt carries no observed_at, so nothing can match it")
    return {receipt.get("observed_at"): (receipt, name) for receipt, name in receipts}


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
    bundled = bundle([(dated_receipt, "dated receipt"), (latest_receipt, "latest receipt")])
    bundled_matches = 0
    fully_compared = 0
    for index, observation in enumerate(observations):
        label = f"history observation {index + 1}"
        verify_observation_shape(observation, label)
        match = bundled.get(observation["observed_at"])
        if match:
            if verify_observation(observation, match[0], match[1]):
                fully_compared += 1
            elif observation["observed_at"] != latest_receipt.get("observed_at"):
                # "Not compared, because the rule version differs" is an honest
                # report only while something else proves the same thing. The
                # latest receipt is recomputed byte for byte from its shipped
                # input package a few lines above, so skipping its state
                # comparison costs nothing. Any OTHER bundled receipt that
                # skips has nothing behind it, and calling it cross-checked
                # would be the claim this project exists to refuse.
                raise ValueError(
                    f"{match[1]} ({observation['observed_at']}) was not compared on state counts "
                    "and ships no input package to recompute it from, so nothing verifies its "
                    "distribution. Ship its inputs or stop bundling it as cross-checked.")
            bundled_matches += 1
    if bundled_matches != len(bundled):
        raise ValueError("history is missing a bundled receipt observation")
    # Two observations ship their payload and are cross-checked against it. The
    # other ten were only checked for shape, so a coherent forgery - an invented
    # day with 791 references, every one no_flags - was accepted. The chain makes
    # each record depend on the one before it, so a single quiet edit no longer
    # verifies.
    head = verify_chain(observations)
    declared = history.get("chain_head")
    if declared != head:
        raise ValueError(f"history chain head is {head} but the file declares {declared!r}")
    # The declared head lived inside the file it protects, so rebuilding the
    # whole chain and updating that one field passed. Anchor it outside: a
    # forger now has to edit a second tracked file, which is a separate line in
    # the diff, and anyone verifying a fixed commit is comparing against a value
    # the history cannot rewrite for itself.
    anchor_path = Path(__file__).resolve().parent / "history-chain-head.txt"
    if not anchor_path.exists():
        raise ValueError(f"{anchor_path} is missing: the chain head has no anchor outside the history")
    anchored = anchor_path.read_text(encoding="utf-8").strip()
    if anchored != head:
        raise ValueError(
            f"history chain head is {head} but {anchor_path.name} anchors {anchored}: "
            "the series was rewritten, or the anchor was not updated with it")
    print(f"history chain: verified ({len(observations)} linked observations)")
    print(f"integrity receipt verification: ok ({len(observations)} observations)")
    # "bundled cross-checks: 2" read as "two observations fully verified" when
    # the state comparison had been skipped on both, because neither records a
    # rule version. Say which half was compared.
    # "reported rather than compared" read as a neutral note. It is not: a
    # reviewer rewrote that record's distribution to 791 blocked, re-linked the
    # chain and the anchor, and this returned ok. Nothing in this repository
    # can re-derive a distribution computed by rule code that no longer exists
    # here, so the honest move is to name the hole rather than phrase it as a
    # procedure. A project that says "I will not assert what I cannot prove" is
    # graded against that sentence.
    unverified = bundled_matches - fully_compared
    print(f"bundled cross-checks: {bundled_matches} "
          f"({fully_compared} compared on state counts, "
          f"{unverified} verified on identity, totals, signals and source digests only)")
    if unverified:
        print(f"UNVERIFIED: {unverified} bundled observation(s) record a state distribution that "
              "nothing in this repository can re-derive, because the rule set that produced it is "
              "not the rule set this code runs. Its totals, signals and source digests are "
              "checked; the split between do_not_compare, investigate and no_flags is not.")
    print("remaining observations are public summaries")
    print(f"history chain head: {head}")
    print(f"history sha256: {hashlib.sha256(args.history.read_bytes()).hexdigest()}")
    return 0


def cli() -> int:
    try:
        return main()
    except ValueError as error:
        print(f"receipt verification failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())

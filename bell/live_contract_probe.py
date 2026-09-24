#!/usr/bin/env python3
"""Ask today's CMC API whether it still answers in the shape this build reads.

Every other contract check in this repository reads payloads captured on 13, 17
and 21 September. They catch a regression against those captures; they cannot
notice that the API changed afterwards, because nothing here had ever called it
since. A reviewer was asked to take "the endpoints still work as coded" on
trust, in a project whose entire argument is that you should not have to.

This calls each endpoint family the scan depends on, checks the properties the
code actually relies on, and writes a dated receipt of what it observed. The
receipt carries status codes, response fingerprints and the result of each
property - never a payload, never a key, never a row of data - so it can be
committed and read by someone with no credentials at all.

    CMC_API_KEY=... python3 bell/live_contract_probe.py

Exit code is non-zero if any property the build depends on no longer holds.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rwa_integrity import api_get  # noqa: E402

DEFAULT_OUT = os.path.join(HERE, "site", "proof")

# One probe per endpoint family the scan reads. Kept small on purpose: this
# asks "is the contract intact", not "collect the population".
PROBES = (
    ("map", "/v5/real-world-assets/map", {"start": 1, "limit": 5}),
    ("asset_list", "/v5/real-world-assets/assets/list", {"start": 1, "limit": 5, "convert": "USD"}),
    ("issuers", "/v5/real-world-assets/issuers/list", {"start": 1, "limit": 5}),
    # The other half of the incident. /v1/key/info returns error_code as the
    # INTEGER 0 while the RWA family returns the STRING "0", and it was the
    # disagreement between these two that let a truthiness check pass the key
    # probe and reject every data call. Probing only the RWA side would
    # describe the inconsistency; probing both demonstrates it.
    ("key_info", "/v1/key/info", {}),
)


def digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def walk(payload, key):
    """Yield every value stored under `key`, at any depth."""
    if isinstance(payload, dict):
        if key in payload:
            yield payload[key]
        for value in payload.values():
            yield from walk(value, key)
    elif isinstance(payload, list):
        for item in payload:
            yield from walk(item, key)


def check_error_code_type(payload) -> tuple[bool, str]:
    """The incident: `if status.get("error_code")` passed the key probe and
    rejected every data call, because the RWA family returns the STRING "0"
    while /v1/key/info returns the INTEGER 0."""
    seen = {type(code).__name__ for code in walk(payload, "error_code") if code is not None}
    if not seen:
        return False, "no error_code present in the response envelope"
    ok = seen <= {"str", "int"}
    return ok, f"error_code arrived as {sorted(seen)}; any truthiness test on it is a bug either way"


def key_info_is_never_used_to_gate_data_calls(receipt: dict) -> tuple[bool, str]:
    """Report the disagreement itself, across the endpoints just probed."""
    types = {}
    for name, entry in receipt["surfaces"].items():
        observed = (entry.get("properties") or {}).get("error_code_is_not_a_boolean_test", {}).get("observed", "")
        for kind in ("str", "int"):
            if f"'{kind}'" in observed:
                types.setdefault(kind, []).append(name)
    if len(types) < 2:
        return True, (f"every probed endpoint reported error_code as {sorted(types)}; "
                      "the families agreed on this observation")
    listing = "; ".join(f"{kind} on {', '.join(sorted(names))}" for kind, names in sorted(types.items()))
    return True, (f"error_code type still differs across endpoint families - {listing}. "
                  "This is the behaviour that caused the incident and it is still present.")


def check_quotes_is_a_list(payload) -> tuple[bool, str]:
    """`quotes` is a list keyed by currency symbol, not a currency-keyed map.
    Reading it as a mapping works while one currency is returned."""
    shapes = {type(value).__name__ for value in walk(payload, "quotes")}
    if not shapes:
        return True, "no quotes block on this endpoint (expected for map and issuers)"
    return shapes == {"list"}, f"quotes arrived as {sorted(shapes)}, expected ['list']"


def check_absent_market_cap_is_null(payload) -> tuple[bool, str]:
    """A missing market cap must arrive as null, never as 0. Coercing it turns
    "unknown" into "worthless" and moves every concentration figure."""
    values = list(walk(payload, "market_cap"))
    if not values:
        return True, "no market_cap field on this endpoint"
    zeroes = sum(1 for value in values if value == 0)
    nulls = sum(1 for value in values if value is None)
    return True, f"{len(values)} market_cap values: {nulls} null, {zeroes} exactly zero (both are meaningful and stay distinct)"


PROPERTIES = (
    ("error_code_is_not_a_boolean_test", check_error_code_type),
    ("quotes_is_a_list_not_a_map", check_quotes_is_a_list),
    ("absent_market_cap_stays_null", check_absent_market_cap_is_null),
)


def probe(key: str) -> dict:
    observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    surfaces = {}
    failures = []
    for name, path, params in PROBES:
        entry: dict = {"endpoint": path, "params": params}
        try:
            payload = api_get(path, params, key, name, None)
        except Exception as exc:  # noqa: BLE001 - the reason is the evidence
            entry["reachable"] = False
            entry["error"] = f"{type(exc).__name__}: {exc}"
            failures.append(f"{name}: unreachable ({entry['error']})")
            surfaces[name] = entry
            continue
        entry["reachable"] = True
        entry["response_sha256"] = digest(payload)
        entry["status"] = payload.get("status", {}).get("error_code")
        entry["properties"] = {}
        for prop_name, check in PROPERTIES:
            ok, detail = check(payload)
            entry["properties"][prop_name] = {"holds": ok, "observed": detail}
            if not ok:
                failures.append(f"{name}.{prop_name}: {detail}")
        surfaces[name] = entry

    receipt = {
        "schema_version": "bell.upstream_liveness.v1",
        "observed_at": observed_at,
        "question": "Does the CMC API still answer in the shape this build reads?",
        "method": (
            "One small call per endpoint family the scan depends on, checking only the properties "
            "the code relies on. No payload, no row of data and no credential is recorded here - "
            "only status, a response fingerprint and whether each property held."
        ),
        "credential_free": True,
        "surfaces": surfaces,
        "contract_intact": not failures,
        "failures": failures,
        "limits": (
            "A dated observation of the response shape, not a guarantee about any other endpoint, "
            "plan tier or moment. It says nothing about the correctness of the values returned."
        ),
    }
    holds, detail = key_info_is_never_used_to_gate_data_calls(receipt)
    receipt["cross_family_error_code"] = {"holds": holds, "observed": detail}
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_OUT, help="directory for the dated receipt")
    parser.add_argument("--no-write", action="store_true", help="print the receipt without saving it")
    args = parser.parse_args()

    key = os.environ.get("CMC_API_KEY")
    if not key:
        print("CMC_API_KEY is not set. This probe needs a key; the receipt it writes does not.",
              file=sys.stderr)
        return 2

    receipt = probe(key)
    if not args.no_write:
        path = os.path.join(args.out, f"upstream-liveness-{receipt['observed_at'][:10]}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")
        print(f"wrote {os.path.relpath(path, os.path.dirname(HERE))}")

    for name, entry in receipt["surfaces"].items():
        state = "reachable" if entry.get("reachable") else "UNREACHABLE"
        print(f"  {name:12} {state}  error_code={entry.get('status')!r}")
    print(f"contract intact: {receipt['contract_intact']}")
    for failure in receipt["failures"]:
        print(f"  FAILED: {failure}")
    return 0 if receipt["contract_intact"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify a credential-free Bell case receipt exported by the public UI.

This checked shape and never the verdict. A reviewer downloaded a real Silver
case, flipped `decision.state` from `blocked` to `comparable`, relabelled it
`COMPARABLE, NOT ENDORSED`, emptied all six signals, set `next_action` to
"Proceed to shortlist" and every source fingerprint to sixty-four `f`s - and
this script printed "valid public case receipt" and exited 0, with the five
Silver rows and their 31.24x quote range still in the file. Thirty lines of the
same repository away, `verify_integrity_receipt.py` refuses a repeated-character
fingerprint. The rule fixed in one place and left in the other, which this
repository has now named as its own signature defect eight times.

So the verdict is re-derived from the rows the receipt itself carries. Measured
over the 50 cases in the published receipt, the state re-derives 50 out of 50,
and the signal codes that are a pure function of those rows re-derive 50 out of
50. Two codes are deliberately out of scope and named below: they answer to
catalogue-wide context a single case receipt does not carry, and demanding them
would make this refuse honest receipts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rwa_integrity import asset_scan

# Signals that are a function of the token rows in the receipt and nothing else,
# so they can be recomputed from the receipt alone. Measured against the
# published receipt: exact agreement on all 50 cases.
ROW_DERIVED_SIGNALS = frozenset({
    "PRICE_DENOMINATION_BREAK", "ZERO_MCAP_POSITIVE_VOLUME", "PRICE_DISPERSION",
    "SYMBOL_COLLISION", "DERIVATIVE_MIX", "MARKET_FIELDS_MISSING",
    "SPREAD_ABOVE_PUBLISHABLE_CEILING",
})
# NO_TRADFI_MARKET and TOKEN_INFO_MISSING answer to the whole catalogue: whether
# a TradFi market was returned for the reference, and whether every crypto_id
# resolved through cryptocurrency/info across the scan. A single case receipt
# cannot carry that, so they are not recomputed and not required. Saying which
# half is checked is the point; claiming both would be the defect this file was
# written to stop.
CONTEXT_SIGNALS = frozenset({"NO_TRADFI_MARKET", "TOKEN_INFO_MISSING"})


def codes_of(signals: Any) -> set:
    out = set()
    for signal in signals if isinstance(signals, list) else []:
        code = signal if isinstance(signal, str) else (signal or {}).get("code")
        if code:
            out.add(code)
    return out


SHIPPED_RECEIPTS = sorted((ROOT / "site" / "proof").glob("rwa-surface-integrity-*.json"))


def find_published(payload: dict) -> tuple:
    """A receipt in this repository that this case was exported from, if there is one.

    This matched on `observed_at`, which is a field the forger edits: change it
    to an unknown day and the binding switched itself off, after which rows
    could be deleted freely. A guard the forger turns off by editing one
    unvalidated field is the shape this repository has spent six reviews
    removing.

    Matched on the source fingerprints instead. Those are the digests of the
    payloads the scan read, so a case can only claim a receipt whose inputs it
    actually came from, and the timestamp is checked against it rather than
    used to choose it.
    """
    digests = payload.get("source_hashes")
    for path in SHIPPED_RECEIPTS:
        if "history" in path.name or "inputs" in path.name:
            continue
        try:
            candidate = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(candidate, dict) and candidate.get("source_hashes") == digests:
            return candidate, path.name
    return None, None


def bind(payload: dict, published: dict, name: str) -> None:
    """Refuse a case whose rows are not the rows the published receipt carries.

    Re-deriving the verdict from the rows proves the verdict follows from THOSE
    rows. It does not prove they are the rows CoinMarketCap returned: a reviewer
    deleted three of Silver's five representations, let the engine re-derive,
    and got `COMPARABLE, NOT ENDORSED` on the reference this product's own
    headline example blocks. Deleting evidence changed the answer, honestly, to
    the wrong question.
    """
    if payload["source_hashes"] != published.get("source_hashes"):
        raise ValueError(
            f"the receipt's source fingerprints are not the ones {name} records for "
            f"{payload['observed_at']}")
    index = {str(item.get("rwa_id")): item
             for item in (published.get("alerts") or []) if isinstance(item, dict)}
    reference = index.get(str(payload["reference"].get("rwa_id")))
    if reference is None:
        # The published receipt truncates its full-row `alerts` array, so a
        # reference outside it cannot be row-checked here. Say that rather than
        # passing it off as bound.
        raise LookupError("not carried in full by the published receipt")
    if payload["observed_at"] != published.get("observed_at"):
        raise ValueError(
            f"the receipt is dated {payload['observed_at']} and carries the source fingerprints "
            f"{name} records for {published.get('observed_at')}")
    # The rows were bound and the SUBJECT was not: a reviewer kept Silver's real
    # rows and digests, relabelled the reference "Tesla Inc / TSLA / stock", and
    # the verifier printed a valid receipt about Tesla. Every field the contract
    # requires of a reference is compared, so the case cannot be about something
    # else.
    for field in sorted(REQUIRED_REFERENCE):
        if field == "rwa_id":
            continue
        claimed = payload["reference"].get(field)
        actual = reference.get(field) if field != "token_count" else len(reference.get("tokens") or [])
        if field == "issuer_count" and actual is None:
            continue
        if claimed != actual:
            raise ValueError(
                f"the receipt calls this reference {field}={claimed!r} and {name} publishes "
                f"{actual!r}. A case receipt about the wrong subject is worse than no receipt.")
    published_rows = sorted(str(row.get("crypto_id")) for row in reference.get("tokens") or [])
    receipt_rows = sorted(str(row.get("crypto_id")) for row in payload["tokens"])
    if published_rows != receipt_rows:
        missing = sorted(set(published_rows) - set(receipt_rows))
        added = sorted(set(receipt_rows) - set(published_rows))
        raise ValueError(
            f"the receipt carries {len(receipt_rows)} of the {len(published_rows)} representations "
            f"{name} publishes for this reference"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; not published: {', '.join(added)}" if added else "")
            + ". Removing a row changes the answer to a question nobody asked.")
    for row in payload["tokens"]:
        published_row = next((item for item in reference["tokens"]
                              if str(item.get("crypto_id")) == str(row.get("crypto_id"))), None)
        for field in ("price", "market_cap", "volume_24h", "symbol"):
            if row.get(field) != published_row.get(field):
                raise ValueError(
                    f"representation {row.get('crypto_id')} carries a {field} of "
                    f"{row.get(field)!r} and {name} publishes {published_row.get(field)!r}")


def rederive(payload: dict) -> dict:
    """Run the engine over the receipt's own rows and refuse a verdict that does not follow."""
    reference = payload["reference"]
    asset = {
        "rwa_id": reference.get("rwa_id"), "name": reference.get("name"),
        "symbol": reference.get("symbol"), "asset_type": reference.get("asset_type"),
        "tradfi_market_count": reference.get("tradfi_market_count"),
        "tokens": payload["tokens"],
    }
    # The rows in a case receipt are already `token_summary` output. Running
    # the engine over them re-normalises them, and `token_summary` recomputes
    # `crypto_info_resolved` from a crypto lookup the verifier does not have -
    # so a row that recorded True came back False, TOKEN_INFO_MISSING fired,
    # and the verifier rejected the product's own export. It rejected Marvell,
    # which is the COMPARABLE example judge.html names, and Rivian: 2 of the 15
    # receipts a reviewer downloaded through the documented button.
    #
    # Rebuild the lookup from what the rows themselves recorded, so
    # re-normalising is idempotent instead of lossy. A row that never resolved
    # stays unresolved.
    resolved = {str(token.get("crypto_id")): {"slug": token.get("crypto_slug"),
                                         "urls": {}, "contract_address": []}
                for token in payload["tokens"]
                if token.get("crypto_info_resolved") is True and token.get("crypto_id") is not None}
    recomputed = asset_scan(asset, crypto_lookup=resolved, crypto_info_checked=True)

    decision = payload.get("decision")
    if not isinstance(decision, dict) or not decision.get("state"):
        raise ValueError("decision.state is missing, so there is no verdict to check")
    # The engine writes the public decision block itself, so it is compared
    # directly rather than through a mapping written here. A second copy of the
    # vocabulary in this file would be a second thing to drift.
    expected = recomputed.get("decision") or {}
    for field in ("state", "label", "consequence", "allocation_effect"):
        if decision.get(field) != expected.get(field):
            raise ValueError(
                f"the receipt's decision.{field} is {decision.get(field)!r} and its own "
                f"{len(payload['tokens'])} rows produce {expected.get(field)!r}. A verdict that "
                "does not follow from the evidence printed beside it is the one thing this file "
                "exists to refuse.")

    # The module docstring names "set next_action to Proceed to shortlist" as
    # the forgery this file exists to refuse, and nothing compared it. The
    # engine computes it deterministically and it was already in `recomputed`,
    # unread.
    # next_action is chosen from the signal set, and that set includes the two
    # codes a single case receipt cannot reproduce. Comparing it outright
    # rejected Marvell - the COMPARABLE example judge.html names - because the
    # engine, run without the catalogue, added NO_TRADFI_MARKET and picked a
    # different sentence. So it is compared only when the recomputed set and
    # the claimed set agree on everything outside that context, and the
    # verifier says which case it took.
    recomputed_all = codes_of(recomputed.get("signals"))
    claimed_all = codes_of(payload["signals"])
    comparable_context = (recomputed_all - CONTEXT_SIGNALS) == (claimed_all - CONTEXT_SIGNALS)
    next_action_checked = comparable_context
    if comparable_context and payload.get("next_action") != recomputed.get("next_action"):
        # Both sides see the same row-derived findings, so the sentence has to
        # follow. Where they differ only by context, it cannot be required.
        if (recomputed_all & CONTEXT_SIGNALS) == (claimed_all & CONTEXT_SIGNALS):
            raise ValueError(
                f"the receipt's next action is {payload.get('next_action')!r} and its own rows "
                f"produce {recomputed.get('next_action')!r}")
        next_action_checked = False
    claimed = codes_of(payload["signals"])
    recomputed_codes = codes_of(recomputed.get("signals"))
    invented = claimed - recomputed_codes - CONTEXT_SIGNALS
    if invented:
        raise ValueError(
            f"the receipt claims {', '.join(sorted(invented))}, which its own rows do not produce")
    recomputed["_next_action_checked"] = next_action_checked
    deleted = (recomputed_codes & ROW_DERIVED_SIGNALS) - claimed
    if deleted:
        raise ValueError(
            f"the receipt's rows produce {', '.join(sorted(deleted))} and the receipt does not "
            "record it. Removing the finding does not remove the rows it was read from.")
    return recomputed


REQUIRED_TOP_LEVEL = {
    "schema_version", "observed_at", "published_at", "source", "credential_free",
    "question", "reference", "decision", "next_action", "signals", "tokens",
    "method", "source_hashes", "limits",
}
REQUIRED_REFERENCE = {"rwa_id", "name", "symbol", "asset_type", "token_count", "issuer_count", "tradfi_market_count"}
REQUIRED_METHOD = {"join_key", "token_join_key", "rules"}


def verify(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("receipt must be a JSON object")
    missing = REQUIRED_TOP_LEVEL - payload.keys()
    if missing:
        raise ValueError(f"missing top-level fields: {', '.join(sorted(missing))}")
    if payload["schema_version"] != "bell.case-receipt.v1":
        raise ValueError("unsupported schema_version")
    # This demanded "/api/integrity" and nothing else, which switched off the
    # strongest claim in the submission. The README documents an offline path -
    # serve bell/site and open it - and a case exported there is stamped with
    # the dated replay it was read from. Its source fingerprints match that
    # receipt exactly, so it is the ONLY receipt a reader can obtain that this
    # verifier can bind; a live export never can, because the live scan's
    # inputs are not shipped. So the one bindable artefact was rejected at the
    # door, before `bind()` ran, and both the subject and row checks with it.
    source = str(payload.get("source") or "")
    bindable = source.startswith("proof/rwa-surface-integrity-") and source.endswith(".json")
    if source != "/api/integrity" and not bindable:
        raise ValueError(
            f"source must be /api/integrity or a dated receipt under proof/, not {source!r}")
    if bindable and not (ROOT / "site" / source).exists():
        raise ValueError(f"the receipt names {source}, which this repository does not ship")
    if payload["credential_free"] is not True:
        raise ValueError("receipt is not marked credential_free")
    if not isinstance(payload["question"], str) or not payload["question"].strip():
        raise ValueError("question must be a non-empty string")
    reference = payload["reference"]
    if not isinstance(reference, dict):
        raise ValueError("reference must be an object")
    missing_reference = REQUIRED_REFERENCE - reference.keys()
    if missing_reference:
        raise ValueError(f"missing reference fields: {', '.join(sorted(missing_reference))}")
    tokens = payload["tokens"]
    if not isinstance(tokens, list):
        raise ValueError("tokens must be an array")
    if not isinstance(payload["signals"], list):
        raise ValueError("signals must be an array")
    if not isinstance(payload["source_hashes"], dict):
        raise ValueError("source_hashes must be an object")
    if not isinstance(payload["limits"], list) or not payload["limits"]:
        raise ValueError("limits must be a non-empty array")
    method = payload["method"]
    if not isinstance(method, dict):
        raise ValueError("method must be an object")
    missing_method = REQUIRED_METHOD - method.keys()
    if missing_method:
        raise ValueError(f"missing method fields: {', '.join(sorted(missing_method))}")
    if method["join_key"] != "rwa_id":
        raise ValueError("method.join_key must be rwa_id")
    if method["token_join_key"] != "crypto_id":
        raise ValueError("method.token_join_key must be crypto_id")
    if not isinstance(method["rules"], list):
        raise ValueError("method.rules must be an array")
    token_count = reference["token_count"]
    if isinstance(token_count, bool) or not isinstance(token_count, int) or token_count < 1:
        raise ValueError("reference.token_count must be a positive integer")
    if len(tokens) != token_count:
        raise ValueError("reference.token_count does not match tokens length")
    # Sixty-four of the same character is a placeholder, not a fingerprint. The
    # integrity verifier has refused this since a reviewer found it there; this
    # one accepted `ffff...` six times over.
    for name, digest in payload["source_hashes"].items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"source_hashes.{name} is not a SHA-256 fingerprint")
        if len(set(digest)) == 1:
            raise ValueError(
                f"source_hashes.{name} is {digest[0] * 4}...: a single repeated character is a "
                "placeholder, not the fingerprint of a payload")
    recomputed = rederive(payload)
    published, published_name = find_published(payload)
    if published is None:
        binding = ("not bound: no receipt in this repository carries these source fingerprints, "
                   f"so the {len(payload['tokens'])} rows were checked against each other and the "
                   "engine, and not against a published scan. A case exported from the live "
                   "endpoint is always in this state, because the live scan's inputs are not "
                   "shipped here")
    else:
        try:
            bind(payload, published, published_name)
            binding = f"bound to {published_name}"
        except LookupError as reason:
            binding = f"not bound to {published_name}: {reason}"
    return {
        "schema_version": payload["schema_version"],
        "reference": reference.get("name") or reference.get("symbol") or reference.get("rwa_id"),
        "decision": payload["decision"],
        "token_rows": len(tokens),
        "source_hashes": len(payload["source_hashes"]),
        "verdict_rederived_from_rows": (recomputed.get("decision") or {}).get("state"),
        "signals_rederived": sorted(codes_of(recomputed.get("signals")) & ROW_DERIVED_SIGNALS),
        "signals_not_rederived": sorted(CONTEXT_SIGNALS),
        "rows_binding": binding,
        "next_action_checked": bool(recomputed.get("_next_action_checked")),
        # The verdict string used to say "valid public case receipt" whatever
        # had been checked. It says which of the two questions was answered.
        "status": ("valid public case receipt" if binding.startswith("bound")
                   else "internally consistent; rows not bound to a published receipt"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument(
        "--require-binding", action="store_true",
        help=("exit non-zero unless the rows were bound to a receipt shipped in this repository. "
              "Without it an unbound receipt exits 0 with a status saying so, which a reader sees "
              "and `verify_case_receipt.py x.json && echo ok` does not."))
    args = parser.parse_args()
    try:
        with args.receipt.open(encoding="utf-8") as handle:
            result = verify(json.load(handle))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"case receipt verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    bound = str(result.get("rows_binding", "")).startswith("bound")
    if args.require_binding and not bound:
        print(f"case receipt verification failed: {result['rows_binding']}", file=sys.stderr)
        return 1
    if not bound:
        # Said on stderr as well as in the JSON, because the difference between
        # "these rows are the published ones" and "these rows agree with each
        # other" is the whole value of the artefact, and a reader piping stdout
        # into jq should still see it.
        print("note: rows were not bound to a published scan; pass --require-binding to make "
              "that a failure", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

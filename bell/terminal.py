"""Deterministic summaries for Bell's universal RWA terminal.

This layer deliberately sits between CMC evidence collection and any optional AI explanation.
It turns the same evidence into a user brief, a desk brief and a small set of inspectable metrics.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def _token_rows(value: Any) -> list[dict[str, Any]]:
    """Token rows only. Unlike `cmc_shapes.records`, a lone object is not a row."""
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _state(asset: dict[str, Any], tokens: list[dict[str, Any]]) -> str:
    if asset.get("has_tokens") is False:
        return "underlying_only"
    if asset.get("has_tokens") is True and not tokens:
        return "coverage_pending"
    if not tokens:
        return "underlying_only"
    if len(tokens) == 1:
        return "single_token"
    return "multi_token"


def build_terminal_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    """Create a reproducible terminal summary from normalized CMC evidence."""

    asset = evidence.get("asset") if isinstance(evidence.get("asset"), dict) else {}
    metadata = evidence.get("metadata") if isinstance(evidence.get("metadata"), dict) else {}
    tokens = _token_rows(evidence.get("tokens"))
    pairs = _token_rows(evidence.get("market_pairs"))
    issuers = _token_rows(evidence.get("issuers"))
    crypto_info = _token_rows(evidence.get("crypto_info"))
    state = _state(asset, tokens)
    issuer_names = {str(item.get("name")) for item in issuers if item.get("name")}
    issuer_names.update(str(item.get("issuer_name")) for item in tokens if item.get("issuer_name"))
    categories = Counter(str(item.get("category") or "unknown").lower() for item in pairs)
    missing_prices = [item.get("symbol") for item in tokens if item.get("price") in (None, "")]
    missing_market_caps = [item.get("symbol") for item in tokens if item.get("market_cap") in (None, "")]
    findings = _token_rows(evidence.get("findings"))
    market_pairs_error = evidence.get("market_pairs_error")
    dex = evidence.get("dex_evidence") if isinstance(evidence.get("dex_evidence"), dict) else {}
    dex_covered = int(dex.get("covered_token_count") or 0)
    dex_contracts = int(dex.get("contract_token_count") or 0)
    dex_unavailable = int(dex.get("unavailable_token_count") or 0)
    dex_no_contract = int(dex.get("no_contract_token_count") or 0)
    dex_surface_counts = dex.get("surface_counts") if isinstance(dex.get("surface_counts"), dict) else {}
    networks = {
        str(item.get("platform", {}).get("name"))
        for item in crypto_info
        if isinstance(item.get("platform"), dict) and item.get("platform", {}).get("name")
    }

    if state == "underlying_only":
        user_brief = "No token representation is mapped for this reference. Bell keeps the case on the underlying rather than manufacturing a token comparison."
        desk_brief = "Underlying-only case. Monitor the reference asset and treat a future token mapping as a new event requiring identity and issuer review."
        output = "MONITOR"
    elif state == "coverage_pending":
        user_brief = "CMC indicates that token representations exist, but this response did not return them. Bell pauses the comparison until the token layer is loaded."
        desk_brief = "Coverage-pending case. Do not infer an underlying-only asset from an empty token response; retry token and issuer evidence before making a market decision."
        output = "LOAD"
    elif state == "single_token":
        user_brief = "One token representation is mapped. Bell opens a dossier for that representation; a ranking against other wrappers would not be meaningful."
        desk_brief = "Single-representation case. Review issuer, network, venue access, holder distribution and operational evidence instead of creating a peer ranking."
        output = "DOSSIER"
    else:
        user_brief = "Multiple token representations are mapped. Bell compares the exposure while separating unit, claim, market type and data-quality differences."
        desk_brief = "Multi-representation case. Separate economic comparability from market access, issuer/network concentration and evidence quality before allocation review."
        output = "COMPARE"

    points = [
        f"{len(tokens)} token representation(s) mapped",
        f"{len(issuer_names)} issuer identity/identities observed" if issuer_names else "issuer identity not resolved in this evidence",
        f"{len(pairs)} market pair(s) returned" if pairs else "market pairs not loaded in this evidence",
    ]
    if categories:
        points.append("market categories: " + ", ".join(f"{key} {value}" for key, value in sorted(categories.items())))
    if missing_prices:
        points.append("missing token prices: " + ", ".join(str(value) for value in missing_prices))
    if missing_market_caps:
        points.append("missing token market caps: " + ", ".join(str(value) for value in missing_market_caps))
    if crypto_info:
        points.append(f"{len(crypto_info)} token metadata record(s); {len(networks)} network(s) resolved")
    if dex:
        points.append(f"DEX evidence: {dex_covered}/{dex_contracts} contract token(s) covered")
        if dex_no_contract:
            points.append(f"{dex_no_contract} token(s) have no resolved contract/network")
        if dex_unavailable:
            points.append(f"{dex_unavailable} contract token(s) were unavailable on the DEX surface")
    if market_pairs_error:
        points.append("CMC market-pair surface unavailable for this API plan; DEX evidence is shown separately")
    if findings:
        points.append(f"{len(findings)} deterministic finding(s) require review")

    return {
        "schema_version": "bell.terminal.summary.v1",
        "asset": asset,
        "metadata": metadata,
        "state": state,
        "output": output,
        "audiences": {"normal": user_brief, "desk": desk_brief},
        "metrics": {
            "token_count": len(tokens),
            "issuer_count": len(issuer_names),
            "market_pair_count": len(pairs),
            "spot_pair_count": categories.get("spot", 0),
            "derivative_pair_count": categories.get("derivatives", 0) + categories.get("perpetual", 0),
            "tokenized_market_cap": asset.get("tokenized_market_cap"),
            "tokenized_volume_24h": asset.get("tokenized_volume_24h"),
            "primary_exchange": metadata.get("primary_exchange"),
            "token_metadata_count": len(crypto_info),
            "network_count": len(networks),
            "dex_covered_token_count": dex_covered,
            "dex_contract_token_count": dex_contracts,
            "dex_unavailable_token_count": dex_unavailable,
            "dex_no_contract_token_count": dex_no_contract,
            "dex_detail_count": int(dex_surface_counts.get("detail") or 0),
            "dex_pool_count": int(dex_surface_counts.get("pools") or 0),
            "dex_security_count": int(dex_surface_counts.get("security") or 0),
            "dex_holder_count": int(dex_surface_counts.get("holders") or 0),
            "dex_holder_tag_count": int(dex_surface_counts.get("holder_tags") or 0),
        },
        "points": points,
        "findings": findings,
        "provenance": evidence.get("provenance", {}),
        "limits": "Deterministic CMC evidence does not prove backing, redemption, legal rights, suitability or executable liquidity.",
    }

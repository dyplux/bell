import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from terminal import build_terminal_summary


def test_terminal_marks_no_token_asset_as_underlying_only():
    result = build_terminal_summary({"asset": {"name": "Royal Bank", "has_tokens": False}})
    assert result["state"] == "underlying_only"
    assert result["output"] == "MONITOR"
    assert result["metrics"]["token_count"] == 0


def test_terminal_does_not_turn_missing_token_rows_into_underlying_only():
    result = build_terminal_summary({"asset": {"name": "Gold", "has_tokens": True}})
    assert result["state"] == "coverage_pending"
    assert result["output"] == "LOAD"


def test_terminal_marks_one_token_asset_as_dossier():
    result = build_terminal_summary({
        "asset": {"name": "SPY", "has_tokens": True},
        "tokens": [{"symbol": "SPYx", "issuer_name": "bStocks", "price": 762.94}],
        "issuers": [{"name": "bStocks"}],
        "market_pairs": [{"category": "spot"}],
    })
    assert result["state"] == "single_token"
    assert result["output"] == "DOSSIER"
    assert result["metrics"]["issuer_count"] == 1
    assert result["metrics"]["spot_pair_count"] == 1


def test_terminal_exposes_multi_token_market_and_data_quality_evidence():
    result = build_terminal_summary({
        "asset": {"name": "Tesla", "has_tokens": True, "tokenized_market_cap": 100},
        "tokens": [
            {"symbol": "TSLAX", "issuer_name": "Backed", "price": 362, "market_cap": 90},
            {"symbol": "TSLA", "issuer_name": "Hyperliquid", "price": 235, "market_cap": None},
        ],
        "issuers": [{"name": "Backed"}, {"name": "Hyperliquid"}],
        "crypto_info": [{"platform": {"name": "Ethereum"}}, {"platform": {"name": "Hyperliquid"}}],
        "market_pairs": [{"category": "spot"}, {"category": "perpetual"}],
        "findings": [{"code": "symbol_collision"}],
    })
    assert result["state"] == "multi_token"
    assert result["output"] == "COMPARE"
    assert result["metrics"]["derivative_pair_count"] == 1
    assert result["metrics"]["network_count"] == 2
    assert any("TSLA" in point for point in result["points"])
    assert result["points"][-1] == "1 deterministic finding(s) require review"


def test_terminal_exposes_dex_coverage_as_a_separate_evidence_layer():
    result = build_terminal_summary({
        "asset": {"name": "Gold", "has_tokens": True},
        "tokens": [{"symbol": "PAXG", "issuer_name": "Paxos", "price": 4300}],
        "issuers": [{"name": "Paxos"}],
        "crypto_info": [{"platform": {"name": "Ethereum"}}],
        "market_pairs": [],
        "market_pairs_error": "CMC request failed for market pairs: HTTP 403",
        "dex_evidence": {
            "covered_token_count": 1,
            "contract_token_count": 1,
            "surface_counts": {"detail": 1, "pools": 1, "security": 1, "holders": 1, "holder_tags": 1},
        },
    })
    assert result["metrics"]["dex_covered_token_count"] == 1
    assert result["metrics"]["dex_holder_tag_count"] == 1
    assert any("DEX evidence" in point for point in result["points"])
    assert any("DEX evidence is shown separately" in point for point in result["points"])

import json

from live_store import LiveStore


def test_live_store_writes_credential_free_atomic_record(tmp_path):
    store = LiveStore(tmp_path)
    record = store.write("terminal", "gold", {"observed_at": "2026-09-14T12:00:00Z", "audit": {"conclusion": "investigate"}})

    assert record["credential_free"] is True
    assert record["slug"] == "gold"
    assert store.read("terminal", "gold")["payload"]["audit"]["conclusion"] == "investigate"
    assert json.loads((tmp_path / "terminal/gold.json").read_text())["schema_version"] == "bell.live.store.v1"


def test_live_store_rejects_path_traversal(tmp_path):
    store = LiveStore(tmp_path)
    try:
        store.read("terminal", "../secret")
    except ValueError as error:
        assert "invalid" in str(error)
    else:
        raise AssertionError("path traversal should be rejected")

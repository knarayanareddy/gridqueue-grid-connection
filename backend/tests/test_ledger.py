import json
import threading

import pytest

from app.tf.ledger import ledger_path, record_telemetry


def test_ledger_line_matches_contract(tmp_path, validator_for):
    entry = record_telemetry(
        "chat.completions",
        "extract_positions",
        "nvidia/nemotron-3-nano",
        100,
        20,
        80,
        cost_usd=0.0001234567,
        latency_ms=12.345,
        runs_dir=tmp_path,
    )
    lines = ledger_path(tmp_path).read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[-1]) == entry
    assert entry["id"].startswith("led_") and entry["ts"].endswith("Z")
    assert entry["cost_usd"] == 0.000123
    assert list(validator_for("LedgerLine").iter_errors(entry)) == []


def test_ids_are_unique(tmp_path):
    ids = {record_telemetry("tavily.search", "s2", None, runs_dir=tmp_path)["id"] for _ in range(20)}
    assert len(ids) == 20


def test_concurrent_writes_do_not_interleave(tmp_path):
    def worker():
        for _ in range(25):
            record_telemetry("chat.completions", "s3", "m", 1, 1, notes="x" * 5000, runs_dir=tmp_path)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = ledger_path(tmp_path).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 200
    for line in lines:
        json.loads(line)


@pytest.mark.parametrize("kwargs", [{"prompt_tokens": -1}, {"prompt_tokens": 10, "cached_tokens": 11}])
def test_rejects_impossible_token_counts(tmp_path, kwargs):
    with pytest.raises(ValueError):
        record_telemetry("chat.completions", "s3", "m", runs_dir=tmp_path, **kwargs)

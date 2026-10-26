"""jobs/ab_branch_eval.py — gate_on vs gate_off over the SYNTHETIC adversarial set (C-T23)."""

import asyncio
import copy
import importlib.util
import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.gate.gate import DeterministicGate, GateResult
from app.main import AnswerRequest, app
from app.stages import s5_answer
from tests.conftest import REPO_ROOT

JOB_PATH = REPO_ROOT / "jobs" / "ab_branch_eval.py"
COMMITTED_RESULTS = REPO_ROOT / "runs" / "ab_experiment_results.json"


def _load_job():
    spec = importlib.util.spec_from_file_location("ab_branch_eval", JOB_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


job = _load_job()


@pytest.fixture(scope="module")
def result():
    return asyncio.run(job.run_experiment())


@pytest.fixture
def ab_validator(validator_for):
    return validator_for("AbExperimentResult")


def _arm(res, name):
    return next(a for a in res["arms"] if a["arm"] == name)


def test_result_is_contract_valid(result, ab_validator):
    errors = [f"{list(e.absolute_path)}: {e.message}" for e in ab_validator.iter_errors(result)]
    assert errors == []


def test_gate_on_rejects_every_fabricated_value(result):
    on = _arm(result, "gate_on")["counters"]
    for name in ("fabricated_dates", "fabricated_kw", "fabricated_binding", "fabricated_routes"):
        assert on[name]["total"] > 0, name
        assert on[name]["passed"] == 0, name
    assert _arm(result, "gate_on")["spec_counters"] == {
        "dates_without_document": 0,
        "kw_without_quote": 0,
        "binding_not_stated": 0,
        "option_without_route": 0,
    }


def test_gate_off_accepts_every_fabricated_value(result):
    off = _arm(result, "gate_off")["counters"]
    for name in ("fabricated_dates", "fabricated_kw", "fabricated_binding", "fabricated_routes"):
        assert off[name]["passed"] == off[name]["total"] > 0, name
    assert _arm(result, "gate_off")["gate_checks_run"] == 0


def test_headline_numbers(result):
    d = result["delta"]
    assert d["fabricated_dates"] == {"gate_on": 0, "gate_off": 10, "total": 10}
    assert d["fabricated_kw"] == {"gate_on": 0, "gate_off": 6, "total": 6}
    assert "gate OFF, 10 dates and 6 kW" in result["headline"] and "gate ON, 0 and 0" in result["headline"]


def test_gate_keeps_genuine_values(result):
    for arm in ("gate_on", "gate_off"):
        a = _arm(result, arm)
        assert a["counters"]["genuine"]["passed"] == a["counters"]["genuine"]["total"] == 10
        assert a["false_rejects"] == 0


def test_misattribution_limitation_is_measured_and_reported(result):
    """The gate checks that a value is stated, not what it means. This pins the measured finding."""
    on = _arm(result, "gate_on")["counters"]["misattributed"]
    assert on == {"total": 5, "passed": 4}
    passed = {
        c["case_id"]
        for c in result["per_case"]
        for lab in c["labels"]
        if lab["label"] == "misattributed" and lab["reached_gate_on"]
    }
    assert passed == {"M01", "M02", "M03", "M04"}  # M05 (wrong route kind) is the one the gate blocks
    assert any("Misattributed" in lim and "4 of 5" in lim for lim in result["limitations"])


def test_execution_is_honest_about_where_it_ran(result):
    ex = result["execution"]
    assert ex["environment"] == "local_process" and ex["token_factory_sandbox"] is False
    assert ex["sandbox_image_uuid"] is None and ex["branch_operation_ids"] is None
    assert result["test_set"]["synthetic"] is True
    assert result["test_set"]["proposal_source"] == "hand_written_adversarial"


def test_both_arms_start_from_one_snapshot_and_are_deterministic(result):
    again = asyncio.run(job.run_experiment())
    assert again["snapshot_id"] == result["snapshot_id"]
    assert [c["snapshot_sha256"] for c in again["per_case"]] == [c["snapshot_sha256"] for c in result["per_case"]]
    assert again["arms"] == result["arms"]


def test_check_passes_on_real_gate(result):
    assert job.check(result) == []


def test_check_fails_when_gate_is_removed(monkeypatch):
    """Replace the gate with one that always says PASS: gate_on must now leak fabricated values."""
    monkeypatch.setattr(
        DeterministicGate, "evaluate", staticmethod(lambda rule_id, *a, **k: GateResult("PASS", rule_id))
    )
    broken = asyncio.run(job.run_experiment())
    assert _arm(broken, "gate_on")["counters"]["fabricated_dates"]["passed"] > 0
    assert any("gate_on passed" in p for p in job.check(broken))


def test_check_fails_when_bypass_is_fake(monkeypatch):
    """If gate_off secretly verified, the experiment would understate the harm. The check must notice."""
    original = s5_answer.AssembleAnswer.__init__

    def always_verify(self, *, verify=True):
        original(self, verify=True)

    monkeypatch.setattr(s5_answer.AssembleAnswer, "__init__", always_verify)
    fake = asyncio.run(job.run_experiment())
    assert any("not a true bypass" in p for p in job.check(fake))


def test_cases_file_must_be_synthetic_and_well_formed(tmp_path):
    data = json.loads(job.CASES_PATH.read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    bad["_synthetic"] = False
    (tmp_path / "a.json").write_text(json.dumps(bad))
    with pytest.raises(ValueError, match="_synthetic"):
        job.load_cases(tmp_path / "a.json")
    dup = copy.deepcopy(data)
    dup["cases"].append(copy.deepcopy(dup["cases"][0]))
    (tmp_path / "b.json").write_text(json.dumps(dup))
    with pytest.raises(ValueError, match="duplicate"):
        job.load_cases(tmp_path / "b.json")
    unlabeled = copy.deepcopy(data)
    unlabeled["cases"][0]["labels"] = []
    (tmp_path / "c.json").write_text(json.dumps(unlabeled))
    with pytest.raises(ValueError, match="labelled"):
        job.load_cases(tmp_path / "c.json")


def test_main_writes_results_and_check_exit_code(tmp_path, ab_validator):
    out = tmp_path / "r.json"
    assert job.main(["--out", str(out), "--check"]) == 0
    assert not list(ab_validator.iter_errors(json.loads(out.read_text())))


def test_committed_results_match_a_fresh_run(result, ab_validator):
    """runs/ab_experiment_results.json is what the UI shows. It must be what the current code produces."""
    committed = json.loads(COMMITTED_RESULTS.read_text(encoding="utf-8"))
    assert not list(ab_validator.iter_errors(committed))
    strip = lambda r: {k: v for k, v in r.items() if k != "generated_at"}  # noqa: E731
    assert strip(committed) == strip(result), "re-run `make ab` and commit runs/ab_experiment_results.json"


# ------------------------------------------------------------------------------------------------ API


def test_ab_results_endpoint(tmp_path):
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, runs_dir=tmp_path)
    try:
        client = TestClient(app)
        r = client.get("/v1/ab-results")
        assert r.status_code == 404 and "make ab" in r.json()["detail"]
        (tmp_path / "ab_experiment_results.json").write_text(COMMITTED_RESULTS.read_text(encoding="utf-8"))
        r = client.get("/v1/ab-results")
        assert r.status_code == 200 and r.json()["experiment_id"] == "ab-gate-v1"
    finally:
        app.dependency_overrides.clear()


def test_api_has_no_way_to_turn_the_gate_off():
    assert set(AnswerRequest.model_fields) == {"postcode", "power_kw", "direction"}
    client = TestClient(app)
    body = client.post(
        "/v1/answer", json={"postcode": "1012", "power_kw": 60, "direction": "feed_in", "verify": False, "gate": "off"}
    ).json()
    assert body["answer"]["per_direction"][0]["indicative_earliest_date"] is None  # the invented 2027-Q2 is dropped
    assert body["answer"]["gate"]["checks_run"] > 0

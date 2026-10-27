"""jobs/sweep_50_postcodes.py — 50-area sweep through the gated pipeline (C-T24)."""

import asyncio
import copy
import importlib.util
import json
import subprocess
import sys
import time

import pytest

from app.config import Settings
from app.stages.s1_resolve_location import DSO_RANGES, resolve
from tests.conftest import REPO_ROOT

JOB_PATH = REPO_ROOT / "jobs" / "sweep_50_postcodes.py"
COMMITTED = REPO_ROOT / "runs" / "sweep_summary.json"


def _load_job():
    spec = importlib.util.spec_from_file_location("sweep_50_postcodes", JOB_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


job = _load_job()


@pytest.fixture(scope="module")
def report():
    return asyncio.run(job.run_sweep(mode="fixture"))


@pytest.fixture
def sweep_validator(validator_for):
    return validator_for("SweepReport")


def _volatile_free(r: dict) -> dict:
    r = copy.deepcopy(r)
    for key in ("generated_at",):
        r.pop(key)
    r["methodology"].pop("run_window")
    r["cost"].pop("wall_seconds")
    for a in r["areas"]:
        a.pop("run_at")
    return r


# ------------------------------------------------------------------------------------------------ selection


def test_selection_is_50_unique_mapped_postcodes_split_evenly():
    areas = job.select_postcodes()
    assert len(areas) == 50 and len({a["postcode4"] for a in areas}) == 50
    assert [sum(1 for a in areas if a["dso"] == r.dso) for r in DSO_RANGES] == [17, 17, 16]
    for a in areas:
        loc, _ = resolve(a["postcode4"])
        assert loc["resolved"] and loc["dso"] == a["dso"] and loc["gemeente"] == a["gemeente"]
    assert job.select_postcodes() == areas  # deterministic
    # range endpoints are included, so the sample spans each range
    assert {"5600", "5658", "1000", "1099", "3000", "3089"} <= {a["postcode4"] for a in areas}


def test_selection_rejects_impossible_allocation():
    with pytest.raises(ValueError):
        job.select_postcodes(n=400)


# ------------------------------------------------------------------------------------------------ the run


def test_report_is_contract_valid_and_honest_about_inputs(report, sweep_validator):
    assert [f"{list(e.absolute_path)}: {e.message}" for e in sweep_validator.iter_errors(report)] == []
    assert report["mode"] == "fixture" and report["synthetic"] is True
    assert report["runner"] == "local_process" and report["serverless_job_id"] is None
    assert "SYNTHETIC" in report["methodology"]["known_biases"]
    assert "abstentions, not negatives" in report["methodology"]["known_biases"]
    assert report["cost"] == {**report["cost"], "total_usd": 0.0, "tavily_calls": 0, "model_calls": 0}


def test_counts_are_complete_and_never_padded(report):
    s = report["summary"]
    assert s["n_requested"] == 50 and s["n_completed"] == 50 and s["n_failed"] == 0
    assert sum(s["by_feed_in_verdict"].values()) == sum(s["by_consumption_verdict"].values()) == 50
    assert sum(v["n_requested"] for v in s["by_dso"].values()) == 50


def test_aggregates_match_the_per_area_rows(report):
    """Every summary number is recomputable from the area rows (no number exists only in the summary)."""
    s, areas = report["summary"], report["areas"]
    for d in ("feed_in", "consumption"):
        recs = [a["directions"][d] for a in areas]
        positioned = [r for r in recs if not r["abstained"]]
        no_firm = [r for r in positioned if r["verdict"] in job.NO_FIRM]
        nf = s["no_firm_capacity"][d]
        assert nf["n_no_firm_capacity"] == len(no_firm)
        assert nf["n_with_official_position"] == len(positioned)
        assert nf["pct_of_areas_with_official_position"] == round(100 * len(no_firm) / len(positioned), 1)
        assert s["indicative_dates"][d]["n_with_date"] == sum(1 for r in recs if r["indicative_date"])
        assert s["non_firm_capacity"][d]["n_with_stated_kw"] == sum(1 for r in recs if r["non_firm_kw"] is not None)
    assert s["direction_split_cases"] == sum(
        1
        for a in areas
        if a["status"] == "completed" and not a["abstained"] and a["feed_in_verdict"] != a["consumption_verdict"]
    )


def test_fixture_values_come_from_the_gated_pipeline(report):
    """In fixture mode each operator's areas carry exactly what /v1/answer returns for that operator."""
    by_dso = report["summary"]["by_dso"]
    assert by_dso["Enexis"]["feed_in"] == {"WAITLIST_ONLY": 17}
    assert by_dso["Enexis"]["consumption"] == {"CAPACITY_AVAILABLE": 17}
    assert by_dso["Liander"]["consumption"] == {"NON_FIRM_ONLY": 17}
    assert by_dso["Stedin"]["feed_in"] == by_dso["Stedin"]["consumption"] == {"NO_OFFICIAL_POSITION_FOUND": 16}
    dates = report["summary"]["indicative_dates"]["feed_in"]
    assert dates["distribution"] == {"2028-Q3": 17} and dates["binding"] == {"non_binding": 17}
    assert report["summary"]["non_firm_capacity"]["feed_in"]["distribution"] == {"60": 17}


def test_abstentions_are_not_counted_as_negatives(report):
    stedin = [a for a in report["areas"] if a["dso"] == "Stedin"]
    assert stedin and all(a["abstained"] and a["source_document_ids"] == [] for a in stedin)
    nf = report["summary"]["no_firm_capacity"]["feed_in"]
    assert nf["n_with_official_position"] == 50 - len(stedin)
    assert report["summary"]["n_abstained"] == len(stedin)


def test_every_date_carries_its_binding_status(report):
    for a in report["areas"]:
        for r in (a["directions"] or {}).values():
            if r["indicative_date"]:
                assert r["binding"] in ("binding", "non_binding", "unknown")


def test_runs_well_under_ten_seconds():
    t = time.perf_counter()
    asyncio.run(job.run_sweep(mode="fixture"))
    assert time.perf_counter() - t < 10


def test_partial_dates_aggregate_by_period_start():
    assert job._month_index("2028-Q3") == 2028 * 12 + 6
    assert job._month_index("2029-H2") == 2029 * 12 + 6
    assert job._month_index("2028-11-05") == 2028 * 12 + 10
    assert job._month_index("2028-Q4/2029-Q2") == job._month_index("2028-Q4")
    assert job._quarter(job._month_index("2030-02")) == "2030-Q1"


# ------------------------------------------------------------------------------------------------ failure paths


def test_failed_area_is_reported_not_padded(monkeypatch, sweep_validator):
    real = job.answer_query

    async def flaky(**kw):
        if kw["postcode"] == "1012":
            raise RuntimeError("publisher timed out")
        return await real(**kw)

    monkeypatch.setattr(job, "answer_query", flaky)
    r = asyncio.run(job.run_sweep(mode="fixture"))
    s = r["summary"]
    assert s["n_completed"] == 49 and s["n_failed"] == 1 and s["n_requested"] == 50
    bad = next(a for a in r["areas"] if a["postcode4"] == "1012")
    assert bad["status"] == "failed" and "publisher timed out" in bad["error"] and bad["directions"] is None
    assert bad["feed_in_verdict"] == bad["consumption_verdict"] == "NOT_RUN"
    assert sum(s["by_feed_in_verdict"].values()) == 49
    assert s["by_dso"]["Liander"] == {**s["by_dso"]["Liander"], "n_requested": 17, "n_completed": 16}
    assert not list(sweep_validator.iter_errors(r))


def test_live_mode_without_keys_refuses(tmp_path, monkeypatch):
    no_keys = Settings(_env_file=None, nebius_api_key=None, tavily_api_key=None, runs_dir=tmp_path)
    with pytest.raises(ValueError, match="live"):
        asyncio.run(job.run_sweep(mode="live", settings=no_keys))
    monkeypatch.setattr(job, "get_settings", lambda: no_keys)
    out = tmp_path / "s.json"
    assert job.main(["--mode", "live", "--out", str(out)]) == 2
    assert not out.exists()


def test_serverless_runner_requires_a_job_id(capsys):
    with pytest.raises(SystemExit) as exc:
        job.main(["--runner", "nebius_serverless_job"])
    assert exc.value.code == 2


def test_contract_rejects_dishonest_reports(report, sweep_validator):
    claims_live = copy.deepcopy(report)
    claims_live["synthetic"] = False
    assert list(sweep_validator.iter_errors(claims_live))
    claims_serverless = copy.deepcopy(report)
    claims_serverless["runner"] = "nebius_serverless_job"
    assert list(sweep_validator.iter_errors(claims_serverless))
    abstained_with_date = copy.deepcopy(report)
    stedin = next(a for a in abstained_with_date["areas"] if a["dso"] == "Stedin")
    stedin["directions"]["feed_in"]["indicative_date"] = "2029-Q1"
    stedin["directions"]["feed_in"]["binding"] = "unknown"
    assert list(sweep_validator.iter_errors(abstained_with_date))
    failed_without_error = copy.deepcopy(report)
    failed_without_error["areas"][0]["status"] = "failed"
    assert list(sweep_validator.iter_errors(failed_without_error))


# ------------------------------------------------------------------------------------------------ CLI + committed file


def test_main_writes_file(tmp_path):
    out = tmp_path / "sweep.json"
    assert job.main(["--out", str(out)]) == 0
    assert json.loads(out.read_text())["summary"]["n_completed"] == 50


def test_plain_python_invocation_works(tmp_path):
    """The acceptance command: `python jobs/sweep_50_postcodes.py` (here with the test interpreter)."""
    out = tmp_path / "sweep.json"
    t = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(JOB_PATH), "--out", str(out)], capture_output=True, text=True, cwd=REPO_ROOT, timeout=60
    )
    assert proc.returncode == 0, proc.stderr
    assert time.perf_counter() - t < 10
    assert "SYNTHETIC" in proc.stdout and out.exists()


def test_committed_summary_matches_a_fresh_run(report, sweep_validator):
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert not list(sweep_validator.iter_errors(committed))
    assert _volatile_free(committed) == _volatile_free(report), "re-run `make sweep` and commit runs/sweep_summary.json"

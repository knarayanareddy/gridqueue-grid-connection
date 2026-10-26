"""C-T23 — gate_on vs gate_off: what does the deterministic citation gate actually stop?

Every case in the committed SYNTHETIC adversarial set (data/fixtures/synthetic/ab/adversarial_cases.json) is run
through S1 → S3 ONCE. That state (retrieved documents + model proposals) is the case's *snapshot*. Two
branches then start from deep copies of the same snapshot:

    gate_on   S5 as served by the API: every quote, date, kW, binding statement and route is re-checked
    gate_off  S5 with verification bypassed: the proposals become the answer as they are

For every hand-labelled value we look at the FINAL ANSWER of each branch and record whether the value reached
it. Counters per branch: fabricated dates / kW / binding statements / routes that passed, misattributed values
that passed, genuine values kept (a genuine value that is dropped is a false reject).

What this is and is not
* It runs the two branches as two in-process arms from one snapshot. It is NOT yet a Token Factory Sandbox
  branch run; ``execution.environment`` says so, and the runbook is in reports/C-T21-T23.TASK_REPORT.md.
* The test set is hand-written and synthetic. It shows which fabrication patterns the gate stops (and which
  misattributions it does not); it does not measure how often a real model invents dates.

Usage (from backend/):
    uv run python ../jobs/ab_branch_eval.py [--out PATH] [--check]
``--check`` exits 1 unless gate_on passes zero fabricated values and gate_off passes all of them.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:  # allow running without an installed package
    sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.pipeline import Services, run_stages  # noqa: E402
from app.stages.context import RunContext  # noqa: E402
from app.stages.s5_answer import AssembleAnswer  # noqa: E402

EXPERIMENT_ID = "ab-gate-v1"
CASES_PATH = REPO_ROOT / "data" / "fixtures" / "synthetic" / "ab" / "adversarial_cases.json"
FIXTURE_PREFIX = "data/fixtures/synthetic/"
RESULTS_FILENAME = "ab_experiment_results.json"

FIELDS = {"date", "kw", "binding", "option_kw", "route"}
LABELS = {"genuine", "fabricated", "misattributed"}
ARMS = (("gate_on", True), ("gate_off", False))

# Counter names. SPEC C-T23 names in brackets.
COUNTERS = (
    "fabricated_dates",  # [dates_without_document]
    "fabricated_kw",  # [kw_without_quote]
    "fabricated_binding",  # [binding_not_stated]
    "fabricated_routes",  # [option_without_route]
    "misattributed",
    "genuine",
)
SPEC_COUNTERS = {
    "dates_without_document": "fabricated_dates",
    "kw_without_quote": "fabricated_kw",
    "binding_not_stated": "fabricated_binding",
    "option_without_route": "fabricated_routes",
}


def counter_for(label: dict[str, Any]) -> str:
    if label["label"] != "fabricated":
        return str(label["label"])
    return {
        "date": "fabricated_dates",
        "kw": "fabricated_kw",
        "option_kw": "fabricated_kw",
        "binding": "fabricated_binding",
        "route": "fabricated_routes",
    }[label["field"]]


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def load_cases(path: Path = CASES_PATH) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if data.get("_synthetic") is not True:
        raise ValueError(f'{path} must declare "_synthetic": true')
    seen: set[str] = set()
    for case in data["cases"]:
        if case["id"] in seen:
            raise ValueError(f"duplicate case id {case['id']}")
        seen.add(case["id"])
        if case["doc"] not in data["documents"]:
            raise ValueError(f"{case['id']}: unknown document key {case['doc']!r}")
        if not case["labels"]:
            raise ValueError(f"{case['id']}: a case needs at least one labelled value")
        if len(case["proposal"]["claims"]) > 1:
            raise ValueError(f"{case['id']}: one claim per case, so the answer-level outcome is the claim's outcome")
        for lab in case["labels"]:
            if lab["field"] not in FIELDS or lab["label"] not in LABELS:
                raise ValueError(f"{case['id']}: bad label {lab}")
            if lab["field"] in ("option_kw", "route") and not lab.get("kind"):
                raise ValueError(f"{case['id']}: {lab['field']} label needs 'kind'")
    return data


class CaseExtractor:
    """Plays one case's hand-written proposal as if it were the model output (S3 still schema-validates it)."""

    kind = "replay"
    model = None

    def __init__(self, case: dict[str, Any], doc_file: str):
        self._case = case
        self._local_path = FIXTURE_PREFIX + doc_file

    async def extract(self, ctx: Any) -> Any:
        doc_id = next((d["document_id"] for d in ctx.documents if d.get("local_path") == self._local_path), None)
        if doc_id is None:
            raise ValueError(f"case {self._case['id']}: document {self._local_path} was not retrieved")
        proposal = copy.deepcopy(self._case["proposal"])
        for item in proposal["claims"] + proposal["options"]:
            item["document_id"] = doc_id
        return proposal


def snapshot_digest(ctx: RunContext) -> str:
    """What both branches start from: retrieved documents (by hash), the location, and the proposals."""
    return sha256_json(
        {
            "documents": [(d["document_id"], d["sha256"]) for d in ctx.documents],
            "location": {k: v for k, v in (ctx.location or {}).items() if k != "resolved_at"},
            "direction": ctx.direction,
            "power_kw": ctx.power_kw,
            "extraction": ctx.extraction,
        }
    )


def reached_answer(answer: dict[str, Any], label: dict[str, Any]) -> bool:
    """Did the labelled value end up in the branch's final answer?"""
    dr = answer["per_direction"][0]
    claim = dr.get("position_claim") or {}
    value, field = label["value"], label["field"]
    if field == "date":
        return dr.get("indicative_earliest_date") == value
    if field == "kw":
        return dr.get("available_capacity_kw") is not None and float(dr["available_capacity_kw"]) == float(value)
    if field == "binding":
        return claim.get("binding") == value
    options = [o for o in answer["options_ranked"] if o["kind"] == label["kind"]]
    if field == "route":
        return bool(options)
    return any(
        o.get("estimated_kw_enabled") is not None and float(o["estimated_kw_enabled"]) == float(value) for o in options
    )


async def run_case(case: dict[str, Any], doc_file: str) -> dict[str, Any]:
    services = Services(mode="fixture", tavily=None, extractor=CaseExtractor(case, doc_file))
    ctx = await run_stages(
        postcode=case["postcode"],
        power_kw=case["power_kw"],
        direction=case["direction"],
        services=services,
        run_id=f"ab-{case['id']}",
    )
    before = snapshot_digest(ctx)
    answers = {
        arm: AssembleAnswer(verify=verify).build(copy.deepcopy(ctx), time.perf_counter()) for arm, verify in ARMS
    }
    if snapshot_digest(ctx) != before:
        raise RuntimeError(f"case {case['id']}: a branch mutated the shared snapshot")
    labels = []
    for lab in case["labels"]:
        labels.append(
            {
                **lab,
                "counter": counter_for(lab),
                **{f"reached_{arm}": reached_answer(answers[arm], lab) for arm, _ in ARMS},
            }
        )
    return {
        "case_id": case["id"],
        "title": case["title"],
        "dso": ctx.location["dso"] if ctx.location else None,
        "direction": case["direction"],
        "snapshot_sha256": before,
        "verdict": {arm: answers[arm]["per_direction"][0]["verdict"] for arm, _ in ARMS},
        "gate_checks_run": {arm: answers[arm]["gate"]["checks_run"] for arm, _ in ARMS},
        "rejected_reasons_gate_on": sorted(r["reason"] for r in answers["gate_on"]["gate"]["rejected_claims"]),
        "labels": labels,
    }


def summarise(per_case: list[dict[str, Any]]) -> list[dict[str, Any]]:
    arms = []
    for arm, verify in ARMS:
        counters = {name: {"total": 0, "passed": 0} for name in COUNTERS}
        verdicts: dict[str, int] = {}
        for case in per_case:
            verdicts[case["verdict"][arm]] = verdicts.get(case["verdict"][arm], 0) + 1
            for lab in case["labels"]:
                counters[lab["counter"]]["total"] += 1
                counters[lab["counter"]]["passed"] += int(lab[f"reached_{arm}"])
        fabricated_total = sum(counters[c]["total"] for c in COUNTERS[:4])
        fabricated_passed = sum(counters[c]["passed"] for c in COUNTERS[:4])
        arms.append(
            {
                "arm": arm,
                "gate_enabled": verify,
                "n_cases": len(per_case),
                "counters": counters,
                "spec_counters": {k: counters[v]["passed"] for k, v in SPEC_COUNTERS.items()},
                "fabricated_values": {"total": fabricated_total, "passed": fabricated_passed},
                "false_rejects": counters["genuine"]["total"] - counters["genuine"]["passed"],
                "verdicts": dict(sorted(verdicts.items())),
                "gate_checks_run": sum(c["gate_checks_run"][arm] for c in per_case),
                "llm_calls_in_gate": 0,
            }
        )
    return arms


def headline(arms: list[dict[str, Any]]) -> str:
    on, off = (a["counters"] for a in arms)
    d, k = "fabricated_dates", "fabricated_kw"
    return (
        f"On {off[d]['total']} fabricated dates and {off[k]['total']} fabricated kW figures in a synthetic adversarial "
        f"set: with the gate OFF, {off[d]['passed']} dates and {off[k]['passed']} kW figures reached the answer; "
        f"with the gate ON, {on[d]['passed']} and {on[k]['passed']}."
    )


async def run_experiment(cases_path: Path = CASES_PATH) -> dict[str, Any]:
    data = load_cases(cases_path)
    per_case = [await run_case(c, data["documents"][c["doc"]]) for c in data["cases"]]
    arms = summarise(per_case)
    on, off = (a["counters"] for a in arms)
    mis = on["misattributed"]
    cases_bytes = cases_path.read_bytes()
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "headline": headline(arms),
        "execution": {
            "environment": "local_process",
            "token_factory_sandbox": False,
            "network_disabled": None,
            "sandbox_image_uuid": None,
            "branch_operation_ids": None,
            "note": "Both arms ran in one local process from deep copies of the same per-case snapshot. Not yet run "
            "as Token Factory Sandbox branches.",
        },
        "test_set": {
            "path": str(cases_path.relative_to(REPO_ROOT)) if cases_path.is_relative_to(REPO_ROOT) else str(cases_path),
            "version": data["version"],
            "sha256": hashlib.sha256(cases_bytes).hexdigest(),
            "synthetic": True,
            "proposal_source": "hand_written_adversarial",
            "n_cases": len(per_case),
            "n_labelled_values": sum(len(c["labels"]) for c in per_case),
        },
        "snapshot_id": sha256_json([c["snapshot_sha256"] for c in per_case]),
        "arms": arms,
        "delta": {
            name: {"gate_on": on[name]["passed"], "gate_off": off[name]["passed"], "total": on[name]["total"]}
            for name in COUNTERS
        },
        "limitations": [
            "The test set is synthetic and hand-written by the same project that wrote the gate. It shows which "
            "fabrication patterns the gate stops; it does not measure how often a real model invents dates.",
            "The two arms ran in one local process from the same snapshot, not as Token Factory Sandbox branches.",
            f"Misattributed values (the quote is in the document but does not mean what is asserted): gate ON let "
            f"{mis['passed']} of {mis['total']} through. The gate checks that a value is stated in the quoted text, "
            "not what the sentence means.",
        ],
        "per_case": per_case,
    }


def check(result: dict[str, Any]) -> list[str]:
    on, off = result["arms"]
    problems = []
    if on["fabricated_values"]["passed"] != 0:
        problems.append(f"gate_on passed {on['fabricated_values']['passed']} fabricated value(s)")
    if off["fabricated_values"]["passed"] != off["fabricated_values"]["total"]:
        problems.append("gate_off did not pass every fabricated value: the bypass is not a true bypass")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cases", type=Path, default=CASES_PATH)
    ap.add_argument("--out", type=Path, default=None, help=f"default: $RUNS_DIR/{RESULTS_FILENAME}")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    result = asyncio.run(run_experiment(args.cases))
    out = args.out or (get_settings().runs_dir / RESULTS_FILENAME)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(result["headline"])
    for arm in result["arms"]:
        c = arm["counters"]
        print(f"  {arm['arm']:<9} " + "  ".join(f"{k}={c[k]['passed']}/{c[k]['total']}" for k in COUNTERS))
    print(f"wrote {out}")
    if args.check:
        problems = check(result)
        for p in problems:
            print(f"CHECK FAILED: {p}", file=sys.stderr)
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

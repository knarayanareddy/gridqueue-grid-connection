"""C-T24 — run the gated /v1/answer pipeline over 50 postcode areas and aggregate what the operators published.

For every area and both directions (feed-in, consumption) this runs exactly what POST /v1/answer runs
(S1 → S2 → S3 → S5, gate on; there is no gate-off path here) and keeps only gate-verified values. It then
aggregates:

* share of areas where the operator's position is "no firm capacity for a new request"
  (verdict WAITLIST_ONLY, NON_FIRM_ONLY or NO_FIRM_CAPACITY), with the denominator stated;
* the indicative dates published for congested areas (distribution, median, mean; always with binding status);
* the kW the operator states for its non-firm connection route.

Output: ``runs/sweep_summary.json`` (schemas/core-schemas.json#/$defs/SweepReport, v1.4.0).

What it is and is not
* **Offline (``--mode fixture``, the default) it reads the SYNTHETIC fixture documents.** There are two (one
  Enexis, one Liander; Stedin has none), so every area of an operator gets the same answer and the aggregates
  only reflect how many areas fall in each operator's range. The report says ``synthetic: true``. **Its numbers
  say nothing about the Dutch grid** and must not be quoted as findings.
* ``--mode live`` uses Tavily + the model (both keys required; never mixed with fixtures). Not run yet.
* Area selection is a fixed, reproducible rule over the three postcode ranges the project maps today
  (backend/app/stages/s1_resolve_location.py, themselves TODO_VERIFY(C-T04)). It is NOT a list of "major
  commercial" areas: no source for such a list is in the repo (TODO_VERIFY(commercial-area-list)).
* Designed to run as a Nebius Serverless Job from jobs/Dockerfile (runbook in reports/C-T24-PACKAGE.TASK_REPORT.md).
  ``--runner`` defaults to ``local_process``; only pass ``nebius_serverless_job`` with the real job id.

Usage (from the repo root, inside the backend environment):
    uv run --project backend python jobs/sweep_50_postcodes.py [--mode fixture|live] [--out PATH] [--stdout]
or  make sweep
Exit codes: 0 written · 1 every area failed · 2 bad invocation (e.g. live mode without keys, missing packages).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import statistics
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "backend") not in sys.path:  # allow running without an installed package
    sys.path.insert(0, str(REPO_ROOT / "backend"))

try:
    from app.config import Settings, get_settings
    from app.pipeline import Services, answer_query, build_services, choose_mode
    from app.stages.s1_resolve_location import DSO_RANGES, MAPPING_SOURCE, DsoRange
    from app.stages.s3_extract import ReplayExtractor
except ModuleNotFoundError as exc:  # pragma: no cover - exercised only outside the backend environment
    # Plain `python jobs/sweep_50_postcodes.py` outside the backend environment: re-run once inside it via uv.
    import os
    import shutil

    if __name__ == "__main__" and shutil.which("uv") and not os.environ.get("GRIDQUEUE_SWEEP_REEXEC"):
        os.environ["GRIDQUEUE_SWEEP_REEXEC"] = "1"
        cmd = ["uv", "run", "--quiet", "--project", str(REPO_ROOT / "backend"), "python", __file__, *sys.argv[1:]]
        os.execvp("uv", cmd)
    sys.stderr.write(
        f"Missing package: {exc.name}. Run inside the backend environment:\n"
        "  uv run --project backend python jobs/sweep_50_postcodes.py   (or: make sweep)\n"
    )
    raise SystemExit(2) from exc

REPORT_ID = "sweep-50-v1"
N_AREAS = 50
DIRECTIONS = ("feed_in", "consumption")
DEFAULT_POWER_KW = 60.0  # the SPEC §1 persona's PV system
OUTPUT_FILENAME = "sweep_summary.json"
NO_FIRM = ("WAITLIST_ONLY", "NON_FIRM_ONLY", "NO_FIRM_CAPACITY")
ABSTAIN = ("NO_OFFICIAL_POSITION_FOUND", "UNDETERMINED")
VERDICTS = ("CAPACITY_AVAILABLE", "PARTIAL_CAPACITY", *NO_FIRM, *ABSTAIN)


# ---------------------------------------------------------------------------------------------- selection


def allocate(n: int, ranges: tuple[DsoRange, ...]) -> list[int]:
    """Split n over the ranges as evenly as possible (earlier ranges get the remainder)."""
    base, extra = divmod(n, len(ranges))
    return [base + (1 if i < extra else 0) for i in range(len(ranges))]


def select_postcodes(n: int = N_AREAS, ranges: tuple[DsoRange, ...] = DSO_RANGES) -> list[dict[str, Any]]:
    """Evenly spaced postcode4 values in each mapped range, endpoints included.

    Deterministic, and uses no congestion data.
    """
    out: list[dict[str, Any]] = []
    for r, k in zip(ranges, allocate(n, ranges), strict=True):
        span = r.high - r.low
        if k > span + 1:
            raise ValueError(f"{r.dso} range {r.low}-{r.high} has fewer than {k} postcodes")
        picks = sorted({r.low + round(i * span / (k - 1)) for i in range(k)} if k > 1 else {r.low})
        if len(picks) != k:
            raise ValueError(f"{r.dso}: even spacing produced duplicates")
        out += [{"postcode4": str(p), "dso": r.dso, "gemeente": r.gemeente} for p in picks]
    return out


# ---------------------------------------------------------------------------------------------- one area


def _direction_record(qr: dict[str, Any]) -> dict[str, Any]:
    answer = qr["answer"]
    dr = answer["per_direction"][0]
    claim = dr.get("position_claim") or {}
    non_firm = [
        o["estimated_kw_enabled"]
        for o in answer["options_ranked"]
        if o["kind"] == "non_firm_connection" and o.get("estimated_kw_enabled") is not None
    ]
    abstained = dr["verdict"] in ABSTAIN
    reasons = [a.get("reason") for a in dr.get("abstentions") or [] if a.get("reason")]
    return {
        "verdict": dr["verdict"],
        "congestion_registered": claim.get("congestion_registered"),
        "queue_status": claim.get("queue_status"),
        "indicative_date": dr.get("indicative_earliest_date"),
        "binding": str(dr.get("binding_chip") or "NOT_APPLICABLE").lower(),
        "available_capacity_kw": dr.get("available_capacity_kw"),
        "non_firm_kw": max(non_firm) if non_firm else None,
        "option_kinds": [o["kind"] for o in answer["options_ranked"]],
        "source_document_ids": sorted({d["document_id"] for d in qr["documents"]}) if not abstained else [],
        "abstained": abstained,
        "abstain_reason": (reasons[0] if reasons else "no_official_position") if abstained else None,
        "gate_checks_run": int(answer["gate"]["checks_run"]),
    }


def _snapshot_id(docs: list[dict[str, Any]]) -> str:
    pairs = sorted({(d["document_id"], d["sha256"]) for d in docs})
    return hashlib.sha256(json.dumps(pairs).encode()).hexdigest()


def _earliest(records: dict[str, dict[str, Any]]) -> tuple[str | None, str | None]:
    dated = [(r["indicative_date"], r["binding"]) for r in records.values() if r["indicative_date"]]
    if not dated:
        return None, None
    return min(dated, key=lambda t: _month_index(t[0]))


async def run_area(
    area: dict[str, Any], *, services: Services, power_kw: float, run_id: str, runs_dir: Path | None
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    """Both directions for one area. Returns (SweepArea, documents seen, call counts). Never raises."""
    base = {
        "postcode4": area["postcode4"],
        "gemeente": area["gemeente"],
        "provincie": None,
        "dso": area["dso"],
        "congestion_area_id": None,
        "selected_by": "systematic_sample",
        "run_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    calls = {"tavily_calls": 0, "model_calls": 0}
    records: dict[str, dict[str, Any]] = {}
    docs: list[dict[str, Any]] = []
    try:
        for direction in DIRECTIONS:
            qr = await answer_query(
                postcode=area["postcode4"],
                power_kw=power_kw,
                direction=direction,  # type: ignore[arg-type]
                services=services,
                run_id=f"{run_id}-{area['postcode4']}-{direction}",
                runs_dir=runs_dir,
            )
            records[direction] = _direction_record(qr)
            docs += qr["documents"]
            calls["tavily_calls"] += int(qr["retrieval"].get("tavily_calls") or 0)
            calls["model_calls"] += 1 if qr["retrieval"].get("extraction") == "live_model" else 0
    except Exception as exc:  # one bad area must not sink the sweep; it is reported, never padded
        return (
            {
                **base,
                "feed_in_verdict": "NOT_RUN",
                "consumption_verdict": "NOT_RUN",
                "indicative_date": None,
                "binding": None,
                "available_capacity_kw": None,
                "source_document_ids": [],
                "abstained": False,
                "abstain_reason": None,
                "corpus_snapshot_id": _snapshot_id(docs),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}"[:300] or type(exc).__name__,
                "directions": None,
            },
            docs,
            calls,
        )
    date, binding = _earliest(records)
    both_abstained = all(r["abstained"] for r in records.values())
    return (
        {
            **base,
            "feed_in_verdict": records["feed_in"]["verdict"],
            "consumption_verdict": records["consumption"]["verdict"],
            "indicative_date": date,
            "binding": binding,
            "available_capacity_kw": None,
            "source_document_ids": sorted({i for r in records.values() for i in r["source_document_ids"]}),
            "abstained": both_abstained,
            "abstain_reason": records["feed_in"]["abstain_reason"] if both_abstained else None,
            "corpus_snapshot_id": _snapshot_id(docs),
            "status": "completed",
            "error": None,
            "directions": records,
        },
        docs,
        calls,
    )


# ---------------------------------------------------------------------------------------------- aggregation


def _month_index(token: str) -> int:
    """Start month of a partial date ('2028-Q3' -> 2028*12+6). Ranges use their start."""
    start = token.split("/")[0]
    year, _, rest = start.partition("-")
    y = int(year)
    if not rest:
        return y * 12
    if rest[0] == "Q":
        return y * 12 + 3 * (int(rest[1]) - 1)
    if rest[0] == "H":
        return y * 12 + 6 * (int(rest[1]) - 1)
    return y * 12 + int(rest[:2]) - 1


def _quarter(index: int) -> str:
    return f"{index // 12}-Q{(index % 12) // 3 + 1}"


def _pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 1) if d else None


def summarise(areas: list[dict[str, Any]]) -> dict[str, Any]:
    done = [a for a in areas if a["status"] == "completed"]
    summary: dict[str, Any] = {
        "n_requested": len(areas),
        "n_completed": len(done),
        "n_failed": len(areas) - len(done),
        "n_abstained": sum(1 for a in done if a["abstained"]),
        "by_feed_in_verdict": dict(sorted(Counter(a["feed_in_verdict"] for a in done).items())),
        "by_consumption_verdict": dict(sorted(Counter(a["consumption_verdict"] for a in done).items())),
        "by_dso": {},
        "direction_split_cases": sum(
            1
            for a in done
            if not any(a["directions"][d]["abstained"] for d in DIRECTIONS)
            and a["feed_in_verdict"] != a["consumption_verdict"]
        ),
        "no_firm_capacity": {},
        "indicative_dates": {},
        "non_firm_capacity": {},
    }
    for dso in sorted({a["dso"] for a in areas}):
        mine = [a for a in areas if a["dso"] == dso]
        ok = [a for a in mine if a["status"] == "completed"]
        summary["by_dso"][dso] = {
            "n_requested": len(mine),
            "n_completed": len(ok),
            "feed_in": dict(sorted(Counter(a["feed_in_verdict"] for a in ok).items())),
            "consumption": dict(sorted(Counter(a["consumption_verdict"] for a in ok).items())),
        }
    for d in DIRECTIONS:
        recs = [a["directions"][d] for a in done]
        positioned = [r for r in recs if not r["abstained"]]
        no_firm = [r for r in positioned if r["verdict"] in NO_FIRM]
        summary["no_firm_capacity"][d] = {
            "n_no_firm_capacity": len(no_firm),
            "n_closed": sum(1 for r in positioned if r["verdict"] == "NO_FIRM_CAPACITY"),
            "n_with_official_position": len(positioned),
            "n_completed": len(recs),
            "pct_of_areas_with_official_position": _pct(len(no_firm), len(positioned)),
            "pct_of_completed_areas": _pct(len(no_firm), len(recs)),
        }
        dated = [r for r in recs if r["indicative_date"]]
        idx = sorted(_month_index(r["indicative_date"]) for r in dated)
        summary["indicative_dates"][d] = {
            "n_with_date": len(dated),
            "n_congested_without_date": sum(1 for r in no_firm if not r["indicative_date"]),
            "distribution": dict(sorted(Counter(r["indicative_date"] for r in dated).items())),
            "binding": dict(sorted(Counter(r["binding"] for r in dated).items())),
            "earliest": _quarter(idx[0]) if idx else None,
            "latest": _quarter(idx[-1]) if idx else None,
            "median_quarter": _quarter(int(statistics.median_low(idx))) if idx else None,
            "mean_quarter": _quarter(int(sum(idx) / len(idx))) if idx else None,
        }
        offered = [r for r in recs if "non_firm_connection" in r["option_kinds"]]
        kws = sorted(r["non_firm_kw"] for r in recs if r["non_firm_kw"] is not None)
        summary["non_firm_capacity"][d] = {
            "n_areas_with_non_firm_route": len(offered),
            "n_with_stated_kw": len(kws),
            "kw_min": kws[0] if kws else None,
            "kw_median": statistics.median(kws) if kws else None,
            "kw_max": kws[-1] if kws else None,
            "distribution": {format(k, "g"): c for k, c in sorted(Counter(kws).items())},
        }
    return summary


def methodology(
    *, mode: str, synthetic: bool, n: int, snapshot_id: str, window: str, interval: float
) -> dict[str, Any]:
    per = allocate(n, DSO_RANGES)
    ranges = "; ".join(f"{r.dso} {r.low}–{r.high} ({r.gemeente}): {k}" for r, k in zip(DSO_RANGES, per, strict=True))
    return {
        "area_selection": (
            f"{n} postcode4 areas, evenly spaced (endpoints included) within each postcode range the project maps "
            f"today, split as evenly as possible: {ranges}. The ranges come from {MAPPING_SOURCE} and are "
            "UNVERIFIED against the operators' service-area publications (TODO_VERIFY(C-T04)). Selection uses no "
            "congestion data, so it is not cherry-picked towards congested areas, but it is not a list of "
            "commercial areas either (TODO_VERIFY(commercial-area-list)); some postcode4 values may not exist."
        ),
        "corpus_snapshot_id": snapshot_id,
        "run_window": window,
        "cache_policy": "None. Every area and direction runs S1–S5 in full. Caching S1–S3 by postcode4 + corpus "
        "snapshot (SPEC C-T24) is not implemented yet.",
        "exclusions": "None. Failed areas are listed with status 'failed' and excluded from every aggregate; they "
        "are counted in n_failed, never padded.",
        "known_biases": (
            "Areas where no official position could be established are abstentions, not negatives: they are left "
            "out of the 'with official position' denominators and reported separately. "
            + (
                "This run used SYNTHETIC fixture documents (one Enexis, one Liander, none for Stedin), so every "
                "area of an operator gets the same answer and the aggregates only reflect how many areas fall in "
                "each operator's range. They say nothing about the Dutch grid."
                if synthetic
                else "One retrieval per area and direction; the answer depends on which operator pages Tavily "
                "returned at run time."
            )
        ),
        "mode": mode,
        "synthetic": synthetic,
        "rate_limit": f"min {interval:g} s between area queries",
        "definitions": {
            "no_firm_capacity": "verdict WAITLIST_ONLY, NON_FIRM_ONLY or NO_FIRM_CAPACITY: the operator's published "
            "position is that a new request gets no firm capacity now. 'closed' = NO_FIRM_CAPACITY only.",
            "indicative_dates": "Operator-published indicative dates (codeerprognoses) that passed the gate, with "
            "their binding status. mean_quarter = mean of the period start months, floored to a quarter; "
            "median_quarter uses the lower median. These are statistics of published estimates, not a forecast.",
            "non_firm_kw": "kW the operator states for its non-firm connection route in that area, verified against "
            "the quote. Per-area figures; never summed (areas share grid assets).",
            "direction_split_cases": "completed areas where both directions have an official position and the "
            "verdicts differ.",
        },
    }


async def run_sweep(
    *,
    mode: str = "fixture",
    settings: Settings | None = None,
    n: int = N_AREAS,
    power_kw: float = DEFAULT_POWER_KW,
    runner: str = "local_process",
    serverless_job_id: str | None = None,
    min_interval: float | None = None,
) -> dict[str, Any]:
    cfg = settings or get_settings()
    if mode == "live" and choose_mode(cfg) != "live":
        raise ValueError("--mode live needs NEBIUS_API_KEY and TAVILY_API_KEY and MOCK_EXTERNAL_CALLS=false")
    run_id = f"sweep-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    services = (
        Services(mode="fixture", tavily=None, extractor=ReplayExtractor())
        if mode == "fixture"
        else build_services(cfg, run_id)
    )
    interval = (2.0 if mode == "live" else 0.0) if min_interval is None else min_interval
    started = datetime.now(UTC)
    t0 = time.perf_counter()
    areas: list[dict[str, Any]] = []
    docs: list[dict[str, Any]] = []
    calls = Counter[str]()
    for i, area in enumerate(select_postcodes(n)):
        if i and interval:
            await asyncio.sleep(interval)
        record, seen, c = await run_area(
            area, services=services, power_kw=power_kw, run_id=run_id, runs_dir=cfg.runs_dir if mode == "live" else None
        )
        areas.append(record)
        docs += seen
        calls.update(c)
    finished = datetime.now(UTC)
    snapshot = _snapshot_id(docs)
    synthetic = mode == "fixture"

    def iso(t: datetime) -> str:
        return t.isoformat(timespec="seconds").replace("+00:00", "Z")

    return {
        "report_id": REPORT_ID,
        "generated_at": iso(finished),
        "runner": runner,
        "serverless_job_id": serverless_job_id,
        "mode": mode,
        "synthetic": synthetic,
        "request": {"power_kw": power_kw, "directions": list(DIRECTIONS), "n_areas": n},
        "summary": summarise(areas),
        "methodology": methodology(
            mode=mode,
            synthetic=synthetic,
            n=n,
            snapshot_id=snapshot,
            window=f"{iso(started)}/{iso(finished)}",
            interval=interval,
        ),
        "cost": {
            "total_usd": 0.0,
            "tavily_calls": calls["tavily_calls"],
            "model_calls": calls["model_calls"],
            "wall_seconds": round(time.perf_counter() - t0, 3),
            "note": "Fixture mode makes no external calls." if synthetic else "Prices not configured; see the ledger.",
        },
        "areas": areas,
    }


def print_summary(report: dict[str, Any]) -> None:
    s = report["summary"]
    tag = "SYNTHETIC fixture run — not a finding about the Dutch grid" if report["synthetic"] else "live run"
    print(f"{report['report_id']} [{tag}] runner={report['runner']} mode={report['mode']}")
    print(
        f"  areas: requested={s['n_requested']} completed={s['n_completed']} failed={s['n_failed']} "
        f"abstained(both directions)={s['n_abstained']} direction_split={s['direction_split_cases']}"
    )
    for d in DIRECTIONS:
        nf, dt, kw = s["no_firm_capacity"][d], s["indicative_dates"][d], s["non_firm_capacity"][d]
        print(
            f"  {d:<11} no firm capacity {nf['n_no_firm_capacity']}/{nf['n_with_official_position']} with a position "
            f"({nf['pct_of_areas_with_official_position']}%) · dates n={dt['n_with_date']} "
            f"median={dt['median_quarter']} binding={dt['binding']} · non-firm kW n={kw['n_with_stated_kw']} "
            f"median={kw['kw_median']}"
        )
    print(
        f"  wall time {report['cost']['wall_seconds']} s · tavily calls {report['cost']['tavily_calls']} · "
        f"model calls {report['cost']['model_calls']}"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else None)
    ap.add_argument("--mode", choices=("fixture", "live"), default="fixture")
    ap.add_argument("--out", type=Path, help="default: <RUNS_DIR>/sweep_summary.json")
    ap.add_argument("--n", type=int, default=N_AREAS)
    ap.add_argument("--power-kw", type=float, default=DEFAULT_POWER_KW)
    ap.add_argument("--min-interval", type=float, help="seconds between areas (default 2 live, 0 fixture)")
    ap.add_argument("--runner", choices=("local_process", "nebius_serverless_job"), default="local_process")
    ap.add_argument("--serverless-job-id", help="required with --runner nebius_serverless_job")
    ap.add_argument("--stdout", action="store_true", help="also print the full JSON (for job logs)")
    args = ap.parse_args(argv)
    if args.runner == "nebius_serverless_job" and not args.serverless_job_id:
        ap.error("--runner nebius_serverless_job requires --serverless-job-id")
    if args.n < len(DSO_RANGES):
        ap.error(f"--n must be at least {len(DSO_RANGES)}")
    try:
        report = asyncio.run(
            run_sweep(
                mode=args.mode,
                n=args.n,
                power_kw=args.power_kw,
                runner=args.runner,
                serverless_job_id=args.serverless_job_id,
                min_interval=args.min_interval,
            )
        )
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    out = args.out or get_settings().runs_dir / OUTPUT_FILENAME
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_summary(report)
    print(f"wrote {out}")
    if args.stdout:
        print(json.dumps(report, ensure_ascii=False))
    return 1 if report["summary"]["n_completed"] == 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

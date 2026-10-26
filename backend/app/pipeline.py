"""Orchestrates S1 → S2 → S3 → S5 for POST /v1/answer and returns a QueryResponse."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from app.config import Settings
from app.stages.context import Mode, RunContext
from app.stages.s1_resolve_location import ResolveLocation
from app.stages.s2_retrieve import RetrieveDocuments
from app.stages.s3_extract import ExtractPositions, LiveExtractor, ReplayExtractor
from app.stages.s5_answer import AssembleAnswer
from app.tools.tavily import TavilyClient


@dataclass
class Services:
    """External dependencies for one request. Tests replace these; production builds them from Settings."""

    mode: Mode
    tavily: TavilyClient | None
    extractor: Any


def choose_mode(settings: Settings) -> Mode:
    """Live only when BOTH keys are configured and mocking is off. Never mix live and fixture data."""
    if settings.mock_external_calls or not (settings.has_tavily_key and settings.has_nebius_key):
        return "fixture"
    return "live"


def build_services(settings: Settings, run_id: str) -> Services:
    mode = choose_mode(settings)
    if mode == "fixture":
        return Services(mode="fixture", tavily=None, extractor=ReplayExtractor())
    assert settings.tavily_api_key is not None
    return Services(
        mode="live",
        tavily=TavilyClient(settings.tavily_api_key.get_secret_value(), runs_dir=settings.runs_dir, run_id=run_id),
        extractor=LiveExtractor(settings),
    )


def new_run_id() -> str:
    return uuid.uuid4().hex[:16]


async def run_stages(
    *,
    postcode: str,
    power_kw: float,
    direction: Literal["feed_in", "consumption"],
    services: Services,
    run_id: str,
    runs_dir: Any = None,
) -> RunContext:
    """S1 → S2 → S3. Returns the context S5 assembles from (also the A/B snapshot, see jobs/ab_branch_eval.py)."""
    ctx = RunContext(
        run_id=run_id,
        postcode=postcode,
        power_kw=power_kw,
        direction=direction,
        mode=services.mode,
        tavily=services.tavily,
        extractor=services.extractor,
        runs_dir=runs_dir,
    )
    ctx.retrieval = {
        "mode": services.mode,
        "synthetic": services.mode == "fixture",
        "performed_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "queries": [],
        "tavily_calls": 0,
        "results_seen": 0,
        "results_used": 0,
        "results_rejected": [],
        "extraction": "not_run",
        "model": None,
    }

    t = time.perf_counter()
    s1 = await ResolveLocation().run(ctx)
    ctx.timings_ms["s1_resolve_location"] = int((time.perf_counter() - t) * 1000)
    if s1.ok:
        await RetrieveDocuments().run(ctx)
        await ExtractPositions().run(ctx)
    return ctx


def query_response(ctx: RunContext, answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer": answer,
        "documents": ctx.documents,
        "citations": list(ctx.citations.values()),
        "retrieval": ctx.retrieval,
    }


async def answer_query(
    *,
    postcode: str,
    power_kw: float,
    direction: Literal["feed_in", "consumption"],
    services: Services,
    run_id: str,
    runs_dir: Any = None,
) -> dict[str, Any]:
    total_started = time.perf_counter()
    ctx = await run_stages(
        postcode=postcode, power_kw=power_kw, direction=direction, services=services, run_id=run_id, runs_dir=runs_dir
    )
    # The API always runs the gate. There is deliberately no parameter to turn it off.
    answer = AssembleAnswer().build(ctx, total_started)
    return query_response(ctx, answer)

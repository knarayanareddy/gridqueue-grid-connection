"""Common stage interface — docs/AGENT-DELEGATION-PROTOCOL.md §3 (contract-first integration)."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel


class StageResult(BaseModel):
    stage: str
    ok: bool
    data: dict[str, Any]  # must validate against the stage's schema in schemas/core-schemas.json
    citation_ids: list[str] = []  # ids of citations produced by this stage
    abstain: bool = False  # True => downstream must not treat data as a verdict
    abstain_reason: str | None = None
    cost_usd: float = 0.0
    latency_ms: int = 0
    ledger_ids: list[str] = []


class Stage(Protocol):
    name: str

    async def run(self, ctx: Any) -> StageResult: ...

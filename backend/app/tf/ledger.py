"""Append-only JSONL telemetry ledger.

One line per model call, Tavily call or Sandbox operation. The line shape is the ``LedgerLine`` contract in
``schemas/core-schemas.json`` (see also docs/PLATFORM-CAPABILITIES.md, "The ledger contract").
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from app.config import settings

LedgerKind = Literal[
    "chat.completions",
    "embeddings",
    "tavily.search",
    "tavily.extract",
    "sandbox.operation",
    "sandbox.branch",
]
LedgerStatus = Literal["ok", "error", "truncated", "schema_violation", "gate_rejected"]

LEDGER_FILENAME = "ledger.jsonl"


def ledger_path(runs_dir: Path | None = None) -> Path:
    return (runs_dir or settings.runs_dir) / LEDGER_FILENAME


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _append_line(path: Path, line: str) -> None:
    """Append one line, holding an exclusive lock so concurrent writers cannot interleave."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        if sys.platform != "win32":
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        else:  # pragma: no cover - best effort on Windows
            f.write(line)


def record_telemetry(
    kind: LedgerKind,
    stage: str,
    model: str | None,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cached_tokens: int = 0,
    cost_usd: float = 0.0,
    latency_ms: float = 0.0,
    status: LedgerStatus = "ok",
    *,
    run_id: str | None = None,
    response: dict[str, Any] | None = None,
    error: str | None = None,
    citation_ids_produced: list[str] | None = None,
    notes: str | None = None,
    runs_dir: Path | None = None,
) -> dict[str, Any]:
    """Append one ledger line and return it."""
    if min(prompt_tokens, completion_tokens, cached_tokens) < 0:
        raise ValueError("token counts must be non-negative")
    if cached_tokens > prompt_tokens:
        raise ValueError("cached_tokens cannot exceed prompt_tokens")

    entry: dict[str, Any] = {
        "id": _new_id("led"),
        "run_id": run_id,
        "ts": _utc_now_iso(),
        "kind": kind,
        "stage": stage,
        "model": model,
        "request": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cached_tokens": cached_tokens,
        },
        "response": response,
        "cost_usd": round(cost_usd, 6),
        "latency_ms": round(latency_ms, 2),
        "status": status,
        "error": error,
        "citation_ids_produced": citation_ids_produced or [],
        "notes": notes,
    }
    _append_line(ledger_path(runs_dir), json.dumps(entry, ensure_ascii=False) + "\n")
    return entry

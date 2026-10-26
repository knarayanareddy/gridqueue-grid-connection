"""Per-request state shared by the stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.tools.tavily import TavilyClient

Mode = Literal["live", "fixture"]


@dataclass
class RunContext:
    run_id: str
    postcode: str
    power_kw: float
    direction: Literal["feed_in", "consumption"]
    mode: Mode
    tavily: TavilyClient | None = None
    extractor: Any = None  # app.stages.s3_extract.Extractor
    runs_dir: Path | None = None

    # Filled in by the stages
    location: dict[str, Any] | None = None
    documents: list[dict[str, Any]] = field(default_factory=list)  # SourceDocument
    doc_texts: dict[str, str] = field(default_factory=dict)  # document_id -> full extracted text
    citations: dict[str, dict[str, Any]] = field(default_factory=dict)  # citation_id -> Citation
    retrieval: dict[str, Any] = field(default_factory=dict)  # QueryResponse.retrieval
    extraction: dict[str, Any] | None = None  # validated model (or replay) output
    abstentions: list[dict[str, Any]] = field(default_factory=list)
    timings_ms: dict[str, int] = field(default_factory=dict)
    tokens: dict[str, int] = field(default_factory=lambda: {"prompt": 0, "completion": 0, "cached": 0})
    llm_model: str | None = None
    llm_ledger_id: str | None = None

    def add_citation(self, citation: dict[str, Any]) -> str:
        self.citations[citation["id"]] = citation
        return str(citation["id"])

    def document(self, document_id: str) -> dict[str, Any] | None:
        return next((d for d in self.documents if d["document_id"] == document_id), None)

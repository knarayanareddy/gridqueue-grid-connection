"""S2 retrieve_documents — find and fetch the operator's current statements (SPEC §3 S2).

Two modes, chosen per request by the pipeline:

* ``live``    — Tavily Search (restricted to the operator's publication domain) → Tavily Extract → one
                ``SourceDocument`` per fetched page, hashed (sha256) and timestamped.
* ``fixture`` — committed documents from ``data/fixtures/synthetic/``. These are SYNTHETIC: written by this
                project to exercise the pipeline offline. They are never mixed with live documents, and the
                response says ``retrieval.synthetic = true`` so the UI can label them.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import REPO_ROOT
from app.stages.base import StageResult
from app.tools.tavily import TavilyError, build_queries

FIXTURE_DIR = REPO_ROOT / "data" / "fixtures" / "synthetic"
FIXTURE_INDEX = FIXTURE_DIR / "index.json"

MAX_DOCUMENTS = 3
MAX_RESULTS_PER_QUERY = 5

# The operator's own publication domain(s). Search is restricted to these so that only the operator's own
# statements can become evidence. Wrong values make retrieval return nothing, so the answer abstains; they
# can't make it accept the wrong source.
# TODO_VERIFY(C-T03: confirm each operator's publication domain(s), incl. any separate PDF/CDN host).
DSO_PUBLICATION_DOMAINS: dict[str, list[str]] = {
    "Enexis": ["enexis.nl"],
    "Liander": ["liander.nl"],
    "Stedin": ["stedin.net"],
}

# Direction vocabulary — data/domain-lexicon.md §1. Used to decide whether a document distinguishes the two
# directions at all (SourceDocument.direction_split_available).
FEED_IN_TERMS = ("teruglevering", "terugleveren", "terugleveringscapaciteit", "productiecapaciteit", "invoeding")
CONSUMPTION_TERMS = ("afname", "afnamecapaciteit")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def direction_split(text: str) -> bool:
    low = text.lower()
    return any(t in low for t in FEED_IN_TERMS) and any(t in low for t in CONSUMPTION_TERMS)


def _format_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext, fmt in ((".pdf", "pdf"), (".xlsx", "xlsx"), (".csv", "csv"), (".json", "json"), (".xml", "xml")):
        if path.endswith(ext):
            return fmt
    return "html"


def _domain_allowed(url: str, allowed: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in allowed)


def _source_document(
    *,
    family_id: str,
    publisher: str,
    title: str,
    url: str,
    text: str,
    fmt: str,
    licence: str,
    extraction_method: str,
    retrieved_at: str,
    publication_date: str | None = None,
    local_path: str | None = None,
) -> dict[str, Any]:
    digest = sha256_text(text)
    return {
        "document_id": f"doc_{family_id}_{digest[:10]}",
        "family_id": family_id,
        "publisher": publisher,
        "title": title,
        "title_en": None,
        "url": url,
        "publication_date": publication_date,
        "retrieved_at": retrieved_at,
        "sha256": digest,
        "format": fmt,
        "language": "nl",
        "licence": licence,
        "redistributable": None,
        "extraction_method": extraction_method,
        "pages_or_rows": None,
        "is_current": True,  # the version the publisher served at retrieved_at
        "superseded_by": None,
        "revision_of": None,
        "direction_split_available": direction_split(text),
        "age_days_at_answer": None,
        "local_path": local_path,
    }


def load_fixture_index(path: Path = FIXTURE_INDEX) -> dict[str, Any]:
    index: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if index.get("_synthetic") is not True:
        raise ValueError(f'{path} must declare "_synthetic": true')
    return index


class RetrieveDocuments:
    name = "s2_retrieve"

    async def run(self, ctx: Any) -> StageResult:
        started = time.perf_counter()
        try:
            if ctx.mode == "fixture":
                self._from_fixtures(ctx)
            else:
                await self._live(ctx)
        finally:
            ctx.timings_ms[self.name] = int((time.perf_counter() - started) * 1000)
        ok = bool(ctx.documents)
        return StageResult(
            stage=self.name,
            ok=ok,
            data={"document_ids": [d["document_id"] for d in ctx.documents]},
            abstain=not ok,
            abstain_reason=None if ok else "no_position_found",
            ledger_ids=list(ctx.tavily.ledger_ids) if ctx.tavily else [],
        )

    # ------------------------------------------------------------------ fixture mode

    def _from_fixtures(self, ctx: Any) -> None:
        index = load_fixture_index()
        dso = ctx.location["dso"]
        scenario = index["scenarios"].get(dso, {"documents": []})
        retrieved_at = _now_iso()
        for meta in scenario["documents"]:
            rel = meta["text_file"]
            text = (FIXTURE_DIR / rel).read_text(encoding="utf-8")
            doc = _source_document(
                family_id=meta["family_id"],
                publisher=meta["publisher"],
                title=meta["title"],
                url=meta["url"],
                text=text,
                fmt="html",
                licence="SYNTHETIC-FIXTURE (Apache-2.0, written by this project)",
                extraction_method="fixture_file",
                retrieved_at=retrieved_at,
                local_path=f"data/fixtures/synthetic/{rel}",
            )
            ctx.documents.append(doc)
            ctx.doc_texts[doc["document_id"]] = text
        ctx.retrieval.update(
            {
                "mode": "fixture",
                "synthetic": True,
                "performed_at": retrieved_at,
                "queries": [],
                "tavily_calls": 0,
                "results_seen": len(scenario["documents"]),
                "results_used": len(ctx.documents),
                "results_rejected": [],
            }
        )

    # ------------------------------------------------------------------ live mode

    async def _live(self, ctx: Any) -> None:
        dso = ctx.location["dso"]
        allowed = DSO_PUBLICATION_DOMAINS.get(dso, [])
        queries = build_queries(dso, ctx.direction, ctx.location.get("gemeente"))
        performed_at = _now_iso()
        rejected: list[dict[str, str]] = []
        seen = 0
        candidates: dict[str, dict[str, Any]] = {}
        ctx.retrieval.update(
            {
                "mode": "live",
                "synthetic": False,
                "performed_at": performed_at,
                "queries": [q.query for q in queries],
                "results_rejected": rejected,
            }
        )

        try:
            for q in queries:
                res = await ctx.tavily.search(q.query, include_domains=allowed, max_results=MAX_RESULTS_PER_QUERY)
                for r in res.get("results") or []:
                    url = r.get("url") or ""
                    seen += 1
                    if not _domain_allowed(url, allowed):
                        rejected.append({"url": url, "reason": "not_official_domain"})
                    elif url in candidates:
                        rejected.append({"url": url, "reason": "duplicate"})
                    else:
                        candidates[url] = {
                            "family_id": q.family_id,
                            "title": r.get("title") or url,
                            "score": float(r.get("score") or 0.0),
                        }

            ranked = sorted(candidates.items(), key=lambda kv: (-kv[1]["score"], kv[0]))
            chosen = ranked[:MAX_DOCUMENTS]
            rejected.extend({"url": u, "reason": "over_limit"} for u, _ in ranked[MAX_DOCUMENTS:])

            if chosen:
                extracted = await ctx.tavily.extract([u for u, _ in chosen])
                by_url = {r.get("url"): r for r in extracted.get("results") or []}
                rejected.extend(
                    {"url": f.get("url", ""), "reason": "extract_failed"} for f in extracted.get("failed_results") or []
                )
                retrieved_at = _now_iso()
                for url, meta in chosen:
                    item = by_url.get(url)
                    if item is None:
                        if not any(r["url"] == url for r in rejected):
                            rejected.append({"url": url, "reason": "extract_failed"})
                        continue
                    text = item.get("raw_content") or ""
                    if not text.strip():
                        rejected.append({"url": url, "reason": "empty_content"})
                        continue
                    doc = _source_document(
                        family_id=meta["family_id"],
                        publisher=dso,
                        title=meta["title"],
                        url=url,
                        text=text,
                        fmt=_format_from_url(url),
                        licence="unknown",
                        extraction_method="tavily.extract(extract_depth=basic, format=text)",
                        retrieved_at=retrieved_at,
                    )
                    if ctx.document(doc["document_id"]) is None:
                        ctx.documents.append(doc)
                        ctx.doc_texts[doc["document_id"]] = text
        except TavilyError as exc:
            ctx.abstentions.append(
                {
                    "reason": "tavily_unavailable",
                    "scope": "answer",
                    "message": f"Live document search failed, so no official statement could be retrieved ({exc}).",
                    "fix_instruction": "Try again later, or ask the grid operator directly using the script below.",
                    "document_id": None,
                    "observed_values": {"status_code": exc.status_code},
                }
            )
        finally:
            ctx.retrieval.update(
                {
                    "tavily_calls": ctx.tavily.calls if ctx.tavily else 0,
                    "results_seen": seen,
                    "results_used": len(ctx.documents),
                }
            )

"""Tavily Search / Extract client and the runtime query builder (SPEC §3 S2, docs/PLATFORM-CAPABILITIES.md §5).

Endpoints, auth and parameters follow the Tavily API reference, checked 2026-10-26:
  https://docs.tavily.com/documentation/api-reference/endpoint/search
  https://docs.tavily.com/documentation/api-reference/endpoint/extract
  - POST https://api.tavily.com/search   body: query, search_depth, max_results, topic, country,
                                         include_domains, include_raw_content, include_usage
  - POST https://api.tavily.com/extract  body: urls, extract_depth, format, include_usage
  - Auth: "Authorization: Bearer <TAVILY_API_KEY>"
Every call — success or failure — appends one line to the ledger (kind tavily.search / tavily.extract).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from app.config import REPO_ROOT
from app.tf.ledger import LedgerKind, LedgerStatus, record_telemetry

TAVILY_BASE_URL = "https://api.tavily.com"
SOURCE_REGISTER_PATH = REPO_ROOT / "data" / "source-register.v0.json"

# The two document families this ticket retrieves (data/source-register.v0.json).
QUERY_FAMILIES = ("dso_congestion_register", "dso_codeerprognose")

# Dutch direction vocabulary — data/domain-lexicon.md §1.
DIRECTION_NL = {"feed_in": "teruglevering", "consumption": "afname"}


class TavilyError(RuntimeError):
    """Tavily was unreachable or returned an error. Callers must abstain (reason tavily_unavailable)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class TavilyQuery:
    family_id: str
    query: str


@lru_cache
def _discovery_queries(register_path: Path = SOURCE_REGISTER_PATH) -> dict[str, list[str]]:
    register = json.loads(register_path.read_text(encoding="utf-8"))
    return {f["family_id"]: list(f.get("discovery_queries_nl") or []) for f in register["document_families"]}


def build_queries(dso: str, direction: str, gemeente: str | None = None) -> list[TavilyQuery]:
    """One query per family, derived from the source register's first Dutch discovery query.

    The generic word 'netbeheerder' is replaced by the operator's name; the Dutch direction word and the
    municipality are appended so the search lands on the direction-specific statement for this area.
    """
    if direction not in DIRECTION_NL:
        raise ValueError(f"direction must be one of {sorted(DIRECTION_NL)}")
    queries = _discovery_queries()
    out: list[TavilyQuery] = []
    for family in QUERY_FAMILIES:
        templates = queries.get(family) or []
        if not templates:
            continue
        q = templates[0]
        q = q.replace("netbeheerder", dso) if "netbeheerder" in q else f"{dso} {q}"
        parts = [q, DIRECTION_NL[direction]]
        if gemeente:
            parts.append(gemeente)
        out.append(TavilyQuery(family_id=family, query=" ".join(parts)))
    return out


class TavilyClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = TAVILY_BASE_URL,
        timeout_s: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
        runs_dir: Path | None = None,
        run_id: str | None = None,
    ):
        if not api_key:
            raise ValueError("Tavily API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_s
        self._transport = transport
        self._runs_dir = runs_dir
        self.run_id = run_id
        self.calls = 0
        self.ledger_ids: list[str] = []

    async def _post(
        self, path: str, body: dict[str, Any], *, kind: LedgerKind, stage: str, note: dict[str, Any]
    ) -> Any:
        self.calls += 1
        started = time.perf_counter()
        status: LedgerStatus = "ok"
        error: str | None = None
        payload: Any = None
        try:
            async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                resp = await client.post(
                    f"{self._base_url}{path}",
                    json=body,
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                )
            if resp.status_code != 200:
                detail = resp.text[:300]
                raise TavilyError(f"Tavily {path} returned HTTP {resp.status_code}: {detail}", resp.status_code)
            payload = resp.json()
            if not isinstance(payload, dict):
                raise TavilyError(f"Tavily {path} returned a non-object JSON body")
            return payload
        except TavilyError as exc:
            status, error = "error", str(exc)
            raise
        except (httpx.HTTPError, ValueError) as exc:
            status, error = "error", f"{type(exc).__name__}: {exc}"
            raise TavilyError(f"Tavily {path} failed: {error}") from exc
        finally:
            if isinstance(payload, dict):
                note["result_count"] = len(payload.get("results") or [])
                note["failed_count"] = len(payload.get("failed_results") or [])
                if isinstance(payload.get("usage"), dict):
                    note["credits"] = payload["usage"].get("credits")
            entry = record_telemetry(
                kind,
                stage,
                None,
                latency_ms=(time.perf_counter() - started) * 1000,
                status=status,
                run_id=self.run_id,
                error=error,
                notes=json.dumps(note, ensure_ascii=False),
                runs_dir=self._runs_dir,
            )
            self.ledger_ids.append(entry["id"])

    async def search(
        self,
        query: str,
        *,
        include_domains: list[str] | None = None,
        max_results: int = 5,
        stage: str = "s2_retrieve",
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "topic": "general",
            "country": "netherlands",
            "include_raw_content": False,
            "include_usage": True,
        }
        if include_domains:
            body["include_domains"] = include_domains
        note = {"query": query, "include_domains": include_domains}
        result: dict[str, Any] = await self._post("/search", body, kind="tavily.search", stage=stage, note=note)
        return result

    async def extract(self, urls: list[str], *, stage: str = "s2_retrieve") -> dict[str, Any]:
        body = {"urls": urls, "extract_depth": "basic", "format": "text", "include_usage": True}
        result: dict[str, Any] = await self._post(
            "/extract", body, kind="tavily.extract", stage=stage, note={"urls": urls}
        )
        return result

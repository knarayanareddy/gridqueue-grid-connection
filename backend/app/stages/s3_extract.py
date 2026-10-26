"""S3 extract_positions (+ candidate options) — Nemotron Ultra on Token Factory (SPEC §3 S3/S4).

The model PROPOSES; the gate DISPOSES (docs/AGENT-DELEGATION-PROTOCOL.md §4). Everything the model returns
is a hypothesis: each quote, date, kW figure, binding statement and application route is re-checked against
the fetched document text by ``DeterministicGate`` in S5, and dropped if it doesn't hold.

Token Factory usage follows https://docs.tokenfactory.nebius.com/ai-models-inference/json (checked
2026-10-26): OpenAI-compatible client, ``base_url=https://api.tokenfactory.nebius.com/v1/``,
``response_format={"type": "json_schema", "json_schema": {"name": ..., "schema": ...}}``.

Deviation from SPEC §5: the ticket asks Ultra to extract both the position and the options in one call, so
Super is not used here (see reports/C-T14-T19.TASK_REPORT.md).
"""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

import jsonschema  # type: ignore[import-untyped]  # runtime dep; stubs would be a new dev dependency

from app.config import Settings
from app.stages.base import StageResult
from app.stages.s2_retrieve import FIXTURE_DIR, load_fixture_index
from app.tf.ledger import LedgerStatus, record_telemetry

MAX_CHARS_PER_DOCUMENT = 40_000  # TODO_VERIFY(C-T02: size against Ultra's context window from the catalog)

OPTION_KINDS = [
    "non_firm_connection",
    "flex_transport_agreement",
    "congestion_management_participation",
    "time_shift_profile",
    "battery_with_export_limit",
    "collective_arrangement",
    "queue_registration",
    "reduce_requested_capacity",
    "phase_installation",
    "energy_hub_participation",
    "other",
]

EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["claims", "options"],
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "document_id",
                    "verbatim_quote",
                    "congestion_registered",
                    "queue_status",
                    "indicative_earliest_date",
                    "binding",
                    "binding_evidence_quote",
                    "available_capacity_kw",
                    "capacity_basis_quote",
                    "publication_date",
                    "publication_date_quote",
                    "confidence",
                ],
                "properties": {
                    "document_id": {"type": "string"},
                    "verbatim_quote": {"type": "string"},
                    "page_or_row": {"type": ["string", "null"]},
                    "congestion_registered": {"enum": [True, False, "unknown"]},
                    "queue_status": {"enum": ["OPEN", "CLOSED", "WAITLIST", "CONDITIONAL", "UNKNOWN"]},
                    "indicative_earliest_date": {"type": ["string", "null"]},
                    "binding": {"enum": ["binding", "non_binding", "unknown"]},
                    "binding_evidence_quote": {"type": ["string", "null"]},
                    "available_capacity_kw": {"type": ["number", "null"]},
                    "capacity_basis_quote": {"type": ["string", "null"]},
                    "publication_date": {"type": ["string", "null"]},
                    "publication_date_quote": {"type": ["string", "null"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["kind", "document_id", "route_quote", "estimated_kw_enabled", "kw_quote", "confidence"],
                "properties": {
                    "kind": {"enum": OPTION_KINDS},
                    "document_id": {"type": "string"},
                    "route_quote": {"type": "string"},
                    "estimated_kw_enabled": {"type": ["number", "null"]},
                    "kw_quote": {"type": ["string", "null"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    },
}

_VALIDATOR = jsonschema.Draft202012Validator(EXTRACTION_SCHEMA)

SYSTEM_PROMPT = """You extract grid-capacity statements from Dutch grid-operator documents for ONE direction.
Rules — follow all of them:
1. Every quote field must be copied EXACTLY, character for character, from the document text, in the original
   Dutch. Never translate, paraphrase, shorten with "..." or merge sentences. A quote that is not in the
   document will be rejected by code.
2. Only report statements about the requested direction ("feed_in" = teruglevering / productie,
   "consumption" = afname). If a document does not distinguish the directions, report nothing from it.
3. indicative_earliest_date: an ISO-like partial date ("2028", "2028-Q3", "2028-H2", "2028-07",
   "2028-07-14") ONLY if that date is written in verbatim_quote. Otherwise null. Never estimate a date.
4. binding: "non_binding" or "binding" only if the document itself says so, with its own words copied into
   binding_evidence_quote. Words like indicatief, prognose, niet-bindend, onder voorbehoud, kan wijzigen mean
   non_binding. If the document does not say, use "unknown" and null.
5. available_capacity_kw only if a kW/MW figure for this direction is written in capacity_basis_quote.
6. publication_date (YYYY-MM-DD) only if the document states it; copy the sentence into publication_date_quote.
7. options: only routes the document itself describes (non-firm connection, flex contract, congestion
   management, ...). route_quote is the document's own sentence describing how to apply. Do not invent routes.
8. If the documents contain no statement for this direction, return {"claims": [], "options": []}.
Return JSON matching the provided schema and nothing else."""


def build_user_prompt(ctx: Any) -> str:
    parts = [
        f"Requested direction: {ctx.direction}",
        f"Requested capacity: {ctx.power_kw:g} kW",
        f"Grid operator: {ctx.location['dso']}; municipality: {ctx.location.get('gemeente') or 'unknown'}",
        "",
    ]
    for doc in ctx.documents:
        text = ctx.doc_texts[doc["document_id"]][:MAX_CHARS_PER_DOCUMENT]
        parts += [f"=== document_id: {doc['document_id']} | {doc['title']} | {doc['url']}", text, ""]
    return "\n".join(parts)


class Extractor(Protocol):
    kind: str  # "live_model" | "replay"
    model: str | None

    async def extract(self, ctx: Any) -> Any: ...


class ReplayExtractor:
    """Returns the recorded SYNTHETIC model output for the fixture scenario. No network, no model call."""

    kind = "replay"
    model = None

    async def extract(self, ctx: Any) -> Any:
        index = load_fixture_index()
        scenario = index["scenarios"].get(ctx.location["dso"], {})
        rel = (scenario.get("extractions") or {}).get(ctx.direction)
        if not rel:
            return {"claims": [], "options": []}
        recorded = json.loads((FIXTURE_DIR / rel).read_text(encoding="utf-8"))
        if recorded.get("_synthetic") is not True:
            raise ValueError(f'{rel} must declare "_synthetic": true')
        # Recorded outputs refer to documents by fixture key; map them to the hashed document ids.
        by_key = {d["fixture_key"]: d["text_file"] for d in scenario.get("documents", [])}
        doc_ids = {d["local_path"]: d["document_id"] for d in ctx.documents}

        def resolve(key: str) -> str:
            return doc_ids.get(f"data/fixtures/synthetic/{by_key.get(key, '')}", key)

        output = {k: v for k, v in recorded.items() if not k.startswith("_")}
        for item in output.get("claims", []) + output.get("options", []):
            item["document_id"] = resolve(item["document_id"])
        return output


class LiveExtractor:
    """Nemotron Ultra via Token Factory. Writes one ledger line per call."""

    kind = "live_model"

    def __init__(self, settings: Settings, client: Any = None):
        self.model = settings.model_ultra  # TODO_VERIFY(C-T02: exact model id in the authenticated catalog)
        if client is None:
            from openai import AsyncOpenAI

            assert settings.nebius_api_key is not None
            client = AsyncOpenAI(base_url=settings.nebius_base_url, api_key=settings.nebius_api_key.get_secret_value())
        self._client = client

    async def extract(self, ctx: Any) -> Any:
        started = time.perf_counter()
        status: LedgerStatus = "ok"
        error: str | None = None
        content: str | None = None
        usage: Any = None
        try:
            completion = await self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(ctx)},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "gridqueue_extraction", "schema": EXTRACTION_SCHEMA},
                },
            )
            usage = getattr(completion, "usage", None)
            choice = completion.choices[0]
            content = choice.message.content
            if choice.finish_reason == "length":
                status = "truncated"
            return json.loads(content or "")
        except json.JSONDecodeError as exc:
            status, error = "schema_violation", f"invalid JSON: {exc}"
            return None
        except Exception as exc:  # network / API errors must not crash the answer
            status, error = "error", f"{type(exc).__name__}: {exc}"
            return None
        finally:
            prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            details = getattr(usage, "prompt_tokens_details", None)
            cached = int(getattr(details, "cached_tokens", 0) or 0)
            ctx.tokens["prompt"] += prompt
            ctx.tokens["completion"] += completion_tokens
            ctx.tokens["cached"] += min(cached, prompt)
            entry = record_telemetry(
                "chat.completions",
                "s3_extract",
                self.model,
                prompt,
                completion_tokens,
                min(cached, prompt),
                latency_ms=(time.perf_counter() - started) * 1000,
                status=status,
                run_id=ctx.run_id,
                response={"finish_reason": status, "valid_json": content is not None and error is None},
                error=error,
                notes="cost_usd not computed: Token Factory prices not configured (TODO_VERIFY)",
                runs_dir=ctx.runs_dir,
            )
            ctx.llm_ledger_id = entry["id"]


class ExtractPositions:
    name = "s3_extract"

    async def run(self, ctx: Any) -> StageResult:
        started = time.perf_counter()
        extractor: Extractor = ctx.extractor
        ctx.retrieval["extraction"] = "not_run"
        ctx.retrieval["model"] = None
        ctx.extraction = {"claims": [], "options": []}
        errors: list[str] = []
        try:
            if ctx.documents:
                ctx.retrieval["extraction"] = extractor.kind
                ctx.retrieval["model"] = extractor.model
                ctx.llm_model = extractor.model
                raw = await extractor.extract(ctx)
                errors = [e.message for e in _VALIDATOR.iter_errors(raw)] if raw is not None else ["no output"]
                if not errors:
                    ctx.extraction = raw
        finally:
            ctx.timings_ms[self.name] = int((time.perf_counter() - started) * 1000)
        return StageResult(
            stage=self.name,
            ok=not errors,
            data={"n_claims": len(ctx.extraction["claims"]), "n_options": len(ctx.extraction["options"])},
            abstain=bool(errors),
            abstain_reason="extraction_invalid" if errors else None,
            ledger_ids=[ctx.llm_ledger_id] if ctx.llm_ledger_id else [],
        )

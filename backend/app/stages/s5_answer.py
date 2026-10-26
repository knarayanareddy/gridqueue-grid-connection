"""S5 gate + answer assembly — pure Python, NO LLM (SPEC §3 S5, §6).

Every value the model proposed is re-checked against the fetched document text with ``DeterministicGate``:

  claim quote          FAIL/UNDETERMINED → claim rejected (quote_not_found_in_document)
  document split       no feed-in/afname distinction → claim rejected (direction_conflated)
  indicative date      not stated in the quote, or no verified publication date → date dropped
                       (date_without_document, GQ-DATE-01)
  publication date     its quote must be in the document and state the date → else null
  binding              its quote must be in the document → else "unknown" (binding_not_stated);
                       an explicit non-binding marker in a verified quote forces "non_binding" (lexicon §3)
  kW                   must be stated in a verified capacity_basis_quote → else dropped (kw_without_quote)
  option route         route_quote must be in the document and name the option's kind → else option dropped
                       (option_without_route / option_cites_missing_document)

No surviving claim for the direction → verdict NO_OFFICIAL_POSITION_FOUND, with the Dutch phone script.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from typing import Any

from app.gate.gate import DeterministicGate, GateResult, normalise
from app.stages.base import StageResult

DIRECTION_LABEL = {"feed_in": "Feed-in (teruglevering)", "consumption": "Consumption (afname)"}

KIND_LABEL = {
    "non_firm_connection": "Non-firm connection (niet-firm transportrecht)",
    "flex_transport_agreement": "Flex contract (transportovereenkomst op maat)",
    "congestion_management_participation": "Congestion management participation",
    "time_shift_profile": "Time-shifted use",
    "battery_with_export_limit": "Battery with export limit",
    "collective_arrangement": "Collective transport agreement",
    "queue_registration": "Register on the waiting list",
    "reduce_requested_capacity": "Reduce requested capacity",
    "phase_installation": "Phase the installation",
    "energy_hub_participation": "Energy hub",
    "other": "Other route",
}
KIND_ORDER = list(KIND_LABEL)

# An option's route quote must actually name the route (data/domain-lexicon.md §1). Kinds without a lexicon
# term are not keyword-checked.
KIND_TERMS: dict[str, tuple[str, ...]] = {
    "non_firm_connection": ("niet-firm", "niet firm", "non-firm", "curtailment", "afregel", "afschakelbaar"),
    "flex_transport_agreement": ("flexcontract", "op maat", "curtailment", "afregel", "afschakelbaar"),
    "congestion_management_participation": ("congestiemanagement",),
    "collective_arrangement": ("groepstransportovereenkomst",),
    "energy_hub_participation": ("energiehub",),
    "queue_registration": ("wachtlijst",),
}

# data/domain-lexicon.md §3
NON_BINDING_MARKERS = (
    "indicatief",
    "naar verwachting",
    "prognose",
    "raming",
    "niet-bindend",
    "niet bindend",
    "onder voorbehoud",
    "kan wijzigen",
    "streefdatum",
)
EXPLICIT_NON_BINDING = ("niet-bindend", "niet bindend", "onder voorbehoud", "kan wijzigen")

DISCLAIMER = (
    "Not connection advice. GridQueue reports what grid operators have published, at the retrieval time shown; "
    "it does not predict capacity. Indicative dates are the operator's own and may be non-binding. "
    "Postcode-to-operator mapping is not yet verified against operator service-area lists."
)
SYNTHETIC_NOTICE = " DEMO MODE: the documents behind this answer are SYNTHETIC fixtures, not official publications."

PHONE_SCRIPTS = {
    # data/domain-lexicon.md §5. Not yet verified by a native speaker (C-T05).
    "feed_in": (
        "Goedendag, ik wil voor postcode {postcode} een zakelijke aansluiting aanvragen met {kw} kW "
        "teruglevercapaciteit (zonnepanelen). Is er voor dit gebied firma transportvermogen beschikbaar richting "
        "teruglevering, of komt mijn aanvraag op de wachtlijst? En als er congestie is: is een niet-firma "
        "aansluiting met een curtailmentregeling of een flexcontract mogelijk, en wat is daarvoor de aanvraagroute?",
        "Hello, for postcode {postcode} I want to apply for a business connection with {kw} kW of feed-in capacity "
        "(solar panels). Is firm transport capacity available for feed-in in this area, or will my application go "
        "on the waiting list? And if there is congestion: is a non-firm connection with a curtailment arrangement "
        "or a flex contract possible, and what is the application route?",
    ),
    "consumption": (
        "Goedendag, voor postcode {postcode} wil ik {kw} kW extra afnamecapaciteit aanvragen (laadpalen en "
        "warmtepomp). Is er afnamecapaciteit beschikbaar, of geldt er congestie voor afname in dit gebied? Zo ja, "
        "is deelname aan congestiemanagement of een afschakelbare regeling een optie?",
        "Hello, for postcode {postcode} I want to apply for {kw} kW of additional consumption capacity (chargers "
        "and heat pump). Is consumption capacity available, or is consumption congested in this area? If so, is "
        "participating in congestion management or an interruptible arrangement an option?",
    ),
}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _hash_id(prefix: str, payload: Any) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return f"{prefix}_{digest[:12]}"


def _date_granularity(date: str | None) -> str:
    if not date:
        return "none"
    if "/" in date:
        return "range"
    if re.fullmatch(r"\d{4}", date):
        return "year"
    if "-Q" in date:
        return "quarter"
    if "-H" in date:
        return "range"
    if re.fullmatch(r"\d{4}-\d{2}", date):
        return "month"
    return "exact"


def _markers(*texts: str | None) -> list[str]:
    low = " ".join(normalise(t).lower() for t in texts if t)
    return [m for m in NON_BINDING_MARKERS if m in low]


def phone_script(location: dict[str, Any], direction: str, power_kw: float) -> dict[str, Any]:
    nl, en = PHONE_SCRIPTS[direction]
    postcode = location.get("postcode") or location.get("postcode4") or "<postcode>"
    kw = f"{power_kw:g}"
    return {
        "dso": location.get("dso") or "your grid operator (netbeheerder) — see your connection documents",
        "direction": direction,
        "asker_role": "owner",
        "text_nl": nl.format(postcode=postcode, kw=kw),
        "text_en": en.format(postcode=postcode, kw=kw),
        "rule_id": "GQ-NOPOSITION-01",
        "contact_route": None,  # TODO_VERIFY(C-T03: operator's published contact route)
        "native_speaker_verified_by": None,
    }


class _Gate:
    """Thin accounting wrapper so every check is counted in Answer.gate."""

    def __init__(self) -> None:
        self.run = 0
        self.passed = 0
        self.rejected: list[dict[str, Any]] = []
        self.dates_surviving = 0
        self.dates_dropped = 0

    def check(self, rule_id: str, assertion: dict[str, Any], quote: str | None, source: str | None) -> GateResult:
        self.run += 1
        result = DeterministicGate.evaluate(rule_id, assertion, quote, source)
        if result.verdict == "PASS":
            self.passed += 1
        return result

    def reject(self, claim: str, reason: str, document_id: str | None) -> None:
        self.rejected.append({"claim": claim, "reason": reason, "document_id": document_id})


def _citation(ctx: Any, doc: dict[str, Any], quote: str) -> str:
    synthetic = bool(ctx.retrieval.get("synthetic"))
    cit = {
        "id": _hash_id("cit", [doc["document_id"], quote]),
        "kind": "source_document",
        "locator": f"{doc['document_id']} {doc['url']} {doc.get('publication_date') or 'publication date unknown'}",
        "document_id": doc["document_id"],
        "quote": quote,
        "retrieved_at": doc["retrieved_at"],
        "sha256": doc["sha256"],
        "ttl_seconds": None,
        "trust": "web" if synthetic else "primary",
    }
    return ctx.add_citation(cit)


def _gate_claim(ctx: Any, gate: _Gate, raw: dict[str, Any]) -> dict[str, Any] | None:
    doc_id = raw["document_id"]
    doc = ctx.document(doc_id)
    quote = raw.get("verbatim_quote") or ""
    short = (quote[:80] + "…") if len(quote) > 80 else quote
    if doc is None:
        gate.reject(f"claim cites unknown document {doc_id!r}: {short}", "quote_not_found_in_document", None)
        if raw.get("indicative_earliest_date"):
            gate.dates_dropped += 1
        return None
    text = ctx.doc_texts[doc_id]

    base = gate.check("GQ-QUOTE-01", {}, quote, text)
    if base.verdict != "PASS":
        gate.reject(f"quote not in document ({base.reason}): {short}", "quote_not_found_in_document", doc_id)
        if raw.get("indicative_earliest_date"):
            gate.dates_dropped += 1
        return None
    if not doc["direction_split_available"]:
        gate.reject(f"document does not distinguish feed-in from afname: {short}", "direction_conflated", doc_id)
        if raw.get("indicative_earliest_date"):
            gate.dates_dropped += 1
        return None

    # Publication date (needed by GQ-DATE-01)
    publication_date = doc.get("publication_date")
    if publication_date is None and raw.get("publication_date"):
        r = gate.check("GQ-DATE-01", {"date": raw["publication_date"]}, raw.get("publication_date_quote"), text)
        if r.verdict == "PASS" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw["publication_date"]):
            publication_date = raw["publication_date"]
            doc["publication_date"] = publication_date

    # Indicative date
    date = raw.get("indicative_earliest_date")
    if date:
        r = gate.check("GQ-DATE-01", {"indicative_earliest_date": date}, quote, text)
        if r.verdict != "PASS":
            gate.reject(f"date {date!r} not stated in the quoted text ({r.reason})", "date_without_document", doc_id)
            gate.dates_dropped += 1
            date = None
        elif publication_date is None:
            gate.reject(
                f"date {date!r} dropped: document publication date not verified", "date_without_document", doc_id
            )
            gate.dates_dropped += 1
            date = None
        else:
            gate.dates_surviving += 1

    # Binding status (GQ-BINDING-01)
    binding = raw.get("binding", "unknown")
    binding_quote = raw.get("binding_evidence_quote")
    if binding in ("binding", "non_binding"):
        r = gate.check("GQ-BINDING-01", {}, binding_quote, text)
        if r.verdict != "PASS":
            gate.reject(
                f"binding={binding!r} not supported by a verbatim quote ({r.reason})", "binding_not_stated", doc_id
            )
            binding, binding_quote = "unknown", None
    else:
        binding, binding_quote = "unknown", None
    markers = _markers(quote, binding_quote)
    explicit = [m for m in EXPLICIT_NON_BINDING if m in markers]
    if explicit and binding != "non_binding":
        binding = "non_binding"
        binding_quote = binding_quote if binding_quote and _markers(binding_quote) else quote

    # Capacity (GQ-KW-01)
    kw = raw.get("available_capacity_kw")
    kw_quote = raw.get("capacity_basis_quote")
    if kw is not None:
        r = gate.check("GQ-KW-01", {"available_capacity_kw": kw}, kw_quote, text)
        if r.verdict != "PASS":
            gate.reject(f"{kw:g} kW not stated in a verbatim quote ({r.reason})", "kw_without_quote", doc_id)
            kw, kw_quote = None, None
    else:
        kw_quote = None

    claim = {
        "direction": ctx.direction,
        "congestion_registered": raw["congestion_registered"],
        "queue_status": raw["queue_status"],
        "indicative_earliest_date": date,
        "date_granularity": _date_granularity(date),
        "binding": binding,
        "binding_evidence_quote": binding_quote,
        "non_binding_markers_found": markers,
        "available_capacity_kw": kw,
        "capacity_basis_quote": kw_quote,
        "document_id": doc_id,
        "verbatim_quote": quote,
        "quote_language": "nl",
        "our_translation": None,
        "page_or_row": raw.get("page_or_row"),
        "publication_date": publication_date,
        "confidence": float(raw["confidence"]),
    }
    claim["id"] = _hash_id("pc", claim)
    claim["dso"] = ctx.location["dso"]
    claim["congestion_area_id"] = None
    claim["citation_id"] = _citation(ctx, doc, quote)
    claim["downgrade_to_verify"] = False
    claim["ledger_id"] = ctx.llm_ledger_id
    return claim


def _gate_option(ctx: Any, gate: _Gate, raw: dict[str, Any]) -> dict[str, Any] | None:
    kind = raw["kind"]
    doc_id = raw["document_id"]
    doc = ctx.document(doc_id)
    label = KIND_LABEL[kind]
    if doc is None:
        gate.reject(f"option {label!r} cites unknown document {doc_id!r}", "option_cites_missing_document", None)
        return None
    text = ctx.doc_texts[doc_id]
    route = raw.get("route_quote") or ""
    r = gate.check("GQ-ROUTE-01", {}, route, text)
    if r.verdict != "PASS":
        gate.reject(f"option {label!r}: route quote not in document ({r.reason})", "option_without_route", doc_id)
        return None
    terms = KIND_TERMS.get(kind)
    if terms and not any(t in normalise(route).lower() for t in terms):
        gate.reject(f"option {label!r}: route quote does not name this route", "option_without_route", doc_id)
        return None

    kw = raw.get("estimated_kw_enabled")
    if kw is not None:
        rk = gate.check("GQ-KW-01", {"kw": kw}, raw.get("kw_quote"), text)
        if rk.verdict != "PASS":
            gate.reject(f"option {label!r}: {kw:g} kW not stated in a verbatim quote", "kw_without_quote", doc_id)
            kw = None

    option = {
        "kind": kind,
        "title": label,
        "estimated_kw_enabled": kw,
        "estimate_basis": "document_quote",
        "assumptions": [],
        "prerequisites": [],
        "application_route": route,
        "who_to_contact": ctx.location["dso"],
        "contact_detail": None,
        "expected_lead_time": None,
        "evidence_document_ids": [doc_id],
        "model_estimate_flag": False,
        "confidence": float(raw["confidence"]),
    }
    option["id"] = _hash_id("opt", option)
    option["citation_ids"] = [_citation(ctx, doc, route)]
    return option


def classify(claim: dict[str, Any], power_kw: float) -> str:
    registered, queue, kw = claim["congestion_registered"], claim["queue_status"], claim["available_capacity_kw"]
    if registered is False:
        return "PARTIAL_CAPACITY" if kw is not None and kw < power_kw else "CAPACITY_AVAILABLE"
    return {"WAITLIST": "WAITLIST_ONLY", "CONDITIONAL": "NON_FIRM_ONLY", "CLOSED": "NO_FIRM_CAPACITY"}.get(
        queue, "PARTIAL_CAPACITY" if queue == "OPEN" and kw is not None and kw < power_kw else "UNDETERMINED"
    )


def headline(verdict: str, direction: str, claim: dict[str, Any] | None, power_kw: float) -> str:
    d = DIRECTION_LABEL[direction]
    kw = claim.get("available_capacity_kw") if claim else None
    kw_txt = f" {kw:g} kW is stated as available." if kw is not None else ""
    return {
        "CAPACITY_AVAILABLE": f"{d}: no congestion registered for this area in the retrieved document.{kw_txt}",
        "PARTIAL_CAPACITY": f"{d}: {kw:g} kW stated as available — less than the {power_kw:g} kW requested."
        if kw is not None
        else f"{d}: capacity is open, but the amount is not stated.",
        "WAITLIST_ONLY": f"{d}: congestion registered — new requests go on the waiting list.",
        "NON_FIRM_ONLY": f"{d}: congestion registered — capacity only on non-firm or conditional terms.",
        "NO_FIRM_CAPACITY": f"{d}: congestion registered — no firm capacity is being offered.",
        "UNDETERMINED": f"{d}: congestion registered, but the document does not state what you can get.",
        "NO_OFFICIAL_POSITION_FOUND": f"{d}: we could not establish an official position for this location and "
        "direction. We will not guess.",
    }[verdict]


def _no_position(ctx: Any, script: dict[str, Any]) -> list[dict[str, Any]]:
    loc = ctx.location
    if not loc["resolved"]:
        reason = "unmapped_postcode"
        message = (
            "This postcode is not in GridQueue's postcode-to-operator table yet, so we cannot tell which grid "
            "operator to check."
            if loc["abstain_reason"] == "unmapped_postcode"
            else "The postcode could not be read. Use a Dutch postcode such as 5612 or 5612 AB."
        )
        return [
            {
                "reason": reason,
                "scope": "answer",
                "message": message,
                "fix_instruction": script["text_nl"],
                "document_id": None,
                "observed_values": {"abstain_reason": loc["abstain_reason"]},
            }
        ]
    out = [a for a in ctx.abstentions]
    if not any(a["reason"] == "tavily_unavailable" for a in out):
        out.append(
            {
                "reason": "no_position_found",
                "scope": "direction",
                "message": (
                    f"No current published statement from {loc['dso']} for this area and direction survived "
                    "verification. We will not guess a date."
                ),
                "fix_instruction": script["text_nl"],
                "document_id": None,
                "observed_values": {"documents_retrieved": len(ctx.documents)},
            }
        )
    for a in out:
        a["fix_instruction"] = script["text_nl"]
    return out


class AssembleAnswer:
    name = "s5_answer"

    def build(self, ctx: Any, total_started: float) -> dict[str, Any]:
        started = time.perf_counter()
        gate = _Gate()
        loc = ctx.location
        extraction = ctx.extraction or {"claims": [], "options": []}

        claims: list[dict[str, Any]] = []
        options: list[dict[str, Any]] = []
        if loc["resolved"]:
            for raw in extraction["claims"]:
                c = _gate_claim(ctx, gate, raw)
                if c is not None:
                    claims.append(c)
            for raw in extraction["options"]:
                o = _gate_option(ctx, gate, raw)
                if o is not None and all(o["id"] != x["id"] for x in options):
                    options.append(o)

        # GQ-NOPOSITION-01: claims whose registration status is unknown don't establish a position.
        positioned = [c for c in claims if c["congestion_registered"] != "unknown"]
        best = max(
            positioned,
            key=lambda c: (
                c["indicative_earliest_date"] is not None,
                c["available_capacity_kw"] is not None,
                c["confidence"],
                c["id"],
            ),
            default=None,
        )

        def rank_key(o: dict[str, Any]) -> tuple[Any, ...]:
            kw = o["estimated_kw_enabled"]
            return (0 if kw is not None and kw >= ctx.power_kw else 1, -(kw or 0), KIND_ORDER.index(o["kind"]), o["id"])

        options.sort(key=rank_key)
        for i, o in enumerate(options, start=1):
            o["rank"] = i
            kw = o["estimated_kw_enabled"]
            o["rank_rationale"] = (
                f"Document states {kw:g} kW for this route."
                if kw is not None
                else "Route quoted from the operator's document; capacity not stated."
            )

        script = phone_script(loc, ctx.direction, ctx.power_kw)
        if best is None:
            verdict = "NO_OFFICIAL_POSITION_FOUND"
            abstentions = _no_position(ctx, script)
        else:
            verdict = classify(best, ctx.power_kw)
            abstentions = []

        if best and best["indicative_earliest_date"]:
            chip = {"binding": "BINDING", "non_binding": "NON_BINDING"}.get(best["binding"], "UNKNOWN")
        else:
            chip = "NOT_APPLICABLE"

        direction_result = {
            "direction": ctx.direction,
            "verdict": verdict,
            "headline": headline(verdict, ctx.direction, best, ctx.power_kw),
            "position_claim": best,
            "binding_chip": chip,
            "available_capacity_kw": best["available_capacity_kw"] if best else None,
            "indicative_earliest_date": best["indicative_earliest_date"] if best else None,
            "revision_history": [],
            "gate_report": None,
            "abstentions": abstentions,
            "phone_script": script,
            "options_for_this_direction": [o["id"] for o in options],
        }

        if options:
            primary = (
                f"Top option: {options[0]['title']} — the application route is quoted from {loc['dso']}'s document."
            )
        elif loc["resolved"]:
            primary = f"Call {loc['dso']} and ask the question below; it is written in their vocabulary."
        else:
            primary = "Find your grid operator on your connection documents, then ask the question below."

        hash_payload = {
            "location": {k: v for k, v in loc.items() if k != "resolved_at"},
            "per_direction": [direction_result],
            "options": options,
            "rejected": gate.rejected,
        }
        determinism_hash = hashlib.sha256(
            json.dumps(hash_payload, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()

        doc_hashes = sorted(d["sha256"] for d in ctx.documents)
        snapshot = hashlib.sha256("".join(doc_hashes).encode()).hexdigest()[:16]
        cited = sorted({c["document_id"] for c in claims} | {d for o in options for d in o["evidence_document_ids"]})
        ctx.timings_ms[self.name] = int((time.perf_counter() - started) * 1000)
        ctx.timings_ms["total"] = int((time.perf_counter() - total_started) * 1000)

        request = {
            "id": f"req_{ctx.run_id}",
            "address_or_postcode": ctx.postcode,
            "postcode4": loc["postcode4"],
            "country": "NL",
            "requested": [{"kind": "other", "kw": ctx.power_kw, "direction": ctx.direction}],
            "asker_role": "other",
            "connection_scale": "unknown",
        }
        return {
            "answer_id": f"ans_{ctx.run_id}",
            "request": request,
            "location": loc,
            "per_direction": [direction_result],
            "load_profile": None,
            "options_ranked": options,
            "action_first": {"primary": primary, "phone_script": script, "copy_targets": [script["text_nl"]]},
            "documents_cited": cited,
            "artifact": None,
            "gate": {
                "checks_run": gate.run,
                "checks_passed": gate.passed,
                "rejected_claims": gate.rejected,
                "abstentions": abstentions,
                "dates_surviving": gate.dates_surviving,
                "dates_dropped": gate.dates_dropped,
                "determinism_hash": determinism_hash,
                "llm_calls_in_gate": 0,
            },
            "corpus_snapshot_id": f"{ctx.mode}:{snapshot}" if doc_hashes else f"{ctx.mode}:empty",
            "currency_check": None,
            "cost": {
                "total_usd": 0.0,
                "by_model": {},
                "text_tokens": ctx.tokens["prompt"] + ctx.tokens["completion"],
                "cached_tokens": ctx.tokens["cached"],
                "tavily_calls": ctx.retrieval.get("tavily_calls", 0),
                "cache_hit": False,
                "pricing_note": "total_usd is not a measurement: Token Factory / Tavily prices are not configured "
                "(TODO_VERIFY).",
            },
            "timings_ms": dict(ctx.timings_ms),
            "generated_at": _now_iso(),
            "disclaimer": DISCLAIMER + (SYNTHETIC_NOTICE if ctx.retrieval.get("synthetic") else ""),
        }

    async def run(self, ctx: Any) -> StageResult:  # protocol conformance; the pipeline calls build()
        answer = self.build(ctx, time.perf_counter())
        return StageResult(stage=self.name, ok=True, data=answer)

"""S1 resolve_location — deterministic postcode → DSO lookup. NO LLM, NO NETWORK (SPEC §3, §4.2).

A wrong DSO silently invalidates every downstream claim, so this stage only resolves postcodes that are in
the static table below, and abstains for everything else.

Source of the table: ticket C-T14-T19 SPEC §1, which names exactly three ranges. They have NOT yet been
verified against each operator's published service-area list — that is ticket C-T04.
TODO_VERIFY(C-T04: confirm each range against the DSO's own service-area publication and an open
postcode → gemeente dataset; add provincie; extend coverage).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.stages.base import StageResult

MAPPING_SOURCE = "ticket C-T14-T19 SPEC §1"
MAPPING_RECORDED_AT = "2026-10-26T00:00:00Z"


@dataclass(frozen=True)
class DsoRange:
    low: int
    high: int  # inclusive
    dso: str
    gemeente: str


DSO_RANGES: tuple[DsoRange, ...] = (
    DsoRange(5600, 5658, "Enexis", "Eindhoven"),
    DsoRange(1000, 1099, "Liander", "Amsterdam"),
    DsoRange(3000, 3089, "Stedin", "Rotterdam"),
)

# Dutch postcode: 4 digits (no leading zero), optionally followed by 2 letters.
_POSTCODE = re.compile(r"^\s*([1-9][0-9]{3})\s?([A-Za-z]{2})?\s*$")


def _citation_id(dso: str) -> str:
    return f"cit_geo_{dso.lower()}"


def mapping_citation(dso: str) -> dict[str, Any]:
    """Citation entry backing a DSO assignment. Honest about its provenance: a project-authored table."""
    return {
        "id": _citation_id(dso),
        "kind": "user_input",
        "locator": (
            f"backend/app/stages/s1_resolve_location.py DSO_RANGES ({dso}); source: {MAPPING_SOURCE}. "
            "UNVERIFIED against the operator's service-area publication (ticket C-T04)."
        ),
        "document_id": None,
        "quote": None,
        "retrieved_at": MAPPING_RECORDED_AT,
        "sha256": None,
        "ttl_seconds": None,
        # Lowest available tier. The Citation schema has no 'unverified' tier — see docs/DISCREPANCIES.md.
        "trust": "web",
    }


def resolve(postcode: str, *, now: datetime | None = None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Return (LocationResolution, citation-or-None). Pure function."""
    resolved_at = (now or datetime.now(UTC)).isoformat(timespec="seconds").replace("+00:00", "Z")
    base: dict[str, Any] = {
        "postcode": None,
        "postcode4": None,
        "gemeente": None,
        "provincie": None,
        "dso": None,
        "dso_evidence_citation": None,
        "tso_region": None,
        "congestion_area_ids": [],
        "resolution_method": "static_table",
        "resolved": False,
        "resolved_at": resolved_at,
        "abstain_reason": None,
    }

    m = _POSTCODE.match(postcode or "")
    if not m:
        return {**base, "abstain_reason": "malformed_postcode"}, None

    pc4 = m.group(1)
    letters = (m.group(2) or "").upper()
    base["postcode4"] = pc4
    base["postcode"] = f"{pc4} {letters}" if letters else pc4

    n = int(pc4)
    for r in DSO_RANGES:
        if r.low <= n <= r.high:
            cit = mapping_citation(r.dso)
            return {
                **base,
                "gemeente": r.gemeente,
                "dso": r.dso,
                "dso_evidence_citation": cit["id"],
                "resolved": True,
            }, cit

    return {**base, "abstain_reason": "unmapped_postcode"}, None


class ResolveLocation:
    name = "s1_resolve_location"

    async def run(self, ctx: Any) -> StageResult:
        location, citation = resolve(ctx.postcode)
        ctx.location = location
        if citation:
            ctx.add_citation(citation)
        return StageResult(
            stage=self.name,
            ok=location["resolved"],
            data=location,
            citation_ids=[citation["id"]] if citation else [],
            abstain=not location["resolved"],
            abstain_reason=location["abstain_reason"],
        )

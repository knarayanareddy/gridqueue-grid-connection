"""S6 application pack — built and verified OFFLINE (tickets C-T21 / C-T22).

Designed to be the guest command of a Token Factory Sandbox operation spawned with the guest network
disabled (REST spawn body ``{"networking": {"enabled": false}}``; docs: sandboxes/guides/
configure-networking-and-secrets, checked 2026-10-26). It therefore:

* imports only the standard library and ``app.gate.gate`` (itself stdlib-only) — no HTTP client, no model SDK;
* reads everything it needs from one JSON *bundle* (the ``QueryResponse`` plus the exact text of every retrieved
  document), so nothing has to be looked up;
* can assert the network boundary the way the Sandboxes docs recommend: ``/sys/class/net`` must contain no
  interface other than ``lo`` (``--require-network-off``).

Verification, before a single byte is rendered:

1. every document's text must hash (SHA-256 of its exact UTF-8 bytes) to the ``sha256`` recorded at retrieval;
2. a citation is *verified* only if its document verified, its ``sha256`` equals that document's, and its quote
   passes the deterministic gate against the document text. Only verified citations go into the pack;
3. every asserted value — indicative date, available kW, binding statement, option route, option kW — must be
   backed by a verified citation / hash-verified document whose quote STATES that value (``DeterministicGate``).

Any failure in (3) withholds the pack (``PackVerificationError``): the pack can only cite documents we actually
hold, byte for byte. The rendered bytes contain no timestamps or environment details, so the same bundle gives
the same SHA-256 locally and inside a Sandbox.

Usage (inside the Sandbox, or locally):
    python -m app.sandbox.pack --bundle bundle.json --out pack.md [--manifest manifest.json] [--require-network-off]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.gate.gate import DeterministicGate, normalise

PACK_VERSION = "gq-pack-v1"
BUNDLE_VERSION = 1
SYS_CLASS_NET = Path("/sys/class/net")

VERDICT_LABEL = {
    "CAPACITY_AVAILABLE": "Capacity available",
    "PARTIAL_CAPACITY": "Partial capacity",
    "WAITLIST_ONLY": "Waiting list only",
    "NON_FIRM_ONLY": "Non-firm only",
    "NO_FIRM_CAPACITY": "No firm capacity",
    "UNDETERMINED": "Undetermined",
    "NO_OFFICIAL_POSITION_FOUND": "No official position found",
}
BINDING_LABEL = {
    "BINDING": "Binding",
    "NON_BINDING": "Non-binding forecast",
    "UNKNOWN": "Binding status not stated",
    "NOT_APPLICABLE": "No date published",
}
DIRECTION_LABEL = {"feed_in": "feed-in (teruglevering)", "consumption": "consumption (afname)"}
DIRECTION_NL = {"feed_in": "teruglevercapaciteit", "consumption": "afnamecapaciteit"}
# Dutch names for the application block. Not yet checked by a native speaker (C-T05).
KIND_NL = {
    "non_firm_connection": "een niet-firm transportrecht",
    "flex_transport_agreement": "een transportovereenkomst op maat (flexcontract)",
    "congestion_management_participation": "deelname aan congestiemanagement",
    "time_shift_profile": "een tijdsafhankelijk gebruiksprofiel",
    "battery_with_export_limit": "een batterij met terugleverbegrenzing",
    "collective_arrangement": "een groepstransportovereenkomst",
    "queue_registration": "registratie op de wachtlijst",
    "reduce_requested_capacity": "een lager aangevraagd vermogen",
    "phase_installation": "een gefaseerde aansluiting",
    "energy_hub_participation": "deelname aan een energiehub",
    "other": "een andere route uit uw publicatie",
}


class PackVerificationError(Exception):
    """The bundle failed offline verification. The pack is withheld."""

    def __init__(self, failures: list[dict[str, Any]]):
        super().__init__(f"{len(failures)} verification failure(s): " + "; ".join(f["reason"] for f in failures))
        self.failures = failures


class NetworkEnabledError(Exception):
    """A non-loopback network interface is present, so the network-off boundary does not hold."""


@dataclass(frozen=True)
class PackResult:
    content: bytes
    sha256: str
    manifest: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


# ------------------------------------------------------------------------------------------- network boundary


def assert_network_disabled(sys_class_net: Path = SYS_CLASS_NET) -> dict[str, Any]:
    """Prove the boundary without contacting anything: only the loopback interface may exist.

    This is the check the Sandboxes cookbook "verify-with-networking-disabled" uses.
    """
    if not sys_class_net.is_dir():
        raise NetworkEnabledError(f"{sys_class_net} is not readable, so the network boundary cannot be proven")
    interfaces = sorted(p.name for p in sys_class_net.iterdir())
    others = [i for i in interfaces if i != "lo"]
    if others:
        raise NetworkEnabledError(f"network interfaces present besides loopback: {', '.join(others)}")
    return {"checked": True, "method": "sys_class_net", "interfaces": interfaces, "network_disabled": True}


# ------------------------------------------------------------------------------------------- bundle


def make_bundle(query_response: dict[str, Any], doc_texts: dict[str, str]) -> dict[str, Any]:
    """Host side: everything the offline generator needs, in one JSON-serialisable object."""
    ids = [d["document_id"] for d in query_response["documents"]]
    return {
        "bundle_version": BUNDLE_VERSION,
        "query_response": query_response,
        "texts": {i: doc_texts[i] for i in ids if i in doc_texts},
    }


def verify_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    """Re-verify the bundle with no network. Returns a report; ``report["failures"]`` empty means OK."""
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        return {
            "documents": {},
            "citations": {},
            "values": [],
            "failures": [{"reason": "unsupported_bundle_version", "detail": str(bundle.get("bundle_version"))}],
        }
    qr = bundle["query_response"]
    texts: dict[str, str] = bundle.get("texts") or {}
    failures: list[dict[str, Any]] = []

    documents: dict[str, dict[str, Any]] = {}
    for d in qr["documents"]:
        text = texts.get(d["document_id"])
        if text is None:
            documents[d["document_id"]] = {"sha256": d["sha256"], "verified": False, "reason": "text_missing"}
        elif sha256_text(text) != d["sha256"]:
            documents[d["document_id"]] = {"sha256": d["sha256"], "verified": False, "reason": "sha256_mismatch"}
        else:
            documents[d["document_id"]] = {"sha256": d["sha256"], "verified": True, "reason": None}

    def doc_ok(doc_id: str | None) -> bool:
        return bool(doc_id) and documents.get(str(doc_id), {}).get("verified") is True

    citations: dict[str, dict[str, Any]] = {}
    for c in qr["citations"]:
        cid, doc_id = c["id"], c.get("document_id")
        if c.get("kind") != "source_document" or not doc_id:
            citations[cid] = {"verified": False, "reason": "not_source_evidence"}
        elif not doc_ok(doc_id):
            doc_reason = documents.get(doc_id, {}).get("reason", "missing")
            citations[cid] = {"verified": False, "reason": f"document_{doc_reason}"}
        elif c.get("sha256") != documents[doc_id]["sha256"]:
            citations[cid] = {"verified": False, "reason": "citation_sha256_mismatch"}
        else:
            r = DeterministicGate.evaluate("GQ-QUOTE-01", {}, c.get("quote"), texts[doc_id])
            citations[cid] = {"verified": r.verdict == "PASS", "reason": None if r.verdict == "PASS" else r.reason}
    cit_by_id = {c["id"]: c for c in qr["citations"]}

    values: list[dict[str, Any]] = []

    def record(kind: str, value: Any, doc_id: str | None, ok: bool, reason: str | None, via: str | None) -> None:
        entry = {
            "kind": kind,
            "value": value,
            "document_id": doc_id,
            "document_sha256": documents.get(str(doc_id), {}).get("sha256"),
            "via": via,
            "verified": ok,
            "reason": reason,
        }
        values.append(entry)
        if not ok:
            failures.append({"reason": f"{kind}_unverified", "detail": f"{value!r}: {reason}", "document_id": doc_id})

    def gate(rule: str, assertion: dict[str, Any], quote: str | None, doc_id: str | None) -> tuple[bool, str | None]:
        if not doc_ok(doc_id):
            return False, "document_not_hash_verified"
        r = DeterministicGate.evaluate(rule, assertion, quote, texts[str(doc_id)])
        return r.verdict == "PASS", r.reason

    answer = qr["answer"]
    for dr in answer["per_direction"]:
        claim = dr.get("position_claim")
        date, kw = dr.get("indicative_earliest_date"), dr.get("available_capacity_kw")
        if claim is None:
            if date is not None or kw is not None:
                record("date" if date else "kw", date or kw, None, False, "value_without_claim", None)
            continue
        doc_id, cid = claim["document_id"], claim["citation_id"]
        cit_ok = citations.get(cid, {}).get("verified") is True and cit_by_id[cid].get("document_id") == doc_id
        record(
            "claim_quote",
            claim["verbatim_quote"],
            doc_id,
            cit_ok,
            None if cit_ok else citations.get(cid, {}).get("reason", "citation_missing"),
            cid,
        )
        if date is not None:
            ok, why = (
                (False, "date_differs_from_claim")
                if claim.get("indicative_earliest_date") != date
                else gate("GQ-DATE-01", {"indicative_earliest_date": date}, claim["verbatim_quote"], doc_id)
            )
            if ok and not cit_ok:
                ok, why = False, "claim_quote_unverified"
            record("date", date, doc_id, ok, why, cid)
        if kw is not None:
            ok, why = gate("GQ-KW-01", {"available_capacity_kw": kw}, claim.get("capacity_basis_quote"), doc_id)
            record("kw", kw, doc_id, ok, why, "capacity_basis_quote")
        if claim.get("binding") in ("binding", "non_binding"):
            ok, why = gate("GQ-BINDING-01", {}, claim.get("binding_evidence_quote"), doc_id)
            record("binding", claim["binding"], doc_id, ok, why, "binding_evidence_quote")

    for opt in answer["options_ranked"]:
        cids = opt.get("citation_ids") or []
        route_cit = cit_by_id.get(cids[0]) if cids else None
        route_ok = (
            route_cit is not None
            and citations.get(route_cit["id"], {}).get("verified") is True
            and normalise(route_cit.get("quote") or "") == normalise(opt["application_route"])
        )
        doc_id = route_cit.get("document_id") if route_cit else None
        record(
            "route",
            opt["kind"],
            doc_id,
            route_ok,
            None if route_ok else "route_citation_unverified",
            route_cit["id"] if route_cit else None,
        )
        kw = opt.get("estimated_kw_enabled")
        if kw is not None:
            ok, why, via = False, "no_verified_citation_states_kw", None
            for cid in cids:
                c = cit_by_id.get(cid)
                if c and citations.get(cid, {}).get("verified"):
                    good, _ = gate("GQ-KW-01", {"kw": kw}, c.get("quote"), c.get("document_id"))
                    if good:
                        ok, why, via = True, None, cid
                        break
            record("option_kw", kw, doc_id, ok, why, via)

    return {"documents": documents, "citations": citations, "values": values, "failures": failures}


# ------------------------------------------------------------------------------------------- rendering


def _partial_date(value: str) -> str:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    parts = value.split("-")
    if len(parts) == 2 and parts[1][:1] in ("Q", "H"):
        return f"{parts[1]} {parts[0]}"
    if len(parts) == 2:
        return f"{months[int(parts[1]) - 1]} {parts[0]}"
    if len(parts) == 3:
        return f"{int(parts[2])} {months[int(parts[1]) - 1]} {parts[0]}"
    return value


def _quote(text: str) -> list[str]:
    return [f"> {line}" if line else ">" for line in text.strip().splitlines()]


def render(bundle: dict[str, Any], report: dict[str, Any]) -> str:
    qr = bundle["query_response"]
    answer, docs = qr["answer"], {d["document_id"]: d for d in qr["documents"]}
    cits = {c["id"]: c for c in qr["citations"]}
    loc, req = answer["location"], answer["request"]
    dso = loc.get("dso") or "your grid operator (netbeheerder)"
    item = req["requested"][0]
    kw_req = f"{item['kw']:g}"
    direction = item["direction"]

    out: list[str] = [f"# GridQueue application pack — {dso} — {DIRECTION_LABEL[direction]}", ""]
    if qr["retrieval"].get("synthetic"):
        out += [
            "> **DEMO — SYNTHETIC SOURCES.** The documents behind this pack were written by the GridQueue",
            "> project for testing. They are not publications of any grid operator.",
            "",
        ]
    out += [
        f"_{answer['disclaimer']}_",
        "",
        "## Request",
        "",
        f"- Postcode: {loc.get('postcode') or req['address_or_postcode']}",
        f"- Requested: {kw_req} kW {DIRECTION_LABEL[direction]}",
        f"- Grid operator: {dso} (from GridQueue's postcode table; not yet verified against the operator's"
        " service-area list)",
        "",
    ]

    for dr in answer["per_direction"]:
        claim = dr.get("position_claim")
        out += [
            f"## Determination — {DIRECTION_LABEL[dr['direction']]}",
            "",
            f"- Verdict: **{VERDICT_LABEL[dr['verdict']]}**",
            f"- {dr['headline']}",
        ]
        if dr.get("indicative_earliest_date"):
            out.append(
                f"- Indicative earliest date: **{_partial_date(dr['indicative_earliest_date'])}** — "
                f"{BINDING_LABEL[dr['binding_chip']]}"
            )
        else:
            out.append("- Indicative earliest date: none published")
        if dr.get("available_capacity_kw") is not None:
            out.append(f"- Available capacity stated by the operator: {dr['available_capacity_kw']:g} kW")
        if claim:
            doc = docs[claim["document_id"]]
            out += [
                "",
                "Operator's own words (nl):",
                *_quote(claim["verbatim_quote"]),
                "",
                f"Source: {doc['publisher']} — {doc['title']} — {doc['url']} — published "
                f"{doc.get('publication_date') or 'unknown'} — retrieved {doc['retrieved_at']} — "
                f"sha256 `{doc['sha256']}`",
            ]
        out.append("")

    dr0 = answer["per_direction"][0]
    claim0 = dr0.get("position_claim")
    options = answer["options_ranked"]
    out += [f"## Application block — {dso}", ""]
    if options:
        for opt in options:
            doc = docs[opt["evidence_document_ids"][0]]
            kw = opt.get("estimated_kw_enabled")
            out += [
                f"### {opt['rank']}. {opt['title']}",
                "",
                "How to apply, in the operator's words (nl):",
                *_quote(opt["application_route"]),
                "",
                "- Capacity: " + (f"up to {kw:g} kW (stated by the operator)" if kw is not None else "not stated"),
                f"- Contact: {opt['who_to_contact']}",
                f"- Evidence: {doc['document_id']} (sha256 `{doc['sha256'][:16]}…`)",
                "",
            ]
        wanted = ", ".join(KIND_NL[o["kind"]] for o in options)
        letter = [
            f"Onderwerp: Aanvraag {kw_req} kW {DIRECTION_NL[direction]} — postcode "
            f"{loc.get('postcode') or req['address_or_postcode']}",
            "",
            f"Geachte {dso},",
            "",
            f"Voor postcode {loc.get('postcode') or req['address_or_postcode']} wil ik {kw_req} kW "
            f"{DIRECTION_NL[direction]} aanvragen.",
        ]
        if claim0:
            letter.append(
                f'In uw publicatie "{docs[claim0["document_id"]]["title"]}" staat: '
                f'"{normalise(claim0["verbatim_quote"])}"'
            )
        letter += [
            f"Graag kom ik in aanmerking voor: {wanted}.",
            "Kunt u mij laten weten welke voorwaarden en doorlooptijd daarbij gelden?",
            "",
            "Met vriendelijke groet,",
        ]
        out += ["Request text to send (nl; not yet checked by a native speaker):", "", "```text", *letter, "```", ""]
    else:
        out += ["No application route was found in the operator's documents. Ask the operator directly (below).", ""]

    script = dr0.get("phone_script")
    if script:
        out += ["## Phone script (nl)", "", *_quote(script["text_nl"]), ""]
        if script.get("text_en"):
            out += ["English:", "", *_quote(script["text_en"]), ""]

    included = sorted(cid for cid, r in report["citations"].items() if r["verified"])
    out += [
        "## Sources (verified offline)",
        "",
        "| Citation | Document | Publisher | URL | Retrieved | SHA-256 |",
        "|---|---|---|---|---|---|",
    ]
    for cid in included:
        c = cits[cid]
        d = docs[c["document_id"]]
        out.append(f"| {cid} | {d['title']} | {d['publisher']} | {d['url']} | {c['retrieved_at']} | `{d['sha256']}` |")
    excluded = sorted((cid, r["reason"]) for cid, r in report["citations"].items() if not r["verified"])
    if excluded:
        out += [
            "",
            "Not included (not verifiable source evidence): "
            + ", ".join(f"{cid} ({reason})" for cid, reason in excluded),
        ]

    out += [
        "",
        "## Verification",
        "",
        f"- Pack format: {PACK_VERSION}",
        f"- Answer determinism hash: `{answer['gate']['determinism_hash']}`",
        f"- Documents hash-verified (SHA-256 of exact text): "
        f"{sum(1 for r in report['documents'].values() if r['verified'])}/{len(report['documents'])}",
        f"- Citations verified: {len(included)}/{len(report['citations'])}",
    ]
    for v in report["values"]:
        out.append(
            f"- {v['kind']} `{v['value']}` ← {v['via'] or '—'} (document sha256 "
            f"`{(v['document_sha256'] or '')[:16]}…`): verified"
        )
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------------------------------- entry points


def build_pack(bundle: dict[str, Any], *, network: dict[str, Any] | None = None) -> PackResult:
    """Verify, then render. Raises ``PackVerificationError`` (pack withheld) if any asserted value fails."""
    report = verify_bundle(bundle)
    if report["failures"]:
        raise PackVerificationError(report["failures"])
    content = render(bundle, report).encode("utf-8")
    digest = sha256_bytes(content)
    manifest = {
        "pack_version": PACK_VERSION,
        "sha256": digest,
        "bytes": len(content),
        "determinism_hash": bundle["query_response"]["answer"]["gate"]["determinism_hash"],
        "documents": report["documents"],
        "citations_included": sorted(c for c, r in report["citations"].items() if r["verified"]),
        "citations_excluded": sorted(
            ({"id": c, "reason": r["reason"]} for c, r in report["citations"].items() if not r["verified"]),
            key=lambda x: x["id"],
        ),
        "values_verified": report["values"],
        "network": network or {"checked": False},
    }
    return PackResult(content=content, sha256=digest, manifest=manifest)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build and verify a GridQueue application pack offline.")
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument(
        "--require-network-off",
        action="store_true",
        help="fail unless /sys/class/net holds only 'lo' (use inside a networking-disabled Sandbox)",
    )
    ap.add_argument("--sys-class-net", type=Path, default=SYS_CLASS_NET, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    network: dict[str, Any] | None = None
    if args.require_network_off:
        try:
            network = assert_network_disabled(args.sys_class_net)
        except NetworkEnabledError as exc:
            print(json.dumps({"error": "network_enabled", "detail": str(exc)}), file=sys.stderr)
            return 3
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    try:
        result = build_pack(bundle, network=network)
    except PackVerificationError as exc:
        print(
            json.dumps({"error": "verification_failed", "failures": exc.failures}, ensure_ascii=False), file=sys.stderr
        )
        return 2
    args.out.write_bytes(result.content)
    if args.manifest:
        args.manifest.write_text(json.dumps(result.manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{result.sha256}  {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

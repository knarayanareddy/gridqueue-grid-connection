"""Contract tests for schemas/core-schemas.json (SPEC §10, 'Contract' row)."""

import json

import jsonschema
import pytest

from tests.conftest import REPO_ROOT


def _errors(validator, instance) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


def _all_refs(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "$ref":
                yield v
            else:
                yield from _all_refs(v)
    elif isinstance(node, list):
        for item in node:
            yield from _all_refs(item)


def test_schema_is_valid_draft_2020_12(core_schema):
    jsonschema.Draft202012Validator.check_schema(core_schema)


def test_every_ref_is_local_and_resolves(core_schema):
    for ref in _all_refs(core_schema):
        assert ref.startswith("#/$defs/"), f"non-local $ref: {ref}"
        assert ref.removeprefix("#/$defs/") in core_schema["$defs"], f"dangling $ref: {ref}"


def test_every_type_compiles(core_schema, validator_for):
    for name in core_schema["types"]:
        validator_for(name).is_valid({})  # raises on unresolvable refs


# ---------------------------------------------------------------- PositionClaim


@pytest.fixture
def claim() -> dict:
    return {
        "id": "pc_001",
        "direction": "feed_in",
        "congestion_registered": True,
        "queue_status": "WAITLIST",
        "binding": "non_binding",
        "binding_evidence_quote": "Deze prognose is indicatief en niet bindend.",
        "document_id": "doc_enexis_prognose",
        "verbatim_quote": "Uitbreiding verwacht in Q3 2028 (indicatief).",
        "confidence": 0.8,
        "indicative_earliest_date": "2028-Q3",
        "publication_date": "2026-07-14",
    }


def test_valid_claim_passes(validator_for, claim):
    assert _errors(validator_for("PositionClaim"), claim) == []


def test_binding_null_fails(validator_for, claim):
    assert _errors(validator_for("PositionClaim"), {**claim, "binding": None})


@pytest.mark.parametrize("value", [None, ""])
def test_asserted_binding_needs_a_real_quote(validator_for, claim, value):
    assert _errors(validator_for("PositionClaim"), {**claim, "binding_evidence_quote": value})


def test_unknown_binding_needs_no_quote(validator_for, claim):
    c = {**claim, "binding": "unknown"}
    c.pop("binding_evidence_quote")
    assert _errors(validator_for("PositionClaim"), c) == []


@pytest.mark.parametrize("drop_or_null", ["drop", "null"])
def test_date_without_publication_date_fails(validator_for, claim, drop_or_null):
    c = dict(claim)
    if drop_or_null == "drop":
        c.pop("publication_date")
    else:
        c["publication_date"] = None
    assert _errors(validator_for("PositionClaim"), c)


def test_date_without_document_fails(validator_for, claim):
    c = dict(claim)
    c.pop("document_id")
    assert _errors(validator_for("PositionClaim"), c)


@pytest.mark.parametrize("bad", ["sometime soon", "Q3 2028", "2028-Q5", "2028-13", "28-Q3"])
def test_free_text_or_malformed_date_fails(validator_for, claim, bad):
    assert _errors(validator_for("PositionClaim"), {**claim, "indicative_earliest_date": bad})


@pytest.mark.parametrize("good", ["2028", "2028-Q3", "2028-H2", "2028-07", "2028-07-14", "2028/2029"])
def test_iso_partial_dates_pass(validator_for, claim, good):
    assert _errors(validator_for("PositionClaim"), {**claim, "indicative_earliest_date": good}) == []


@pytest.mark.parametrize("basis", ["drop", None, ""])
def test_kw_without_basis_quote_fails(validator_for, claim, basis):
    c = {**claim, "available_capacity_kw": 250}
    if basis != "drop":
        c["capacity_basis_quote"] = basis
    assert _errors(validator_for("PositionClaim"), c)


def test_both_is_not_a_claim_direction(validator_for, claim):
    assert _errors(validator_for("PositionClaim"), {**claim, "direction": "both"})


# ---------------------------------------------------------------- Option


@pytest.fixture
def option() -> dict:
    return {
        "id": "opt_001",
        "kind": "non_firm_connection",
        "estimate_basis": "document_quote",
        "application_route": "Aanvraag niet-firm transportrecht via het klantportaal",
        "evidence_document_ids": ["doc_x"],
        "model_estimate_flag": False,
        "confidence": 0.7,
    }


def test_valid_option_passes(validator_for, option):
    assert _errors(validator_for("Option"), option) == []


def test_model_estimate_without_flag_fails(validator_for, option):
    assert _errors(validator_for("Option"), {**option, "estimate_basis": "model_estimate"})


def test_computed_profile_needs_assumptions(validator_for, option):
    v = validator_for("Option")
    assert _errors(v, {**option, "estimate_basis": "computed_profile"})
    assert _errors(v, {**option, "estimate_basis": "computed_profile", "assumptions": []})
    assert _errors(v, {**option, "estimate_basis": "computed_profile", "assumptions": ["8h/day"]}) == []


def test_option_without_evidence_fails(validator_for, option):
    assert _errors(validator_for("Option"), {**option, "evidence_document_ids": []})


# ---------------------------------------------------------------- LocationResolution


def test_resolved_location_without_dso_citation_fails(validator_for):
    loc = {
        "resolved": True,
        "resolution_method": "static_table",
        "resolved_at": "2026-10-26T12:00:00Z",
        "dso": "Enexis",
        "dso_evidence_citation": None,
    }
    v = validator_for("LocationResolution")
    assert _errors(v, loc)
    assert _errors(v, {**loc, "dso_evidence_citation": "cit_001"}) == []


def test_unresolved_location_abstains(validator_for):
    loc = {
        "resolved": False,
        "resolution_method": "static_table",
        "resolved_at": "2026-10-26T12:00:00Z",
        "abstain_reason": "unmapped_postcode",
    }
    assert _errors(validator_for("LocationResolution"), loc) == []


# ---------------------------------------------------------------- RevisionEvent


def test_self_reported_revision_needs_both_quotes(validator_for):
    ev = {
        "id": "rev_001",
        "document_family": "dso-codeerprognose-brabant",
        "source": "document_self_reported",
        "detected_at": "2026-10-26T12:00:00Z",
        "quote_before": None,
        "quote_after": "verwacht Q3 2028",
    }
    v = validator_for("RevisionEvent")
    assert _errors(v, ev)
    assert _errors(v, {**ev, "quote_before": "verwacht Q1 2028"}) == []


# ---------------------------------------------------------------- Citation / LedgerLine


def test_document_citation_needs_hash_and_quote(validator_for):
    cit = {
        "id": "cit_001",
        "kind": "source_document",
        "locator": "doc_x https://example.invalid 2026-07-14",
        "retrieved_at": "2026-10-26T12:00:00Z",
        "trust": "primary",
    }
    v = validator_for("Citation")
    assert _errors(v, cit)
    ok = {**cit, "document_id": "doc_x", "sha256": "a" * 64, "quote": "Uitbreiding verwacht in Q3 2028."}
    assert _errors(v, ok) == []


def test_model_derived_citation_is_rejected(validator_for):
    cit = {
        "id": "cit_002",
        "kind": "computed",
        "locator": "profile(…)",
        "retrieved_at": "2026-10-26T12:00:00Z",
        "trust": "model_derived",
    }
    assert _errors(validator_for("Citation"), cit)


def test_sample_ledger_lines_validate(validator_for):
    v = validator_for("LedgerLine")
    lines = (REPO_ROOT / "runs" / "sample_ledger.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines, "sample ledger must not be empty"
    for line in lines:
        assert _errors(v, json.loads(line)) == []

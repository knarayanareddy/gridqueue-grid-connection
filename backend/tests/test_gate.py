"""Deterministic gate (SPEC §6, §10 'Adversarial' row)."""

import ast
from pathlib import Path

import pytest

from app.gate.gate import (
    DeterministicGate,
    date_supported_by,
    kw_supported_by,
    normalise,
    verbatim_supports,
)

GATE = DeterministicGate.evaluate
SOURCE = (
    "Netcongestie Brabant — codeerprognose, versie 3 (14 juli 2026).\n"
    "De indicatieve datum voor\nuitbreiding van de productie-\ncapaciteit is Q3 2028 (onder voorbehoud).\n"
    "Beschikbaar transportvermogen voor afname: 1.250 kW. Voor teruglevering is 0,25 MW beschikbaar.\n"
    "Dit is een niet\u00a0bindende prognose.\n"
)


def verdict(assertion, quote, source=SOURCE):
    return GATE("GQ-DATE-01", assertion, quote, source)


# ------------------------------------------------------------------ the four cases from the review


def test_line_wrapped_quote_passes():
    quote = "De indicatieve datum voor uitbreiding van de productiecapaciteit is Q3 2028"
    r = verdict({"indicative_earliest_date": "2028-Q3"}, quote)
    assert r.verdict == "PASS", r


def test_trivial_quote_is_undetermined():
    r = verdict({"indicative_earliest_date": "2031-Q1"}, "2")
    assert (r.verdict, r.reason) == ("UNDETERMINED", "quote_too_short")


def test_real_quote_not_containing_date_is_undetermined():
    r = verdict({"indicative_earliest_date": "2031-Q1"}, "capaciteit is Q3 2028 (onder voorbehoud)")
    assert (r.verdict, r.reason) == ("UNDETERMINED", "date_not_in_quote")


def test_paraphrase_fails():
    r = verdict({}, "capacity returns in 2028")
    assert (r.verdict, r.reason) == ("FAIL", "quote_not_found_in_document")


# ------------------------------------------------------------------ evidence presence


@pytest.mark.parametrize("quote", [None, "", "   "])
def test_missing_quote_is_undetermined(quote):
    r = verdict({}, quote)
    assert (r.verdict, r.reason) == ("UNDETERMINED", "missing_quote")


@pytest.mark.parametrize("source", [None, "", "\n"])
def test_missing_source_is_undetermined(source):
    r = verdict({}, "De indicatieve datum voor uitbreiding", source)
    assert (r.verdict, r.reason) == ("UNDETERMINED", "date_without_document")


def test_pass_carries_verified_evidence():
    q = "Dit is een niet bindende prognose."
    r = verdict({}, q)
    assert r.verdict == "PASS" and r.verified_evidence == q
    assert r.to_dict()["verdict"] == "PASS"


# ------------------------------------------------------------------ normalisation


def test_nbsp_and_whitespace_normalised():
    assert verbatim_supports("een niet bindende prognose", SOURCE)


@pytest.mark.parametrize("quote", ["van de productiecapaciteit", "van de productie-capaciteit"])
def test_hyphenated_line_break_accepts_both_readings(quote):
    assert verbatim_supports(quote, SOURCE)


def test_curly_quotes_and_dashes_normalised():
    src = "Het zogenaamde \u201cniet-firm\u201d contract \u2013 ook wel flexcontract."
    assert verbatim_supports('Het zogenaamde "niet-firm" contract - ook wel', src)


def test_matching_is_case_sensitive():
    assert not verbatim_supports("de indicatieve datum voor uitbreiding".upper(), SOURCE)


def test_normalise_is_idempotent():
    once = normalise(SOURCE)
    assert normalise(once) == once


# ------------------------------------------------------------------ date support


@pytest.mark.parametrize(
    "asserted,quote",
    [
        ("2028-Q3", "verwacht in Q3 2028"),
        ("2028-Q3", "verwacht in 2028-Q3"),
        ("2028-Q3", "in het derde kwartaal van 2028"),
        ("2028-Q3", "in het 3e kwartaal 2028"),
        ("2028-Q3", "in the third quarter of 2028"),
        ("2028-H2", "in de tweede helft van 2028"),
        ("2028-H1", "H1 2028"),
        ("2028-07", "vanaf juli 2028"),
        ("2028-07", "from July 2028"),
        ("2028-07", "vanaf 07-2028"),
        ("2028-07-14", "op 14 juli 2028"),
        ("2028-07-14", "on July 14, 2028"),
        ("2028-07-14", "op 14-07-2028"),
        ("2028", "niet voor 2028"),
        ("2028/2029", "tussen 2028 en 2029"),
    ],
)
def test_date_supported(asserted, quote):
    assert date_supported_by(asserted, quote) is True


@pytest.mark.parametrize(
    "asserted,quote",
    [
        ("2028-Q3", "verwacht in Q1 2028"),
        ("2028-Q3", "Q3 2027, en in 2028 meer"),  # quarter not adjacent to the year
        ("2028-05", "capacity may become available in 2028"),  # 'may' is not May
        ("2028-03", "in 2028, mark my words"),
        ("2028-Q3", "vanaf Q3 '28"),  # two-digit years are too ambiguous to accept
        ("2029", "in 2028"),
        ("2028", "in 20280"),
        ("2028/2029", "vanaf 2028"),
    ],
)
def test_date_not_supported(asserted, quote):
    assert date_supported_by(asserted, quote) is False


@pytest.mark.parametrize("asserted", ["sometime soon", "Q3 2028", "2028-Q5", "binnenkort"])
def test_unparseable_date_is_undetermined(asserted):
    assert date_supported_by(asserted, "Q3 2028") is None
    r = verdict({"indicative_earliest_date": asserted}, "capaciteit is Q3 2028 (onder voorbehoud)")
    assert (r.verdict, r.reason) == ("UNDETERMINED", "date_unparseable")


# ------------------------------------------------------------------ kW support


@pytest.mark.parametrize(
    "kw,quote",
    [
        (1250, "afname: 1.250 kW"),
        (1.25, "afname: 1,25 kW"),
        (250, "0,25 MW beschikbaar"),
        (250, "0.25MW"),
        (250, "250 kW"),
        (1_500_000, "1.500 MW"),
        (2500, "2,5 MW"),
    ],
)
def test_kw_supported(kw, quote):
    assert kw_supported_by(kw, quote)


@pytest.mark.parametrize("kw,quote", [(250, "25 kW"), (250, "250 kVA"), (250, "250 huishoudens"), (250, "no number")])
def test_kw_not_supported(kw, quote):
    assert not kw_supported_by(kw, quote)


def test_gate_checks_kw():
    q = "Voor teruglevering is 0,25 MW beschikbaar."
    assert verdict({"available_capacity_kw": 250}, q).verdict == "PASS"
    r = verdict({"available_capacity_kw": 400}, q)
    assert (r.verdict, r.reason) == ("UNDETERMINED", "kw_without_quote")


def test_kw_check_runs_even_when_date_passes():
    q = "capaciteit is Q3 2028 (onder voorbehoud)"
    r = verdict({"indicative_earliest_date": "2028-Q3", "available_capacity_kw": 100}, q)
    assert r.reason == "kw_without_quote"


# ------------------------------------------------------------------ determinism & purity


def test_deterministic():
    args = ({"indicative_earliest_date": "2028-Q3"}, "capaciteit is Q3 2028 (onder voorbehoud)")
    assert len({repr(verdict(*args)) for _ in range(5)}) == 1


def test_gate_module_makes_no_llm_or_network_calls():
    """SPEC §6: the gate is pure Python. Forbid importing any client that could reach a model or the network."""
    forbidden = {"openai", "httpx", "requests", "urllib", "socket", "aiohttp", "app.tf", "tavily"}
    gate_dir = Path(__file__).resolve().parents[1] / "app" / "gate"
    for path in gate_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert not any(name == f or name.startswith(f + ".") for f in forbidden), f"{path.name}: {name}"

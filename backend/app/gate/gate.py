"""Tri-state deterministic gate (SPEC §6). NO LLM CALLS, NO NETWORK.

``DeterministicGate.evaluate`` decides whether one asserted claim is supported by a verbatim quote from a
fetched source document:

* ``FAIL``         — the quote provably does not occur in the source. The claim is fabricated or paraphrased
                     and must be rejected (reason ``quote_not_found_in_document``).
* ``UNDETERMINED`` — the evidence is insufficient: no quote, no source text, a quote too short to be
                     meaningful, or a quote that exists but does not contain the asserted date / kW value.
                     The asserted value must be dropped; the answer abstains rather than guesses.
* ``PASS``         — the quote occurs in the source (modulo PDF-extraction whitespace artefacts) **and** every
                     asserted date / kW value is present in that quote.

Matching is deliberately conservative: case-sensitive, and only whitespace/typography artefacts introduced
by text extraction are normalised away. Semantic support (does the sentence *mean* what the claim says?) is
NOT judged here — that is what the human-readable quote on screen is for.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Literal

Verdict = Literal["PASS", "FAIL", "UNDETERMINED"]

MIN_QUOTE_CHARS = 10  # mirrors PositionClaim.verbatim_quote.minLength in schemas/core-schemas.json

DATE_KEYS = ("indicative_earliest_date", "date")
KW_KEYS = ("available_capacity_kw", "kw")


@dataclass(frozen=True)
class GateResult:
    verdict: Verdict
    rule_id: str
    reason: str | None = None
    message: str = ""
    verified_evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------------------------------------------
# Text normalisation
# --------------------------------------------------------------------------------------------------------------

_TYPOGRAPHY = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00ad": None,  # soft hyphen
        "\u200b": None,  # zero-width space
        "\ufeff": None,  # BOM
    }
)
_WS = re.compile(r"\s+")
_HYPHEN_BREAK = re.compile(r"-[ \t]*\r?\n[ \t]*")


def _base_normalise(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(_TYPOGRAPHY)


def normalise(text: str) -> str:
    """Normalise extraction artefacts: Unicode compatibility forms, curly quotes, dashes, whitespace."""
    return _WS.sub(" ", _base_normalise(text)).strip()


def _source_variants(raw_source: str) -> tuple[str, ...]:
    """A hyphen at a line break is either a real hyphen ("Noord-\\nBrabant") or a word split
    ("capa-\\nciteit"). We cannot know which, so accept either reading."""
    base = _base_normalise(raw_source)
    joined = _WS.sub(" ", _HYPHEN_BREAK.sub("", base)).strip()
    kept = _WS.sub(" ", _HYPHEN_BREAK.sub("-", base)).strip()
    return (joined,) if joined == kept else (joined, kept)


def verbatim_supports(quote: str, raw_source: str) -> bool:
    """True iff ``quote`` occurs in ``raw_source`` after artefact normalisation (case-sensitive)."""
    q = normalise(quote)
    return bool(q) and any(q in variant for variant in _source_variants(raw_source))


# --------------------------------------------------------------------------------------------------------------
# Date support
# --------------------------------------------------------------------------------------------------------------

_MONTHS: dict[int, tuple[str, ...]] = {
    1: ("januari", "january", "jan"),
    2: ("februari", "february", "feb"),
    3: ("maart", "march", "mrt", "mar"),
    4: ("april", "apr"),
    5: ("mei", "may"),
    6: ("juni", "june", "jun"),
    7: ("juli", "july", "jul"),
    8: ("augustus", "august", "aug"),
    9: ("september", "sept", "sep"),
    10: ("oktober", "october", "okt", "oct"),
    11: ("november", "nov"),
    12: ("december", "dec"),
}
_ORDINALS_NL = {1: "eerste", 2: "tweede", 3: "derde", 4: "vierde"}
_ORDINALS_EN = {1: "first", 2: "second", 3: "third", 4: "fourth"}
_ORDINAL_SUFFIX_EN = {1: "st", 2: "nd", 3: "rd", 4: "th"}

_ASSERTED_DATE = re.compile(
    r"^(?P<year>20\d{2})"
    r"(?:-(?:Q(?P<quarter>[1-4])|H(?P<half>[12])|(?P<month>0[1-9]|1[0-2])(?:-(?P<day>0[1-9]|[12]\d|3[01]))?))?$"
)
_ASSERTED_RANGE = re.compile(r"^(?P<a>20\d{2}(?:-\S+)?)\s*(?:/|\.\.|–|—| to | - )\s*(?P<b>20\d{2}(?:-\S+)?)$")


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


_JOIN = r"\s*(?:van\s+|of\s+|in\s+)?"  # "Q3 2028", "derde kwartaal van 2028", "third quarter of 2028"


def _adjacent_to_year(alternatives: list[str], year: str, text: str) -> bool:
    """The period expression must sit right next to the full year — a stray "Q3" elsewhere does not count."""
    alt = "|".join(alternatives)
    patterns = [
        rf"\b(?:{alt}){_JOIN}{year}\b",
        rf"\b{year}\s*[-/]?\s*(?:{alt})\b",
    ]
    return any(_has(p, text) for p in patterns)


def _quarter_in(q: int, year: str, text: str) -> bool:
    alternatives = [
        rf"Q\s?{q}",
        rf"K{q}",
        rf"{q}\s?(?:e|de|ste)\s+kwartaal",
        rf"{_ORDINALS_NL[q]}\s+kwartaal",
        rf"kwartaal\s+{q}",
        rf"(?:the\s+)?{_ORDINALS_EN[q]}\s+quarter",
        rf"{q}{_ORDINAL_SUFFIX_EN[q]}\s+quarter",
    ]
    return _adjacent_to_year(alternatives, year, text)


def _half_in(h: int, year: str, text: str) -> bool:
    alternatives = [
        rf"H{h}",
        rf"{_ORDINALS_NL[h]}\s+helft",
        rf"{h}\s?(?:e|ste|de)\s+helft",
        rf"(?:the\s+)?{_ORDINALS_EN[h]}\s+half",
        rf"{h}{_ORDINAL_SUFFIX_EN[h]}\s+half",
    ]
    return _adjacent_to_year(alternatives, year, text)


def _month_in(m: int, year: str, text: str) -> bool:
    names = "|".join(_MONTHS[m])
    patterns = [
        # "juli 2028", "July 2028", "14 juli 2028", "July 14, 2028"
        rf"\b(?:\d{{1,2}}\s+)?(?:{names})\.?\s+(?:\d{{1,2}}(?:st|nd|rd|th)?,?\s+)?{year}\b",
        rf"\b{year}[-/.]0?{m}\b",
        rf"\b0?{m}[-/.]{year}\b",
    ]
    return any(_has(p, text) for p in patterns)


def _day_in(d: int, m: int, year: str, text: str) -> bool:
    names = "|".join(_MONTHS[m])
    patterns = [
        rf"\b{year}-0?{m}-0?{d}\b",
        rf"\b0?{d}[-/.]0?{m}[-/.]{year}\b",
        rf"\b0?{d}\s+(?:{names})\.?\s+{year}\b",
        rf"\b(?:{names})\.?\s+0?{d}(?:st|nd|rd|th)?,?\s+{year}\b",
    ]
    return any(_has(p, text) for p in patterns)


def date_supported_by(asserted: str, quote: str) -> bool | None:
    """True/False if ``asserted`` (ISO-like partial date) is / is not stated in ``quote``.
    None if ``asserted`` is not a parseable ISO-like partial date (free text is never accepted)."""
    asserted = asserted.strip()
    text = normalise(quote)

    rng = _ASSERTED_RANGE.match(asserted)
    if rng:
        a, b = date_supported_by(rng["a"], quote), date_supported_by(rng["b"], quote)
        if a is None or b is None:
            return None
        return a and b

    m = _ASSERTED_DATE.match(asserted)
    if not m:
        return None
    year = m["year"]
    if not re.search(rf"(?<!\d){year}(?!\d)", text):
        return False
    if m["quarter"]:
        return _quarter_in(int(m["quarter"]), year, text)
    if m["half"]:
        return _half_in(int(m["half"]), year, text)
    if m["day"]:
        return _day_in(int(m["day"]), int(m["month"]), year, text)
    if m["month"]:
        return _month_in(int(m["month"]), year, text)
    return True


# --------------------------------------------------------------------------------------------------------------
# kW support
# --------------------------------------------------------------------------------------------------------------

_POWER = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(kW|MW)\b", re.IGNORECASE)


def _number_readings(token: str) -> set[float]:
    """All plausible numeric readings of a Dutch- or English-formatted number.

    "1.250" is 1250 in Dutch and 1.25 in English; with no other context both readings are kept.
    """
    if "," in token and "." in token:
        decimal = "," if token.rfind(",") > token.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        return {float(token.replace(thousands, "").replace(decimal, "."))}
    for sep in (",", "."):
        if sep in token:
            readings: set[float] = set()
            groups = token.split(sep)
            if len(groups) == 2:
                readings.add(float(token.replace(sep, ".")))  # decimal separator
            if all(len(g) == 3 for g in groups[1:]):
                readings.add(float(token.replace(sep, "")))  # thousands separator
            return readings
    return {float(token)}


def powers_in_kw(quote: str) -> set[float]:
    values: set[float] = set()
    for number, unit in _POWER.findall(normalise(quote)):
        factor = 1000.0 if unit.lower() == "mw" else 1.0
        values.update(r * factor for r in _number_readings(number))
    return values


def kw_supported_by(asserted_kw: float, quote: str) -> bool:
    return any(abs(v - asserted_kw) <= 1e-6 * max(1.0, abs(asserted_kw)) for v in powers_in_kw(quote))


# --------------------------------------------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------------------------------------------


def _first(assertion: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for k in keys:
        if assertion.get(k) is not None:
            return assertion[k]
    return None


class DeterministicGate:
    """Tri-state deterministic gate enforcing code-level invariants."""

    @staticmethod
    def evaluate(
        rule_id: str,
        assertion: dict[str, Any],
        evidence_quote: str | None,
        raw_source: str | None,
    ) -> GateResult:
        def undetermined(reason: str, message: str) -> GateResult:
            return GateResult("UNDETERMINED", rule_id, reason, message)

        if not evidence_quote or not evidence_quote.strip():
            return undetermined("missing_quote", "No supporting evidence quote was provided.")
        if not raw_source or not raw_source.strip():
            return undetermined("date_without_document", "No source document text is available to check against.")
        if len(normalise(evidence_quote)) < MIN_QUOTE_CHARS:
            return undetermined(
                "quote_too_short",
                f"Evidence quote is shorter than {MIN_QUOTE_CHARS} characters and cannot anchor a claim.",
            )

        if not verbatim_supports(evidence_quote, raw_source):
            return GateResult(
                "FAIL",
                rule_id,
                "quote_not_found_in_document",
                "Evidence quote does not occur verbatim in the source document.",
            )

        asserted_date = _first(assertion, DATE_KEYS)
        if asserted_date is not None:
            supported = date_supported_by(str(asserted_date), evidence_quote)
            if supported is None:
                return undetermined(
                    "date_unparseable",
                    f"Asserted date {asserted_date!r} is not an ISO-like partial date (YYYY, YYYY-Qn, YYYY-Hn, "
                    "YYYY-MM, YYYY-MM-DD or a range of these).",
                )
            if not supported:
                return undetermined(
                    "date_not_in_quote", f"Asserted date {asserted_date!r} is not stated in the evidence quote."
                )

        asserted_kw = _first(assertion, KW_KEYS)
        if asserted_kw is not None:
            try:
                kw = float(asserted_kw)
            except (TypeError, ValueError):
                return undetermined("kw_without_quote", f"Asserted capacity {asserted_kw!r} is not a number.")
            if not kw_supported_by(kw, evidence_quote):
                return undetermined(
                    "kw_without_quote", f"Asserted capacity {kw:g} kW is not stated in the evidence quote."
                )

        return GateResult("PASS", rule_id, None, "Evidence verified.", verified_evidence=evidence_quote)

"""C-T24-PACKAGE — README, LIMITATIONS and the video script must say only what the run files measured."""

import json
import re

import pytest

from tests.conftest import REPO_ROOT

README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
LIMITATIONS = (REPO_ROOT / "LIMITATIONS.md").read_text(encoding="utf-8")
SCRIPT = (REPO_ROOT / "video" / "script.md").read_text(encoding="utf-8")
AB = json.loads((REPO_ROOT / "runs" / "ab_experiment_results.json").read_text(encoding="utf-8"))
SWEEP = json.loads((REPO_ROOT / "runs" / "sweep_summary.json").read_text(encoding="utf-8"))

FABRICATED = ("fabricated_dates", "fabricated_kw", "fabricated_binding", "fabricated_routes")
ROW_LABELS = {
    "fabricated_dates": "Fabricated dates",
    "fabricated_kw": "Fabricated kW figures",
    "fabricated_binding": "Fabricated binding claims",
    "fabricated_routes": "Fabricated application routes",
    "misattributed": "Misattributed (real quote, wrong meaning)",
    "genuine": "Genuine values kept",
}


def _blocked() -> tuple[int, int]:
    d = AB["delta"]
    total = sum(d[k]["total"] for k in FABRICATED)
    return total - sum(d[k]["gate_on"] for k in FABRICATED), total


# ------------------------------------------------------------------------------------------------ README


def test_headline_banner_is_the_measured_one():
    d = AB["delta"]["fabricated_dates"]
    blocked, total = _blocked()
    banner = (
        f"### Gate ON: {d['gate_on']} invented dates · Gate OFF: {d['gate_off']} fabricated dates accepted · "
        f"{blocked}/{total} fabricated values blocked"
    )
    assert banner in README
    # the qualifier sits directly under the banner
    after = README.split(banner, 1)[1][:900]
    assert "SYNTHETIC" in after and "hand-written" in after and "not a Token Factory Sandbox" in after


def test_banner_states_meaning_level_precision():
    d = AB["delta"]
    reached = sum(v["gate_on"] for v in d.values())
    assert f"{d['genuine']['gate_on']} of those {reached} were correct" in README
    assert f"{d['misattributed']['gate_on']} misattributed values" in README


def test_readme_has_every_measured_ab_number():
    for key, label in ROW_LABELS.items():
        v = AB["delta"][key]
        row = f"| {label} | {v['gate_off']}/{v['total']} | **{v['gate_on']}/{v['total']}** |"
        assert row in README, f"README is missing or misreports: {row}"


def test_no_unmeasured_precision_claim():
    assert "citation precision" not in README.lower()
    assert "citation precision" not in SCRIPT.lower()


@pytest.mark.parametrize(
    ("heading", "must_mention"),
    [
        ("### Technological Implementation", ("Tavily", "Nemotron Ultra", "Token Factory Sandbox")),
        ("### Design", ("Direction Card", "accessib")),
        ("### Potential Impact", ("50-area sweep",)),
        ("### Quality of the Idea", ("non-binding",)),
    ],
)
def test_four_criterion_sections(heading, must_mention):
    assert heading in README
    section = README.split(heading, 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
    for term in must_mention:
        assert term in section, f"{heading} should mention {term}"
    honesty = ("**Not done:**", "Not yet", "not yet", "**Known gap", "**Still to do")
    assert any(m in section for m in honesty), f"{heading} must state what is not done or not yet measured"


def test_sweep_section_matches_the_report_and_quotes_no_synthetic_aggregates():
    s = SWEEP["summary"]
    section = README.split("### Potential Impact", 1)[1].split("\n### ", 1)[0]
    assert (
        f"{s['n_requested']} areas requested, {s['n_completed']} completed, {s['n_failed']} failed, and "
        f"{s['n_abstained']} Stedin areas" in section
    )
    assert "SYNTHETIC" in section
    assert "%" not in section  # no share of "congested areas" from synthetic data


# ------------------------------------------------------------------------------------------------ LIMITATIONS


def test_limitations_states_the_two_required_positions():
    assert "official published positions, not predictive grid physics" in LIMITATIONS
    assert "remain legally non-binding" in LIMITATIONS


def test_limitations_numbers_match_the_runs():
    d = AB["delta"]
    fd, fk = d["fabricated_dates"], d["fabricated_kw"]
    assert f"{fd['gate_off']}/{fd['total']} / **{fd['gate_on']}/{fd['total']}**" in LIMITATIONS
    assert f"{fk['gate_off']}/{fk['total']} / **{fk['gate_on']}/{fk['total']}**" in LIMITATIONS
    assert f"**{d['misattributed']['gate_on']}/{d['misattributed']['total']}**" in LIMITATIONS
    blocked, total = _blocked()
    assert f"| {blocked}/{total} |" in LIMITATIONS
    s = SWEEP["summary"]
    assert f"| {s['n_requested']} / {s['n_completed']} / {s['n_failed']} |" in LIMITATIONS


# ------------------------------------------------------------------------------------------------ video script


def _shots() -> list[dict]:
    rows = []
    for line in SCRIPT.splitlines():
        m = re.match(r"^\| (S\d\d) \| (\d+):(\d\d) \| (\d+):(\d\d) \| (\d+) \|(.*)\|$", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(7).split(" | ")]
        rows.append(
            {
                "id": m.group(1),
                "start": int(m.group(2)) * 60 + int(m.group(3)),
                "end": int(m.group(4)) * 60 + int(m.group(5)),
                "dur": int(m.group(6)),
                "transition": cells[0],
                "visual": cells[1],
                "vo": cells[2],
                "owner": cells[3],
            }
        )
    return rows


def test_script_runs_exactly_2_50_with_contiguous_shots():
    shots = _shots()
    assert len(shots) >= 10
    assert [s["id"] for s in shots] == [f"S{i:02d}" for i in range(1, len(shots) + 1)]
    assert shots[0]["start"] == 0 and shots[-1]["end"] == 170
    for a, b in zip(shots, shots[1:], strict=False):
        assert a["end"] == b["start"], f"gap or overlap between {a['id']} and {b['id']}"
    for s in shots:
        assert s["end"] - s["start"] == s["dur"] > 0, s["id"]
        assert s["transition"] and s["owner"], s["id"]


def test_narration_fits_its_shots():
    shots = _shots()
    words = {s["id"]: len(re.findall(r"[\w'’-]+", s["vo"])) for s in shots}
    for s in shots:
        assert words[s["id"]] <= 2.7 * s["dur"], f"{s['id']}: {words[s['id']]} words in {s['dur']} s"
    assert sum(words.values()) <= 430


def test_insight_shots_are_at_most_25_seconds_and_refusal_present():
    shots = _shots()
    insights = [s for s in shots if "INSIGHT" in s["visual"]]
    assert len(insights) == 3 and all(s["dur"] <= 25 for s in insights)
    assert any("THE REFUSAL" in s["visual"] and "We will not guess" in s["vo"] for s in shots)


def test_every_spoken_number_is_published():
    published = set(re.findall(r"\d+", README + LIMITATIONS))
    for s in _shots():
        for n in re.findall(r"\d+", s["vo"]):
            assert n in published, f"{s['id']} speaks {n}, which is not in README.md or LIMITATIONS.md"


def test_spoken_ab_numbers_are_the_measured_ones():
    vo = " ".join(s["vo"] for s in _shots())
    d = AB["delta"]
    blocked, total = _blocked()
    assert f"gate off, {d['fabricated_dates']['gate_off']} fabricated dates" in vo
    assert f"With it on, {d['fabricated_dates']['gate_on']}." in vo
    assert f"{blocked} of {total} fabricated values blocked" in vo
    assert f"{d['misattributed']['gate_on']} of {d['misattributed']['total']} misattributed" in vo

"""Devpost copy (docs/DEVPOST_SUBMISSION.md, docs/DEVPOST_FEEDBACK.md) and the README badge: say only what was measured.

Same rule as test_packaging.py (D-023): the headline numbers are derived from runs/*.json, so a re-run with different
results breaks the build until the copy is updated.
"""

import json
import re

from tests.conftest import REPO_ROOT

README = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
SUBMISSION = (REPO_ROOT / "docs" / "DEVPOST_SUBMISSION.md").read_text(encoding="utf-8")
FEEDBACK = (REPO_ROOT / "docs" / "DEVPOST_FEEDBACK.md").read_text(encoding="utf-8")
AB = json.loads((REPO_ROOT / "runs" / "ab_experiment_results.json").read_text(encoding="utf-8"))
SWEEP = json.loads((REPO_ROOT / "runs" / "sweep_summary.json").read_text(encoding="utf-8"))

PAGES_URL = "https://knarayanareddy.github.io/gridqueue-grid-connection/"
BADGE = f"[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-2ea44f?style=for-the-badge)]({PAGES_URL})"
FABRICATED = ("fabricated_dates", "fabricated_kw", "fabricated_binding", "fabricated_routes")
REAL_TRACKS = ("Coding and Agentic Engineering", "Best Apps and Agents", "Personal AI", "Physical AI")


def _flat(markdown: str) -> str:
    """Join lines and drop blockquote markers, so wrapped prose can be matched as one string."""
    return re.sub(r"\s+", " ", re.sub(r"(?m)^>\s?", "", markdown))


def _ab_headline(ab: dict) -> str:
    d = ab["delta"]
    total = sum(d[k]["total"] for k in FABRICATED)
    blocked = total - sum(d[k]["gate_on"] for k in FABRICATED)
    dates, genuine = d["fabricated_dates"], d["genuine"]
    return (
        f"**Gate OFF accepted {dates['gate_off']} of {dates['total']} fabricated dates. Gate ON blocked {blocked} "
        f"of {total} fabricated values ({dates['gate_on']} invented dates) and kept {genuine['gate_on']} of "
        f"{genuine['total']} genuine ones.**"
    )


def _headline_block() -> str:
    section = SUBMISSION.split('## 2. Description (paste into "About the project")', 1)[1]
    block = section.split("\n\n", 2)[1]  # the blockquote right under the heading
    assert block.startswith(">"), "the A/B headline must open the description"
    return _flat(block)


# ------------------------------------------------------------------------------------------------ README


def test_readme_opens_with_the_live_demo_badge():
    head = README.split("\n> ", 1)[0]  # everything above the tagline
    assert BADGE in head


def test_readme_no_longer_says_the_demo_is_pending():
    assert "live once\nthe Pages workflow has deployed" not in README
    assert "live only after it runs on `main`" not in README


# ------------------------------------------------------------------------------------------------ submission


def test_ab_delta_headline_is_derived_from_the_run():
    assert _ab_headline(AB) in _headline_block()


def test_a_misreported_headline_would_be_caught():
    tampered = json.loads(json.dumps(AB))
    tampered["delta"]["fabricated_dates"]["gate_off"] -= 1
    assert _ab_headline(tampered) not in _headline_block()


def test_headline_states_its_real_scope_and_keeps_the_sweep_separate():
    block = _headline_block()
    n_cases = AB["test_set"]["n_cases"]
    assert "SYNTHETIC" in block and f"{n_cases} cases" in block
    mis = AB["delta"]["misattributed"]
    assert f"{mis['gate_on']} of {mis['total']} misattributed" in block
    s = SWEEP["summary"]
    assert f"{s['n_completed']} of {s['n_requested']} completed, {s['n_failed']} failed" in block
    assert "gate on only" in block
    # the A/B numbers are never attributed to the sweep
    flat = _flat(SUBMISSION)
    assert not re.search(r"(?:blocked|accepted|fabricated)[^.]{0,120}across the 50-area sweep", flat)


def test_only_a_real_track_is_selected():
    track = re.search(r"\*\*Track:\*\* ([^(·\n]+)", SUBMISSION)
    assert track and track.group(1).strip() in REAL_TRACKS
    for m in re.finditer(r"Clean Energy Track", SUBMISSION):
        assert re.search(r"\bno\s+(?:\*\*)?$", SUBMISSION[max(0, m.start() - 12) : m.start()]), (
            "'Clean Energy Track' may only appear as 'no Clean Energy Track' — the hackathon has none"
        )


def test_tavily_bonus_is_claimed_only_with_its_condition():
    b1 = next(line for line in SUBMISSION.splitlines() if line.startswith("| B1 |"))
    tavily = next(line for line in SUBMISSION.splitlines() if line.startswith("| **Best Use of Tavily"))
    assert "functional runtime call to the Tavily API" in tavily
    if "**TODO**" in b1:  # live run not done yet
        assert "once B1 is done" in tavily


def test_live_demo_and_video_links():
    links = SUBMISSION.split("**Links**", 1)[1].split("\n\n", 1)[0]
    assert PAGES_URL in links
    video = next(line for line in links.splitlines() if "**Video:**" in line)
    assert "TODO(B3)" in video or re.search(r"https://(?:www\.youtube\.com/watch\?v=|youtu\.be/)[\w-]{6,}", video)
    b4 = next(line for line in SUBMISSION.splitlines() if line.startswith("| B4 |"))
    assert "**Done" in b4 and "actions/runs/" in b4


# ------------------------------------------------------------------------------------------------ feedback


def test_feedback_meets_the_template_targets():
    words = len(re.findall(r"\w+", FEEDBACK))
    urls = set(re.findall(r"https://[^\s)>`\]]+", FEEDBACK))
    assert words >= 400
    assert len(urls) >= 4
    for heading in ("## 1. What worked", "## 5. What I wished existed", "## 6. Non-English", "My fault"):
        assert heading in FEEDBACK
    assert "*Use case:*" in FEEDBACK.split("## 5.", 1)[1]
    assert "TODO(url)" not in FEEDBACK


def test_feedback_does_not_repeat_the_retracted_upload_claim():
    assert "could not find the **REST endpoint" not in FEEDBACK
    assert "/sandboxes/v1/files" in FEEDBACK

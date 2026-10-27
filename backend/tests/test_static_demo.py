"""Static GitHub Pages demo (scripts/build_static_demo.py) and the recorded demo video's artifacts.

The Pages site has no backend: everything it shows was precomputed by the real pipeline. These tests rebuild the
snapshot into a temp dir and check it is complete, schema-valid, SYNTHETIC-labelled, consistent with the committed
sweep, and that the builder refuses to publish an area or an answer it cannot vouch for.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import REPO_ROOT

SCRIPT = REPO_ROOT / "scripts" / "build_static_demo.py"
RUNS = REPO_ROOT / "runs"


def _load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("build_static_demo", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder() -> Any:
    return _load_builder()


@pytest.fixture(scope="module")
def snapshot(builder: Any, tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    out = tmp_path_factory.mktemp("demo")
    index = asyncio.run(builder.build(out))
    return out, index


def _answer(out: Path, pc4: str, direction: str) -> dict[str, Any]:
    return json.loads((out / "answers" / f"{pc4}.{direction}.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------- snapshot content


def test_snapshot_has_every_sweep_area_plus_the_video_areas_in_both_directions(snapshot):
    out, index = snapshot
    sweep = json.loads((RUNS / "sweep_summary.json").read_text(encoding="utf-8"))
    sweep_pcs = [a["postcode4"] for a in sweep["areas"]]
    pcs = [a["postcode4"] for a in index["areas"]]
    assert pcs[: len(sweep_pcs)] == sweep_pcs
    assert set(pcs) == set(sweep_pcs) | {"5612", "3011"}
    assert "1012" in sweep_pcs  # the README's third example is a sweep area
    assert {a["postcode4"] for a in index["areas"] if a["source"] == "video_demo"} == {"5612", "3011"}
    files = sorted(p.name for p in (out / "answers").iterdir())
    assert len(files) == len(pcs) * 2 == 104
    assert files == sorted(f"{pc}.{d}.json" for pc in pcs for d in ("feed_in", "consumption"))


def test_every_answer_is_a_valid_synthetic_query_response_at_the_snapshot_power(snapshot, validator_for):
    out, index = snapshot
    validator = validator_for("QueryResponse")
    assert index["synthetic"] is True and index["mode"] == "fixture" and index["power_kw"] == 60.0
    for area in index["areas"]:
        for direction in ("feed_in", "consumption"):
            qr = _answer(out, area["postcode4"], direction)
            validator.validate(qr)
            assert qr["retrieval"]["synthetic"] is True
            assert qr["retrieval"]["tavily_calls"] == 0  # precomputed offline: never claims a live call
            assert qr["answer"]["request"]["requested"] == [{"kind": "other", "kw": 60.0, "direction": direction}]
            assert qr["answer"]["per_direction"][0]["direction"] == direction
            assert area["verdicts"][direction] == qr["answer"]["per_direction"][0]["verdict"]


def test_the_video_beats_are_in_the_snapshot(snapshot):
    out, _ = snapshot
    feed = _answer(out, "5612", "feed_in")["answer"]
    cons = _answer(out, "5612", "consumption")["answer"]
    f, c = feed["per_direction"][0], cons["per_direction"][0]
    assert f["verdict"] == "WAITLIST_ONLY"
    assert f["indicative_earliest_date"] == "2028-Q3"
    assert f["binding_chip"] == "NON_BINDING"
    assert f["position_claim"]["binding"] == "non_binding"
    assert c["verdict"] == "CAPACITY_AVAILABLE" and c["available_capacity_kw"] == 250
    assert any(o["kind"] == "non_firm_connection" for o in feed["options_ranked"])
    for direction in ("feed_in", "consumption"):
        refusal = _answer(out, "3011", direction)["answer"]["per_direction"][0]
        assert refusal["verdict"] == "NO_OFFICIAL_POSITION_FOUND"
        assert refusal["indicative_earliest_date"] is None


def test_snapshot_agrees_with_the_committed_sweep(snapshot):
    """Same pipeline, same fixtures, same power: the Pages demo must show what runs/sweep_summary.json reports."""
    out, _ = snapshot
    sweep = json.loads((RUNS / "sweep_summary.json").read_text(encoding="utf-8"))
    for area in sweep["areas"]:
        for direction, rec in area["directions"].items():
            d = _answer(out, area["postcode4"], direction)["answer"]["per_direction"][0]
            assert d["verdict"] == rec["verdict"], (area["postcode4"], direction)
            assert d["indicative_earliest_date"] == rec["indicative_date"], (area["postcode4"], direction)


def test_ab_and_sweep_results_are_bundled_unchanged(snapshot):
    out, _ = snapshot
    for name in ("ab_experiment_results.json", "sweep_summary.json"):
        assert (out / name).read_bytes() == (RUNS / name).read_bytes()


# ---------------------------------------------------------------------------------------------- failure paths


def test_an_extra_area_without_an_operator_is_refused(builder, monkeypatch, tmp_path):
    monkeypatch.setattr(builder, "EXTRA_AREAS", (("9999", "not mapped"),))
    with pytest.raises(SystemExit, match="9999 does not resolve"):
        asyncio.run(builder.build(tmp_path / "demo"))


def test_an_invalid_answer_is_not_published(builder, monkeypatch, tmp_path):
    real = builder.answer_query

    async def broken(**kwargs: Any) -> dict[str, Any]:
        qr = await real(**kwargs)
        qr["answer"]["per_direction"][0]["verdict"] = "PROBABLY_FINE"
        return qr

    monkeypatch.setattr(builder, "answer_query", broken)
    with pytest.raises(SystemExit, match="QueryResponse invalid"):
        asyncio.run(builder.build(tmp_path / "demo"))


def test_a_non_synthetic_answer_is_not_published_as_the_demo(builder, monkeypatch, tmp_path):
    real = builder.answer_query

    async def live_looking(**kwargs: Any) -> dict[str, Any]:
        qr = await real(**kwargs)
        qr["retrieval"]["synthetic"] = False
        return qr

    monkeypatch.setattr(builder, "answer_query", live_looking)
    with pytest.raises(SystemExit, match="expected a SYNTHETIC"):
        asyncio.run(builder.build(tmp_path / "demo"))


# ---------------------------------------------------------------------------------------------- Pages wiring


def test_pages_build_uses_the_repo_base_and_static_mode_only_in_pages_mode():
    vite = (REPO_ROOT / "frontend" / "vite.config.ts").read_text(encoding="utf-8")
    assert 'PAGES_BASE = "/gridqueue-grid-connection/"' in vite
    assert 'base: mode === "pages" ? PAGES_BASE : "/"' in vite
    env = (REPO_ROOT / "frontend" / ".env.pages").read_text(encoding="utf-8")
    assert re.search(r"^VITE_STATIC_DEMO=true$", env, re.M)
    data = (REPO_ROOT / "frontend" / "src" / "data.ts").read_text(encoding="utf-8")
    assert 'import.meta.env.VITE_STATIC_DEMO === "true"' in data
    assert "demo/answers/${pc4}.${req.direction}.json" in data


def test_make_target_and_workflow_build_and_deploy_the_static_site():
    make = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    target = "build-pages: require-uv\n\tcd $(BACKEND) && $(UV) run python ../scripts/build_static_demo.py\n"
    assert target in make
    assert "npm run build -- --mode pages" in make
    workflow = (REPO_ROOT / "docs" / "ci" / "deploy-pages.yml").read_text(encoding="utf-8")
    assert "branches: [main]" in workflow
    assert "run: make build-pages" in workflow
    assert "path: frontend/dist" in workflow
    assert "actions/deploy-pages@" in workflow and "pages: write" in workflow and "id-token: write" in workflow
    live = REPO_ROOT / ".github" / "workflows" / "deploy-pages.yml"
    if live.exists():  # the canonical copy, when the token could push it, must not drift from the mirror
        strip = lambda s: "\n".join(line for line in s.splitlines() if not line.startswith("#"))  # noqa: E731
        assert strip(live.read_text(encoding="utf-8")) == strip(workflow)


# ---------------------------------------------------------------------------------------------- demo video


def _script_shots() -> list[dict[str, str]]:
    md = (REPO_ROOT / "video" / "script.md").read_text(encoding="utf-8")
    section = md[md.index("## Shot list") : md.index("## Swaps allowed")]
    rows = [line.split("|")[1:-1] for line in section.splitlines() if re.match(r"^\| S\d\d \|", line)]
    return [{"id": r[0].strip(), "vo": r[6].strip()} for r in rows]


def test_recorder_voices_every_shot_exactly_once_and_the_clips_exist():
    ts = (REPO_ROOT / "scripts" / "record-demo.ts").read_text(encoding="utf-8")
    block = ts[ts.index("const VOICEOVER: VoiceSegment[] = [") : ts.index("];", ts.index("const VOICEOVER"))]
    voiced = re.findall(r'"(S\d\d)"', block.split("shots:", 1)[0] + "".join(re.findall(r"shots: \[([^\]]*)\]", block)))
    assert sorted(voiced) == [s["id"] for s in _script_shots()]
    for clip in set(re.findall(r'file: "([^"]+\.mp3)"', block)):
        assert (REPO_ROOT / "video" / "voiceover" / clip).stat().st_size > 10_000


MEDIA = REPO_ROOT / "docs" / "media"


@pytest.mark.skipif(not (MEDIA / "gridqueue-demo.timeline.json").exists(), reason="video not recorded yet")
def test_recorded_video_matches_the_locked_script():
    timeline = json.loads((MEDIA / "gridqueue-demo.timeline.json").read_text(encoding="utf-8"))
    assert timeline["runtime_s"] == 170
    assert [s["id"] for s in timeline["shots"]] == [s["id"] for s in _script_shots()]
    assert all(-0.05 < s["late"] < 0.25 for s in timeline["shots"])  # each shot started on its timecode
    for name in ("mp4", "webm"):
        out = timeline["outputs"][name]
        assert abs(out["duration"] - 170) <= 0.1
        assert (out["width"], out["height"]) == (1920, 1080)
        assert (MEDIA / f"gridqueue-demo.{name}").stat().st_size == out["bytes"]
    assert "8 passed" in timeline["s09_pytest_summary"]


@pytest.mark.skipif(not (MEDIA / "gridqueue-demo.vtt").exists(), reason="video not recorded yet")
def test_captions_are_the_script_narration_word_for_word():
    vtt = (MEDIA / "gridqueue-demo.vtt").read_text(encoding="utf-8")
    assert vtt.startswith("WEBVTT")
    cues = re.findall(r"\d\d:\d\d:\d\d\.\d{3} --> (\d\d:\d\d:\d\d\.\d{3})\n(.+)", vtt)
    assert cues and all(end <= "00:02:50.000" for end, _ in cues)
    words = lambda s: re.findall(r"[\w']+", s.lower())  # noqa: E731
    assert words(" ".join(t for _, t in cues)) == words(" ".join(s["vo"] for s in _script_shots()))

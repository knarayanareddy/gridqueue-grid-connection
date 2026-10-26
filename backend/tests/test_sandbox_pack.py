"""app/sandbox/pack.py — offline application pack (C-T21/C-T22): hash verification, network-off, withholding."""

import ast
import asyncio
import copy
import hashlib
import json
import socket
import sys
import time

import pytest

from app.pipeline import Services, query_response, run_stages
from app.sandbox import pack as pack_mod
from app.sandbox.pack import (
    NetworkEnabledError,
    PackVerificationError,
    assert_network_disabled,
    build_pack,
    make_bundle,
    verify_bundle,
)
from app.stages.s3_extract import ReplayExtractor
from app.stages.s5_answer import AssembleAnswer
from tests.conftest import REPO_ROOT


def _bundle(postcode: str, direction: str, kw: float = 60) -> dict:
    async def go():
        services = Services(mode="fixture", tavily=None, extractor=ReplayExtractor())
        ctx = await run_stages(postcode=postcode, power_kw=kw, direction=direction, services=services, run_id="pk")
        return make_bundle(query_response(ctx, AssembleAnswer().build(ctx, time.perf_counter())), ctx.doc_texts)

    return asyncio.run(go())


@pytest.fixture(scope="module")
def feed_in_bundle():
    return _bundle("5612 AB", "feed_in")


@pytest.fixture(scope="module")
def consumption_bundle():
    return _bundle("5612", "consumption")


@pytest.fixture
def no_network(monkeypatch):
    """Any attempt to open a connection or resolve a name fails, as in a Sandbox with networking disabled."""

    def blocked(*a, **k):
        raise OSError("network disabled in test")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)


@pytest.fixture
def only_loopback(tmp_path):
    d = tmp_path / "net"
    (d / "lo").mkdir(parents=True)
    return d


# ------------------------------------------------------------------------------------------------ happy path


def test_pack_bytes_and_sha256_are_verifiable_and_deterministic(feed_in_bundle, no_network):
    result = build_pack(feed_in_bundle)
    assert result.sha256 == hashlib.sha256(result.content).hexdigest() == result.manifest["sha256"]
    assert result.manifest["bytes"] == len(result.content)
    # Same bundle after a JSON round trip (= shipped into the Sandbox) → identical bytes
    shipped = json.loads(json.dumps(feed_in_bundle))
    assert build_pack(shipped).content == result.content


def test_pack_contains_application_block_and_verified_values(feed_in_bundle):
    result = build_pack(feed_in_bundle)
    text = result.content.decode("utf-8")
    assert "## Application block — Enexis" in text
    assert "Non-firm connection" in text and "Congestion management participation" in text
    assert "Q3 2028" in text and "Non-binding forecast" in text
    assert "SYNTHETIC" in text  # fixture-backed packs say so
    kinds = {(v["kind"], v["value"]) for v in result.manifest["values_verified"]}
    assert {("date", "2028-Q3"), ("binding", "non_binding"), ("option_kw", 60)} <= kinds
    doc_sha = feed_in_bundle["query_response"]["documents"][0]["sha256"]
    assert all(v["document_sha256"] == doc_sha for v in result.manifest["values_verified"])


def test_only_verified_citations_are_injected(feed_in_bundle):
    result = build_pack(feed_in_bundle)
    text = result.content.decode("utf-8")
    qr = feed_in_bundle["query_response"]
    included = result.manifest["citations_included"]
    assert included and all(c.startswith("cit_") for c in included)
    by_id = {c["id"]: c for c in qr["citations"]}
    assert all(by_id[c]["kind"] == "source_document" for c in included)
    # the unverified postcode-table citation is excluded and listed as such
    assert {"id": "cit_geo_enexis", "reason": "not_source_evidence"} in result.manifest["citations_excluded"]
    sources = text.split("## Sources (verified offline)")[1].split("## Verification")[0]
    assert "| cit_geo_enexis |" not in sources


def test_consumption_kw_is_verified(consumption_bundle):
    result = build_pack(consumption_bundle)
    assert ("kw", 250) in {(v["kind"], v["value"]) for v in result.manifest["values_verified"]}


def test_no_position_pack_still_renders_phone_script():
    result = build_pack(_bundle("3011", "feed_in"))
    text = result.content.decode("utf-8")
    assert "No official position found" in text and "## Phone script (nl)" in text and "3011" in text


def test_answer_artifact_is_not_claimed(feed_in_bundle):
    # The schema demands generated_in_sandbox=true; nothing here ran in a Sandbox, so it must stay null.
    assert feed_in_bundle["query_response"]["answer"]["artifact"] is None


# ------------------------------------------------------------------------------------------------ network-off


def test_network_boundary_check_follows_sys_class_net(tmp_path, only_loopback):
    info = assert_network_disabled(only_loopback)
    assert info == {"checked": True, "method": "sys_class_net", "interfaces": ["lo"], "network_disabled": True}
    (only_loopback / "eth0").mkdir()
    with pytest.raises(NetworkEnabledError, match="eth0"):
        assert_network_disabled(only_loopback)
    with pytest.raises(NetworkEnabledError):
        assert_network_disabled(tmp_path / "missing")


def test_cli_runs_with_network_disabled(tmp_path, feed_in_bundle, no_network, only_loopback):
    bundle_path, out, manifest = tmp_path / "bundle.json", tmp_path / "pack.md", tmp_path / "manifest.json"
    bundle_path.write_text(json.dumps(feed_in_bundle), encoding="utf-8")
    rc = pack_mod.main(
        [
            "--bundle",
            str(bundle_path),
            "--out",
            str(out),
            "--manifest",
            str(manifest),
            "--require-network-off",
            "--sys-class-net",
            str(only_loopback),
        ]
    )
    assert rc == 0
    m = json.loads(manifest.read_text())
    assert m["network"]["network_disabled"] is True
    assert hashlib.sha256(out.read_bytes()).hexdigest() == m["sha256"]


def test_cli_refuses_when_network_present(tmp_path, feed_in_bundle, only_loopback):
    (only_loopback / "eth0").mkdir()
    bundle_path, out = tmp_path / "bundle.json", tmp_path / "pack.md"
    bundle_path.write_text(json.dumps(feed_in_bundle), encoding="utf-8")
    rc = pack_mod.main(
        [
            "--bundle",
            str(bundle_path),
            "--out",
            str(out),
            "--require-network-off",
            "--sys-class-net",
            str(only_loopback),
        ]
    )
    assert rc == 3 and not out.exists()


def test_pack_module_imports_only_stdlib_and_the_gate():
    """The guest needs no network-capable dependency: stdlib + app.gate.gate (itself stdlib-only)."""
    allowed_first_party = {"app.gate.gate"}
    for path in (REPO_ROOT / "backend/app/sandbox/pack.py", REPO_ROOT / "backend/app/gate/gate.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                assert top in sys.stdlib_module_names or top == "__future__" or name in allowed_first_party, (
                    f"{path.name} imports {name}"
                )


# ------------------------------------------------------------------------------------------------ withheld


def _expect_withheld(bundle: dict, reason: str) -> list:
    with pytest.raises(PackVerificationError) as exc:
        build_pack(bundle)
    assert reason in {f["reason"] for f in exc.value.failures}, exc.value.failures
    return exc.value.failures


def test_tampered_document_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    doc_id = next(iter(b["texts"]))
    b["texts"][doc_id] = b["texts"][doc_id].replace("2028", "2027")
    report = verify_bundle(b)
    assert report["documents"][doc_id]["reason"] == "sha256_mismatch"
    _expect_withheld(b, "claim_quote_unverified")


def test_missing_document_text_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    b["texts"] = {}
    _expect_withheld(b, "claim_quote_unverified")


def test_injected_unsupported_date_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    dr = b["query_response"]["answer"]["per_direction"][0]
    dr["indicative_earliest_date"] = dr["position_claim"]["indicative_earliest_date"] = "2027-Q1"
    _expect_withheld(b, "date_unverified")


def test_date_that_differs_from_claim_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    b["query_response"]["answer"]["per_direction"][0]["indicative_earliest_date"] = "2028-Q2"
    _expect_withheld(b, "date_unverified")


def test_injected_kw_withholds_pack(consumption_bundle):
    b = copy.deepcopy(consumption_bundle)
    b["query_response"]["answer"]["per_direction"][0]["available_capacity_kw"] = 2500
    _expect_withheld(b, "kw_unverified")


def test_injected_option_kw_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    opt = next(o for o in b["query_response"]["answer"]["options_ranked"] if o["kind"] == "non_firm_connection")
    opt["estimated_kw_enabled"] = 80
    _expect_withheld(b, "option_kw_unverified")


def test_altered_citation_hash_excludes_citation_and_withholds(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    claim = b["query_response"]["answer"]["per_direction"][0]["position_claim"]
    cit = next(c for c in b["query_response"]["citations"] if c["id"] == claim["citation_id"])
    cit["sha256"] = "0" * 64
    assert verify_bundle(b)["citations"][cit["id"]]["reason"] == "citation_sha256_mismatch"
    _expect_withheld(b, "claim_quote_unverified")


def test_fabricated_route_withholds_pack(feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    b["query_response"]["answer"]["options_ranked"][0]["application_route"] = "Bel ons en u krijgt direct capaciteit."
    _expect_withheld(b, "route_unverified")


def test_cli_returns_2_and_writes_nothing_when_withheld(tmp_path, feed_in_bundle):
    b = copy.deepcopy(feed_in_bundle)
    b["query_response"]["answer"]["per_direction"][0]["indicative_earliest_date"] = "2027-Q1"
    bundle_path, out = tmp_path / "bundle.json", tmp_path / "pack.md"
    bundle_path.write_text(json.dumps(b), encoding="utf-8")
    assert pack_mod.main(["--bundle", str(bundle_path), "--out", str(out)]) == 2
    assert not out.exists()

"""POST /v1/answer — end to end, offline.

Every response is validated against schemas/core-schemas.json#/$defs/QueryResponse. Fixture-mode tests use
the SYNTHETIC documents in data/fixtures/synthetic/; live-mode tests use an httpx.MockTransport for Tavily
and a stub model client, so the real S2/S3/S5 code runs without network or keys.
"""

import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.gate.gate import normalise
from app.main import app, service_factory
from app.pipeline import Services, choose_mode
from app.stages.s3_extract import LiveExtractor, ReplayExtractor
from app.tools.tavily import TavilyClient
from tests.conftest import REPO_ROOT

ENEXIS_TEXT = (REPO_ROOT / "data/fixtures/synthetic/documents/enexis_eindhoven.txt").read_text(encoding="utf-8")
LIVE_URL = "https://www.enexis.nl/zakelijk/netcapaciteit/eindhoven"


@pytest.fixture
def qr_validator(validator_for):
    return validator_for("QueryResponse")


def _client(services_factory, tmp_path) -> TestClient:
    cfg = Settings(_env_file=None, runs_dir=tmp_path)

    def override():
        return services_factory(), "testrun0000000001", cfg

    app.dependency_overrides[service_factory] = override
    return TestClient(app)


@pytest.fixture
def fixture_client(tmp_path):
    yield _client(lambda: Services(mode="fixture", tavily=None, extractor=ReplayExtractor()), tmp_path)
    app.dependency_overrides.clear()


def _post(client, qr_validator, postcode, kw=60, direction="feed_in"):
    r = client.post("/v1/answer", json={"postcode": postcode, "power_kw": kw, "direction": direction})
    assert r.status_code == 200, r.text
    body = r.json()
    errors = [f"{list(e.absolute_path)}: {e.message}" for e in qr_validator.iter_errors(body)]
    assert errors == [], errors
    return body


def _dir(body):
    return body["answer"]["per_direction"][0]


# --------------------------------------------------------------------------- fixture mode (SYNTHETIC)


def test_eindhoven_feed_in_waitlist_with_gated_nonbinding_date(fixture_client, qr_validator):
    body = _post(fixture_client, qr_validator, "5612 AB")
    d = _dir(body)
    assert d["verdict"] == "WAITLIST_ONLY"
    assert d["indicative_earliest_date"] == "2028-Q3"
    assert d["binding_chip"] == "NON_BINDING"
    claim = d["position_claim"]
    assert claim["verbatim_quote"] in ENEXIS_TEXT and "2028" in claim["verbatim_quote"]
    assert claim["publication_date"] == "2026-07-14"
    assert {"indicatief", "niet bindend", "kan wijzigen"} <= set(claim["non_binding_markers_found"])
    # the claim's citation is present and points at the retrieved document
    cits = {c["id"]: c for c in body["citations"]}
    assert cits[claim["citation_id"]]["document_id"] == claim["document_id"]
    assert body["retrieval"]["synthetic"] is True and "SYNTHETIC" in body["answer"]["disclaimer"]
    assert body["answer"]["gate"]["llm_calls_in_gate"] == 0
    assert body["answer"]["gate"]["rejected_claims"] == []


def test_options_are_gated_and_ranked_deterministically(fixture_client, qr_validator):
    opts = _post(fixture_client, qr_validator, "5612", kw=60)["answer"]["options_ranked"]
    assert [o["kind"] for o in opts] == [
        "non_firm_connection",  # states 60 kW >= requested 60 kW → first
        "flex_transport_agreement",
        "congestion_management_participation",
    ]
    assert [o["rank"] for o in opts] == [1, 2, 3]
    assert opts[0]["estimated_kw_enabled"] == 60
    assert all(normalise(o["application_route"]) in normalise(ENEXIS_TEXT) for o in opts)
    # above the stated 60 kW, the non-firm option no longer covers the request; kW still sorts it first
    opts_big = _post(fixture_client, qr_validator, "5612", kw=500)["answer"]["options_ranked"]
    assert opts_big[0]["kind"] == "non_firm_connection"


def test_eindhoven_consumption_capacity_and_partial(fixture_client, qr_validator):
    d = _dir(_post(fixture_client, qr_validator, "5612", kw=100, direction="consumption"))
    assert d["verdict"] == "CAPACITY_AVAILABLE" and d["available_capacity_kw"] == 250
    assert d["binding_chip"] == "NOT_APPLICABLE" and d["indicative_earliest_date"] is None
    d = _dir(_post(fixture_client, qr_validator, "5612", kw=400, direction="consumption"))
    assert d["verdict"] == "PARTIAL_CAPACITY"


def test_invented_date_and_fabrications_rejected_by_gate(fixture_client, qr_validator):
    """Liander replay invents 2027-Q2, a binding quote, 500 kW, a whole claim and a route. All must go."""
    body = _post(fixture_client, qr_validator, "1012")
    d, gate = _dir(body), body["answer"]["gate"]
    assert d["verdict"] == "WAITLIST_ONLY"  # the one verbatim statement survives
    assert d["indicative_earliest_date"] is None and d["position_claim"]["indicative_earliest_date"] is None
    assert d["position_claim"]["binding"] == "unknown" and d["available_capacity_kw"] is None
    assert d["binding_chip"] == "NOT_APPLICABLE"
    reasons = sorted(r["reason"] for r in gate["rejected_claims"])
    assert reasons == sorted(
        [
            "date_without_document",
            "binding_not_stated",
            "kw_without_quote",
            "quote_not_found_in_document",
            "option_without_route",
        ]
    )
    assert gate["dates_surviving"] == 0 and gate["dates_dropped"] == 2
    assert "2027" not in json.dumps(body["answer"]["per_direction"])
    assert [o["kind"] for o in body["answer"]["options_ranked"]] == ["congestion_management_participation"]


def test_rotterdam_no_document_gives_no_official_position(fixture_client, qr_validator):
    body = _post(fixture_client, qr_validator, "3011")
    d = _dir(body)
    assert d["verdict"] == "NO_OFFICIAL_POSITION_FOUND"
    assert d["position_claim"] is None and d["indicative_earliest_date"] is None
    assert [a["reason"] for a in d["abstentions"]] == ["no_position_found"]
    assert "Stedin" in d["phone_script"]["text_nl"] or d["phone_script"]["dso"] == "Stedin"
    assert "3011" in d["phone_script"]["text_nl"] and "teruglevering" in d["phone_script"]["text_nl"]
    assert body["answer"]["options_ranked"] == []


@pytest.mark.parametrize("postcode", ["9999", "abcd"])
def test_unmapped_or_malformed_postcode_abstains(fixture_client, qr_validator, postcode):
    body = _post(fixture_client, qr_validator, postcode)
    d = _dir(body)
    assert d["verdict"] == "NO_OFFICIAL_POSITION_FOUND"
    assert d["abstentions"][0]["reason"] == "unmapped_postcode"
    assert body["documents"] == [] and body["retrieval"]["extraction"] == "not_run"


@pytest.mark.parametrize(
    "payload",
    [
        {"postcode": "5612", "power_kw": 60, "direction": "both"},
        {"postcode": "5612", "power_kw": 0, "direction": "feed_in"},
        {"postcode": "5612", "power_kw": -5, "direction": "feed_in"},
        {"postcode": "5612", "direction": "feed_in"},
        {"postcode": "56", "power_kw": 60, "direction": "feed_in"},
    ],
)
def test_bad_input_is_422(fixture_client, payload):
    assert fixture_client.post("/v1/answer", json=payload).status_code == 422


def test_determinism_hash_stable(fixture_client, qr_validator):
    a = _post(fixture_client, qr_validator, "5612 AB")["answer"]["gate"]["determinism_hash"]
    b = _post(fixture_client, qr_validator, "5612 AB")["answer"]["gate"]["determinism_hash"]
    c = _post(fixture_client, qr_validator, "5612 AB", direction="consumption")["answer"]["gate"]["determinism_hash"]
    assert a == b and a != c


def test_mode_selection_needs_both_keys(tmp_path):
    assert choose_mode(Settings(_env_file=None, nebius_api_key=None, tavily_api_key=None)) == "fixture"
    assert choose_mode(Settings(_env_file=None, nebius_api_key="n", tavily_api_key=None)) == "fixture"
    assert choose_mode(Settings(_env_file=None, nebius_api_key="n", tavily_api_key="t")) == "live"
    assert (
        choose_mode(Settings(_env_file=None, nebius_api_key="n", tavily_api_key="t", mock_external_calls=True))
        == "fixture"
    )


# --------------------------------------------------------------------------- live mode (mocked network)


def _tavily_transport(*, fail_status: int | None = None, calls: list | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if calls is not None:
            calls.append((request.url.path, body))
        if fail_status:
            return httpx.Response(fail_status, json={"detail": {"error": "Unauthorized"}})
        if request.url.path == "/search":
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"url": LIVE_URL, "title": "Netcapaciteit Eindhoven", "score": 0.9},
                        {"url": "https://blog.example.com/enexis-congestie", "title": "blog", "score": 0.95},
                    ]
                },
            )
        return httpx.Response(
            200, json={"results": [{"url": u, "raw_content": ENEXIS_TEXT} for u in body["urls"]], "failed_results": []}
        )

    return httpx.MockTransport(handler)


class FakeExtractor:
    """Stands in for Nemotron Ultra. Returns whatever proposals the test gives it."""

    kind = "live_model"
    model = "fake/test-model"

    def __init__(self, claims, options=()):
        self._claims, self._options = claims, list(options)
        self.called = 0

    async def extract(self, ctx):
        self.called += 1
        doc_id = ctx.documents[0]["document_id"]
        return {
            "claims": [{**c, "document_id": doc_id} for c in self._claims],
            "options": [{**o, "document_id": doc_id} for o in self._options],
        }


def _claim(**over):
    base = {
        "verbatim_quote": "De indicatieve datum waarop weer productiecapaciteit beschikbaar komt is het derde kwartaal "
        "van 2028.",
        "page_or_row": None,
        "congestion_registered": True,
        "queue_status": "WAITLIST",
        "indicative_earliest_date": "2028-Q3",
        "binding": "non_binding",
        "binding_evidence_quote": "Deze codeerprognose is indicatief en niet bindend; de datum kan wijzigen.",
        "available_capacity_kw": None,
        "capacity_basis_quote": None,
        "publication_date": "2026-07-14",
        "publication_date_quote": "Versie 3, gepubliceerd op 14 juli 2026.",
        "confidence": 0.8,
    }
    return {**base, **over}


def _live_client(tmp_path, extractor, **transport_kw):
    def make():
        tav = TavilyClient(
            "tvly-test", transport=_tavily_transport(**transport_kw), runs_dir=tmp_path, run_id="testrun0000000001"
        )
        return Services(mode="live", tavily=tav, extractor=extractor)

    return _client(make, tmp_path)


def test_live_path_retrieves_official_domain_only_and_gates(tmp_path, qr_validator):
    calls: list = []
    client = _live_client(tmp_path, FakeExtractor([_claim()]), calls=calls)
    try:
        body = _post(client, qr_validator, "5612 AB")
    finally:
        app.dependency_overrides.clear()
    ret = body["retrieval"]
    assert ret["mode"] == "live" and ret["synthetic"] is False and ret["extraction"] == "live_model"
    assert ret["tavily_calls"] == 3  # 2 searches + 1 extract
    assert [p for p, _ in calls] == ["/search", "/search", "/extract"]
    assert calls[0][1]["include_domains"] == ["enexis.nl"]
    assert calls[2][1]["urls"] == [LIVE_URL]
    assert {"url": "https://blog.example.com/enexis-congestie", "reason": "not_official_domain"} in ret[
        "results_rejected"
    ]
    assert [d["url"] for d in body["documents"]] == [LIVE_URL]
    assert body["documents"][0]["direction_split_available"] is True
    d = _dir(body)
    assert d["verdict"] == "WAITLIST_ONLY" and d["indicative_earliest_date"] == "2028-Q3"
    assert "SYNTHETIC" not in body["answer"]["disclaimer"]
    ledger = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert [x["kind"] for x in ledger] == ["tavily.search", "tavily.search", "tavily.extract"]


def test_live_invented_date_is_dropped(tmp_path, qr_validator):
    """Model asserts a date the quote doesn't contain → date removed, claim (verbatim) kept."""
    client = _live_client(tmp_path, FakeExtractor([_claim(indicative_earliest_date="2027-Q1")]))
    try:
        body = _post(client, qr_validator, "5612")
    finally:
        app.dependency_overrides.clear()
    d = _dir(body)
    assert d["indicative_earliest_date"] is None and d["binding_chip"] == "NOT_APPLICABLE"
    assert any(r["reason"] == "date_without_document" for r in body["answer"]["gate"]["rejected_claims"])
    assert "2027" not in json.dumps(body["answer"]["per_direction"])


def test_live_paraphrased_quote_gives_no_official_position(tmp_path, qr_validator):
    paraphrase = _claim(verbatim_quote="Capaciteit is naar verwachting in Q3 2028 weer beschikbaar.")
    client = _live_client(tmp_path, FakeExtractor([paraphrase]))
    try:
        body = _post(client, qr_validator, "5612")
    finally:
        app.dependency_overrides.clear()
    d = _dir(body)
    assert d["verdict"] == "NO_OFFICIAL_POSITION_FOUND" and d["position_claim"] is None
    assert body["answer"]["gate"]["rejected_claims"][0]["reason"] == "quote_not_found_in_document"


def test_live_tavily_failure_abstains_without_fixture_fallback(tmp_path, qr_validator):
    extractor = FakeExtractor([_claim()])
    client = _live_client(tmp_path, extractor, fail_status=401)
    try:
        body = _post(client, qr_validator, "5612")
    finally:
        app.dependency_overrides.clear()
    d = _dir(body)
    assert d["verdict"] == "NO_OFFICIAL_POSITION_FOUND"
    assert [a["reason"] for a in d["abstentions"]] == ["tavily_unavailable"]
    assert body["documents"] == [] and body["retrieval"]["synthetic"] is False
    assert extractor.called == 0  # nothing retrieved → no model call


def test_live_extractor_calls_token_factory_shape_and_ledgers(tmp_path, qr_validator, validator_for):
    """The real LiveExtractor with a stub OpenAI client: request shape, strict schema, ledger + tokens."""
    seen = {}

    class StubCompletions:
        async def create(self, **kw):
            seen.update(kw)
            content = json.dumps({"claims": [{**_claim(), "document_id": DOC_ID[0]}], "options": []})
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content), finish_reason="stop")],
                usage=SimpleNamespace(
                    prompt_tokens=1200, completion_tokens=150, prompt_tokens_details=SimpleNamespace(cached_tokens=200)
                ),
            )

    DOC_ID = [None]
    stub = SimpleNamespace(chat=SimpleNamespace(completions=StubCompletions()))
    extractor = LiveExtractor(Settings(_env_file=None, nebius_api_key="n"), client=stub)

    real_extract = extractor.extract

    async def capture(ctx):
        DOC_ID[0] = ctx.documents[0]["document_id"]
        return await real_extract(ctx)

    extractor.extract = capture  # type: ignore[method-assign]
    client = _live_client(tmp_path, extractor)
    try:
        body = _post(client, qr_validator, "5612")
    finally:
        app.dependency_overrides.clear()

    assert seen["model"] == Settings(_env_file=None).model_ultra
    assert seen["temperature"] == 0
    assert seen["response_format"]["type"] == "json_schema"
    assert seen["response_format"]["json_schema"]["name"] == "gridqueue_extraction"
    assert "teruglevering" in seen["messages"][0]["content"]
    assert ENEXIS_TEXT[:60] in seen["messages"][1]["content"]
    assert _dir(body)["indicative_earliest_date"] == "2028-Q3"
    assert body["answer"]["cost"]["text_tokens"] == 1350 and body["answer"]["cost"]["cached_tokens"] == 200
    ledger = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    llm = [x for x in ledger if x["kind"] == "chat.completions"]
    assert len(llm) == 1 and llm[0]["stage"] == "s3_extract" and llm[0]["status"] == "ok"
    assert not list(validator_for("LedgerLine").iter_errors(llm[0]))
    assert _dir(body)["position_claim"]["ledger_id"] == llm[0]["id"]


def test_live_extractor_invalid_output_abstains(tmp_path, qr_validator):
    class Garbage:
        async def create(self, **kw):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Q3 2028, probably"), finish_reason="stop")],
                usage=None,
            )

    stub = SimpleNamespace(chat=SimpleNamespace(completions=Garbage()))
    extractor = LiveExtractor(Settings(_env_file=None, nebius_api_key="n"), client=stub)
    client = _live_client(tmp_path, extractor)
    try:
        body = _post(client, qr_validator, "5612")
    finally:
        app.dependency_overrides.clear()
    assert _dir(body)["verdict"] == "NO_OFFICIAL_POSITION_FOUND"
    ledger = [json.loads(x) for x in (tmp_path / "ledger.jsonl").read_text().splitlines()]
    assert [x["status"] for x in ledger if x["kind"] == "chat.completions"] == ["schema_violation"]

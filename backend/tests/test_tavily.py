"""tools/tavily.py — request shape, error handling and ledger lines, with httpx.MockTransport (no network)."""

import asyncio
import json

import httpx
import pytest

from app.tools.tavily import TavilyClient, TavilyError, build_queries


def _ledger(tmp_path):
    path = tmp_path / "ledger.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_build_queries_uses_register_dso_direction_and_gemeente():
    qs = build_queries("Enexis", "feed_in", "Eindhoven")
    assert [q.family_id for q in qs] == ["dso_congestion_register", "dso_codeerprognose"]
    for q in qs:
        assert "Enexis" in q.query and "teruglevering" in q.query and q.query.endswith("Eindhoven")
        assert "netbeheerder" not in q.query
    assert all("afname" in q.query for q in build_queries("Stedin", "consumption"))
    with pytest.raises(ValueError):
        build_queries("Enexis", "both")


def test_search_request_shape_and_ledger(tmp_path, validator_for):
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200, json={"results": [{"url": "https://www.enexis.nl/a", "score": 0.9}], "usage": {"credits": 1}}
        )

    client = TavilyClient("tvly-test", transport=httpx.MockTransport(handler), runs_dir=tmp_path, run_id="r1")
    out = asyncio.run(client.search("Enexis congestie", include_domains=["enexis.nl"]))
    assert out["results"][0]["url"] == "https://www.enexis.nl/a"
    assert seen["url"] == "https://api.tavily.com/search"
    assert seen["auth"] == "Bearer tvly-test"
    body = seen["body"]
    assert body["query"] == "Enexis congestie" and body["include_domains"] == ["enexis.nl"]
    assert body["search_depth"] == "basic" and body["topic"] == "general" and body["country"] == "netherlands"
    assert body["include_usage"] is True
    lines = _ledger(tmp_path)
    assert len(lines) == 1 and client.calls == 1 and client.ledger_ids == [lines[0]["id"]]
    assert lines[0]["kind"] == "tavily.search" and lines[0]["status"] == "ok" and lines[0]["run_id"] == "r1"
    assert "tvly-test" not in json.dumps(lines)
    assert not list(validator_for("LedgerLine").iter_errors(lines[0]))


def test_extract_request_shape(tmp_path):
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"results": [{"url": "u", "raw_content": "tekst"}], "failed_results": []})

    client = TavilyClient("k", transport=httpx.MockTransport(handler), runs_dir=tmp_path)
    asyncio.run(client.extract(["https://www.enexis.nl/a"]))
    assert seen["path"] == "/extract"
    assert seen["body"] == {
        "urls": ["https://www.enexis.nl/a"],
        "extract_depth": "basic",
        "format": "text",
        "include_usage": True,
    }
    assert _ledger(tmp_path)[0]["kind"] == "tavily.extract"


@pytest.mark.parametrize("status", [401, 429, 432, 500])
def test_http_errors_raise_and_are_ledgered(tmp_path, status):
    transport = httpx.MockTransport(lambda r: httpx.Response(status, json={"detail": {"error": "nope"}}))
    client = TavilyClient("k", transport=transport, runs_dir=tmp_path)
    with pytest.raises(TavilyError) as exc:
        asyncio.run(client.search("q"))
    assert exc.value.status_code == status
    line = _ledger(tmp_path)[0]
    assert line["status"] == "error" and str(status) in line["error"]


def test_network_error_becomes_tavily_error(tmp_path):
    def boom(request):
        raise httpx.ConnectError("unreachable")

    client = TavilyClient("k", transport=httpx.MockTransport(boom), runs_dir=tmp_path)
    with pytest.raises(TavilyError):
        asyncio.run(client.search("q"))
    assert _ledger(tmp_path)[0]["status"] == "error"


def test_empty_key_rejected():
    with pytest.raises(ValueError):
        TavilyClient("")

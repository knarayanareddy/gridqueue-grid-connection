"""Smoke tests: the package imports and the API answers. (Guards against the v0 syntax error in app/__init__.py.)"""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_info_lists_models_without_leaking_keys():
    body = client.get("/v1/info").json()
    assert set(body["models"]) == {"ultra", "super", "nano"}
    assert set(body["keys_configured"]) == {"nebius", "tavily"}
    assert "api_key" not in str(body).lower()


def test_settings_read_env_and_have_no_fake_key(monkeypatch, tmp_path):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    s = Settings(_env_file=None)
    assert s.nebius_api_key is None and not s.has_nebius_key

    monkeypatch.setenv("NEBIUS_API_KEY", "abc")
    monkeypatch.setenv("RUNS_DIR", str(tmp_path))
    s = Settings(_env_file=None)
    assert s.has_nebius_key and s.runs_dir == tmp_path
    assert "abc" not in repr(s)

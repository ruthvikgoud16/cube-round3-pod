"""Interview upgrades: auth, request ids, sqlite store, circuit breaker, metrics."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orchestration.auth import is_public_path
from orchestration.clients import CircuitOpen, HttpClient, classify_http, reset_breakers
from orchestration.metrics import Metrics
from orchestration.store import EvidenceConflict, SqliteStore, build_store


@pytest.fixture(autouse=True)
def _reset_breakers():
    reset_breakers()
    yield
    reset_breakers()


def test_public_paths_and_api_key_extract():
    assert is_public_path("/health")
    assert is_public_path("/metrics")
    assert is_public_path("/ready")
    assert not is_public_path("/workflows")
    assert not is_public_path("/intake")


def test_api_key_gate_blocks_without_key(monkeypatch):
    monkeypatch.setenv("ORCH_API_KEY", "secret-demo-key")
    monkeypatch.setenv("STORE_BACKEND", "memory")
    # Rebuild app store/middleware with env — import fresh module pieces via TestClient on api.app
    from orchestration import api as api_mod

    api_mod.STORE = build_store()
    client = TestClient(api_mod.app)
    denied = client.get("/workflows")
    assert denied.status_code == 401
    ok = client.get("/workflows", headers={"X-API-Key": "secret-demo-key"})
    assert ok.status_code == 200
    health = client.get("/health")
    assert health.status_code == 200
    monkeypatch.delenv("ORCH_API_KEY", raising=False)


def test_request_id_echoed(monkeypatch):
    monkeypatch.delenv("ORCH_API_KEY", raising=False)
    monkeypatch.setenv("STORE_BACKEND", "memory")
    from orchestration import api as api_mod

    api_mod.STORE = build_store()
    client = TestClient(api_mod.app)
    resp = client.get("/ready", headers={"X-Request-ID": "interview-demo-1"})
    assert resp.status_code == 200
    assert resp.headers.get("x-request-id") == "interview-demo-1"


def test_sqlite_store_roundtrip_and_immutability(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("OUT_DIR", str(tmp_path))
    monkeypatch.delenv("SEED_DIR", raising=False)
    store = SqliteStore(tmp_path / "t.sqlite3")
    wf = {
        "workflow_id": "WF-org_demo_alpha-UNIT-X",
        "org_id": "org_demo_alpha",
        "subject_id": "UNIT-X",
        "status": "COMPLETED",
        "timestamps": {"updated_at": "2026-10-17T00:00:00Z"},
        "evidence_references": [],
        "overrides": [],
        "errors": [],
        "stage_results": [],
    }
    store.save_workflow(wf)
    assert store.list_workflow_ids() == ["WF-org_demo_alpha-UNIT-X"]
    assert store.load_workflow("WF-org_demo_alpha-UNIT-X")["status"] == "COMPLETED"

    record = {"record_id": "RCV-1", "content_hash": "aaa", "stage": "receiving"}
    store.put_evidence(record)
    store.put_evidence(record)  # identical rewrite is fine
    with pytest.raises(EvidenceConflict):
        store.put_evidence({"record_id": "RCV-1", "content_hash": "bbb", "stage": "receiving"})


def test_circuit_breaker_opens_after_threshold(monkeypatch):
    monkeypatch.setenv("CIRCUIT_FAILURE_THRESHOLD", "2")
    monkeypatch.setenv("CIRCUIT_COOLDOWN_S", "60")
    reset_breakers()
    client = HttpClient({"stage": "prep", "url": "http://127.0.0.1:9", "mode": "http"})
    with pytest.raises(Exception):
        client.run({"workflow_id": "w"}, timeout_s=0.2)
    with pytest.raises(Exception):
        client.run({"workflow_id": "w"}, timeout_s=0.2)
    with pytest.raises(CircuitOpen):
        client.run({"workflow_id": "w"}, timeout_s=0.2)
    snap = client.breaker.snapshot()
    assert snap["open"] is True and snap["failures"] >= 2


def test_schema_refusal_does_not_trip_circuit(monkeypatch):
    """Regression: a 422 with no envelope must stop the stage without opening the breaker."""
    kind, _ = classify_http(422, {"detail": "bad"})
    assert kind == "schema_refusal"

    class FakeResp:
        status_code = 422
        text = '{"detail":"bad"}'

        def json(self):
            return {"detail": "bad"}

    monkeypatch.setenv("CIRCUIT_FAILURE_THRESHOLD", "1")
    reset_breakers()
    client = HttpClient({"stage": "pack", "url": "http://127.0.0.1:8103", "mode": "http"})

    def fake_post(*_a, **_k):
        return FakeResp()

    monkeypatch.setattr("orchestration.clients.httpx.post", fake_post)
    from orchestration.clients import AgentSchemaRefusal

    with pytest.raises(AgentSchemaRefusal):
        client.run({"workflow_id": "w"}, timeout_s=1)
    assert client.breaker.failures == 0
    assert client.breaker.snapshot()["open"] is False


def test_metrics_prometheus_and_json():
    m = Metrics()
    m.inc("workflows_started")
    m.record_agent("receiving", ok=True)
    m.record_agent("prep", ok=False)
    m.record_workflow("COMPLETED", "CLEAN")
    body = m.as_dict()
    assert body["counters"]["workflows_started"] == 1
    assert body["agent_calls"]["receiving"] == 1
    assert body["agent_failures"]["prep"] == 1
    prom = m.as_prometheus()
    assert "cube_agent_calls_total" in prom
    assert 'outcome="CLEAN"' in prom


def test_metrics_endpoint(monkeypatch):
    monkeypatch.delenv("ORCH_API_KEY", raising=False)
    monkeypatch.setenv("STORE_BACKEND", "memory")
    from orchestration import api as api_mod

    api_mod.STORE = build_store()
    client = TestClient(api_mod.app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "counters" in r.json()
    p = client.get("/metrics?format=prometheus")
    assert p.status_code == 200
    assert "cube_orchestrator_info" in p.text

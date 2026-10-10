"""The evidence desk lists stored workflows and serves the page."""

from fastapi.testclient import TestClient

from orchestration.store import FileStore


def test_desk_lists_one_workflow(tmp_path, monkeypatch):
    import orchestration.api as api

    api.STORE = FileStore(tmp_path)
    api.STORE.save_workflow(
        {
            "workflow_id": "WF-DESK-1",
            "status": "COMPLETED",
            "stage_results": [],
            "evidence_references": [],
            "final_outcome": {"outcome": "CLEAN", "reason": "All applicable stages passed.", "provisional": False},
        }
    )
    client = TestClient(api.app)
    listed = client.get("/workflows")
    assert listed.status_code == 200
    assert listed.json()["workflow_ids"] == ["WF-DESK-1"]
    page = client.get("/desk")
    assert page.status_code == 200
    assert b"Pod 4 evidence desk" in page.content


def test_create_requires_product_facts_and_does_not_invent_them():
    import orchestration.api as api

    client = TestClient(api.app)
    response = client.post("/workflows", json={"org_id": "org_demo_alpha", "unit_id": "NOT-A-PRODUCT"})
    assert response.status_code == 422
    assert "No sample product" in response.json()["detail"]
    assert api.STORE.load_workflow("WF-org_demo_alpha-NOT-A-PRODUCT") is None


def test_health_accepts_ok_without_status_key():
    import orchestration.api as api

    assert api.reported_status({"ok": True, "stage": "pack"}) == "ok"
    assert api.reported_status({"ok": True, "degraded": True}) == "degraded"
    assert api.reported_status({"status": "ok"}) == "ok"
    assert api.reported_status({"ok": False}) == "down"

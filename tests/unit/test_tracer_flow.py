import base64
import os
from pathlib import Path

from orchestration.orchestrator import agent_context, discover_inputs, load_flow, run_workflow
from orchestration.store import MemoryStore
from shared.utils.schema import errors


def test_case_fields_are_visible_to_every_agent():
    context = agent_context({
        "overrides": [{"override_id": "OVR-001"}],
        "context": {
            "product_name": "iPhone 17",
            "parts_list": ["handset", "cable"],
            "order": {"items": [{"name": "cable", "expected_qty": 1}]},
            "work_order": {"unitId": "TRACER-01"},
            "charges": [{"line_id": "FEE-1", "charge_type": "inbound_defect_fee"}],
        },
    })
    assert context["product_name"] == "iPhone 17"
    assert context["parts_list"] == ["handset", "cable"]
    assert context["order"]["items"][0]["name"] == "cable"
    assert context["work_order"]["unitId"] == "TRACER-01"
    assert context["charges"][0]["line_id"] == "FEE-1"
    assert context["overrides"][0]["override_id"] == "OVR-001"


def test_tracer_flow_calls_all_five_stages():
    flow = load_flow(Path(__file__).resolve().parents[2] / "orchestration" / "flow.pod4-tracers.json")
    assert [step["stage"] for step in flow["steps"]] == [
        "receiving", "prep", "pack", "returns", "recovery",
    ]
    assert flow["defaults"]["on_pending"] == "continue"
    assert flow["defaults"]["timeout_s"] >= 180


def test_demo_units_finish_without_a_model_call():
    flow = load_flow(Path(__file__).resolve().parents[2] / "orchestration" / "flow.pod4-tracers.json")
    store = MemoryStore()
    expected = {
        "UNIT-001": ("COMPLETED", "CLEAN"),
        "UNIT-002": ("BLOCKED", "NEEDS_REVIEW"),
        "UNIT-003": ("COMPLETED", "CLAIM_RECOMMENDED"),
    }
    for unit, (status, outcome) in expected.items():
        wf = run_workflow(
            {"org_id": "org_demo_alpha", "unit_id": unit, "subject_id": unit, "route": "fba", "returned": True},
            flow,
            store,
        )
        assert errors("workflow-state", wf) == []
        assert wf["status"] == status
        assert wf["final_outcome"]["outcome"] == outcome
        for record_id in wf["evidence_references"]:
            record = store.get_evidence(record_id)
            assert errors("evidence", record) == []
            assert record["model"]["name"] == "demo-override"
            assert record["model"]["calls"] == 0
            assert record["decision"]["verdict"] in {"PASS", "FAIL", "UNCERTAIN"}
    recovery = store.get_evidence("RCY-UNIT-003")
    assert recovery["payload"]["evidence_flags"] == ["CONTRADICTS"]
    assert "PRP-UNIT-003" in recovery["checks"][0]["evidence_refs"]
    assert "RTN-UNIT-003" in recovery["checks"][0]["evidence_refs"]


def test_a_crashing_agent_does_not_kill_the_workflow():
    class Boom:
        def run(self, request, timeout_s):
            raise RuntimeError("vision timeout")

    flow = load_flow(Path(__file__).resolve().parents[2] / "orchestration" / "flow.pod4-tracers.json")
    clients = {stage: Boom() for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    wf = run_workflow(
        {"org_id": "org_demo_alpha", "unit_id": "TRACER-CRASH", "subject_id": "TRACER-CRASH", "route": "fba", "returned": True},
        flow,
        MemoryStore(),
        clients,
    )
    assert wf["status"] == "FAILED"
    assert wf["final_outcome"]["outcome"] == "INCOMPLETE"
    assert wf["final_outcome"]["verdict"] == "UNCERTAIN"
    assert all(sr["verdict"] == "UNCERTAIN" for sr in wf["stage_results"])


def test_discovered_photo_carries_its_bytes(tmp_path, monkeypatch):
    folder = tmp_path / "TRACER-01" / "prep"
    folder.mkdir(parents=True)
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    (folder / "front.png").write_bytes(png)
    monkeypatch.setenv("INPUT_DIR", str(tmp_path))
    rows = discover_inputs("TRACER-01", "prep")
    assert len(rows) == 1
    assert rows[0]["kind"] == "image"
    assert base64.b64decode(rows[0]["data_base64"]) == png
    os.environ.pop("INPUT_DIR", None)

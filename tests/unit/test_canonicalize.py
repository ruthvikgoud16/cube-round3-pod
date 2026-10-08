import json
from pathlib import Path

from orchestration.orchestrator import canonicalize_output, load_flow, run_workflow
from orchestration.store import MemoryStore
from shared.utils.hashing import verify
from shared.utils.records import build_output, build_record, check
from shared.utils.schema import errors


def _bad_envelope(request: dict) -> dict:
    record = build_record(
        request,
        agent_id="pack-manager@1.0.0",
        record_id="PCK-KEEP",
        captured_at="2026-10-08T12:00:00Z",
        checks=[check("line_match", "UNCERTAIN", 0.4, detail="brand unclear")],
        outcome="review_required",
        reason="brand unclear",
        model={"name": "claude", "version": "claude-sonnet-4-5", "calls": 1},
        verdict="UNCERTAIN",
        confidence=0.4,
        needs_human=True,
    )
    record["checks"][0].pop("uncertain_reason")
    record["content_hash"] = "0" * 64
    output = build_output(record, next_step="continue", reason="brand unclear")
    output["next_step_recommendation"]["action"] = "hold"
    return output


def test_hold_and_a_private_hash_become_a_stored_judgment():
    request = {
        "schema_version": "1.0",
        "request_id": "req-1",
        "workflow_id": "WF-org_demo_alpha-KEEP",
        "stage": "pack",
        "subject": {"org_id": "org_demo_alpha", "subject_id": "KEEP", "route": "mfn"},
    }
    fixed = canonicalize_output(_bad_envelope(request))
    assert fixed["next_step_recommendation"]["action"] == "review"
    assert fixed["evidence"]["checks"][0]["uncertain_reason"] == "insufficient_evidence"
    assert verify(fixed["evidence"])
    assert errors("agent-output", fixed) == []


def test_a_real_saved_prep_and_pack_envelope_validates_after_sealing():
    samples = [
        Path("/Users/ruthvikgoud/cube26-prp-0070-mpreethika16/data/round3-evidence/PRP-bd8eb3d9ee1e.json"),
        Path("/Users/ruthvikgoud/cube-03-pack-manager1/data/round3-evidence/PCK-8fc604309ad2.json"),
        Path("/Users/ruthvikgoud/cube-03-pack-manager1/data/round3-evidence/PCK-cd147954babd.json"),
    ]
    if not all(path.exists() for path in samples):
        return
    for path in samples:
        raw = json.loads(path.read_text())
        fixed = canonicalize_output(raw)
        assert verify(fixed["evidence"])
        assert errors("agent-output", fixed) == [], path.name


class _Client:
    def run(self, request, timeout_s):
        if request["stage"] == "pack":
            return _bad_envelope(request)
        prefix = {"receiving": "RCV", "recovery": "RCY"}[request["stage"]]
        record = build_record(
            request,
            agent_id=f"{request['stage']}-manager@1.0.0",
            record_id=f"{prefix}-KEEP",
            captured_at="2026-10-08T12:00:00Z",
            checks=[check(request["stage"], "PASS", 1.0, detail="ok")],
            outcome="accept",
            reason="ok",
            model={"name": "rules", "version": "0", "calls": 0},
            verdict="PASS",
            confidence=1.0,
            needs_human=False,
        )
        return build_output(record, reason="ok")


def test_workflow_keeps_the_agent_verdict():
    flow = load_flow(Path(__file__).resolve().parents[2] / "orchestration" / "flow.json")
    case = {"org_id": "org_demo_alpha", "unit_id": "KEEP", "subject_id": "KEEP", "route": "mfn", "returned": False}
    clients = {stage: _Client() for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    wf = run_workflow(case, flow, MemoryStore(), clients)
    pack = next(sr for sr in wf["stage_results"] if sr["stage"] == "pack")
    assert pack["state"] == "completed"
    assert pack["verdict"] == "UNCERTAIN"
    assert pack["needs_human"] is True

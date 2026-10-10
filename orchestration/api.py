"""Optional HTTP front door for the orchestrator (useful for a deployed demo).

  uvicorn orchestration.api:app --port 8100
  POST /workflows                 {"org_id": "org_demo_alpha", "unit_id": "UNIT-0002"}   -> Workflow State (runs it)
  GET  /workflows/{id}            -> Workflow State
  GET  /workflows/{id}/evidence   -> the workflow plus all its evidence records
  POST /workflows/{id}/resume     -> continue after a halt / decision / failure
  POST /workflows/{id}/overrides  {"record_id": "...", "new_verdict": "PASS", "actor": "...", "reason": "..."}
  GET  /health                    -> orchestrator and every agent in the flow
No authentication is included. Add it before you deploy anywhere public.
"""
from __future__ import annotations

import os

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .clients import HttpClient, client_for, load_manifest
from .orchestrator import apply_override, bundle, default_flow_path, flow_stages, load_flow, resume, run_workflow
from .store import EvidenceConflict, FileStore

app = FastAPI(title="CUBE Round 3 orchestrator")
_origins = [item.strip() for item in os.environ.get("CORS_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
FLOW = os.environ.get("ORCH_FLOW") or default_flow_path()
STORE = FileStore()


DESK = Path(__file__).resolve().parent / "static" / "desk.html"


@app.get("/desk")
def desk() -> FileResponse:
    return FileResponse(DESK)


@app.get("/workflows")
def workflows() -> dict:
    folder = STORE.root / "workflows"
    ids = sorted(path.stem for path in folder.glob("*.json") if path.is_file())
    return {"workflow_ids": ids}


def reported_status(body: dict) -> str:
    """Agents do not share one health shape. Prep, Pack, and Returns send ok; Recovery sends status."""
    status = body.get("status")
    if status in {"ok", "down", "degraded"}:
        return status
    if body.get("ok") is True:
        return "degraded" if body.get("degraded") else "ok"
    if body.get("ok") is False:
        return "down"
    return "unknown"


@app.get("/health")
def health() -> dict:
    agents = {}
    for stage in flow_stages(load_flow(FLOW)):
        client = client_for(stage)
        try:
            raw = client.health() if isinstance(client, HttpClient) else {"status": "ok", "mode": "inproc"}
            if not isinstance(raw, dict):
                agents[stage] = {"status": "down", "error": "health was not an object"}
            else:
                agents[stage] = {**raw, "status": reported_status(raw)}
        except Exception as exc:
            agents[stage] = {"status": "down", "error": str(exc)[:200], "owner": load_manifest(stage)["owner"]}
    statuses = [a.get("status") for a in agents.values()]
    if statuses and all(item == "ok" for item in statuses):
        overall = "ok"
    elif any(item == "down" for item in statuses):
        overall = "down"
    else:
        overall = "degraded"
    return {"status": overall, "flow": load_flow(FLOW)["flow_id"], "agents": agents}


@app.post("/workflows")
def create(body: dict) -> dict:
    org, subject = body.get("org_id"), body.get("subject_id") or body.get("unit_id")
    if not org or not subject:
        raise HTTPException(422, "org_id and unit_id (or subject_id) are required")
    if body.get("route") not in {"fba", "mfn"} or not isinstance(body.get("returned"), bool):
        raise HTTPException(
            422,
            "route (fba or mfn) and returned (true or false) are required. No sample product is filled in.",
        )
    case = {"org_id": org, "unit_id": subject, "route": body["route"], "returned": body["returned"]}
    for key in ("product_name", "sku", "spec_variant", "qty_ordered", "cartons_ordered", "parts_list", "order", "work_order", "charges", "live", "include_ai_summary"):
        if key in body:
            case[key] = body[key]
    return run_workflow(case, load_flow(FLOW), STORE)


def _get(workflow_id: str) -> dict:
    wf = STORE.load_workflow(workflow_id)
    if wf is None:
        raise HTTPException(404, f"no workflow {workflow_id}")
    return wf


@app.get("/workflows/{workflow_id}")
def get(workflow_id: str) -> dict:
    return _get(workflow_id)


@app.get("/workflows/{workflow_id}/evidence")
def evidence(workflow_id: str) -> dict:
    return bundle(_get(workflow_id), STORE)


@app.post("/workflows/{workflow_id}/resume")
def resume_workflow(workflow_id: str) -> dict:
    _get(workflow_id)
    return resume(workflow_id, load_flow(FLOW), STORE)


@app.post("/workflows/{workflow_id}/overrides")
def override(workflow_id: str, body: dict) -> dict:
    _get(workflow_id)
    try:
        return apply_override(workflow_id, STORE, record_id=body.get("record_id", ""), new_verdict=body.get("new_verdict", ""),
                              actor=body.get("actor", ""), reason=body.get("reason", ""), new_outcome=body.get("new_outcome"))
    except (ValueError, EvidenceConflict) as exc:
        raise HTTPException(422, str(exc)) from exc

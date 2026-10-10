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

import base64
import os
import re
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .clients import HttpClient, client_for, load_manifest
from .orchestrator import (
    apply_override,
    bundle,
    default_flow_path,
    flow_stages,
    load_flow,
    new_workflow,
    resume,
    run_workflow,
    workflow_id_for,
)
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
LIVE = Path(__file__).resolve().parent / "static" / "live.html"
STAGE_DIRS = ("receiving", "prep", "pack", "returns")


@app.get("/desk")
def desk() -> FileResponse:
    return FileResponse(DESK)


@app.get("/live")
def live() -> FileResponse:
    return FileResponse(LIVE)


def _stage_of(path: str) -> str | None:
    for part in Path(path).parts:
        token = part.lower()
        for stage in STAGE_DIRS:
            if token == stage or token.endswith("-" + stage) or token.endswith("_" + stage):
                return stage
    return None


@app.post("/intake")
def intake(body: dict) -> dict:
    """Save an uploaded photo folder and start that unit. The response returns before the agents finish."""
    org, subject = body.get("org_id"), body.get("subject_id") or body.get("unit_id")
    if not org or not subject:
        raise HTTPException(422, "org_id and unit_id are required")
    if body.get("route") not in {"fba", "mfn"} or not isinstance(body.get("returned"), bool):
        raise HTTPException(422, "route (fba or mfn) and returned (true or false) are required")
    unit = re.sub(r"[^A-Za-z0-9._-]", "-", str(subject))[:80]
    root = Path(os.environ.get("INPUT_DIR", "data/input"))
    staged = []
    for item in body.get("files") or []:
        rel = str(item.get("path") or "")
        stage = _stage_of(rel)
        name = Path(rel).name
        if not stage or not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        try:
            raw = base64.b64decode(item.get("data_base64") or "", validate=True)
        except Exception:
            continue
        if not raw or len(raw) > 8_000_000:
            continue
        dest = root / unit / stage / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        staged.append(f"{stage}/{name}")
    if not staged:
        raise HTTPException(422, "No photos were placed. Folders must be named receiving, prep, pack, or returns.")
    case = {"org_id": org, "unit_id": unit, "route": body["route"], "returned": body["returned"], "live": True}
    for key in ("product_name", "sku", "spec_variant", "qty_ordered"):
        if body.get(key):
            case[key] = body[key]
    if STORE.load_workflow(workflow_id_for(case)) is not None:
        raise HTTPException(409, f"{workflow_id_for(case)} already exists. Use a new unit id for a new run.")
    flow = load_flow(FLOW)
    wf = new_workflow(case, flow)
    STORE.save_workflow(wf)
    threading.Thread(target=run_workflow, args=(case, flow, STORE), daemon=True).start()
    return {"workflow_id": wf["workflow_id"], "staged": staged, "status": "started"}


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

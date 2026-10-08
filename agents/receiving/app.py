"""Receiving Manager — elite Round 3 agent.

Architecture (fixed):
  Agent Input
    → quality gate (reject unusable frames before the model)
    → ONE Claude observation call (facts only; no disposition)
    → schema validate observation
    → receiving_policy_v1 (deterministic checks + outcome)
    → Evidence Record RCV-* via shared.utils.records
    → Agent Output

Fail-open: any model/schema/IO failure → pending_output (never crash orchestrator).
Tenancy: wrong org → LookupError (HTTP 404).
unit_scope: po_line (F-08). Supplier shortfall stays in payload (F-10).
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from shared.utils.records import build_output, build_record, pending_output, utcnow
from shared.utils.server import make_app

from .observer import observe_receiving
from .policy import apply_receiving_policy
from .po_context import extract_po_context
from .quality_gate import gate_photos
from .shots import attach_roles

STAGE = "receiving"
AGENT_ID = os.environ.get("RECEIVING_AGENT_ID", "receiving-manager@1.0.0")
DEMO_ORGS = {"org_demo_alpha", "org_demo_bravo"}
ROOT = Path(__file__).resolve().parents[2]


def handle(request: dict) -> dict:
    subject = request.get("subject") or {}
    org_id = subject.get("org_id")
    subject_id = subject.get("subject_id")
    if not org_id or org_id not in DEMO_ORGS:
        raise LookupError(f"unknown or disallowed tenant: {org_id!r}")
    if not subject_id:
        raise LookupError("subject.subject_id is required")
    if request.get("stage") and request["stage"] != STAGE:
        return pending_output(
            request,
            code="wrong_stage",
            message="stage must be receiving",
            agent_id=AGENT_ID,
            retryable=False,
        )

    po = extract_po_context(request)
    mode = _receiving_mode()
    if mode == "mock":
        po = _merge_fixture_po(po, subject_id)
    photos, input_refs, gate_notes = _load_photos(request, subject_id)

    # Mock builds may run with fixture placeholders until real dock photos arrive.
    if not photos and mode == "mock":
        photos = _placeholder_photos(subject_id)
        gate_notes.append("mock_placeholders: replace with real pallet/carton/unit photos")

    usable, unusable = gate_photos(photos)
    usable = attach_roles(usable)
    unusable = attach_roles(unusable)

    if not usable:
        if mode == "mock":
            # Still allow fixture observation without pixels (honest payload note).
            usable = attach_roles(_placeholder_photos(subject_id))
            unusable = []
            gate_notes.append("quality_gate_bypassed_for_mock_fixtures")
        else:
            return pending_output(
                request,
                code="unusable_photos",
                message="; ".join(gate_notes) or "No usable receiving photographs after quality gate",
                agent_id=AGENT_ID,
                retryable=True,
            )

    try:
        observation, model_meta = observe_receiving(po=po, photos=usable)
        checks, outcome, verdict, reason, payload = apply_receiving_policy(
            po=po,
            observation=observation,
            photos=usable,
            model_version=model_meta["version"],
            latency_ms=model_meta["latency_ms"],
        )
    except Exception as exc:  # noqa: BLE001 — fail open
        return pending_output(
            request,
            code="model_or_policy_failure",
            message=str(exc),
            agent_id=AGENT_ID,
            retryable=True,
        )

    calls = int(model_meta.get("calls", 1 if model_meta.get("name") == "claude" else 0))
    provider = "anthropic" if model_meta.get("name") == "claude" else "fixture"
    record_id = _stable_record_id(request["request_id"], subject_id)
    record = build_record(
        request,
        agent_id=AGENT_ID,
        record_id=record_id,
        captured_at=po.get("captured_at") or utcnow(),
        operator_id=po.get("operator_id"),
        unit_scope="po_line",
        refs={
            "po_number": po.get("po_number"),
            "po_line": po.get("po_line"),
            "sku": po.get("sku"),
            "asin": po.get("asin"),
            "product_name": po.get("product_name"),
        },
        checks=checks,
        outcome=outcome,
        verdict=verdict,
        reason=reason,
        model={
            "name": model_meta["name"],
            "version": model_meta["version"],
            "provider": provider,
            "prompt_version": model_meta.get("prompt_version", "receiving-observe-v1"),
            "calls": calls,
            "cost_usd": None,
        },
        inputs=[{"ref": p["ref"], "sha256": p.get("sha256"), "kind": "image"} for p in usable],
        payload={
            **payload,
            "receiving_mode": mode,
            "quality_gate": {
                "usable": len(usable),
                "unusable": len(unusable),
                "notes": gate_notes,
            },
            "input_refs_requested": input_refs,
            "finding_notes": {
                "F-08": "unit_scope=po_line",
                "F-10": "shortfall_units is supplier-side; not channel lost_inbound proof",
            },
        },
        latency_ms=model_meta["latency_ms"],
        client_id=po.get("client_id"),
        needs_human=outcome == "pending_review" or verdict == "UNCERTAIN",
    )
    return build_output(record)


def _stable_record_id(request_id: str, subject_id: str) -> str:
    digest = hashlib.sha256(f"{request_id}:{subject_id}".encode()).hexdigest()[:12]
    return f"RCV-{digest}"


def _load_photos(request: dict, subject_id: str) -> tuple[list[dict], list[str], list[str]]:
    notes: list[str] = []
    refs: list[str] = []
    out: list[dict] = []
    for row in request.get("inputs") or []:
        ref = row.get("ref") or f"input-{len(out)}"
        refs.append(ref)
        if row.get("data_base64"):
            raw = base64.b64decode(row["data_base64"])
            out.append(
                {
                    "ref": ref,
                    "bytes": raw,
                    "media_type": row.get("media_type") or "image/jpeg",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
            continue
        for candidate in _ref_candidates(ref, subject_id):
            if candidate.is_file():
                raw = candidate.read_bytes()
                out.append(
                    {
                        "ref": ref,
                        "bytes": raw,
                        "media_type": _guess_media(candidate),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
                break
        else:
            notes.append(f"missing image ref: {ref}")

    if not out:
        folder = ROOT / "data" / "input" / subject_id / "receiving"
        if folder.is_dir():
            for path in sorted(folder.iterdir()):
                if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    raw = path.read_bytes()
                    rel = f"{subject_id}/receiving/{path.name}"
                    out.append(
                        {
                            "ref": rel,
                            "bytes": raw,
                            "media_type": _guess_media(path),
                            "sha256": hashlib.sha256(raw).hexdigest(),
                        }
                    )
                    refs.append(rel)
        else:
            notes.append(f"no photos in inputs and no folder {folder}")
    return out, refs, notes


def _ref_candidates(ref: str, subject_id: str) -> list[Path]:
    return [
        Path(ref),
        ROOT / ref,
        ROOT / "data" / "input" / subject_id / "receiving" / Path(ref).name,
        ROOT / "data" / "fixtures" / "receiving" / Path(ref).name,
    ]


def _guess_media(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/jpeg"


def _receiving_mode() -> str:
    forced = (os.environ.get("RECEIVING_MODE") or "").strip().lower()
    if forced in {"mock", "live"}:
        return forced
    return "mock" if not os.environ.get("ANTHROPIC_API_KEY") else "live"


def _merge_fixture_po(po: dict, subject_id: str) -> dict:
    """Fill missing PO fields from fixture cases so mock demos need less context."""
    cases_path = ROOT / "data" / "fixtures" / "receiving" / "cases.json"
    if not cases_path.is_file():
        return po
    try:
        import json

        rows = {r["subject_id"]: r for r in json.loads(cases_path.read_text()).get("cases", [])}
        fixture_po = (rows.get(subject_id) or {}).get("po") or {}
    except Exception:  # noqa: BLE001
        return po
    merged = dict(po)
    for key, value in fixture_po.items():
        if merged.get(key) in (None, "", "UNKNOWN", "PO-UNKNOWN"):
            merged[key] = value
    return merged


def _placeholder_photos(subject_id: str) -> list[dict]:
    """Minimal valid JPEGs so the pipeline runs before real dock photos exist."""
    from io import BytesIO

    from PIL import Image

    out: list[dict] = []
    for name, color in (("01_pallet", (40, 80, 120)), ("02_carton", (90, 90, 90)), ("03_unit", (180, 160, 120))):
        img = Image.new("RGB", (640, 640), color)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=85)
        raw = buf.getvalue()
        ref = f"{subject_id}/receiving/{name}.jpg"
        out.append(
            {
                "ref": ref,
                "bytes": raw,
                "media_type": "image/jpeg",
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return out


app = make_app(STAGE, handle, version="1.1.0")

_STATIC = Path(__file__).resolve().parent / "static"
_EVAL = ROOT / "eval"
_DOCS = ROOT / "docs"


def _page(name: str) -> FileResponse:
    return FileResponse(_STATIC / name, media_type="text/html")


@app.get("/", response_class=HTMLResponse)
def desk() -> FileResponse:
    return _page("desk.html")


@app.get("/evaluation", response_class=HTMLResponse)
def evaluation_page() -> FileResponse:
    return _page("evaluation.html")


@app.get("/failures", response_class=HTMLResponse)
def failures_page() -> FileResponse:
    return _page("failures.html")


@app.get("/about", response_class=HTMLResponse)
def about_page() -> FileResponse:
    return _page("about.html")


@app.get("/static/{path:path}")
def static_files(path: str) -> FileResponse:
    target = (_STATIC / path).resolve()
    if not str(target).startswith(str(_STATIC.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail="static not found")
    media = (
        "text/css"
        if target.suffix == ".css"
        else "application/javascript"
        if target.suffix == ".js"
        else "application/octet-stream"
    )
    return FileResponse(target, media_type=media)


@app.get("/photos/{unit_id}/{filename}")
def photos(unit_id: str, filename: str) -> FileResponse:
    if not unit_id.startswith("UNIT-RCV-") or "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="bad photo path")
    path = ROOT / "data" / "input" / unit_id / "receiving" / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="photo not found")
    return FileResponse(path, media_type="image/jpeg")


@app.get("/api/project")
def api_project() -> dict:
    import json

    cases = json.loads((_EVAL.parent / "data/fixtures/receiving/cases.json").read_text())["cases"]
    return {
        "stage": STAGE,
        "agent_id": AGENT_ID,
        "mode": _receiving_mode(),
        "project_set": "UNIT-RCV-01..12",
        "note": "Twelve real dock deliveries — not mocks",
        "cases": [
            {
                "id": c["subject_id"],
                "label": c.get("label"),
                "product_name": (c.get("po") or {}).get("product_name"),
                "expected_outcome": c.get("expected_outcome"),
            }
            for c in cases
            if str(c["subject_id"]).startswith("UNIT-RCV-")
            and int(str(c["subject_id"]).split("-")[-1]) <= 12
        ],
    }


@app.get("/api/eval/score")
def api_eval_score() -> dict:
    import json

    path = _EVAL / "score.json"
    if not path.is_file():
        return {"error": "score.json missing — run eval/score.py"}
    return json.loads(path.read_text())


@app.get("/api/eval/predictions")
def api_eval_predictions() -> dict:
    import json

    path = _EVAL / "predictions.json"
    if not path.is_file():
        return {"cases": []}
    return json.loads(path.read_text())


@app.get("/api/eval/digest")
def api_eval_digest() -> dict:
    import json

    path = _EVAL / "case-digest.json"
    if not path.is_file():
        return {"cases": [], "failed": []}
    return json.loads(path.read_text())


@app.get("/eval/{path:path}")
def eval_files(path: str) -> FileResponse:
    target = (_EVAL / path).resolve()
    if not str(target).startswith(str(_EVAL.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail="eval file not found")
    media = (
        "text/markdown"
        if target.suffix == ".md"
        else "text/html"
        if target.suffix == ".html"
        else "application/json"
        if target.suffix == ".json"
        else "text/csv"
        if target.suffix == ".csv"
        else "application/pdf"
        if target.suffix == ".pdf"
        else "text/plain"
    )
    return FileResponse(target, media_type=media)


@app.get("/docs/demo/{path:path}")
def demo_docs(path: str) -> FileResponse:
    base = _DOCS / "demo"
    target = (base / path).resolve()
    if not str(target).startswith(str(base.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail="doc not found")
    media = (
        "text/markdown"
        if target.suffix == ".md"
        else "text/html"
        if target.suffix == ".html"
        else "application/pdf"
        if target.suffix == ".pdf"
        else "text/plain"
    )
    return FileResponse(target, media_type=media)


@app.get("/docs/INTEGRATION.md")
def integration_doc() -> FileResponse:
    path = _DOCS / "INTEGRATION.md"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="missing INTEGRATION.md")
    return FileResponse(path, media_type="text/markdown")

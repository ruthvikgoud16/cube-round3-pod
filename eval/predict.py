#!/usr/bin/env python3
"""Run Receiving agent (live) on all labeled deliveries. One model call each."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if env_path.is_file():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

os.environ["RECEIVING_MODE"] = "live"

from agents.receiving.app import handle  # noqa: E402

OUT = Path(__file__).resolve().parent / "predictions.json"
CASES = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY missing")
        return 2

    rows = []
    started = time.time()
    for case in CASES:
        sid = case["subject_id"]
        folder = ROOT / "data" / "input" / sid / "receiving"
        if not any(folder.glob("*.jpg")):
            rows.append(
                {
                    "case_id": sid,
                    "status": "no_photo",
                    "checks": {},
                    "outcome": None,
                    "verdict": None,
                    "model_calls": 0,
                    "error": f"no images in {folder}",
                }
            )
            print(f"[SKIP] {sid} no photos")
            continue

        t0 = time.time()
        try:
            out = handle(
                {
                    "schema_version": "1.0",
                    "request_id": f"eval-{sid}",
                    "workflow_id": f"WF-org_demo_alpha-{sid}",
                    "stage": "receiving",
                    "subject": {"org_id": "org_demo_alpha", "subject_id": sid, "route": "fba"},
                    "previous_evidence": [],
                    "context": case.get("po") or {},
                    "inputs": [],
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "case_id": sid,
                    "status": "error",
                    "checks": {},
                    "outcome": None,
                    "verdict": None,
                    "model_calls": 0,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "error": str(exc),
                }
            )
            print(f"[ERR] {sid} {exc}")
            continue

        evidence = out.get("evidence") or {}
        checks = {c["check_key"]: c["verdict"] for c in evidence.get("checks") or []}
        outcome = (evidence.get("decision") or {}).get("outcome")
        model = evidence.get("model") or {}
        row = {
            "case_id": sid,
            "status": "ok" if checks else "pending_or_error",
            "checks": checks,
            "outcome": outcome or out.get("status"),
            "verdict": out.get("verdict") or evidence.get("verdict"),
            "model_calls": int(model.get("calls") or (1 if checks else 0)),
            "model_name": model.get("name"),
            "model_version": model.get("version"),
            "latency_ms": evidence.get("latency_ms") or int((time.time() - t0) * 1000),
            "record_id": evidence.get("record_id"),
            "error": (out.get("error") or {}).get("message") if isinstance(out.get("error"), dict) else out.get("error"),
        }
        rows.append(row)
        print(f"[OK] {sid} outcome={row['outcome']} checks={checks}")

    payload = {
        "schema_version": "receiving-eval-predict-1",
        "mode": "live",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - started, 1),
        "cases": rows,
        "model_calls_total": sum(int(r.get("model_calls") or 0) for r in rows),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {OUT}  calls={payload['model_calls_total']}  elapsed={payload['elapsed_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Live Receiving smoke: Claude + staged dock photos under data/input/.

Requires ANTHROPIC_API_KEY in .env. Costs ~12 vision calls if run for all cases.
Pass subject ids to limit, e.g. UNIT-RCV-01 UNIT-RCV-07 UNIT-RCV-12
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Load .env without printing secrets
env_path = ROOT / ".env"
if env_path.is_file():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

os.environ["RECEIVING_MODE"] = "live"

from agents.receiving.app import handle  # noqa: E402


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY missing — abort live run")
        return 2

    cases = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]
    wanted = set(sys.argv[1:]) if len(sys.argv) > 1 else {c["subject_id"] for c in cases}
    rows = [c for c in cases if c["subject_id"] in wanted]
    print(f"Receiving LIVE — {len(rows)} cases\n")

    ok = 0
    for case in rows:
        sid = case["subject_id"]
        folder = ROOT / "data" / "input" / sid / "receiving"
        if not folder.is_dir() or not any(folder.glob("*.jpg")):
            print(f"[SKIP] {sid} — no staged photos in {folder}")
            continue
        out = handle(
            {
                "schema_version": "1.0",
                "request_id": f"live-{sid}",
                "workflow_id": f"WF-org_demo_alpha-{sid}",
                "stage": "receiving",
                "subject": {"org_id": "org_demo_alpha", "subject_id": sid, "route": "fba"},
                "previous_evidence": [],
                "context": case.get("po") or {},
                "inputs": [],
            }
        )
        outcome = (out.get("evidence") or {}).get("decision", {}).get("outcome") or out.get("status")
        expected = case["expected_outcome"]
        # Live vision can differ from mock fixtures; treat pending_review as soft-ok for dark/blur/sealed
        soft = expected == "pending_review" and outcome in {"pending_review", "pending"}
        mark = "OK" if outcome == expected or soft else "DIFF"
        if mark == "OK":
            ok += 1
        print(f"[{mark}] {sid} ({case['label']})")
        print(f"     outcome={outcome} expected={expected} verdict={out.get('verdict')}")
        if out.get("evidence"):
            checks = ", ".join(f"{c['check_key']}={c['verdict']}" for c in out["evidence"]["checks"])
            print(f"     {checks}")
            print(f"     record={out['evidence']['record_id']} mode={out['evidence']['payload'].get('receiving_mode')}")
        else:
            print(f"     error={out.get('error') or out}")
        print()

    print(f"{ok}/{len(rows)} matched (or soft-matched) expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run Receiving agent on all mock fixture cases (no photos / no API required)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("RECEIVING_MODE", "mock")

from agents.receiving.app import handle  # noqa: E402


def main() -> int:
    cases = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]
    print(f"Receiving mock demo — {len(cases)} cases\n")
    ok = 0
    for case in cases:
        sid = case["subject_id"]
        out = handle(
            {
                "schema_version": "1.0",
                "request_id": f"demo-{sid}",
                "workflow_id": f"WF-org_demo_alpha-{sid}",
                "stage": "receiving",
                "subject": {"org_id": "org_demo_alpha", "subject_id": sid, "route": "fba"},
                "previous_evidence": [],
                "context": {},
                "inputs": [],
            }
        )
        outcome = out["evidence"]["decision"]["outcome"]
        expected = case["expected_outcome"]
        mark = "OK" if outcome == expected else "MISS"
        if mark == "OK":
            ok += 1
        checks = ", ".join(f"{c['check_key']}={c['verdict']}" for c in out["evidence"]["checks"])
        print(f"[{mark}] {sid} ({case['label']})")
        print(f"     outcome={outcome} expected={expected} verdict={out['verdict']}")
        print(f"     {checks}")
        print(f"     record={out['evidence']['record_id']} mode={out['evidence']['payload'].get('receiving_mode')}")
        print()
    print(f"{ok}/{len(cases)} matched expected outcomes")
    return 0 if ok == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())

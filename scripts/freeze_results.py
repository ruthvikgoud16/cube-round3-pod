"""Copy the stored workflows into static files for the frozen results site.

  OUT_DIR=/path/to/out .venv/bin/python scripts/freeze_results.py [web/public/orch]

The Control Tower reads /orch/health, /orch/workflows, /orch/workflows/{id} and
/orch/workflows/{id}/evidence. web/netlify.toml rewrites those paths onto the files written here,
so the frozen site needs no orchestrator at all. Nothing is re-judged: the records are copied as
stored. Local folder paths are blanked and any image payload is dropped before writing.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.orchestrator import bundle  # noqa: E402
from orchestration.store import FileStore  # noqa: E402

PATHS = re.compile(r"/(?:Users|private|tmp|home)/\S+")
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?\d{10}(?!\d)")


def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k != "data_base64"}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, str):
        return PATHS.sub("[local folder]", value)
    return value


def main() -> int:
    out_dir = os.environ.get("OUT_DIR") or "out"
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "web/public/orch")
    store = FileStore(out_dir)
    ids = sorted(p.stem for p in (Path(out_dir) / "workflows").glob("*.json"))
    if not ids:
        print(f"no workflows under {out_dir}")
        return 1
    (target / "wf").mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(os.environ.get("ORCH_URL", "http://127.0.0.1:8100") + "/health", timeout=10) as r:
            health = json.load(r)
    except Exception:
        health = {"status": "unknown", "flow": None, "agents": {}}
    health["frozen"] = True
    (target / "health.json").write_text(json.dumps(scrub(health), indent=1))
    (target / "workflows.json").write_text(json.dumps({"workflow_ids": ids}, indent=1))
    suspicious = []
    for wid in ids:
        wf = store.load_workflow(wid)
        folder = target / "wf" / wid
        folder.mkdir(parents=True, exist_ok=True)
        workflow_text = json.dumps(scrub(wf), indent=1)
        bundle_text = json.dumps(scrub(bundle(wf, store)), indent=1)
        (folder / "workflow.json").write_text(workflow_text)
        (folder / "evidence.json").write_text(bundle_text)
        if PHONE.search(bundle_text):
            suspicious.append(wid)
        print(wid, wf["status"], (wf.get("final_outcome") or {}).get("outcome"))
    if suspicious:
        print("CHECK before publishing, a ten digit number appears in:", ", ".join(suspicious))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

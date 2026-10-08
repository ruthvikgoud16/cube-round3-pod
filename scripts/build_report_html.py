#!/usr/bin/env python3
"""Build printable HTML report (open in browser → Print → Save as PDF)."""
from __future__ import annotations

import json
from pathlib import Path

EVAL = Path(__file__).resolve().parents[1] / "eval"


def main() -> int:
    score = json.loads((EVAL / "score.json").read_text()) if (EVAL / "score.json").is_file() else {}
    failed = ""
    if (EVAL / "FAILED-CASES.md").is_file():
        failed = (EVAL / "FAILED-CASES.md").read_text()
    eval_md = (EVAL / "EVALUATION.md").read_text() if (EVAL / "EVALUATION.md").is_file() else ""

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Receiving Manager — Evaluation Report</title>
<style>
  body {{ font: 12pt/1.45 Georgia, serif; max-width: 720px; margin: 32px auto; color: #122; padding: 0 16px; }}
  h1,h2 {{ font-family: "Helvetica Neue", Arial, sans-serif; }}
  pre {{ white-space: pre-wrap; font: 10pt/1.4 ui-monospace, monospace; background: #f4f4f1; padding: 12px; }}
  .meta {{ color: #555; }}
  @media print {{ body {{ margin: 0; }} }}
</style></head><body>
<h1>Receiving Manager — Evaluation Report</h1>
<p class="meta">Pod 4 · Project set UNIT-RCV-01…12 (real dock photos, not mocks) · Labelers Jaanu &amp; Soanli</p>
<p class="meta">Model calls: {score.get("model_calls", "—")} · Full agreement cases: {score.get("n_agreed_all_checks", "—")}</p>
<h2>Evaluation</h2>
<pre>{eval_md.replace("<", "&lt;")}</pre>
<h2>Failed / mismatched cases</h2>
<pre>{failed.replace("<", "&lt;")}</pre>
<p class="meta">Print this page to PDF for the submission pack.</p>
</body></html>
"""
    out = EVAL / "report.html"
    out.write_text(html)
    demo = Path(__file__).resolve().parents[1] / "docs" / "demo" / "report.html"
    demo.parent.mkdir(parents=True, exist_ok=True)
    demo.write_text(html)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

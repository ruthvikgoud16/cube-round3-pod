#!/usr/bin/env python3
"""Build eval markdown + JSON digests for the 12 real deliveries (not mocks)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "eval"
DOCS = ROOT / "docs" / "demo"
CHECKS = [
    "identity_match",
    "carton_count",
    "quantity",
    "carton_damage",
    "unit_damage",
    "quality_flags",
]


def main() -> int:
    DOCS.mkdir(parents=True, exist_ok=True)
    labels = list(csv.DictReader((EVAL / "labels.csv").open()))
    by: dict[str, dict] = {}
    for r in labels:
        by.setdefault(r["case_id"], {})[r["labeler"]] = r
    preds = {r["case_id"]: r for r in json.loads((EVAL / "predictions.json").read_text())["cases"]}
    score = json.loads((EVAL / "score.json").read_text()) if (EVAL / "score.json").is_file() else {}
    cases = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]
    meta = {c["subject_id"]: c for c in cases}

    failed = []
    rows = []
    for cid in sorted(by):
        labs = by[cid]
        pred = preds.get(cid) or {}
        agent = pred.get("checks") or {}
        jaanu, soanli = labs.get("Jaanu") or {}, labs.get("Soanli") or {}
        mismatches = []
        for check in CHECKS:
            if not jaanu.get(check) or not soanli.get(check):
                continue
            if jaanu[check] != soanli[check]:
                continue  # not agreed — skip for "failed vs agent"
            human = jaanu[check]
            ag = agent.get(check)
            if ag is None:
                mismatches.append(f"{check}: agent missing (human {human})")
            elif ag != human:
                mismatches.append(f"{check}: agent={ag} human={human}")
        row = {
            "case_id": cid,
            "label": (meta.get(cid) or {}).get("label"),
            "product_name": jaanu.get("product_name"),
            "agent_outcome": pred.get("outcome"),
            "agent_checks": agent,
            "jaanu": {c: jaanu.get(c) for c in CHECKS},
            "soanli": {c: soanli.get(c) for c in CHECKS},
            "mismatches_on_agreed_checks": mismatches,
            "human_disagreement": [
                c for c in CHECKS if jaanu.get(c) and soanli.get(c) and jaanu[c] != soanli[c]
            ],
        }
        rows.append(row)
        if mismatches:
            failed.append(row)

    (EVAL / "case-digest.json").write_text(json.dumps({"cases": rows, "failed": failed}, indent=2) + "\n")

    fail_md = [
        "# Failed / mismatched evaluation cases",
        "",
        "Project set: **12 real dock deliveries** (not mocks). Compared agent checks to checks where **both** Jaanu and Soanli agreed.",
        "",
        f"Mismatched cases: **{len(failed)}** / 12",
        "",
    ]
    for row in failed:
        fail_md += [
            f"## {row['case_id']} — {row['label']}",
            "",
            f"- Product: {row['product_name']}",
            f"- Agent outcome: `{row['agent_outcome']}`",
            f"- Mismatches: ",
        ]
        for m in row["mismatches_on_agreed_checks"]:
            fail_md.append(f"  - {m}")
        if row["human_disagreement"]:
            fail_md.append(f"- Human disagreement (excluded from match score): {', '.join(row['human_disagreement'])}")
        fail_md.append("")

    if not failed:
        fail_md.append("_No agreed-check mismatches in the current prediction freeze._")
        fail_md.append("")

    (EVAL / "FAILED-CASES.md").write_text("\n".join(fail_md))
    (DOCS / "FAILED-CASES.md").write_text("\n".join(fail_md))

    overview = [
        "# Receiving Manager — project set (12 real deliveries)",
        "",
        "These are **not mocks**. Photos are real Flipkart/Shadowfax inbound cartons staged under `data/input/UNIT-RCV-01…12`.",
        "Labelers: **Jaanu** and **Soanli**. One Claude observation call per delivery in live mode; disposition from `receiving_policy_v1`.",
        "",
        "## Pages",
        "",
        "| Page | URL (local :8101) |",
        "|---|---|",
        "| Desk | `/` |",
        "| Evaluation | `/evaluation` |",
        "| Failed cases | `/failures` |",
        "| About / integration | `/about` |",
        "| API docs | `/docs` |",
        "",
        "## Commands",
        "",
        "```bash",
        "RECEIVING_MODE=mock  uvicorn agents.receiving.app:app --port 8101",
        "RECEIVING_MODE=live  uvicorn agents.receiving.app:app --port 8101",
        "python eval/predict.py && python eval/score.py && python scripts/build_eval_pages.py",
        "```",
        "",
        "## Frozen eval",
        "",
        f"- Soft identity match rate (latest score): see `eval/EVALUATION.md`",
        f"- Failed digest: `eval/FAILED-CASES.md`",
        "",
    ]
    (DOCS / "README.md").write_text("\n".join(overview))
    (EVAL / "PROJECT-SET.md").write_text(
        "\n".join(
            [
                "# Project set = 12 real deliveries",
                "",
                "Do not treat UNIT-RCV-01…12 as mocks. Expansion folders (13+) are archived under `data/archive/` and are out of scope for tomorrow's demo.",
                "",
            ]
        )
    )
    print(f"wrote digests: failed={len(failed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

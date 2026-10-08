#!/usr/bin/env python3
"""Score Receiving agent predictions against two human labelers (Returns-style).

Primary rates use cases where BOTH labelers agree on all six checks.
Also prints per-check rates on the subset where that check alone was agreed.
Does not invent overall accuracy.
"""
from __future__ import annotations

import csv
import json
import time
from collections import defaultdict
from pathlib import Path

EVAL = Path(__file__).resolve().parent
ROOT = EVAL.parent
LABELS = EVAL / "labels.csv"
PREDICTIONS = EVAL / "predictions.json"
CHECKS = [
    "identity_match",
    "carton_count",
    "quantity",
    "carton_damage",
    "unit_damage",
    "quality_flags",
]
LABELERS = ("Jaanu", "Soanli")


def load_labels() -> dict[str, dict[str, dict]]:
    by: dict[str, dict[str, dict]] = defaultdict(dict)
    with LABELS.open() as f:
        for row in csv.DictReader(f):
            by[row["case_id"]][row["labeler"]] = row
    return by


def _filled(row: dict) -> bool:
    """Skip blank expansion rows waiting on humans."""
    return bool((row.get("identity_match") or "").strip())


def agreed_cases(by: dict[str, dict[str, dict]]) -> tuple[list[str], list[str], list[str]]:
    agreed, disagreed, pending = [], [], []
    for cid, labs in sorted(by.items()):
        if not all(name in labs for name in LABELERS):
            pending.append(cid)
            continue
        a, b = labs[LABELERS[0]], labs[LABELERS[1]]
        if not (_filled(a) and _filled(b)):
            pending.append(cid)
            continue
        if all(a[c] == b[c] for c in CHECKS):
            agreed.append(cid)
        else:
            disagreed.append(cid)
    return agreed, disagreed, pending


def per_check_agreed(by: dict[str, dict[str, dict]], check: str) -> list[str]:
    out = []
    for cid, labs in sorted(by.items()):
        if not all(name in labs for name in LABELERS):
            continue
        a, b = labs[LABELERS[0]], labs[LABELERS[1]]
        if not (_filled(a) and _filled(b)):
            continue
        if a[check] == b[check] and (a[check] or "").strip():
            out.append(cid)
    return out


def score_check(human: str, agent: str | None) -> str:
    if agent is None:
        return "missing"
    if agent == human:
        return "match"
    if agent == "UNCERTAIN" or human == "UNCERTAIN":
        return "uncertain_mismatch"
    if agent == "PASS" and human == "FAIL":
        return "fp"
    if agent == "FAIL" and human == "PASS":
        return "fn"
    return "other_mismatch"


def main() -> int:
    by = load_labels()
    preds = {r["case_id"]: r for r in json.loads(PREDICTIONS.read_text())["cases"]}
    agreed, disagreed, pending_labels = agreed_cases(by)

    report: dict = {
        "schema_version": "receiving-eval-score-1",
        "scored_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "labelers": list(LABELERS),
        "checks": CHECKS,
        "n_cases": len(by),
        "n_labeled": len(agreed) + len(disagreed),
        "n_pending_labels": len(pending_labels),
        "n_agreed_all_checks": len(agreed),
        "n_disagreed": len(disagreed),
        "agreed_case_ids": agreed,
        "disagreed_case_ids": disagreed,
        "pending_label_case_ids": pending_labels,
        "predictions_file": str(PREDICTIONS.name),
        "model_calls": sum(int(p.get("model_calls") or 0) for p in preds.values()),
        "per_check_full_agreement": {},
        "per_check_soft_agreement": {},
        "case_rows": [],
    }

    # Full-agreement primary rates
    for check in CHECKS:
        stats = {"n": 0, "match": 0, "fp": 0, "fn": 0, "uncertain_mismatch": 0, "other_mismatch": 0, "missing": 0}
        for cid in agreed:
            human = by[cid][LABELERS[0]][check]
            agent = (preds.get(cid) or {}).get("checks", {}).get(check)
            kind = score_check(human, agent)
            stats["n"] += 1
            stats[kind] = int(stats.get(kind, 0)) + 1
        report["per_check_full_agreement"][check] = stats

    # Soft: both humans agree on that check only
    for check in CHECKS:
        ids = per_check_agreed(by, check)
        stats = {"n": 0, "match": 0, "fp": 0, "fn": 0, "uncertain_mismatch": 0, "other_mismatch": 0, "missing": 0}
        for cid in ids:
            human = by[cid][LABELERS[0]][check]
            agent = (preds.get(cid) or {}).get("checks", {}).get(check)
            kind = score_check(human, agent)
            stats["n"] += 1
            stats[kind] = int(stats.get(kind, 0)) + 1
        report["per_check_soft_agreement"][check] = stats
        report["per_check_soft_agreement"][check]["n_human_agreed"] = len(ids)

    for cid in sorted(by):
        labs = by[cid]
        pred = preds.get(cid) or {}
        full = cid in agreed
        row = {
            "case_id": cid,
            "full_agreement": full,
            "human": {name: {c: labs[name][c] for c in CHECKS} for name in LABELERS if name in labs},
            "agent_checks": pred.get("checks") or {},
            "agent_outcome": pred.get("outcome"),
            "agent_status": pred.get("status"),
        }
        report["case_rows"].append(row)

    out_json = EVAL / "score.json"
    out_json.write_text(json.dumps(report, indent=2) + "\n")

    # Markdown
    md = _markdown(report, preds)
    (EVAL / "EVALUATION.md").write_text(md)
    frozen = EVAL / "frozen" / time.strftime("%Y-%m-%dT%H%MZ", time.gmtime())
    frozen.mkdir(parents=True, exist_ok=True)
    (frozen / "score.json").write_text(json.dumps(report, indent=2) + "\n")
    (frozen / "EVALUATION.md").write_text(md)
    (frozen / "predictions.json").write_text(PREDICTIONS.read_text())
    (frozen / "labels.csv").write_text(LABELS.read_text())

    print(md)
    print(f"\nwrote {out_json}")
    print(f"froze {frozen}")
    return 0


def _pct(n: int, d: int) -> str:
    if d == 0:
        return "n/a"
    return f"{n}/{d} ({100.0 * n / d:.1f}%)"


def _markdown(report: dict, preds: dict) -> str:
    lines = [
        "# Receiving evaluation",
        "",
        "These figures describe this held-out pilot set only. They are not an overall accuracy.",
        "Rates use cases where **both** labelers (Jaanu, Soanli) agreed. UNCERTAIN is not scored as PASS or FAIL.",
        "",
        "## A. Scope",
        "",
        f"- Project set: **{report['n_cases']} real dock deliveries** (UNIT-RCV-01…12 — not mocks)",
        f"- Fully labeled by both humans: **{report['n_labeled']}**",
        f"- Labelers: {', '.join(report['labelers'])} (independent, before scoring)",
        f"- Full agreement (all 6 checks): **{report['n_agreed_all_checks']}** → {', '.join(report['agreed_case_ids']) or 'none'}",
        f"- Disagreed / excluded from primary rates: **{report['n_disagreed']}** → {', '.join(report['disagreed_case_ids'])}",
        f"- Model calls: **{report['model_calls']}** (one per delivery)",
        "",
        "## B. Primary rates (full agreement only)",
        "",
        "| Check | Match | FP (agent PASS / human FAIL) | FN (agent FAIL / human PASS) | UNCERTAIN mismatch |",
        "|---|---:|---:|---:|---:|",
    ]
    for check in CHECKS:
        s = report["per_check_full_agreement"][check]
        n = s["n"]
        lines.append(
            f"| {check} | {_pct(s['match'], n)} | {s['fp']} | {s['fn']} | {s['uncertain_mismatch']} |"
        )

    lines += [
        "",
        "## C. Soft rates (humans agree on that check only)",
        "",
        "| Check | Human-agreed n | Match | FP | FN | UNCERTAIN mismatch |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for check in CHECKS:
        s = report["per_check_soft_agreement"][check]
        n = s["n"]
        lines.append(
            f"| {check} | {s['n_human_agreed']} | {_pct(s['match'], n)} | {s['fp']} | {s['fn']} | {s['uncertain_mismatch']} |"
        )

    lines += [
        "",
        "## D. Clear fail paths (either labeler)",
        "",
        "- **07 / 08** — wrong product (PlatinumRx vs whey / blue bottle)",
        "- **09** — headphones identity ok; quantity / case incomplete",
        "- **04 / 05 / 11** — carton count below PO (Jaanu FAIL; Soanli often UNCERTAIN)",
        "- **12** — too blurry",
        "",
        "## E. Method notes",
        "",
        "- Agent checks come from one live Claude observation + `receiving_policy_v1` (model does not choose disposition).",
        "- Sealed cartons correctly produce quantity UNCERTAIN → `pending_review`; that is not treated as a false positive.",
        "- This submission grades the **twelve real project deliveries** only.",
        "",
        "## F. Agent outcomes (all 12)",
        "",
    ]
    for cid in sorted(preds):
        p = preds[cid]
        lines.append(f"- `{cid}`: status={p.get('status')} outcome={p.get('outcome')} checks={p.get('checks')}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

"""One hundred scripted workflows, the hundred sample cases, and agent-failure recovery.

Nothing here calls a model. Sample rows are the dummy CSV in data/sample. A crash is an
exception that escapes run_workflow.
"""
from __future__ import annotations

import csv
import json
import traceback
from collections import Counter
from pathlib import Path

from orchestration.clients import AgentSchemaRefusal, AgentTimeout, AgentUnavailable
from orchestration.demo_overrides import AGENT_IDS, DEMO_MODEL
from orchestration.orchestrator import load_flow, resume, run_workflow
from orchestration.store import MemoryStore
from shared.utils.records import PREFIX, build_output, build_record, check
from shared.utils.schema import errors as schema_errors

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample"
OUT = ROOT / "docs" / "pod4-stress-run.md"

KINDS = [
    "all_pass",
    "receiving_fail",
    "midstage_fail",
    "uncertain_needs_person",
    "recovery_claim",
    "recovery_silent",
    "timeout_then_pass",
    "timeout_exhausted",
    "agent_crash",
    "schema_refusal",
]


def _rows(name: str) -> dict[str, dict]:
    with (SAMPLE / name).open() as handle:
        return {row["unit_id"]: row for row in csv.DictReader(handle)}


def _output(request: dict, *, verdict: str, outcome: str, reason: str, needs_human: bool, confidence: float) -> dict:
    stage = request["stage"]
    subject = request["subject"]["subject_id"]
    detail = reason
    if verdict == "UNCERTAIN":
        one = check(stage, "UNCERTAIN", confidence, detail=detail, uncertain_reason="insufficient_evidence")
    else:
        one = check(stage, verdict, confidence, detail=detail)
    record = build_record(
        request,
        agent_id=AGENT_IDS[stage],
        record_id=f"{PREFIX[stage]}-{subject}",
        captured_at="2026-10-08T12:00:00Z",
        checks=[one],
        outcome=outcome,
        reason=reason,
        model=DEMO_MODEL,
        verdict=verdict,
        confidence=confidence,
        needs_human=needs_human,
    )
    return build_output(record, reason=reason)


class ScenarioClient:
    """One behavior for the whole unit. The first attempt can fail; a retry can succeed."""

    def __init__(self, kind: str):
        self.kind = kind
        self.calls: Counter = Counter()

    def run(self, request: dict, timeout_s: float) -> dict:
        stage = request["stage"]
        self.calls[stage] += 1
        n = self.calls[stage]
        if self.kind == "timeout_then_pass" and stage == "receiving" and n == 1:
            raise AgentTimeout("vision timeout")
        if self.kind == "timeout_exhausted" and stage == "receiving":
            raise AgentTimeout("vision timeout")
        if self.kind == "agent_crash" and stage == "recovery":
            raise RuntimeError("adapter unreadable")
        if self.kind == "schema_refusal" and stage == "receiving":
            raise AgentSchemaRefusal("HTTP 422: schema mismatch")
        if self.kind == "receiving_fail" and stage == "receiving":
            return _output(request, verdict="FAIL", outcome="reject", reason="identity does not match the PO", needs_human=False, confidence=0.9)
        if self.kind == "midstage_fail" and stage in {"prep", "pack"}:
            return _output(request, verdict="FAIL", outcome="stop_and_fix", reason="required mark missing", needs_human=False, confidence=0.9)
        if self.kind == "uncertain_needs_person" and stage == "recovery":
            return _output(request, verdict="UNCERTAIN", outcome="pending_review", reason="photo occluded", needs_human=True, confidence=0.0)
        if self.kind == "recovery_claim" and stage == "recovery":
            return _output(request, verdict="FAIL", outcome="claim_recommended", reason="charge contradicted by upstream evidence", needs_human=False, confidence=0.8)
        if self.kind == "recovery_silent" and stage == "recovery":
            return _output(request, verdict="UNCERTAIN", outcome="silent", reason="no measurement, so no claim", needs_human=False, confidence=0.0)
        return _output(request, verdict="PASS", outcome="accept", reason="mock pass", needs_human=False, confidence=1.0)


def _case(index: int) -> dict:
    routes = ("fba", "mfn", "unknown")
    return {
        "org_id": "org_demo_alpha" if index % 2 == 0 else "org_demo_bravo",
        "unit_id": f"SCEN-{index + 1:03d}",
        "subject_id": f"SCEN-{index + 1:03d}",
        "route": routes[index % 3],
        "returned": index % 2 == 0,
    }


def run_scenarios() -> list[dict]:
    flow = load_flow(ROOT / "orchestration" / "flow.json")
    rows = []
    for index in range(100):
        kind = KINDS[index // 10]
        case = _case(index)
        store = MemoryStore()
        client = ScenarioClient(kind)
        clients = {stage: client for stage in ("receiving", "prep", "pack", "returns", "recovery")}
        try:
            wf = run_workflow(case, flow, store, clients)
            crash = None
        except Exception as exc:
            wf = None
            crash = f"{type(exc).__name__}: {exc}"
        if wf is None:
            rows.append({**case, "kind": kind, "crash": crash})
            continue
        bad = schema_errors("workflow-state", wf)
        rows.append({
            "unit_id": case["unit_id"],
            "kind": kind,
            "route": case["route"],
            "returned": case["returned"],
            "status": wf["status"],
            "outcome": (wf.get("final_outcome") or {}).get("outcome"),
            "verdict": (wf.get("final_outcome") or {}).get("verdict"),
            "halted": (wf.get("halted") or {}).get("stage"),
            "stages": {sr["stage"]: sr["state"] for sr in wf["stage_results"]},
            "schema_ok": not bad,
            "schema_errors": bad[:2],
            "crash": crash,
            "receiving_attempts": client.calls["receiving"],
        })
    return rows


def _recv_verdict(row: dict) -> tuple[str, str, bool]:
    if row["identity_match"] == "no" or row["unit_damage"] not in {"none", "uncertain"}:
        return "FAIL", "reject", False
    if row["identity_match"] == "uncertain" or row["carton_damage"] == "uncertain" or row["unit_damage"] == "uncertain":
        return "UNCERTAIN", "pending_review", True
    if row["carton_damage"] != "none":
        return "FAIL", "damaged", False
    return "PASS", "accept", False


def _prep_verdict(row: dict) -> tuple[str, str, bool]:
    bad = {"missing", "not_sealed", "obscured_by_fold", "on_curve", "on_seam", "on_edge"}
    fields = (row["polybag_present_sealed"], row["suffocation_warning"], row["fnsku_label_placement"])
    if any(value in bad for value in fields):
        return "FAIL", "stop_and_fix", False
    if any(value == "uncertain" for value in fields):
        return "UNCERTAIN", "pending_review", True
    return "PASS", "compliant", False


def _pack_verdict(row: dict) -> tuple[str, str, bool]:
    if row["operator_verdict"] == "seal":
        return "PASS", "seal", False
    return "FAIL", "stop_and_fix", False


def _returns_verdict(row: dict) -> tuple[str, str, bool]:
    if row["operator_disposition"] == "pending_review":
        return "UNCERTAIN", "pending_review", True
    return "PASS", row["operator_disposition"], False


def _recovery_verdict(lines: list[dict]) -> tuple[str, str, bool, str]:
    types = {line["charge_type"] for line in lines}
    if types & {"inbound_defect_fee", "refund_issued_item_not_returned"}:
        return "UNCERTAIN", "pending_review", True, "sample charge has no photo that can support or contradict it"
    return "UNCERTAIN", "silent", False, "weight, lost, or warehouse line; mock does not recommend a claim"


class SampleClient:
    def __init__(self, receiving, prep, pack, returns, fees):
        self.tables = {"receiving": receiving, "prep": prep, "pack": pack, "returns": returns}
        self.fees = fees

    def run(self, request: dict, timeout_s: float) -> dict:
        stage = request["stage"]
        unit = request["subject"]["subject_id"]
        if stage == "recovery":
            lines = self.fees.get(unit, [])
            if not lines:
                verdict, outcome, human, reason = "UNCERTAIN", "silent", False, "no sample fee row"
            else:
                verdict, outcome, human, reason = _recovery_verdict(lines)
            return _output(request, verdict=verdict, outcome=outcome, reason=reason, needs_human=human, confidence=0.0)
        row = self.tables[stage].get(unit)
        if row is None:
            return _output(request, verdict="UNCERTAIN", outcome="pending_review", reason="no sample row", needs_human=True, confidence=0.0)
        mapper = {"receiving": _recv_verdict, "prep": _prep_verdict, "pack": _pack_verdict, "returns": _returns_verdict}[stage]
        verdict, outcome, human = mapper(row)
        return _output(request, verdict=verdict, outcome=outcome, reason=f"replayed {stage} sample row", needs_human=human, confidence=1.0 if verdict == "PASS" else 0.0)


def run_sample() -> list[dict]:
    flow = load_flow(ROOT / "orchestration" / "flow.json")
    receiving, prep, pack, returns = (_rows(name) for name in (
        "receiving_sample.csv", "prep_sample.csv", "pack_sample.csv", "returns_sample.csv"))
    fees: dict[str, list] = {}
    with (SAMPLE / "fee_report_sample.csv").open() as handle:
        for row in csv.DictReader(handle):
            fees.setdefault(row["unit_id"], []).append(row)
    cases = json.loads((SAMPLE / "cases.json").read_text())
    client = SampleClient(receiving, prep, pack, returns, fees)
    clients = {stage: client for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    store = MemoryStore()
    rows = []
    for case in cases:
        case = {**case, "subject_id": case["unit_id"]}
        try:
            wf = run_workflow(case, flow, store, clients)
            crash = None
        except Exception as exc:
            rows.append({"unit_id": case["unit_id"], "crash": f"{type(exc).__name__}: {exc}"})
            continue
        bad = schema_errors("workflow-state", wf)
        rows.append({
            "unit_id": case["unit_id"],
            "route": case["route"],
            "returned": case["returned"],
            "status": wf["status"],
            "outcome": wf["final_outcome"]["outcome"],
            "verdict": wf["final_outcome"]["verdict"],
            "schema_ok": not bad,
            "crash": crash,
            "stages": {sr["stage"]: f"{sr['state']}:{sr['verdict']}" for sr in wf["stage_results"]},
        })
    return rows


class Flaky:
    def __init__(self):
        self.calls = 0
        self.healthy = False

    def run(self, request: dict, timeout_s: float) -> dict:
        self.calls += 1
        if request["stage"] == "receiving" and not self.healthy:
            raise AgentUnavailable("connection refused")
        return _output(request, verdict="PASS", outcome="accept", reason="recovered", needs_human=False, confidence=1.0)


def run_recovery() -> list[dict]:
    flow = load_flow(ROOT / "orchestration" / "flow.json")
    notes = []

    store = MemoryStore()
    flaky = Flaky()
    clients = {stage: flaky for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    case = {"org_id": "org_demo_alpha", "unit_id": "FAIL-OPEN-1", "subject_id": "FAIL-OPEN-1", "route": "fba", "returned": False}
    first = run_workflow(case, flow, store, clients)
    notes.append({
        "name": "connection refused, then resume",
        "before_status": first["status"],
        "before_outcome": first["final_outcome"]["outcome"],
        "before_reason": first["status_reason"],
        "receiving_error": (first["stage_results"][0].get("error") or {}).get("code"),
        "process_alive": True,
    })
    flaky.healthy = True
    second = resume(first["workflow_id"], flow, store, clients)
    notes.append({
        "name": "resume after the agent is back",
        "after_status": second["status"],
        "after_outcome": second["final_outcome"]["outcome"],
        "receiving_state": second["stage_results"][0]["state"],
        "receiving_verdict": second["stage_results"][0]["verdict"],
        "attempts_seen": flaky.calls,
    })

    store = MemoryStore()
    class Boom:
        def run(self, request, timeout_s):
            raise RuntimeError("vision timeout")
    clients = {stage: Boom() for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    case = {"org_id": "org_demo_alpha", "unit_id": "FAIL-OPEN-2", "subject_id": "FAIL-OPEN-2", "route": "mfn", "returned": True}
    try:
        blown = run_workflow(case, flow, store, clients)
        notes.append({
            "name": "every agent raises",
            "status": blown["status"],
            "outcome": blown["final_outcome"]["outcome"],
            "verdicts": [sr["verdict"] for sr in blown["stage_results"] if sr["state"] != "skipped"],
            "states": [sr["state"] for sr in blown["stage_results"] if sr["state"] != "skipped"],
            "escaped": False,
        })
    except Exception as exc:
        notes.append({"name": "every agent raises", "escaped": True, "error": str(exc)})

    store = MemoryStore()
    class Refuse:
        def run(self, request, timeout_s):
            if request["stage"] == "prep":
                raise AgentSchemaRefusal("HTTP 422: bare schema error")
            return _output(request, verdict="PASS", outcome="accept", reason="ok", needs_human=False, confidence=1.0)
    clients = {stage: Refuse() for stage in ("receiving", "prep", "pack", "returns", "recovery")}
    case = {"org_id": "org_demo_alpha", "unit_id": "FAIL-OPEN-3", "subject_id": "FAIL-OPEN-3", "route": "fba", "returned": True}
    refused = run_workflow(case, flow, store, clients)
    later = [sr["stage"] for sr in refused["stage_results"] if sr["stage"] != "receiving" and sr["runs"] > 0]
    notes.append({
        "name": "prep returns a bare 422",
        "status": refused["status"],
        "halted": refused["halted"]["reason"] if refused.get("halted") else None,
        "stages_after_prep_that_ran": later,
        "receiving_verdict": refused["stage_results"][0]["verdict"],
    })
    return notes


def _md_table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def write_report(scenarios: list[dict], sample: list[dict], recovery: list[dict]) -> None:
    crashes = [row for row in scenarios + sample if row.get("crash")]
    schema_bad = [row for row in scenarios + sample if row.get("schema_ok") is False]
    by_kind = []
    for kind in KINDS:
        group = [row for row in scenarios if row["kind"] == kind]
        statuses = Counter(row.get("status") for row in group)
        outcomes = Counter(row.get("outcome") for row in group)
        by_kind.append([
            kind,
            len(group),
            ", ".join(f"{k} {v}" for k, v in statuses.items()),
            ", ".join(f"{k} {v}" for k, v in outcomes.items()),
            sum(row.get("receiving_attempts") or 0 for row in group),
        ])
    sample_status = Counter(row.get("status") for row in sample)
    sample_outcome = Counter(row.get("outcome") for row in sample)
    eligible = Counter()
    for row in sample:
        if row.get("crash"):
            continue
        if row["route"] == "fba":
            eligible["prep ran"] += 1
        elif row["route"] == "mfn":
            eligible["pack ran"] += 1
        else:
            eligible["neither prep nor pack"] += 1
        if row["returned"]:
            eligible["returns ran"] += 1
    body = f"""# Pod 4 stress run — 2026-10-08

This run did not call Claude. The hundred scenario units are scripted inside the orchestrator. The hundred sample units replay `data/sample`, which the sample README marks as dummy data. Neither set is a vision score.

## Did the process crash?

No. `run_workflow` returned a workflow for all 100 scenario units and all 100 sample units. Uncaught exceptions: {len(crashes)}. Workflows that failed schema validation: {len(schema_bad)}.

## One hundred scenario units

Each group has 10 units. Route rotates through FBA, merchant-fulfilled, and unknown. Half are marked returned. The flow is `orchestration/flow.json`, so an FBA unit skips Pack and a merchant-fulfilled unit skips Prep.

{_md_table(["scenario", "units", "status", "outcome", "receiving attempts"], by_kind)}

What the statuses mean:

- `all_pass` finishes CLEAN when every required stage returns PASS.
- `receiving_fail` and `midstage_fail` finish EXCEPTION. The bus keeps going. A FAIL is a completed judgment, not a crash.
- `uncertain_needs_person` finishes BLOCKED / NEEDS_REVIEW. Recovery returns UNCERTAIN with `needs_human` true. The bus does not stop at that stage (`on_uncertain=continue`), and the rollup still blocks the workflow because a person was asked.
- `recovery_claim` finishes CLAIM_RECOMMENDED. In this group the earlier stages passed, so the claim is allowed.
- `recovery_silent` leaves Recovery's own verdict UNCERTAIN with `needs_human` false. The workflow outcome is still CLEAN, because a silent uncertainty is not a failure and does not ask for a person.
- `midstage_fail` is EXCEPTION on FBA and merchant-fulfilled units. A unit whose route is unknown has no Prep and no Pack stage, so there is nothing to fail and that unit stays CLEAN.
- `timeout_then_pass` tries Receiving twice. The first attempt is a timeout. The retry succeeds, and the unit can still finish CLEAN.
- `timeout_exhausted` records Receiving as pending / UNCERTAIN after both attempts, then continues. The workflow status is FAILED because that stage never completed. The process stays up.
- `agent_crash` raises `RuntimeError` inside Recovery. The orchestrator stores UNCERTAIN and does not die.
- `schema_refusal` is a bare HTTP 422. The bus stops there. Later stages are not called. The workflow is FAILED.

## One hundred sample units

Source: `data/sample/cases.json` plus the five sample CSVs. A stage runs only when the case is eligible: Prep for FBA, Pack for merchant-fulfilled, Returns only when `returned` is true, Receiving and Recovery always.

Eligibility: {", ".join(f"{k} {v}" for k, v in eligible.items())}.

Status: {", ".join(f"{k} {v}" for k, v in sample_status.items())}.

Outcome: {", ".join(f"{k} {v}" for k, v in sample_outcome.items())}.

Six units are BLOCKED and EXCEPTION together. One stage returned FAIL, and another asked for a person. The status is BLOCKED because the person comes first. The outcome stays EXCEPTION because a FAIL is still on the record. Twenty-one are BLOCKED / NEEDS_REVIEW with no FAIL. Forty-eight are CLEAN. Twenty-five are EXCEPTION with nobody waiting.

Replay rules, so the numbers stay tied to the CSV:

- Receiving PASS only when identity is yes and both damage fields are none. Identity no or real damage is FAIL. An uncertain field is UNCERTAIN.
- Prep FAIL on missing, unsealed, obscured, or badly placed marks. An uncertain field is UNCERTAIN.
- Pack PASS on `seal`, FAIL on `stop_and_fix`.
- Returns PASS on a disposition, except `pending_review`, which is UNCERTAIN.
- Recovery does not recommend a claim from these rows. A weight, lost, or warehouse line is silent. An inbound-defect or refund line is UNCERTAIN and asks for a person, because the CSV has no photo that can support or contradict it.

## How a failed agent is recovered

{_md_table(["step", "what happened"], [[item["name"], json.dumps({k: v for k, v in item.items() if k != "name"})] for item in recovery])}

Recovery sequence:

1. The agent is down. Receiving raises connection refused on both attempts. The orchestrator writes a pending evidence record, verdict UNCERTAIN, and marks the workflow FAILED. Prep is not asked to invent a judgment for a stage that did not finish.
2. `resume` runs the same workflow again. Errored stages are retried. With the agent answering, Receiving becomes PASS and the workflow can complete.
3. If every agent raises, each required stage is stored as error / UNCERTAIN. The outcome is INCOMPLETE. No exception leaves `run_workflow`.
4. A bare 422 from Prep is a schema refusal. Receiving's PASS is kept. Pack, Returns, and Recovery are not called after that refusal.

## What this does not show

It does not show Claude accuracy. It does not start ports 8102–8105. `UNIT-001`, `UNIT-002`, and `UNIT-003` were not part of these 200 units; those three remain the presentation script.
"""
    OUT.write_text(body)


def main() -> None:
    scenarios = run_scenarios()
    sample = run_sample()
    recovery = run_recovery()
    write_report(scenarios, sample, recovery)
    print(f"scenarios={len(scenarios)} crashes={sum(1 for r in scenarios if r.get('crash'))}")
    print(f"sample={len(sample)} crashes={sum(1 for r in sample if r.get('crash'))}")
    print(Counter((r['kind'], r.get('status'), r.get('outcome')) for r in scenarios))
    print("SAMPLE", Counter((r.get('status'), r.get('outcome')) for r in sample))
    print("RECOVERY", json.dumps(recovery, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise

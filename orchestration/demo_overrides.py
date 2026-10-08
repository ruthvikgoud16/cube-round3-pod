"""Scripted presentation path for three unit ids.

These records are not Claude judgments. model.name is demo-override and model.calls is 0.
Any other subject, and these three with context.live true, go to the real agents.
"""
from __future__ import annotations

from shared.utils.records import build_output, build_record, check

DEMO_UNITS = {"UNIT-001", "UNIT-002", "UNIT-003"}
DEMO_MODEL = {
    "name": "demo-override",
    "version": "pod4-2026-10-08",
    "provider": None,
    "prompt_version": None,
    "calls": 0,
    "cost_usd": 0,
}
AGENT_IDS = {
    "receiving": "receiving-manager@1.0.0",
    "prep": "prep-manager@1.0.0",
    "pack": "pack-manager@1.0.0",
    "returns": "returns-manager@0.1.0",
    "recovery": "recovery-manager@1.0.0",
}


def demo_applies(request: dict) -> bool:
    subject = (request.get("subject") or {}).get("subject_id")
    if subject not in DEMO_UNITS:
        return False
    context = request.get("context") or {}
    return context.get("live") is not True


class DemoClient:
    """Returns a contract-valid Agent Output without calling a model or a network."""

    def run(self, request: dict, timeout_s: float) -> dict:
        return demo_output(request)


def demo_output(request: dict) -> dict:
    subject = request["subject"]["subject_id"]
    stage = request["stage"]
    prior = {row.get("stage"): row.get("record_id") for row in request.get("previous_evidence") or []}
    spec = _spec(subject, stage, prior)
    record = build_record(
        request,
        agent_id=AGENT_IDS[stage],
        record_id=f"{_prefix(stage)}-{subject}",
        captured_at=request.get("context", {}).get("captured_at") or "2026-10-10T09:00:00Z",
        checks=spec["checks"],
        outcome=spec["outcome"],
        reason=spec["reason"],
        model=DEMO_MODEL,
        status="completed",
        verdict=spec["verdict"],
        confidence=spec["confidence"],
        needs_human=spec["needs_human"],
        upstream_refs=[row["record_id"] for row in request.get("previous_evidence") or [] if row.get("record_id")],
        payload={
            "demo": True,
            "live_available": True,
            "evidence_flags": spec["flags"],
            "note": "Presentation script. Set context.live true to call the real agent on this same unit id.",
        },
    )
    return build_output(record, next_step=spec["next_step"], reason=spec["reason"])


def _prefix(stage: str) -> str:
    return {"receiving": "RCV", "prep": "PRP", "pack": "PCK", "returns": "RTN", "recovery": "RCY"}[stage]


def _pass(key: str, detail: str) -> dict:
    return check(key, "PASS", 1.0, detail=detail)


def _spec(subject: str, stage: str, prior: dict) -> dict:
    if subject == "UNIT-001":
        return _happy(stage)
    if subject == "UNIT-002":
        return _uncertain(stage)
    return _contradiction(stage, prior)


def _happy(stage: str) -> dict:
    detail = {
        "receiving": "Demo receipt matches the purchase order.",
        "prep": "Demo prep requirements are met.",
        "pack": "Demo open box matches the order lines.",
        "returns": "Demo return is complete and restockable.",
        "recovery": "Demo fee is not contradicted. No claim.",
    }[stage]
    outcome = {
        "receiving": "accept",
        "prep": "compliant",
        "pack": "seal",
        "returns": "restock",
        "recovery": "no_claim",
    }[stage]
    key = {
        "receiving": "identity_match",
        "prep": "prep_compliance",
        "pack": "line_match",
        "returns": "completeness",
        "recovery": "charge_position",
    }[stage]
    return {
        "verdict": "PASS",
        "confidence": 1.0,
        "needs_human": False,
        "outcome": outcome,
        "reason": detail,
        "flags": ["PASS"],
        "next_step": "continue",
        "checks": [_pass(key, detail)],
    }


def _uncertain(stage: str) -> dict:
    if stage != "returns":
        row = _happy(stage)
        if stage == "recovery":
            row["verdict"] = "UNCERTAIN"
            row["confidence"] = 0.0
            row["needs_human"] = True
            row["outcome"] = "pending_review"
            row["reason"] = "Returns did not finish a disposition, so Recovery makes no claim."
            row["flags"] = ["UNCERTAIN"]
            row["next_step"] = "review"
            row["checks"] = [check(
                "charge_position", "UNCERTAIN", 0.0,
                detail=row["reason"], uncertain_reason="insufficient_evidence",
            )]
        return row
    reason = "The return photo does not show the adapter. Completeness stays uncertain."
    return {
        "verdict": "UNCERTAIN",
        "confidence": 0.0,
        "needs_human": True,
        "outcome": "pending_review",
        "reason": reason,
        "flags": ["UNCERTAIN", "occluded"],
        "next_step": "review",
        "checks": [check(
            "completeness", "UNCERTAIN", 0.0,
            detail=reason, uncertain_reason="occluded",
        )],
    }


def _contradiction(stage: str, prior: dict) -> dict:
    if stage == "prep":
        return {
            "verdict": "PASS",
            "confidence": 1.0,
            "needs_human": False,
            "outcome": "compliant",
            "reason": "Demo prep record: the polybag warning label is present.",
            "flags": ["PASS"],
            "next_step": "continue",
            "checks": [_pass("suffocation_warning_presence", "Warning label recorded present.")],
        }
    if stage == "returns":
        return {
            "verdict": "FAIL",
            "confidence": 1.0,
            "needs_human": False,
            "outcome": "pending_review",
            "reason": "Demo returns record: the warning label is missing.",
            "flags": ["FAIL", "missing_label"],
            "next_step": "route_to_recovery",
            "checks": [check(
                "label_present", "FAIL", 1.0,
                detail="The warning label is not on the returned unit.",
            )],
        }
    if stage == "recovery":
        cited = [prior[name] for name in ("prep", "returns") if prior.get(name)]
        reason = (
            "CONTRADICTS the inbound defect fee. "
            "Prep says the warning label is present and Returns says it is missing."
        )
        return {
            "verdict": "FAIL",
            "confidence": 1.0,
            "needs_human": False,
            "outcome": "claim_recommended",
            "reason": reason,
            "flags": ["CONTRADICTS"],
            "next_step": "complete",
            "checks": [check(
                "charge_position", "FAIL", 1.0,
                detail=reason, evidence_refs=cited,
            )],
        }
    return _happy(stage)

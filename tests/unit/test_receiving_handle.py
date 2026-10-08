"""Contract tests for Receiving handle() — mock mode, no API key required."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.receiving.app import handle
from shared.utils.schema import validate

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv("RECEIVING_MODE", "mock")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def _request(subject_id: str, org_id: str = "org_demo_alpha", **ctx):
    return {
        "schema_version": "1.0",
        "request_id": f"req-{subject_id}",
        "workflow_id": f"WF-{org_id}-{subject_id}",
        "stage": "receiving",
        "subject": {"org_id": org_id, "subject_id": subject_id, "route": "fba"},
        "previous_evidence": [],
        "context": ctx,
        "inputs": [],
    }


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["subject_id"])
def test_fixture_cases_match_expected_outcome(case):
    out = handle(_request(case["subject_id"]))
    validate("agent-output", out)
    assert out["stage"] == "receiving"
    assert out["evidence"]["subject"]["unit_scope"] == "po_line"
    assert out["evidence"]["record_id"].startswith("RCV-")
    assert out["evidence"]["decision"]["outcome"] == case["expected_outcome"]
    keys = [c["check_key"] for c in out["evidence"]["checks"]]
    assert keys == [
        "identity_match",
        "carton_count",
        "quantity",
        "carton_damage",
        "unit_damage",
        "quality_flags",
    ]


def test_tenancy_rejects_unknown_org():
    with pytest.raises(LookupError):
        handle(_request("UNIT-RCV-01", org_id="org_evil"))


def test_idempotent_record_id():
    a = handle(_request("UNIT-RCV-01"))
    b = handle(_request("UNIT-RCV-01"))
    assert a["evidence"]["record_id"] == b["evidence"]["record_id"]


def test_shortfall_is_supplier_side_only():
    out = handle(_request("UNIT-RCV-03"))
    payload = out["evidence"]["payload"]
    assert payload["shortfall_units"] == 3
    assert payload["claim_boundary"] == "supplier_side_only"
    assert payload["finding_notes"]["F-10"]


def test_uncertain_counts_hold_for_human():
    out = handle(_request("UNIT-RCV-10"))
    assert out["evidence"]["decision"]["outcome"] == "pending_review"
    assert out["evidence"]["decision"]["needs_human"] is True

"""Fixture-driven observer for photo-less / CI builds.

RECEIVING_MODE=mock (default when no key, or forced).
Looks up observation by subject_id in data/fixtures/receiving/cases.json.
Never invents a PASS for missing evidence — fixtures are explicit.
"""
from __future__ import annotations

import json
from pathlib import Path

from .schema import validate_observation

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "data" / "fixtures" / "receiving" / "cases.json"


def observe_mock(*, po: dict, photos: list[dict]) -> tuple[dict, dict]:
    cases = _load_cases()
    subject_id = str(po.get("subject_id") or "")
    case = cases.get(subject_id)
    if case is None:
        # Honest default: cannot judge without a fixture or live vision
        observation = {
            "identity_match": "uncertain",
            "carton_count_visible": "uncertain",
            "cartons_observed": None,
            "quantity_visible": "uncertain",
            "units_observed": None,
            "carton_damage": "uncertain",
            "unit_damage": "uncertain",
            "quality_flags": [],
            "quality_flags_uncertain": True,
            "evidence": (
                f"Mock mode: no fixture for {subject_id or 'unknown'}; "
                "counts and identity left UNCERTAIN."
            ),
            "confidence": None,
        }
    else:
        observation = dict(case["observation"])
    validate_observation(observation)
    meta = {
        "name": "fixture-mock",
        "version": case.get("fixture_version", "mock-1") if case else "mock-1",
        "latency_ms": 0,
        "prompt_version": "receiving-mock-v1",
        "calls": 0,
    }
    return observation, meta


def _load_cases() -> dict:
    if not CASES_PATH.is_file():
        return {}
    data = json.loads(CASES_PATH.read_text())
    return {row["subject_id"]: row for row in data.get("cases", [])}

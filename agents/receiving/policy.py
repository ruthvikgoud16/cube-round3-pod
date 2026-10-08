"""Deterministic receiving_policy_v1. Model never chooses disposition."""
from __future__ import annotations

from typing import Any

from shared.utils.records import check

from .shots import refs_for

POLICY_VERSION = "receiving_policy_v1"
DAMAGE_BAD = {"crushing", "water", "tears"}


def apply_receiving_policy(
    *,
    po: dict,
    observation: dict,
    photos: list[dict] | None = None,
    evidence_refs: list[str] | None = None,
    model_version: str,
    latency_ms: int | None,
) -> tuple[list[dict], str, str, str, dict[str, Any]]:
    photos = photos or []
    all_refs = evidence_refs or [p["ref"] for p in photos]
    pallet_refs = refs_for(photos, "pallet") if photos else all_refs
    carton_refs = refs_for(photos, "carton", "pallet") if photos else all_refs
    unit_refs = refs_for(photos, "unit", "carton") if photos else all_refs

    conf = observation.get("confidence")
    detail = observation.get("evidence") or ""

    identity = _yn(observation.get("identity_match"))
    carton_damage = _damage(observation.get("carton_damage"))
    unit_damage = _damage(observation.get("unit_damage"))

    cartons_ordered = po.get("cartons_ordered")
    qty_ordered = po.get("qty_ordered")
    cartons_obs = observation.get("cartons_observed")
    units_obs = observation.get("units_observed")

    if observation.get("carton_count_visible") != "yes" or cartons_obs is None or cartons_ordered is None:
        carton_count = "UNCERTAIN"
        carton_observed: Any = cartons_obs
        carton_reason = "insufficient_evidence"
    else:
        carton_count = "PASS" if int(cartons_obs) == int(cartons_ordered) else "FAIL"
        carton_observed = int(cartons_obs)
        carton_reason = None

    if observation.get("quantity_visible") != "yes" or units_obs is None or qty_ordered is None:
        quantity = "UNCERTAIN"
        qty_observed: Any = units_obs
        qty_reason = "insufficient_evidence"
    else:
        quantity = "PASS" if int(units_obs) == int(qty_ordered) else "FAIL"
        qty_observed = int(units_obs)
        qty_reason = None

    flags = list(observation.get("quality_flags") or [])
    if observation.get("quality_flags_uncertain"):
        quality = "UNCERTAIN"
        quality_reason = "insufficient_evidence"
    else:
        quality = "FAIL" if flags else "PASS"
        quality_reason = None

    checks = [
        check(
            "identity_match",
            identity,
            conf,
            expected=f"{po.get('sku')} ({po.get('product_name')})",
            observed=observation.get("identity_match"),
            detail=detail,
            evidence_refs=unit_refs or carton_refs,
            uncertain_reason="poor_image" if identity == "UNCERTAIN" else None,
        ),
        check(
            "carton_count",
            carton_count,
            conf if carton_count != "UNCERTAIN" else None,
            expected=cartons_ordered,
            observed=carton_observed,
            detail=detail,
            evidence_refs=pallet_refs,
            uncertain_reason=carton_reason,
        ),
        check(
            "quantity",
            quantity,
            conf if quantity != "UNCERTAIN" else None,
            expected=qty_ordered,
            observed=qty_observed,
            detail=detail,
            evidence_refs=unit_refs or pallet_refs,
            uncertain_reason=qty_reason,
        ),
        check(
            "carton_damage",
            carton_damage,
            conf,
            expected="none",
            observed=observation.get("carton_damage"),
            detail=detail,
            evidence_refs=carton_refs,
            uncertain_reason="poor_image" if carton_damage == "UNCERTAIN" else None,
        ),
        check(
            "unit_damage",
            unit_damage,
            conf,
            expected="none",
            observed=observation.get("unit_damage"),
            detail=detail,
            evidence_refs=unit_refs,
            uncertain_reason="poor_image" if unit_damage == "UNCERTAIN" else None,
        ),
        check(
            "quality_flags",
            quality,
            conf if quality != "UNCERTAIN" else None,
            expected=list(po.get("spec_components") or []),
            observed=flags,
            detail=detail,
            evidence_refs=unit_refs,
            uncertain_reason=quality_reason,
        ),
    ]

    verdicts = {c["verdict"] for c in checks}
    if "FAIL" in verdicts:
        verdict = "FAIL"
    elif "UNCERTAIN" in verdicts:
        verdict = "UNCERTAIN"
    else:
        verdict = "PASS"

    identity_fail = identity == "FAIL"
    fail_keys = [c["check_key"] for c in checks if c["verdict"] == "FAIL"]
    uncertain_keys = [c["check_key"] for c in checks if c["verdict"] == "UNCERTAIN"]

    if uncertain_keys:
        outcome = "pending_review"
        reason = (
            f"{POLICY_VERSION}: UNCERTAIN on {', '.join(uncertain_keys)}; "
            "UNCERTAIN is not a pass. Holding for a person."
        )
    elif verdict == "PASS":
        outcome = "accept"
        reason = f"{POLICY_VERSION}: all receiving checks passed."
    elif identity_fail or len(fail_keys) >= 3:
        outcome = "reject"
        reason = f"{POLICY_VERSION}: reject due to {', '.join(fail_keys)}."
    else:
        outcome = "accept_with_exceptions"
        reason = f"{POLICY_VERSION}: accept with exceptions: {', '.join(fail_keys)}."

    shortfall = None
    if qty_ordered is not None and isinstance(units_obs, int):
        shortfall = max(int(qty_ordered) - int(units_obs), 0)
    carton_shortfall = None
    if cartons_ordered is not None and isinstance(cartons_obs, int):
        carton_shortfall = max(int(cartons_ordered) - int(cartons_obs), 0)

    payload = {
        "policy_version": POLICY_VERSION,
        "supplier": po.get("supplier"),
        "qty_ordered": qty_ordered,
        "qty_received": units_obs if isinstance(units_obs, int) else None,
        "cartons_ordered": cartons_ordered,
        "cartons_received": cartons_obs if isinstance(cartons_obs, int) else None,
        "shortfall_units": shortfall,
        "shortfall_cartons": carton_shortfall,
        "quality_flags": flags,
        "observation_confidence": conf,
        "claim_boundary": "supplier_side_only",
        "shot_roles": {
            "pallet": pallet_refs,
            "carton": carton_refs,
            "unit": unit_refs,
        },
        "trace": {
            "uncertain_checks": uncertain_keys,
            "failed_checks": fail_keys,
            "human_required": bool(uncertain_keys) or outcome == "pending_review",
        },
    }
    return checks, outcome, verdict, reason, payload


def _yn(value: str | None) -> str:
    if value == "yes":
        return "PASS"
    if value == "no":
        return "FAIL"
    return "UNCERTAIN"


def _damage(value: str | None) -> str:
    if value == "none":
        return "PASS"
    if value in DAMAGE_BAD:
        return "FAIL"
    return "UNCERTAIN"

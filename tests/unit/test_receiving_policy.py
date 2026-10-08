"""Policy unit tests — no API key required."""
from agents.receiving.policy import apply_receiving_policy


def test_accept_all_pass():
    po = {"sku": "SKU-1", "product_name": "Lamp", "qty_ordered": 24, "cartons_ordered": 2, "supplier": "East"}
    obs = {
        "identity_match": "yes",
        "carton_count_visible": "yes",
        "cartons_observed": 2,
        "quantity_visible": "yes",
        "units_observed": 24,
        "carton_damage": "none",
        "unit_damage": "none",
        "quality_flags": [],
        "evidence": "Two undamaged cartons of the named lamp are visible.",
        "confidence": 0.9,
    }
    checks, outcome, verdict, reason, payload = apply_receiving_policy(
        po=po,
        observation=obs,
        photos=[{"ref": "01_pallet.jpg"}, {"ref": "02_carton.jpg"}, {"ref": "03_unit.jpg"}],
        model_version="x",
        latency_ms=10,
    )
    assert verdict == "PASS"
    assert outcome == "accept"
    assert [c["check_key"] for c in checks] == [
        "identity_match",
        "carton_count",
        "quantity",
        "carton_damage",
        "unit_damage",
        "quality_flags",
    ]
    assert payload["shortfall_units"] == 0
    assert payload["claim_boundary"] == "supplier_side_only"


def test_uncertain_counts_pending_review():
    po = {"sku": "SKU-1", "product_name": "Lamp", "qty_ordered": 24, "cartons_ordered": 2}
    obs = {
        "identity_match": "yes",
        "carton_count_visible": "uncertain",
        "cartons_observed": None,
        "quantity_visible": "uncertain",
        "units_observed": None,
        "carton_damage": "none",
        "unit_damage": "none",
        "quality_flags": [],
        "evidence": "Sealed cartons; counts not reliable from these angles.",
        "confidence": 0.5,
    }
    checks, outcome, verdict, *_ = apply_receiving_policy(
        po=po, observation=obs, evidence_refs=["a.jpg"], model_version="x", latency_ms=10
    )
    assert verdict == "UNCERTAIN"
    assert outcome == "pending_review"
    assert any(c["check_key"] == "quantity" and c["verdict"] == "UNCERTAIN" for c in checks)


def test_identity_fail_rejects():
    po = {"sku": "SKU-1", "product_name": "Lamp", "qty_ordered": 24, "cartons_ordered": 2}
    obs = {
        "identity_match": "no",
        "carton_count_visible": "yes",
        "cartons_observed": 2,
        "quantity_visible": "yes",
        "units_observed": 24,
        "carton_damage": "none",
        "unit_damage": "none",
        "quality_flags": [],
        "evidence": "Visible goods do not match the named SKU.",
        "confidence": 0.8,
    }
    _, outcome, verdict, *_ = apply_receiving_policy(
        po=po, observation=obs, evidence_refs=["a.jpg"], model_version="x", latency_ms=10
    )
    assert verdict == "FAIL"
    assert outcome == "reject"


def test_fail_plus_uncertain_holds():
    po = {"sku": "SKU-1", "product_name": "Lamp", "qty_ordered": 24, "cartons_ordered": 2}
    obs = {
        "identity_match": "no",
        "carton_count_visible": "uncertain",
        "cartons_observed": None,
        "quantity_visible": "uncertain",
        "units_observed": None,
        "carton_damage": "none",
        "unit_damage": "none",
        "quality_flags": [],
        "evidence": "Identity looks wrong and counts cannot be read.",
        "confidence": 0.4,
    }
    _, outcome, verdict, *_ = apply_receiving_policy(
        po=po, observation=obs, evidence_refs=["a.jpg"], model_version="x", latency_ms=10
    )
    assert verdict == "FAIL"
    assert outcome == "pending_review"


def test_shot_roles_routed_to_checks():
    po = {"sku": "SKU-1", "product_name": "Lamp", "qty_ordered": 24, "cartons_ordered": 2}
    obs = {
        "identity_match": "yes",
        "carton_count_visible": "yes",
        "cartons_observed": 2,
        "quantity_visible": "yes",
        "units_observed": 24,
        "carton_damage": "crushing",
        "unit_damage": "none",
        "quality_flags": [],
        "evidence": "Crushed carton corner; product intact.",
        "confidence": 0.8,
    }
    photos = [
        {"ref": "x/receiving/01_pallet.jpg", "shot_role": "pallet"},
        {"ref": "x/receiving/02_carton.jpg", "shot_role": "carton"},
        {"ref": "x/receiving/03_unit.jpg", "shot_role": "unit"},
    ]
    checks, outcome, *_rest = apply_receiving_policy(
        po=po, observation=obs, photos=photos, model_version="x", latency_ms=10
    )
    by_key = {c["check_key"]: c for c in checks}
    assert "01_pallet.jpg" in by_key["carton_count"]["evidence_refs"][0]
    assert "02_carton.jpg" in by_key["carton_damage"]["evidence_refs"][0]
    assert "03_unit.jpg" in by_key["identity_match"]["evidence_refs"][0]
    assert outcome == "accept_with_exceptions"

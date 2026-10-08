"""Extract purchase-order context from Agent Input."""
from __future__ import annotations

from typing import Any


def extract_po_context(request: dict) -> dict[str, Any]:
    ctx = request.get("context") or {}
    subject = request.get("subject") or {}
    refs = (subject.get("refs") or {}) if isinstance(subject.get("refs"), dict) else {}

    def pick(*keys: str, default: Any = None) -> Any:
        for key in keys:
            if key in ctx and ctx[key] not in (None, ""):
                return ctx[key]
            if key in refs and refs[key] not in (None, ""):
                return refs[key]
        return default

    qty_ordered = _as_int(pick("qty_ordered", "expected_quantity", "quantity_expected"), default=None)
    cartons_ordered = _as_int(pick("cartons_ordered", "expected_cartons"), default=None)
    components = pick("spec_components", "required_components", "parts_list", default=[])
    if isinstance(components, str):
        components = [c.strip() for c in components.replace(";", ",").split(",") if c.strip()]

    return {
        "po_number": str(pick("po_number", default="PO-UNKNOWN")),
        "po_line": str(pick("po_line", "po_line_id", default="1")),
        "supplier": pick("supplier"),
        "sku": str(pick("sku", "ordered_sku", default="UNKNOWN")),
        "asin": str(pick("asin", "ordered_asin", default="UNKNOWN")),
        "product_name": str(pick("product_name", "product_title", default=subject.get("subject_id") or "UNKNOWN")),
        "spec_colour": pick("spec_colour", "colour", "color"),
        "spec_variant": pick("spec_variant", "variant"),
        "spec_components": list(components) if isinstance(components, list) else [],
        "qty_ordered": qty_ordered,
        "cartons_ordered": cartons_ordered,
        "units_per_carton_ordered": _as_int(pick("units_per_carton_ordered", "units_per_carton"), default=None),
        "operator_id": pick("operator_id", "operator_label", default="dock"),
        "client_id": pick("client_id"),
        "captured_at": pick("captured_at"),
        "subject_id": subject.get("subject_id"),
        "org_id": subject.get("org_id"),
        "route": subject.get("route"),
    }


def _as_int(value: Any, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

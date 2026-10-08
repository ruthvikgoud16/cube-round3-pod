"""Shared observation schema for live Claude + mock fixtures."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

OBSERVATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "identity_match",
        "carton_count_visible",
        "cartons_observed",
        "quantity_visible",
        "units_observed",
        "carton_damage",
        "unit_damage",
        "quality_flags",
        "evidence",
        "confidence",
    ],
    "properties": {
        "identity_match": {"enum": ["yes", "no", "uncertain"]},
        "carton_count_visible": {"enum": ["yes", "no", "uncertain"]},
        "cartons_observed": {"type": ["integer", "null"], "minimum": 0},
        "quantity_visible": {"enum": ["yes", "no", "uncertain"]},
        "units_observed": {"type": ["integer", "null"], "minimum": 0},
        "carton_damage": {"enum": ["none", "crushing", "water", "tears", "uncertain"]},
        "unit_damage": {"enum": ["none", "crushing", "water", "tears", "uncertain"]},
        "quality_flags": {
            "type": "array",
            "items": {
                "enum": [
                    "wrong_colour",
                    "wrong_variant",
                    "missing_components",
                    "obvious_defect",
                ]
            },
        },
        "quality_flags_uncertain": {"type": "boolean"},
        "evidence": {"type": "string", "minLength": 8},
        "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
    },
}

VALIDATOR = Draft202012Validator(OBSERVATION_SCHEMA)


def validate_observation(observation: dict) -> dict:
    errors = sorted(VALIDATOR.iter_errors(observation), key=lambda e: list(e.path))
    if errors:
        raise RuntimeError(f"observation failed schema: {errors[0].message}")
    return observation

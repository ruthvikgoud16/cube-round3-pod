"""Tag photos by shot role so checks cite the right frames."""
from __future__ import annotations

import re
from pathlib import Path

ROLE_PATTERNS = (
    ("pallet", re.compile(r"(pallet|stack|overview|wide|01_)", re.I)),
    ("carton", re.compile(r"(carton|box|outer|label|02_)", re.I)),
    ("unit", re.compile(r"(unit|product|open|contents|inside|03_)", re.I)),
)


def tag_role(ref: str) -> str:
    name = Path(ref).name
    for role, pattern in ROLE_PATTERNS:
        if pattern.search(name):
            return role
    return "other"


def attach_roles(photos: list[dict]) -> list[dict]:
    out = []
    for photo in photos:
        row = dict(photo)
        row["shot_role"] = tag_role(str(photo.get("ref") or ""))
        out.append(row)
    return out


def refs_for(photos: list[dict], *roles: str) -> list[str]:
    """Prefer roles in the order given (e.g. carton before pallet)."""
    picked: list[str] = []
    for role in roles:
        for p in photos:
            if p.get("shot_role") == role and p.get("ref") not in picked:
                picked.append(p["ref"])
    if picked:
        return picked
    return [p["ref"] for p in photos if p.get("ref")]

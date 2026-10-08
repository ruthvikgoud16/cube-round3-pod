"""Pre-model quality gate. Unusable frames never reach Claude."""
from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageStat

MIN_SIDE = 480
MIN_BYTES = 8_000
MIN_MEAN_LUMA = 18.0
MAX_MEAN_LUMA = 245.0
MAX_PHOTOS = 8


def gate_photos(photos: list[dict]) -> tuple[list[dict], list[dict]]:
    usable: list[dict] = []
    unusable: list[dict] = []
    for photo in photos[:MAX_PHOTOS]:
        reasons = _reasons(photo)
        row = {**photo, "quality": "usable" if not reasons else "unusable", "reasons": reasons}
        (unusable if reasons else usable).append(row)
    return usable, unusable


def _reasons(photo: dict) -> list[str]:
    raw: bytes = photo.get("bytes") or b""
    reasons: list[str] = []
    if len(raw) < MIN_BYTES:
        reasons.append("file_too_small")
        return reasons
    try:
        img = Image.open(BytesIO(raw))
        img.load()
        w, h = img.size
        if min(w, h) < MIN_SIDE:
            reasons.append("resolution_below_480")
        gray = img.convert("L")
        mean = float(ImageStat.Stat(gray).mean[0])
        if mean < MIN_MEAN_LUMA:
            reasons.append("too_dark")
        if mean > MAX_MEAN_LUMA:
            reasons.append("too_bright")
        # crude blur proxy: low variance
        var = float(ImageStat.Stat(gray).var[0])
        if var < 40.0:
            reasons.append("low_contrast_or_blur")
    except Exception:  # noqa: BLE001
        reasons.append("unreadable_image")
    return reasons

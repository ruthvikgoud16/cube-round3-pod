#!/usr/bin/env python3
"""Light PII redaction on staged receiving photos.

Blurs likely address blocks on shipping labels WITHOUT wiping brand tape/logos
needed for identity (Nutrabay, PlatinumRx, AJIO, Innovist, ONYC).
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "input"


def _blur_region(img: Image.Image, box: tuple[int, int, int, int], radius: int = 14) -> None:
    x0, y0, x1, y1 = [max(0, v) for v in box]
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    crop = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(radius=radius))
    img.paste(crop, (x0, y0))


def redact_file(path: Path) -> None:
    img = Image.open(path).convert("RGB")
    w, h = img.size
    # Lower half of a typical top label = address / phone lines (keep upper brand band)
    _blur_region(img, (int(w * 0.12), int(h * 0.22), int(w * 0.88), int(h * 0.40)), radius=15)
    # Common side-panel address sticker
    _blur_region(img, (int(w * 0.60), int(h * 0.45), int(w * 0.95), int(h * 0.70)), radius=14)
    img.save(path, format="JPEG", quality=90)


def main() -> int:
    # Restage must run before this. We only touch already-staged files.
    n = 0
    for path in sorted(INPUT.glob("UNIT-RCV-*/receiving/*.jpg")):
        redact_file(path)
        n += 1
    print(f"light-redacted {n} staged jpgs (brand tape preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

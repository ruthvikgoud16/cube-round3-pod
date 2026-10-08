#!/usr/bin/env python3
"""Stage dock photos into data/input/UNIT-RCV-*/receiving/.

Goals:
- Coherent brand angles for identity
- Tighter pallet shots (prefer single-brand / countable frames; no hub face shots)
- Case 11: mild darken so quality gate still passes but model sees uncertainty
- Expand staged set toward more deliveries for later labeling (13+)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
CARTONS = Path("/Users/ruthvikgoud/Downloads/pod4/receiving-cartons")
RTN = Path("/Users/ruthvikgoud/cube-04-returns-manager/fixtures/images/vision-gate")
OUT = ROOT / "data" / "input"
MANIFEST = ROOT / "data" / "fixtures" / "receiving" / "photo_map.json"

# Prefer floor carton stacks without people. Never use IMG_1336–1339 hub portraits.
MAP = {
    # --- core 12 (eval-labeled) ---
    "UNIT-RCV-01": {
        "01_pallet.jpg": CARTONS / "IMG_1343.jpg",  # tighter stack than mixed 1340
        "02_carton.jpg": CARTONS / "IMG_1344.jpg",
        "03_unit.jpg": CARTONS / "IMG_1345.jpg",
        "label": "clean_ok",
        "notes": "Nutrabay — tighter stack + close angles",
    },
    "UNIT-RCV-02": {
        "01_pallet.jpg": CARTONS / "IMG_1353.jpg",  # single Innovist as pallet when PO=1
        "02_carton.jpg": CARTONS / "IMG_1352.jpg",
        "03_unit.jpg": CARTONS / "IMG_1354.jpg",
        "label": "clean_ok_2",
        "notes": "Innovist single-carton countable set",
    },
    "UNIT-RCV-03": {
        "01_pallet.jpg": CARTONS / "IMG_1361.jpg",
        "02_carton.jpg": CARTONS / "IMG_1362.jpg",
        "03_unit.jpg": CARTONS / "IMG_1361.jpg",
        "label": "short_units",
        "notes": "AJIO packing-list short qty path",
    },
    "UNIT-RCV-04": {
        "01_pallet.jpg": CARTONS / "IMG_1346.jpg",  # one Nutrabay focus (short vs 4)
        "02_carton.jpg": CARTONS / "IMG_1347.jpg",
        "03_unit.jpg": CARTONS / "IMG_1346.jpg",
        "label": "short_cartons",
        "notes": "Single Nutrabay focus vs PO=4",
    },
    "UNIT-RCV-05": {
        "01_pallet.jpg": CARTONS / "IMG_1363.jpg",
        "02_carton.jpg": CARTONS / "IMG_1363.jpg",
        "03_unit.jpg": CARTONS / "IMG_1364.jpg",
        "label": "crush",
        "notes": "ONYC crush — single carton countable",
    },
    "UNIT-RCV-06": {
        "01_pallet.jpg": CARTONS / "IMG_1357.jpg",
        "02_carton.jpg": CARTONS / "IMG_1358.jpg",
        "03_unit.jpg": CARTONS / "IMG_1359.jpg",
        "label": "tears",
        "notes": "FRAGILE set",
    },
    "UNIT-RCV-07": {
        "01_pallet.jpg": CARTONS / "IMG_1348.jpg",
        "02_carton.jpg": CARTONS / "IMG_1349.jpg",
        "03_unit.jpg": CARTONS / "IMG_1348.jpg",
        "label": "wrong_sku",
        "notes": "PlatinumRx vs whey PO — brand must FAIL identity",
    },
    "UNIT-RCV-08": {
        "01_pallet.jpg": CARTONS / "IMG_1350.jpg",
        "02_carton.jpg": CARTONS / "IMG_1351.jpg",
        "03_unit.jpg": CARTONS / "IMG_1350.jpg",
        "label": "wrong_variant",
        "notes": "PlatinumRx vs blue bottle PO",
    },
    "UNIT-RCV-09": {
        "01_pallet.jpg": CARTONS / "IMG_1352.jpg",
        "02_carton.jpg": CARTONS / "IMG_1354.jpg",
        "03_unit.jpg": RTN / "dev-003-photo-1.jpg",
        "label": "missing_parts",
        "notes": "Innovist shipper + headphones unit",
    },
    "UNIT-RCV-10": {
        "01_pallet.jpg": CARTONS / "IMG_1355.jpg",
        "02_carton.jpg": CARTONS / "IMG_1356.jpg",
        "03_unit.jpg": CARTONS / "IMG_1355.jpg",
        "label": "sealed",
        "notes": "Sealed fragile Flipkart/Shadowfax",
    },
    "UNIT-RCV-11": {
        "01_pallet.jpg": "__darken__",
        "02_carton.jpg": "__darken__",
        "03_unit.jpg": "__darken__",
        "source": CARTONS / "IMG_1346.jpg",
        "darken": 0.38,  # was 0.12 — too dark for quality gate
        "label": "dark",
        "notes": "Mild darken so model can return UNCERTAIN",
    },
    "UNIT-RCV-12": {
        "01_pallet.jpg": CARTONS / "IMG_1379.jpg",
        "02_carton.jpg": CARTONS / "IMG_1379.jpg",
        "03_unit.jpg": CARTONS / "IMG_1379.jpg",
        "label": "blur",
        "notes": "Soft-focus",
    },
}


def _copy_jpeg(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in {".jpg", ".jpeg"}:
        shutil.copy2(src, dest)
        return
    Image.open(src).convert("RGB").save(dest, format="JPEG", quality=90)


def _darken(src: Path, dest: Path, factor: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(src).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(factor)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img.save(dest, format="JPEG", quality=88)


def main() -> int:
    missing: list[str] = []
    written: dict = {"cases": {}, "sources": {"cartons": str(CARTONS), "rtn": str(RTN)}}

    for unit, spec in MAP.items():
        folder = OUT / unit / "receiving"
        folder.mkdir(parents=True, exist_ok=True)
        entry = {"label": spec["label"], "notes": spec["notes"], "files": {}}
        if spec.get("01_pallet.jpg") == "__darken__":
            src = Path(spec["source"])
            factor = float(spec.get("darken", 0.38))
            if not src.is_file():
                missing.append(str(src))
                continue
            for name in ("01_pallet.jpg", "02_carton.jpg", "03_unit.jpg"):
                _darken(src, folder / name, factor)
                entry["files"][name] = {"source": str(src), "transform": f"darken:{factor}"}
        else:
            for name in ("01_pallet.jpg", "02_carton.jpg", "03_unit.jpg"):
                src = Path(spec[name])
                if not src.is_file():
                    missing.append(f"{unit}/{name} <- {src}")
                    continue
                _copy_jpeg(src, folder / name)
                entry["files"][name] = {"source": str(src)}
        written["cases"][unit] = entry
        print(f"staged {unit} ({spec['label']})")

    MANIFEST.write_text(json.dumps(written, indent=2) + "\n")
    if missing:
        print("MISSING:")
        for m in missing:
            print(f"  {m}")
        return 1
    print(f"\nwrote {MANIFEST} ({len(MAP)} deliveries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

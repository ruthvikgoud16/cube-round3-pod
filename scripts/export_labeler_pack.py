#!/usr/bin/env python3
"""Build a Drive-ready labeler pack from staged UNIT-RCV folders + cases.json.

Output: eval/labeler-pack/
  README-LABELERS.md
  po.csv
  labels.csv          (blank — two rows per case for Labeler A / Labeler B)
  photo_source_map.csv
  cases/
    UNIT-RCV-01/
      PO.txt
      receiving/01_pallet.jpg …
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "data/fixtures/receiving/cases.json").read_text())["cases"]
PHOTO_MAP = json.loads((ROOT / "data/fixtures/receiving/photo_map.json").read_text())["cases"]
INPUT = ROOT / "data" / "input"
OUT = ROOT / "eval" / "labeler-pack"
CASES_OUT = OUT / "cases"

LABELER_NAMES = ("Labeler A", "Labeler B")


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    CASES_OUT.mkdir(parents=True)

    po_rows: list[dict] = []
    label_rows: list[dict] = []
    map_rows: list[dict] = []

    for case in CASES:
        sid = case["subject_id"]
        po = case["po"]
        src_dir = INPUT / sid / "receiving"
        if not src_dir.is_dir():
            raise SystemExit(f"missing staged photos: {src_dir}")

        dest = CASES_OUT / sid / "receiving"
        dest.mkdir(parents=True)
        for name in ("01_pallet.jpg", "02_carton.jpg", "03_unit.jpg"):
            src = src_dir / name
            if not src.is_file():
                raise SystemExit(f"missing {src}")
            shutil.copy2(src, dest / name)

        components = po.get("spec_components") or []
        if isinstance(components, list):
            components_s = ";".join(components)
        else:
            components_s = str(components)

        po_txt = (
            f"delivery_id: {sid}\n"
            f"po_number: {po.get('po_number')}\n"
            f"po_line: {po.get('po_line')}\n"
            f"sku: {po.get('sku')}\n"
            f"product_name: {po.get('product_name')}\n"
            f"spec_colour: {po.get('spec_colour') or ''}\n"
            f"spec_components: {components_s}\n"
            f"cartons_ordered: {po.get('cartons_ordered')}\n"
            f"qty_ordered: {po.get('qty_ordered')}\n"
            f"supplier: {po.get('supplier') or ''}\n"
            f"\nPhotos in receiving/:\n"
            f"  01_pallet.jpg  — stack / floor spread (count cartons)\n"
            f"  02_carton.jpg  — outer carton (label / damage)\n"
            f"  03_unit.jpg    — unit / open / sealed stand-in\n"
        )
        (CASES_OUT / sid / "PO.txt").write_text(po_txt)

        po_rows.append(
            {
                "delivery_id": sid,
                "po_number": po.get("po_number"),
                "po_line": po.get("po_line"),
                "sku": po.get("sku"),
                "product_name": po.get("product_name"),
                "spec_colour": po.get("spec_colour") or "",
                "spec_components": components_s,
                "cartons_ordered": po.get("cartons_ordered"),
                "qty_ordered": po.get("qty_ordered"),
                "supplier": po.get("supplier") or "",
                "photo_folder": f"cases/{sid}/receiving/",
            }
        )

        for labeler in LABELER_NAMES:
            label_rows.append(
                {
                    "case_id": sid,
                    "labeler": labeler,
                    "identity_match": "",
                    "carton_count": "",
                    "quantity": "",
                    "carton_damage": "",
                    "unit_damage": "",
                    "quality_flags": "",
                    "evidence_sufficient": "",
                    "product_name": po.get("product_name"),
                    "sku": po.get("sku"),
                    "cartons_ordered": po.get("cartons_ordered"),
                    "qty_ordered": po.get("qty_ordered"),
                    "note": "",
                }
            )

        files = (PHOTO_MAP.get(sid) or {}).get("files") or {}
        for role, meta in files.items():
            map_rows.append(
                {
                    "delivery_id": sid,
                    "role_file": role,
                    "source_file": Path(meta.get("source", "")).name if meta.get("source") else "",
                    "transform": meta.get("transform", ""),
                }
            )

    _write_csv(OUT / "po.csv", po_rows)
    _write_csv(OUT / "labels.csv", label_rows)
    _write_csv(OUT / "photo_source_map.csv", map_rows)
    (OUT / "README-LABELERS.md").write_text(_readme(len(CASES)))
    print(f"wrote {OUT} ({len(CASES)} deliveries)")
    return 0


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _readme(n: int) -> str:
    return f"""# Receiving labeler pack ({n} deliveries)

Ignore the loose HEIC folder on Drive (“Ruthviks Reciveing manager”).  
**Use this pack only.**

## Folder layout

```text
labeler-pack/
  README-LABELERS.md   ← you are here
  po.csv               ← all PO lines
  labels.csv           ← blank — fill this and send back
  photo_source_map.csv ← optional: maps to original IMG_*.HEIC names
  cases/
    UNIT-RCV-01/
      PO.txt
      receiving/
        01_pallet.jpg
        02_carton.jpg
        03_unit.jpg
    UNIT-RCV-02/
      …
```

## How to label

1. Open `cases/UNIT-RCV-XX/PO.txt` (or the matching row in `po.csv`).
2. Look at the three photos in `receiving/`.
3. Fill **your** rows in `labels.csv` (replace `Labeler A` / `Labeler B` with your real name).
4. Work alone. Do not look at the agent’s scores.

### Columns (PASS / FAIL / UNCERTAIN)

| Column | Meaning |
|---|---|
| identity_match | Photos match the PO product/brand? |
| carton_count | Can you count cartons, and does count = cartons_ordered? |
| quantity | Can you count units, and does count = qty_ordered? |
| carton_damage | PASS=none · FAIL=crush/water/tears · UNCERTAIN=unclear |
| unit_damage | Same for the product |
| quality_flags | PASS=none · FAIL=wrong colour/variant/missing parts clear · UNCERTAIN=unclear |
| evidence_sufficient | yes / no |
| note | 1–2 sentences |

### Rules

- UNCERTAIN is allowed. Do not guess.
- Sealed carton → `quantity` is usually UNCERTAIN.
- Part not in frame → UNCERTAIN, not FAIL.
- Wrong product only if photos clearly show a different brand/product.

## Return

Send back the filled `labels.csv` (keep the header). One file with both labelers’ rows is fine.
"""


if __name__ == "__main__":
    raise SystemExit(main())

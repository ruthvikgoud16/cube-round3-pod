# Receiving labeler pack (12 deliveries)

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

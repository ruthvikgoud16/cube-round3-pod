# Photos — staged

**Status: 12 deliveries × 3 photos = 36 staged** under `data/input/UNIT-RCV-*/receiving/`.

Source Drive (cartons): https://drive.google.com/drive/folders/1ntPKrpVc9ebb0cDLwAQYyityM01RHMZA  
Unit samples: Returns vision-gate fixtures.  
Rebuild map: `python scripts/stage_receiving_photos.py`  
Manifest: `data/fixtures/receiving/photo_map.json`

## Shot roles

| # | File | What |
|---|---|---|
| 1 | `01_pallet.jpg` | Stack / floor spread — count cartons |
| 2 | `02_carton.jpg` | Outer carton: label, crush, tears, sealed |
| 3 | `03_unit.jpg` | Open unit or sealed stand-in |

## Cases

| Unit | Case | Notes | Expected (mock) |
|---|---|---|---|
| 01 | Clean OK | Nutrabay stack | `accept` |
| 02 | Clean OK #2 | Innovist | `accept` |
| 03 | Short units | AJIO path | `accept_with_exceptions` |
| 04 | Short cartons | Fewer boxes than PO | `pending_review` |
| 05 | Crush | onyc crushed corner | `accept_with_exceptions` |
| 06 | Tears | FRAGILE wear (**no water photo** — remapped) | `accept_with_exceptions` |
| 07 | Wrong SKU | PlatinumRx vs whey PO | `reject` |
| 08 | Wrong variant | Medicine vs blue bottle PO | `reject` |
| 09 | Missing parts | Headphones / no case | `accept_with_exceptions` |
| 10 | Sealed | Flipkart/Shadowfax sealed | `pending_review` |
| 11 | Dark | Darkened carton | `pending_review` |
| 12 | Blur | IMG_1379 soft focus | `pending_review` |

## Privacy

Crop or blur full addresses and faces before any public submit. Local demo uses floor spreads without hub portraits where possible.

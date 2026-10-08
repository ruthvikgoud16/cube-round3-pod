# Failed / mismatched evaluation cases

Project set: **12 real dock deliveries** (not mocks). Compared agent checks to checks where **both** Jaanu and Soanli agreed.

Mismatched cases: **11** / 12

## UNIT-RCV-01 — clean_ok

- Product: Nutrabay supplement inbound carton
- Agent outcome: `pending_review`
- Mismatches: 
  - carton_count: agent=FAIL human=UNCERTAIN

## UNIT-RCV-03 — short_units

- Product: AJIO footwear assortment
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
- Human disagreement (excluded from match score): quantity, carton_damage

## UNIT-RCV-04 — short_cartons

- Product: Nutrabay supplement inbound carton
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
- Human disagreement (excluded from match score): carton_count

## UNIT-RCV-05 — crush

- Product: Onyc inbound carton
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
- Human disagreement (excluded from match score): carton_count

## UNIT-RCV-06 — tears

- Product: Fragile handled inbound parcel
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
  - carton_count: agent=FAIL human=UNCERTAIN

## UNIT-RCV-07 — wrong_sku

- Product: Whey Protein 1kg vanilla
- Agent outcome: `pending_review`
- Mismatches: 
  - quality_flags: agent=PASS human=FAIL
- Human disagreement (excluded from match score): carton_count

## UNIT-RCV-08 — wrong_variant

- Product: Insulated Bottle Blue
- Agent outcome: `pending_review`
- Mismatches: 
  - quality_flags: agent=PASS human=FAIL
- Human disagreement (excluded from match score): carton_count, carton_damage

## UNIT-RCV-09 — missing_parts

- Product: Red/Black Wired Over-Ear Headphones
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=FAIL human=PASS
  - unit_damage: agent=UNCERTAIN human=PASS
  - quality_flags: agent=PASS human=UNCERTAIN
- Human disagreement (excluded from match score): quantity

## UNIT-RCV-10 — sealed

- Product: Fragile handled inbound parcel
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
  - carton_count: agent=FAIL human=UNCERTAIN
  - carton_damage: agent=FAIL human=PASS

## UNIT-RCV-11 — dark

- Product: Nutrabay supplement inbound carton
- Agent outcome: `pending_review`
- Mismatches: 
  - identity_match: agent=UNCERTAIN human=PASS
- Human disagreement (excluded from match score): carton_count, carton_damage, quality_flags

## UNIT-RCV-12 — blur

- Product: Fragile handled inbound parcel
- Agent outcome: `pending_review`
- Mismatches: 
  - carton_damage: agent=PASS human=UNCERTAIN
  - quality_flags: agent=PASS human=UNCERTAIN
- Human disagreement (excluded from match score): carton_count

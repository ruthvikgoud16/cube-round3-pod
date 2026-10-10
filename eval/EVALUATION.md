# Receiving evaluation

These figures describe this held-out pilot set only. They are not an overall accuracy.
Rates use cases where **both** labelers (Jaanu, Soanli) agreed. UNCERTAIN is not scored as PASS or FAIL.

## A. Scope

- Project set: **12 real dock deliveries** (UNIT-RCV-01…12 — not mocks)
- Fully labeled by both humans: **12**
- Labelers: Jaanu, Soanli (independent, before scoring)
- Full agreement (all 6 checks): **3** → UNIT-RCV-01, UNIT-RCV-06, UNIT-RCV-10
- Disagreed / excluded from primary rates: **9** → UNIT-RCV-02, UNIT-RCV-03, UNIT-RCV-04, UNIT-RCV-05, UNIT-RCV-07, UNIT-RCV-08, UNIT-RCV-09, UNIT-RCV-11, UNIT-RCV-12
- Model calls: **12** (one per delivery)

## B. Primary rates (full agreement only)

| Check | Match | FP (agent PASS / human FAIL) | FN (agent FAIL / human PASS) | UNCERTAIN mismatch |
|---|---:|---:|---:|---:|
| identity_match | 1/3 (33.3%) | 0 | 0 | 2 |
| carton_count | 0/3 (0.0%) | 0 | 0 | 3 |
| quantity | 3/3 (100.0%) | 0 | 0 | 0 |
| carton_damage | 2/3 (66.7%) | 0 | 1 | 0 |
| unit_damage | 3/3 (100.0%) | 0 | 0 | 0 |
| quality_flags | 3/3 (100.0%) | 0 | 0 | 0 |

## C. Soft rates (humans agree on that check only)

| Check | Human-agreed n | Match | FP | FN | UNCERTAIN mismatch |
|---|---:|---:|---:|---:|---:|
| identity_match | 12 | 5/12 (41.7%) | 0 | 1 | 6 |
| carton_count | 6 | 3/6 (50.0%) | 0 | 0 | 3 |
| quantity | 10 | 10/10 (100.0%) | 0 | 0 | 0 |
| carton_damage | 8 | 6/8 (75.0%) | 0 | 1 | 1 |
| unit_damage | 12 | 11/12 (91.7%) | 0 | 0 | 1 |
| quality_flags | 11 | 7/11 (63.6%) | 2 | 0 | 2 |

## D. Clear fail paths (either labeler)

- **07 / 08** — wrong product (PlatinumRx vs whey / blue bottle)
- **09** — headphones identity ok; quantity / case incomplete
- **04 / 05 / 11** — carton count below PO (Jaanu FAIL; Soanli often UNCERTAIN)
- **12** — too blurry

## E. Method notes

- Agent checks come from one live Claude observation + `receiving_policy_v1` (model does not choose disposition).
- Sealed cartons correctly produce quantity UNCERTAIN → `pending_review`; that is not treated as a false positive.
- This submission grades the **twelve real project deliveries** only.

## F. Cost and limits

Token totals were not stored. The meter is 12 Claude calls, one per delivery. That is not an invoice.

The primary table is the 3 units where Jaanu and Soanli agreed on all six checks. The soft table is larger and is not a substitute for that primary set. Nine units stay out of the primary rates because the labelers disagreed. This is the finished pilot. It is not a 50-case evaluation.

## G. Agent outcomes (all 12)

- `UNIT-RCV-01`: status=ok outcome=pending_review checks={'identity_match': 'PASS', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-02`: status=ok outcome=pending_review checks={'identity_match': 'PASS', 'carton_count': 'PASS', 'quantity': 'UNCERTAIN', 'carton_damage': 'PASS', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-03`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'PASS', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-04`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-05`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'UNCERTAIN', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-06`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-07`: status=ok outcome=pending_review checks={'identity_match': 'FAIL', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-08`: status=ok outcome=pending_review checks={'identity_match': 'FAIL', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-09`: status=ok outcome=pending_review checks={'identity_match': 'FAIL', 'carton_count': 'PASS', 'quantity': 'UNCERTAIN', 'carton_damage': 'PASS', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-10`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'FAIL', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-11`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'PASS', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}
- `UNIT-RCV-12`: status=ok outcome=pending_review checks={'identity_match': 'UNCERTAIN', 'carton_count': 'FAIL', 'quantity': 'UNCERTAIN', 'carton_damage': 'PASS', 'unit_damage': 'UNCERTAIN', 'quality_flags': 'PASS'}

# PRODUCT-03

- Drive folder: `PRODUCT-03`
- Workflow id: `WF-org_demo_alpha-PRODUCT-03-r2`
- Unit id: `PRODUCT-03-r2`
- Why this unit id: WF-org_demo_alpha-PRODUCT-03 already exists. Pack and returns did not see photos, and recovery already completed. The old evidence was not deleted. This run uses unit PRODUCT-03-r2.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `False`. product3-details.txt says returns images repeat prep photos and do not prove a return transaction. returned was not a boolean. This run sent returned=false.
- Product name from Drive: GOBOULT Mustang Torq 60Hrs True Wireless Earbuds
- SKU from Drive: 8906133855741 sku_or_barcode also lists FSN ACCH7KPDT628ZWDZ. sku sent is the barcode written in that field.
- Variant from Drive: Silver
- Quantity from Drive: 1
- Order id from Drive: OD438837663084490500
- Fee: Details say the recovery folder has a sales invoice and a Protect Promise fee, not an eligible recovery charge, and no recovery amount is assigned. No charge was sent.
- Photo stages with no Drive image: pack

## Workflow

- Status: `FAILED`
- Status reason: stage did not complete: prep, pack, returns
- Final outcome: `INCOMPLETE`
- Final verdict: `UNCERTAIN`
- Final reason: Stage did not complete: prep, pack, returns.
- Needs human: `true`
- Claimable USD: `(none)`

## Stages

### receiving

- State: `completed`
- Evidence status: `completed`
- Record id: `RCV-1611847adba5`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: receiving_policy_v1: UNCERTAIN on identity_match, carton_count, quantity, carton_damage; UNCERTAIN is not a pass. Holding for a person.
- Image inputs on the evidence record: 2
- Stage error: (none)

### prep

- State: `error`
- Evidence status: `pending`
- Record id: `PRP-102da7eb2dde`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: Prep received 8 usable photo(s). Front, back, and label are required, so observation was not run.
- Image inputs on the evidence record: 0
- Stage error: Prep received 8 usable photo(s). Front, back, and label are required, so observation was not run.

### pack

- State: `error`
- Evidence status: `pending`
- Record id: `PCK-8282bf2e11b6`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: No usable photos were attached to this Agent Input
- Image inputs on the evidence record: 0
- Stage error: No usable photos were attached to this Agent Input

Drive had no pack photo for this product.

### returns

- State: `error`
- Evidence status: `pending`
- Record id: `RTN-756b5ff4b405`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: At least one check is UNCERTAIN. The operator decides. UNCERTAIN is not a pass.
- Image inputs on the evidence record: 3
- Stage error: (none)

### recovery

- State: `completed`
- Evidence status: `completed`
- Record id: `RCY-342d19b36fab`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `FAILED` and stored final verdict is `UNCERTAIN`.

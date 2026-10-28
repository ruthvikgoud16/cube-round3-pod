# PRODUCT-02

- Drive folder: `PRODUCT-02`
- Workflow id: `WF-org_demo_alpha-PRODUCT-02-r2`
- Unit id: `PRODUCT-02-r2`
- Why this unit id: WF-org_demo_alpha-PRODUCT-02 already exists and finished FAILED without pack or returns photos. Recovery on that run already completed. The old evidence was not deleted. This run uses unit PRODUCT-02-r2.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `False`. product2-details.txt leaves the Returns fields blank. returned was not stated. This run sent returned=false.
- Product name from Drive: Red Tape Classic sneakers (Prep photos); BLACK COTTEDE plastic study table (Receiving carton label)
- SKU from Drive: BLACK COTTEDE (carton label); shipping barcode visible on Red Tape parcel The details file says not to treat the carton and the sneaker photos as one verified order. The sku field is copied as written.
- Variant from Drive: Black/white/red sneakers; black study table
- Quantity from Drive: 1 quantity_ordered line says '1 (study table carton label)'.
- Order id from Drive: OD338303263747180100 order_id is the study table carton id from the details file.
- Fee: No recovery fee line and no fee file. No charge was sent.
- Photo stages with no Drive image: pack, returns

## Workflow

- Status: `FAILED`
- Status reason: stage did not complete: prep, pack, returns
- Final outcome: `EXCEPTION`
- Final verdict: `FAIL`
- Final reason: Failed verdict from: receiving; no claim recommended. Flagged for review: prep, pack, returns, receiving, prep, pack, returns.
- Needs human: `true`
- Claimable USD: `(none)`

## Stages

### receiving

- State: `completed`
- Evidence status: `completed`
- Record id: `RCV-c66096e8f61a`
- Quoted from: evidence
- Verdict: `FAIL`
- Outcome: `pending_review`
- Reason: receiving_policy_v1: UNCERTAIN on carton_count, quantity, unit_damage; UNCERTAIN is not a pass. Holding for a person.
- Image inputs on the evidence record: 2
- Stage error: (none)

### prep

- State: `error`
- Evidence status: `pending`
- Record id: `PRP-9f3d7a93ea17`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: Prep received 4 usable photo(s). Front, back, and label are required, so observation was not run.
- Image inputs on the evidence record: 0
- Stage error: Prep received 4 usable photo(s). Front, back, and label are required, so observation was not run.

### pack

- State: `error`
- Evidence status: `pending`
- Record id: `PCK-5072b7f6d0ea`
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
- Record id: `RTN-PRODUCT-02-r2`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: No usable photos were attached to this Agent Input
- Image inputs on the evidence record: 0
- Stage error: No usable photos were attached to this Agent Input

Drive had no returns photo for this product.

### recovery

- State: `completed`
- Evidence status: `completed`
- Record id: `RCY-d5a344657c9d`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `FAILED` and stored final verdict is `FAIL`.

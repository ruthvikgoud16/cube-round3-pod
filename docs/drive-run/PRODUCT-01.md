# PRODUCT-01

- Drive folder: `PRODUCT-01`
- Workflow id: `WF-org_demo_alpha-PRODUCT-01-r2`
- Unit id: `PRODUCT-01-r2`
- Why this unit id: WF-org_demo_alpha-PRODUCT-01 already exists and finished FAILED before these Drive photos were in the input folder. Recovery on that run already completed. Resume would not re-judge completed stages. The old evidence was not deleted. This run uses unit PRODUCT-01-r2.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `False`. product1-details.txt leaves the Returns fields blank and says 'No return evidence.' returned was not a boolean in the file. This run sent returned=false and does not treat that as a finding that a return did not happen.
- Product name from Drive: Bond Street By Red Tape Men's Casual Sneakers
- SKU from Drive: BSE0871-9 sku_or_barcode field also names security seal Y26A0758393.
- Variant from Drive: White/Beige, size 9
- Quantity from Drive: 1 quantity_ordered line says '1 pair'.
- Order id from Drive: OD338734740660891100
- Fee: Recovery folder has invoice-shoe.pdf. The details file says the invoice price is not a recovery fee and leaves amount blank. No charge was sent.
- Photo stages with no Drive image: returns

## Workflow

- Status: `FAILED`
- Status reason: stage did not complete: prep, returns
- Final outcome: `INCOMPLETE`
- Final verdict: `UNCERTAIN`
- Final reason: Stage did not complete: prep, returns.
- Needs human: `true`
- Claimable USD: `(none)`

## Stages

### receiving

- State: `completed`
- Evidence status: `completed`
- Record id: `RCV-a15c91f24118`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: receiving_policy_v1: UNCERTAIN on carton_count; UNCERTAIN is not a pass. Holding for a person.
- Image inputs on the evidence record: 1
- Stage error: (none)

### prep

- State: `error`
- Evidence status: `pending`
- Record id: `PRP-5f4f9b62d057`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: Prep received 5 usable photo(s). Front, back, and label are required, so observation was not run.
- Image inputs on the evidence record: 0
- Stage error: Prep received 5 usable photo(s). Front, back, and label are required, so observation was not run.

### pack

- State: `completed`
- Evidence status: `completed`
- Record id: `PCK-ae21b8d46e8a`
- Quoted from: evidence
- Verdict: `PASS`
- Outcome: `seal`
- Reason: All expected items present, correct quantity, correct variant, NO extra items.
- Image inputs on the evidence record: 1
- Stage error: (none)

### returns

- State: `error`
- Evidence status: `pending`
- Record id: `RTN-PRODUCT-01-r2`
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
- Record id: `RCY-73868d3258f4`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `FAILED` and stored final verdict is `UNCERTAIN`.

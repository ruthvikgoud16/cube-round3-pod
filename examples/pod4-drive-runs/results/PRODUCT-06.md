# PRODUCT-06

- Drive folder: `PRODUCT-06`
- Workflow id: `WF-org_demo_alpha-PRODUCT-06`
- Unit id: `PRODUCT-06`
- Why this unit id: No workflow existed for PRODUCT-06. Unit id matches the Drive folder.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `False`. The Google Doc describes photographed contents under Returns but does not set returned to true or false. This run sent returned=false.
- Product name from Drive: Apple MacBook Air (13-inch; exact generation unclear)
- SKU from Drive: (blank) sku_or_barcode is blank. fee-report.txt names 'MacBook Air 13-inch' as sku and says that file is not a real charge. No sku was sent.
- Variant from Drive: Silver
- Quantity from Drive: (blank)
- Order id from Drive: (blank)
- Fee: fee-report.txt says amount: none, currency: none, and that it is not a real charge. No charge was sent.
- Photo stages with no Drive image: none

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
- Record id: `RCV-94d91eb3fc00`
- Quoted from: evidence
- Verdict: `PASS`
- Outcome: `accept`
- Reason: receiving_policy_v1: all receiving checks passed.
- Image inputs on the evidence record: 4
- Stage error: (none)

### prep

- State: `error`
- Evidence status: `pending`
- Record id: `PRP-0289ea1e5cf8`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: prep operational status REVIEW_REQUIRED
- Image inputs on the evidence record: 3
- Stage error: (none)

### pack

- State: `completed`
- Evidence status: `completed`
- Record id: `PCK-b41a0d87502c`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: At least one visible item is low confidence or the brand is not clear, so this pack cannot be sealed.
- Image inputs on the evidence record: 1
- Stage error: (none)

### returns

- State: `error`
- Evidence status: `error`
- Record id: `RTN-PENDING-WF-org_demo_alpha-PRODUCT-06-returns-r2`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: agent_rejected: HTTP 413: {"statusCode": 413, "code": "FST_ERR_CTP_BODY_TOO_LARGE", "error": "Payload Too Large", "message": "Request body is too large"}
- Image inputs on the evidence record: 0
- Stage error: HTTP 413: {"statusCode": 413, "code": "FST_ERR_CTP_BODY_TOO_LARGE", "error": "Payload Too Large", "message": "Request body is too large"}

### recovery

- State: `completed`
- Evidence status: `completed`
- Record id: `RCY-2f785d492fd6`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `FAILED` and stored final verdict is `UNCERTAIN`.

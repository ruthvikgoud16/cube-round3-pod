# PRODUCT-04

- Drive folder: `PRODUCT-04`
- Workflow id: `WF-org_demo_alpha-PRODUCT-04`
- Unit id: `PRODUCT-04`
- Why this unit id: No workflow existed for PRODUCT-04. Unit id matches the Drive folder.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `False`. product4-details.txt says: 'This product is not a return case; no actual return event has occurred.' returned=false is taken from that sentence.
- Product name from Drive: Oblique Sally Tech Pouch
- SKU from Drive: 8906126921460
- Variant from Drive: Tan; 36 cm x 5 cm x 23 cm
- Quantity from Drive: 1
- Order id from Drive: (blank)
- Fee: Invoice total INR 1450 is described as a purchase total, not a recovery fee. Amount on the recovery fee line is blank. No charge was sent.
- Photo stages with no Drive image: none

## Workflow

- Status: `BLOCKED`
- Status reason: a person must decide: receiving, prep, pack
- Final outcome: `EXCEPTION`
- Final verdict: `FAIL`
- Final reason: Failed verdict from: prep; no claim recommended. Flagged for review: receiving, prep, pack.
- Needs human: `true`
- Claimable USD: `(none)`

## Stages

### receiving

- State: `completed`
- Evidence status: `completed`
- Record id: `RCV-7e332f3270f4`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `pending_review`
- Reason: receiving_policy_v1: UNCERTAIN on unit_damage; UNCERTAIN is not a pass. Holding for a person.
- Image inputs on the evidence record: 3
- Stage error: (none)

### prep

- State: `completed`
- Evidence status: `completed`
- Record id: `PRP-b7ec38b3c3c8`
- Quoted from: evidence
- Verdict: `FAIL`
- Outcome: `stop_and_fix`
- Reason: prep operational status STOP_AND_FIX
- Image inputs on the evidence record: 3
- Stage error: (none)

### pack

- State: `completed`
- Evidence status: `completed`
- Record id: `PCK-9dcaf5ca560b`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: The model could not confirm Oblique Sally tech pouch, so this pack cannot be sealed. Model: While a brown tech pouch matching the general description is present in quantity of 1, I cannot definitively confirm this is the 'Oblique Sally tech pouch' specifically. No visible branding, tags, or labels are clear enough in the photos to verify the exact model name 'Sally' or brand 'Oblique'. The retail box text is not legible enough to confirm product identity.
- Image inputs on the evidence record: 1
- Stage error: (none)

### returns

- State: `completed`
- Evidence status: `completed`
- Record id: `RTN-6b4f55912642`
- Quoted from: evidence
- Verdict: `PASS`
- Outcome: `restock`
- Reason: Identity matches, required parts are visible, and the visual grade is Like New or Very Good.
- Image inputs on the evidence record: 3
- Stage error: (none)

### recovery

- State: `completed`
- Evidence status: `completed`
- Record id: `RCY-9528cac65c2d`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `BLOCKED` and stored final verdict is `FAIL`.

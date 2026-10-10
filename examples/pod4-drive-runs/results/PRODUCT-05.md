# PRODUCT-05

- Drive folder: `PRODUCT-05`
- Workflow id: `WF-org_demo_alpha-PRODUCT-05`
- Unit id: `PRODUCT-05`
- Why this unit id: No workflow existed for PRODUCT-05. Unit id matches the Drive folder.
- Route sent to the API: `fba`. Drive details do not state route (fba or mfn). The orchestrator requires one of those two values, so this run sent route=fba. That value was not read from the folder and is not a commerce finding.
- Returned sent to the API: `True`. PRODUCT-05-LIVE-DEMO.txt states returned: true.
- Product name from Drive: JOMPERS Embroidered Kurta
- SKU from Drive: KO_D_5088Black_S
- Variant from Drive: Black; Size S (36)
- Quantity from Drive: 1
- Order id from Drive: FN6754808641
- Fee: Recovery fee fields are blank. LIVE-DEMO.txt says recovery has no fee line. No charge was sent.
- Photo stages with no Drive image: none

## Workflow

- Status: `FAILED`
- Status reason: stage did not complete: prep
- Final outcome: `EXCEPTION`
- Final verdict: `FAIL`
- Final reason: Failed verdict from: receiving, pack; no claim recommended. Flagged for review: prep, prep, pack.
- Needs human: `true`
- Claimable USD: `(none)`

## Stages

### receiving

- State: `completed`
- Evidence status: `completed`
- Record id: `RCV-ad852c465895`
- Quoted from: evidence
- Verdict: `FAIL`
- Outcome: `accept_with_exceptions`
- Reason: receiving_policy_v1: accept with exceptions: carton_count.
- Image inputs on the evidence record: 6
- Stage error: (none)

### prep

- State: `error`
- Evidence status: `pending`
- Record id: `PRP-c0210356ad5b`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `review_required`
- Reason: Prep received 8 usable photo(s). Front, back, and label are required, so observation was not run.
- Image inputs on the evidence record: 0
- Stage error: Prep received 8 usable photo(s). Front, back, and label are required, so observation was not run.

### pack

- State: `completed`
- Evidence status: `completed`
- Record id: `PCK-d2b9ac783e59`
- Quoted from: evidence
- Verdict: `FAIL`
- Outcome: `stop_and_fix`
- Reason: Variant/color mismatch.
- Image inputs on the evidence record: 1
- Stage error: (none)

### returns

- State: `completed`
- Evidence status: `completed`
- Record id: `RTN-87f1d4a6031b`
- Quoted from: evidence
- Verdict: `PASS`
- Outcome: `restock`
- Reason: Identity matches, required parts are visible, and the visual grade is Like New or Very Good.
- Image inputs on the evidence record: 4
- Stage error: (none)

### recovery

- State: `completed`
- Evidence status: `completed`
- Record id: `RCY-63d21ea3438e`
- Quoted from: evidence
- Verdict: `UNCERTAIN`
- Outcome: `insufficient_evidence`
- Reason: No fee report lines were supplied or found for this subject; nothing to assess.
- Image inputs on the evidence record: 0
- Stage error: (none)

This file does not mark the product PASS. Stored workflow status is `FAILED` and stored final verdict is `FAIL`.

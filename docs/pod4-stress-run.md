# Pod 4 stress run — 2026-10-08

This run did not call Claude. The hundred scenario units are scripted inside the orchestrator. The hundred sample units replay `data/sample`, which the sample README marks as dummy data. Neither set is a vision score.

## Did the process crash?

No. `run_workflow` returned a workflow for all 100 scenario units and all 100 sample units. Uncaught exceptions: 0. Workflows that failed schema validation: 0.

## One hundred scenario units

Each group has 10 units. Route rotates through FBA, merchant-fulfilled, and unknown. Half are marked returned. The flow is `orchestration/flow.json`, so an FBA unit skips Pack and a merchant-fulfilled unit skips Prep.

| scenario | units | status | outcome | receiving attempts |
| --- | --- | --- | --- | --- |
| all_pass | 10 | COMPLETED 10 | CLEAN 10 | 10 |
| receiving_fail | 10 | COMPLETED 10 | EXCEPTION 10 | 10 |
| midstage_fail | 10 | COMPLETED 10 | CLEAN 4, EXCEPTION 6 | 10 |
| uncertain_needs_person | 10 | BLOCKED 10 | NEEDS_REVIEW 10 | 10 |
| recovery_claim | 10 | COMPLETED 10 | CLAIM_RECOMMENDED 10 | 10 |
| recovery_silent | 10 | COMPLETED 10 | CLEAN 10 | 10 |
| timeout_then_pass | 10 | COMPLETED 10 | CLEAN 10 | 20 |
| timeout_exhausted | 10 | FAILED 10 | INCOMPLETE 10 | 20 |
| agent_crash | 10 | FAILED 10 | INCOMPLETE 10 | 10 |
| schema_refusal | 10 | FAILED 10 | INCOMPLETE 10 | 10 |

What the statuses mean:

- `all_pass` finishes CLEAN when every required stage returns PASS.
- `receiving_fail` and `midstage_fail` finish EXCEPTION. The bus keeps going. A FAIL is a completed judgment, not a crash.
- `uncertain_needs_person` finishes BLOCKED / NEEDS_REVIEW. Recovery returns UNCERTAIN with `needs_human` true. The bus does not stop at that stage (`on_uncertain=continue`), and the rollup still blocks the workflow because a person was asked.
- `recovery_claim` finishes CLAIM_RECOMMENDED. In this group the earlier stages passed, so the claim is allowed.
- `recovery_silent` leaves Recovery's own verdict UNCERTAIN with `needs_human` false. The workflow outcome is still CLEAN, because a silent uncertainty is not a failure and does not ask for a person.
- `midstage_fail` is EXCEPTION on FBA and merchant-fulfilled units. A unit whose route is unknown has no Prep and no Pack stage, so there is nothing to fail and that unit stays CLEAN.
- `timeout_then_pass` tries Receiving twice. The first attempt is a timeout. The retry succeeds, and the unit can still finish CLEAN.
- `timeout_exhausted` records Receiving as pending / UNCERTAIN after both attempts, then continues. The workflow status is FAILED because that stage never completed. The process stays up.
- `agent_crash` raises `RuntimeError` inside Recovery. The orchestrator stores UNCERTAIN and does not die.
- `schema_refusal` is a bare HTTP 422. The bus stops there. Later stages are not called. The workflow is FAILED.

## One hundred sample units

Source: `data/sample/cases.json` plus the five sample CSVs. A stage runs only when the case is eligible: Prep for FBA, Pack for merchant-fulfilled, Returns only when `returned` is true, Receiving and Recovery always.

Eligibility: neither prep nor pack 9, prep ran 62, returns ran 24, pack ran 29.

Status: COMPLETED 73, BLOCKED 27.

Outcome: CLEAN 48, EXCEPTION 31, NEEDS_REVIEW 21.

Six units are BLOCKED and EXCEPTION together. One stage returned FAIL, and another asked for a person. The status is BLOCKED because the person comes first. The outcome stays EXCEPTION because a FAIL is still on the record. Twenty-one are BLOCKED / NEEDS_REVIEW with no FAIL. Forty-eight are CLEAN. Twenty-five are EXCEPTION with nobody waiting.

Replay rules, so the numbers stay tied to the CSV:

- Receiving PASS only when identity is yes and both damage fields are none. Identity no or real damage is FAIL. An uncertain field is UNCERTAIN.
- Prep FAIL on missing, unsealed, obscured, or badly placed marks. An uncertain field is UNCERTAIN.
- Pack PASS on `seal`, FAIL on `stop_and_fix`.
- Returns PASS on a disposition, except `pending_review`, which is UNCERTAIN.
- Recovery does not recommend a claim from these rows. A weight, lost, or warehouse line is silent. An inbound-defect or refund line is UNCERTAIN and asks for a person, because the CSV has no photo that can support or contradict it.

## How a failed agent is recovered

| step | what happened |
| --- | --- |
| connection refused, then resume | {"before_status": "FAILED", "before_outcome": "INCOMPLETE", "before_reason": "stage did not complete: receiving", "receiving_error": "agent_unavailable", "process_alive": true} |
| resume after the agent is back | {"after_status": "COMPLETED", "after_outcome": "CLEAN", "receiving_state": "completed", "receiving_verdict": "PASS", "attempts_seen": 5} |
| every agent raises | {"status": "FAILED", "outcome": "INCOMPLETE", "verdicts": ["UNCERTAIN", "UNCERTAIN", "UNCERTAIN", "UNCERTAIN"], "states": ["error", "error", "error", "error"], "escaped": false} |
| prep returns a bare 422 | {"status": "FAILED", "halted": "stage prep did not judge (status=error); not continuing", "stages_after_prep_that_ran": ["prep"], "receiving_verdict": "PASS"} |

Recovery sequence:

1. The agent is down. Receiving raises connection refused on both attempts. The orchestrator writes a pending evidence record, verdict UNCERTAIN, and marks the workflow FAILED. Prep is not asked to invent a judgment for a stage that did not finish.
2. `resume` runs the same workflow again. Errored stages are retried. With the agent answering, Receiving becomes PASS and the workflow can complete.
3. If every agent raises, each required stage is stored as error / UNCERTAIN. The outcome is INCOMPLETE. No exception leaves `run_workflow`.
4. A bare 422 from Prep is a schema refusal. Receiving's PASS is kept. Pack, Returns, and Recovery are not called after that refusal.

## What this does not show

It does not show Claude accuracy. It does not start ports 8102–8105. `UNIT-001`, `UNIT-002`, and `UNIT-003` were not part of these 200 units; those three remain the presentation script.

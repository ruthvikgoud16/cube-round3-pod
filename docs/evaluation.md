# Pod 4 system evaluation

This page is the system scorecard. A stage percentage below is that stage's own Claude run. The stress table is a crash test of the orchestrator. Neither number is a five-agent accuracy.

## Stage scores already measured

| Stage | What was measured | Result | What it is not |
|---|---|---|---|
| Receiving | 12 Claude calls, two labelers, frozen 2026-10-07 | Full agreement on every check: 3 units. On checks where the two labelers agreed: quantity 10/10, identity 5/12 | Not a 50-case eval. Token cost was not stored. |
| Prep | 15 Claude calls, one frozen sheet, 2026-10-08 | 104/122 fields (85.2%). 7 disagreements, 11 model-uncertain | Not a second labeler. Not a Gemini score. |
| Pack | 15 Claude calls, 2026-10-09, one labeler | 3/14 verdicts (21.4%) after ORD-005 was removed. 0 false seals | ORD-005's carton shows a person's head and is not in the denominator. The agent sealed no labeled pass. |
| Returns | 47 Claude calls, 40 scored | Identity 37/40 (92.5%), completeness 30/40 (75%), condition 17/40 (42.5%) | Disposition agreement is policy consistency, not accuracy. |
| Recovery | Rules on six copied fee lines. Model calls 0 | No match rate. No line became `claimable_usd` | Not a claim-accuracy number. |

## Orchestrator stress, 2026-10-08

Source: `docs/pod4-stress-run.md`. No Claude calls. 0 crashes. 0 schema failures.

| Set | Workflows | What came out |
|---|---:|---|
| Scripted scenarios | 100 | 60 COMPLETED, 10 BLOCKED, 30 FAILED. Outcomes include CLEAN, EXCEPTION, NEEDS_REVIEW, CLAIM_RECOMMENDED, INCOMPLETE |
| Sample CSV cases | 100 | 73 COMPLETED, 27 BLOCKED. CLEAN 48, EXCEPTION 31, NEEDS_REVIEW 21 |

Failure injection, same run:

| Break | Stored result |
|---|---|
| Agent connection refused | FAILED / INCOMPLETE, UNCERTAIN, `agent_unavailable` |
| Resume after the agent answers | COMPLETED / CLEAN |
| Every agent raises | FAILED / INCOMPLETE. The exception does not escape |
| Bare 422 from Prep | Receiving PASS is kept. Later stages are not called |

## What is not measured

No workflow in this repo has been scored as a five-stage Claude outcome. Tracer photo folders are empty. A false-claim rate on live Recovery lines does not exist, because there is no labeled fee sheet large enough to score.

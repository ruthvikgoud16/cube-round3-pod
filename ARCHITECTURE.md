# Architecture

This document describes the **starter**. At the bottom is a section for **your Pod's architecture**, which you must fill in and which is part of the submission. A submission whose `ARCHITECTURE.md` still only describes the starter has not documented its system.

## 1. The system

```text
                POD
                 │
       ┌─────────▼─────────┐      owns workflow state; derives status and final outcome from the evidence chain
       │    Orchestrator   │      routes · validates · records evidence · retries · handles failures and UNCERTAIN
       └─────────┬─────────┘
                 │  Agent Input ▼          ▲ Agent Output (evidence)
       ┌─────────▼─────────┐
       │     Receiving     │
       └─────────┬─────────┘
                 ↓
       ┌───────────────────┐
       │       Prep        │   (FBA units)
       └─────────┬─────────┘
                 ↓
       ┌───────────────────┐
       │       Pack        │   (merchant-fulfilled / 3PL units)
       └─────────┬─────────┘
                 ↓
       ┌───────────────────┐
       │      Returns      │   (if a return happened)
       └─────────┬─────────┘
                 ↓
       ┌───────────────────┐
       │     Recovery      │   reads ALL accumulated evidence
       └─────────┬─────────┘
                 ↓
          Final Outcome        derived by the orchestrator, not copied from any agent

  shared/schemas · shared/contracts · shared/utils      data/input · data/sample · data/expected      examples/
```

The arrows show the *expected commerce journey*. Physically, every hand-off goes through the orchestrator ([`INTEGRATION-GUIDE.md`](INTEGRATION-GUIDE.md) section 1).

## 2. Responsibilities

| Component | Responsible for | Not responsible for |
|---|---|---|
| **Agent** (`agents/<stage>/`) | One stage's judgment, returned as an Agent Output with an Evidence Record. Failing open. Refusing other tenants. | Calling other agents. Setting workflow state. Rewriting earlier evidence. |
| **Orchestrator** (`orchestration/`) | Starting workflows; identifying the current stage; invoking agents with context; validating and recording evidence; updating state; routing; retries; failures; UNCERTAIN; the final outcome. | Making stage judgments. Fabricating or deleting evidence. Turning UNCERTAIN into PASS/FAIL without an explicit rule. |
| **Contract** (`shared/schemas/`) | One strict set of data shapes. | Agent-specific logic (that goes in `payload`). |
| **Stubs** (`agents/*/app.py` as shipped) | Replaying Round 2 CSV rows as valid evidence, so the plumbing can be tested. | Pretending to be agents. |

## 3. Shared data

| Object | Owner | Lives in |
|---|---|---|
| Evidence Record | the agent that produced it (immutable) | the evidence store |
| Workflow State | **the orchestrator** | the workflow store |
| Overrides | the orchestrator records them; a person makes them | Workflow State (`overrides[]`), referencing evidence |
| Final Outcome | **the orchestrator**, derived | Workflow State (`final_outcome`) |
| Captures | the Pod | `data/input/<subject>/<stage>/`, referenced by `sha256` |

## 4. Evidence flow and workflow state

```text
Agent Result → Evidence Record → Orchestrator state transition → Next stage → New evidence → Updated workflow state → Final Outcome
```

- Each stage's evidence is stored and passed to **every later stage** as `previous_evidence`.
- State is `PENDING → IN_PROGRESS → COMPLETED`, or `FAILED` / `BLOCKED` / `RECOVERY_REQUIRED` ([`ORCHESTRATION-GUIDE.md`](ORCHESTRATION-GUIDE.md) section 5), always derived from the evidence and overrides.
- `transitions[]` is the audit trail.
- A reviewer can walk from the Final Outcome to `contributing_records`, to checks, to `evidence_refs`, to the `sha256` of the exact bytes examined.

## 5. Error handling

Every failure is **recorded and never becomes success**: a degraded evidence record stands in (no checks, UNCERTAIN, the error), the stage is `error`, the workflow `FAILED` with outcome `INCOMPLETE`. Transient failures retry; refusals and invalid output do not; UNCERTAIN is preserved; `resume` retries. Full table: [`ORCHESTRATION-GUIDE.md`](ORCHESTRATION-GUIDE.md) section 8. Tenancy: `org_id` on every request, record and workflow; a record about another org is rejected as a security event; **your storage must enforce it too**.

## 6. Final outcome

`CLEAN`, `CLAIM_RECOMMENDED`, `EXCEPTION`, `NEEDS_REVIEW` or `INCOMPLETE`, with the reason, the contributing evidence, `needs_human`, and `provisional` (true unless the workflow is `COMPLETED`). Default rules: [`ORCHESTRATION-GUIDE.md`](ORCHESTRATION-GUIDE.md) section 6.

## 7. What is fixed and what is yours

**Fixed (the contract, strict):**

- The five required agents and their stages (Specialist Pods: four agents plus integration work, see [`FAQ.md`](FAQ.md))
- Common evidence requirements: the Agent Input/Output and Evidence Record shapes; PASS / FAIL / UNCERTAIN; the status vocabularies
- Required traceability: workflow id, agent id, hashes, `upstream_refs`, overrides that reference what they supersede
- An orchestrator that owns workflow state and produces a **Final Outcome**
- Minimum testing, and the submission and evaluation requirements ([`SUBMISSION-GUIDE.md`](SUBMISSION-GUIDE.md), [`ROUND3-RUBRIC.md`](ROUND3-RUBRIC.md))

**Participant-designed (the implementation, flexible):**

- Internal architecture, programming language, frameworks, how each agent is built
- How the orchestrator is implemented (the starter is one option; LangGraph, a queue, a state machine, your own)
- The communication mechanism (in-process, HTTP, queue) as long as the contract holds
- Database, persistence, deployment platform
- UI, review queue, dashboards
- Additional services, additional features
- The final-outcome policy, routing and `on_uncertain` / `on_error` policies (documented in `docs/decisions.md`)

## 8. Extension points

| You want to… | Change |
|---|---|
| Add or reroute a stage | `orchestration/flow.json` (and write a decision) |
| Change the final decision or status rules | `orchestration/rollup.py` (and its tests, and a decision) |
| Plug in a real agent | `agents/<stage>/app.py` + `agent.json` |
| Run an agent as a service in any language | `agent.json` `mode: "http"` + [`agent-api.md`](shared/contracts/agent-api.md) |
| Run your own subjects | `data/input/<subject>/<stage>/` + a cases file |
| Add agent-specific data to evidence | `payload` (never the envelope) |
| Persist to a database | implement the four store methods in `orchestration/store.py` |

## 9. Deployment options (yours)

- **Single process:** `uvicorn orchestration.api:app` with all agents `inproc`. Simplest.
- **Orchestrator + agent services:** each agent its own process, `mode: "http"`, `<STAGE>_URL` set; `GET /health` for readiness.
- Whatever you pick, the demo runs from the submitted commit and any URL works without your accounts. The API ships with **no authentication**: add it before exposing it.

---

## Your Pod's architecture

Pod 4 runs one orchestrator and five stage agents. The orchestrator in `orchestration/` owns workflow state. It does not judge a stage. The in-tree `agents/*/app.py` files that replay sample CSVs are not the live agents. Prep, Pack, Returns, and Recovery are the HTTP services named in each `agent.json`. Receiving is the in-process agent in `agents/receiving/`.

```
case
  → Orchestrator :8100   (FileStore under out/)
       Receiving   in-process, optional HTTP :8101   receiving-manager, owner @Vinayteja467
       Prep        HTTP :8102                        prep-manager, owner @MPreethika16
       Pack        HTTP :8103                        pack-manager, owner @Vivek21-7
       Returns     HTTP :8104                        returns-manager, owner @ruthvikgoud16
       Recovery    HTTP :8105                        recovery-manager, owner @mdmoghnishah
  → Workflow State + Final Outcome
```

Official `orchestration/flow.json` still routes Prep only for FBA and Pack only for merchant-fulfilled, and Returns only when `returned` is true. `orchestration/flow.pod4-tracers.json` (D-008) runs all five stages for TRACER-01, TRACER-02, and TRACER-03. A unit is not both FBA and merchant-fulfilled.

### What each agent really is

| Stage | What judges | Model | Still a stub? |
|---|---|---|---|
| Receiving | Observer plus policy. The model does not set the verdict. | Claude when `ANTHROPIC_API_KEY` is set | No. In-tree agent. |
| Prep | Work-order guards plus one Claude observation. | claude-sonnet-4-5 when the key is set | The in-tree `app.py` is a CSV stub. The live service is the Prep repo on port 8102. |
| Pack | One Claude inspection of the open box against the order. A closed carton returns UNCERTAIN and makes no call. | claude-sonnet-4-5 | In-tree `app.py` is a CSV stub. Live service is port 8103. |
| Returns | One Claude call for identity, completeness, and condition. Disposition follows the policy. | Claude | In-tree `app.py` is a CSV stub. Live service is port 8104. |
| Recovery | Rules on the fee line and the upstream evidence. A model summary cannot change the position. | No model call required | In-tree `app.py` is illustrative. Live service is port 8105. |

Demo units UNIT-001, UNIT-002, and UNIT-003 are scripted in `orchestration/demo_overrides.py` (D-009). They are labeled as a script. `context.live: true` and the TRACER subjects skip that script.

### Orchestrator

`orchestration/orchestrator.py` starts, advances, resumes, and records overrides. State is JSON files in `out/workflows/` and `out/evidence/` through `FileStore`. Evidence is immutable: a second write of the same `record_id` with a different `content_hash` is rejected. Retries come from the flow (`retries`, `timeout_s`). A person records an override with actor, reason, and the record it supersedes (`POST /workflows/{id}/overrides`).

Decisions that define this Pod, in `docs/decisions.md`:

- D-007. A bare HTTP 422 stops the bus. A 422 that already contains an Agent Output is kept. A completed FAIL does not stop the bus. A pending stage stops `flow.json` so Recovery cannot treat an unjudged stage as finished.
- D-008. The tracer flow runs every stage and continues on pending.
- D-009. The three demo units are a script, not a vision result.
- D-010. Before validation, `canonicalize_output` maps `hold` to `review`, fills a missing `uncertain_reason`, and reseals `content_hash`. Verdicts and check results stay the agent's.

Photos at `data/input/<subject>/<stage>/` are embedded as `data_base64` when they are images of 8MB or less, so an agent in another repo can see them.

### Routing and the final outcome

`orchestration/rollup.py` derives the outcome. It is not copied from an agent.

| Situation | Outcome |
|---|---|
| Every applicable stage passed | CLEAN |
| A stage other than Recovery finished FAIL | EXCEPTION |
| A stage asked for a person | NEEDS_REVIEW, workflow BLOCKED |
| A stage errored or stayed pending | INCOMPLETE, workflow FAILED |
| Recovery verdict FAIL and every earlier record completed | CLAIM_RECOMMENDED |
| Recovery verdict FAIL while an earlier record is not completed | INCOMPLETE, and no claim amount is attached |
| Recovery silent (`UNCERTAIN`, `needs_human` false) | Does not by itself halt the workflow |

`provisional` is true unless the workflow status is COMPLETED.

### Tenancy

Demo tenants are `org_demo_alpha` and `org_demo_bravo`. Each request, record, and workflow carries `org_id`. An unknown tenant is HTTP 404 from the live agents. Records whose `org_id` or unit does not match the subject are dropped before Recovery judges. The stress run and the HTTP classify tests cover the refusal path. The orchestrator API itself has no login.

### Failure model

What the stress run broke, with the process still alive (`docs/pod4-stress-run.md`):

- Connection refused becomes FAILED / INCOMPLETE, verdict UNCERTAIN, error `agent_unavailable`. Resume after the agent answers can finish COMPLETED / CLEAN.
- An exception inside an agent is stored as UNCERTAIN. It does not escape `run_workflow`.
- A bare 422 from Prep keeps Receiving's PASS and does not call the later stages.

### Deployment

Local only. Nothing here is a public URL.

```
uvicorn orchestration.api:app --port 8100
```

The read-only desk is `http://127.0.0.1:8100/desk`. Health is `GET /health`. Prep, Pack, Returns, and Recovery must already be listening on 8102–8105 or those stages report down. Set `ORCH_FLOW` to `orchestration/flow.pod4-tracers.json` for the five-stage demo path. `make run` still uses `flow.json`.

### Known limits

- `data/input/TRACER-01`, `TRACER-02`, and `TRACER-03` have no photos, so a live five-stage tracer run is not frozen.
- There is no system claim-precision number. Stage scores live in `docs/evaluation.md`. The stress numbers are not vision accuracy.
- The desk reads workflows already stored under `out/`. It does not start agents.
- Receiving's agreed-on-every-check set is 3 units. Pack's held-out verdict match is 3 of 14. Recovery has no match rate.

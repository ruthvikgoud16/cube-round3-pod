# Decisions

Every non-obvious design choice gets one entry, so a reviewer can see **what you chose, why, and what you rejected.** Newest last. This is where *Decision quality* and *Orchestration* in the [rubric](../ROUND3-RUBRIC.md) are won or lost. It is not meant to become a long report: a few lines per decision.

Write an entry whenever you: change the flow or its policies; change how the orchestrator stores state or evidence; change the final-outcome or status rules; choose a communication mechanism; decide how retries and overrides work; pick a side on a **known finding** (below); add to the contract's `payload`; or choose a deployment shape.

## Template

```text
### D-NNN · Short title
- Date / Owner:
- Context: what forced a decision?
- Options considered: A, B, C
- Decision: what we chose
- Why: the evidence or reasoning
- Consequences: what gets easier / harder; what would make us revisit
```

## Questions your Pod's decisions should answer

- Why this orchestration approach, and who owns what in it?
- Why this communication mechanism (in-process, HTTP, queue)?
- How is workflow state stored, and how does it survive a restart?
- How are retries, timeouts and resume handled?
- How is evidence persisted, and how is its immutability enforced?
- How are overrides captured, referenced, and used downstream?
- What do we do about UNCERTAIN: continue or block, and who decides?
- How does the final outcome treat weak or uncertain evidence?

## Starter decisions (made by the organisers; change them with a new entry)

### D-000 · The default flow is routed, not strictly sequential
- Context: the Round 2 sample gives each unit a Prep record *or* a Pack record, never both, and Returns only for returned units.
- Decision: `flow.json` routes FBA units through Prep, merchant-fulfilled units through Pack, and runs Returns only when a return happened. A stage that does not apply is `skipped` with the reason recorded.
- Why: forcing every unit through all five stages would invent evidence. Units with neither route (F-12) skip both.

### D-001 · The orchestrator owns state; status and outcome are derived
- Decision: workflow status and final outcome are pure functions of the stored evidence and the overrides (`orchestration/rollup.py`). Agents return evidence and a recommendation; they never write state.
- Why: "the latest agent outcome" and "Recovery's reading of it" are not the source of truth; the traceable evidence chain is.

### D-002 · UNCERTAIN continues by default; blocking is a policy
- Decision: `on_uncertain: continue` by default; `block` halts only when the UNCERTAIN result asks for a person (`needs_human`). Either way the workflow is `BLOCKED` with outcome `NEEDS_REVIEW` until an override resolves it.
- Why: a warehouse line must not wait, and the evidence of later stages is not lost. Recovery's SILENT (UNCERTAIN, `needs_human: false`) must not halt anything.

### D-003 · Failures are recorded, never hidden; never success
- Decision: a failed stage gets a degraded evidence record (no checks, UNCERTAIN, the error) and the workflow ends `FAILED` / `INCOMPLETE` (`provisional`). `resume` retries it and keeps the failed attempt's evidence.

### D-004 · Overrides are workflow entries that reference evidence
- Decision: evidence is immutable. A person's override is appended to the workflow's `overrides` with actor, reason, timestamp, the record it supersedes, the previous effective verdict and the new one. The latest wins; downstream agents receive them in `context.overrides`.

### D-005 · Zero-amount reimbursements are not claimable (F-09)
- Decision: the Recovery stub treats a 0.00 line as SILENT. Why: claiming $0 is meaningless and the meaning of 0.00 is unresolved.

### D-006 · Field names (F-15)
- Decision: `check_key`, `detail`, `content_hash`, `latency_ms`, `client_id` follow the Round 2 Returns list; `org_id`, `operator_id`, `inputs`, `model.version` follow the CSVs. Mapping in [`EVIDENCE-CONTRACT.md`](../EVIDENCE-CONTRACT.md). Open for the organisers.

## Known findings carried over from Round 2

Round 2 participants raised these contradictions and gaps in the shared data and documents. They are **open**: the organisers will rule on them. Until then **do not silently pick a side**: add an entry above with your assumption, and design so that changing it is cheap. `F-07` to `F-12` match the issue numbers on the Round 2 Recovery repo.

| ID | Finding | Why it matters for integration | Source |
|---|---|---|---|
| **F-07** | 42 of 61 sample fee lines are `fulfilment_fee_weight_tier`, and no upstream sample records measured weight or dimensions. | Recovery can only mark these SILENT. Prep is the natural source: see `payload.measurements`. | [Recovery #7](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/7) |
| **F-08** | `unit_id` means a **PO line** in Receiving (RCV-0003: 48 ordered, 44 received) but a **single unit** in the fee report. UNIT-0003 is lost inbound, then charged a fulfilment fee, then returned: that cannot be one physical unit. | Joins on a bare id can be wrong. The contract adds `subject.unit_scope` and `subject.refs`. | [Recovery #8](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/8) |
| **F-09** | A `lost_inbound` adjustment is posted with `amount_usd` 0.00. "Not reimbursed" (a claim to raise) or "amount missing"? | The answer flips the verdict. See D-005. | [Recovery #9](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/9) |
| **F-10** | Receiving shortfalls are supplier-side and happen before goods reach the channel, so they cannot support a channel `lost_inbound` claim. | Keep supplier shortfall and channel loss separate in your decision logic. | [Recovery #10](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/10) |
| **F-11** | Returns records exist for FBA-routed units (UNIT-0003 has a Prep record **and** a seller-side Returns record). Do FBA returns come back to the seller or to the channel's warehouse? | Decides whether Returns evidence can contradict `refund_issued_item_not_returned`. | [Recovery #11](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/11) |
| **F-12** | 9 of the 100 sample units have neither a Prep nor a Pack record, although each unit is meant to take one route. | The starter marks these `route: "unknown"` and skips both stages. Recovery's SILENT rate depends on it. | [Recovery #12](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/12) |
| **F-13** | The Round 2 rules said the organisers would provide an official evidence contract. None was published, and one participant's v0 proposal was withdrawn pending it. | **Resolved for Round 3:** [`EVIDENCE-CONTRACT.md`](../EVIDENCE-CONTRACT.md) v1.0. | [Receiving #4](https://github.com/Cube-Build-A-Thon/cube-01-receiving-manager/issues/4), [Recovery #13](https://github.com/Cube-Build-A-Thon/cube-05-recovery-manager/issues/13) |
| **F-14** | The Round 2 repos do not all carry the same rules: Receiving, Prep and Recovery share one short `RULES.md`; Pack's differs in wording; Returns has a much longer one (field names, evaluation method, mandatory LinkedIn post) that also ends mid-sentence. | Round 3 carries over the **union**; the organisers should confirm which is authoritative and finish the truncated section (presumably how Round 2 counts towards the final result). | [Returns `RULES.md`](https://github.com/Cube-Build-A-Thon/cube-04-returns-manager/blob/main/RULES.md) |
| **F-15** | The only organiser-authored list of "official evidence contract" fields is in the Returns repo (`organization_id`, `operator_label`, `images`, …) and is "concepts such as", not a schema. The sample CSVs use `org_id`, `operator_id`. | v1.0 uses a mix; see D-006 and the note at the top of [`EVIDENCE-CONTRACT.md`](../EVIDENCE-CONTRACT.md). | [Returns README](https://github.com/Cube-Build-A-Thon/cube-04-returns-manager/blob/main/README.md) |

### Raising a new finding

A contradiction between documents or data is a **finding**, not a failure. Open an issue on your Pod's repo with the `finding` label: what contradicts what, an example row, and what you assumed (and add the assumption above). Good findings are credited under *Decision quality*.

## Your Pod's decisions

### D-007 · A 422 and a 200 pending envelope are the same stop
- Date / Owner: 2026-10-08 / ruthvikgoud16
- Context: Receiving answers a bad input with HTTP 422 and a FastAPI error body. Prep and Returns answer the same situation with HTTP 422 or 200 and a pending Agent Output. The starter treated every 4xx as `agent_rejected` and then kept calling later stages. Recovery could then read an unjudged stage as if it had finished.
- Options considered: leave the starter (continue after every error); halt on every error including timeouts; halt only when the stage did not judge.
- Decision: a 422 that already contains an Agent Output is accepted as that output. A 422 that does not is recorded as `schema_rejected`, not as a dead process. Either way the workflow stops. A completed `FAIL` (Prep `stop_and_fix`) does not stop the bus. A timeout is still retried and, after that, still follows `on_error`. If Recovery's verdict is `FAIL` while any earlier record is not `completed`, the final outcome is `INCOMPLETE` and no claim amount is attached.
- Why: the five services do not share one HTTP habit. The bus has to. A claim from an unjudged barcode or an unjudged return is the failure mode Round 3 will hit first.
- Consequences: one refused or pending stage means later stages stay `pending` until `resume`. A demo that needs five envelopes has to send a unit every applicable stage can actually judge. Forcing Pack and Prep on the same unit is still rejected: a unit is FBA or merchant-fulfilled, not both (D-000).

### D-008 · Three tracer units call all five agents
- Date / Owner: 2026-10-08 / ruthvikgoud16
- Context: the sample flow (D-000) sends a unit through Prep or Pack, not both. The October 10 demo is three physical units photographed for every stage. Their photos are not in the sample CSVs.
- Options considered: rewrite the four other agents into one codebase; point the bus at the organiser stubs; add a second flow that calls the existing HTTP services.
- Decision: `flow.json` stays the sample route. `orchestration/flow.pod4-tracers.json` runs Receiving, Prep, Pack, Returns, and Recovery for `TRACER-01`, `TRACER-02`, and `TRACER-03`. Those four services stay in their own repos, mode `http`, ports 8102–8105. Receiving stays in-process on this repo. Photo bytes are attached to the Agent Input because a relative path in this repo is invisible to the other four. `on_pending: continue` is set only on this flow, so a pending stage does not hide the later agents. A schema 422 still stops. No golden PASS is written before a real run.
- Why: the agents already return the contract. The missing piece was the pipe, not a new domain model. A claim still cannot be manufactured from an unjudged stage (rollup).
- Consequences: `make run` does not use this flow. A tracer with an empty photo folder returns pending from that stage and the workflow stays incomplete. Order lines for Pack are added on the case when the photos arrive.

### D-009 · Three presentation units are scripted, and the same ids can go live
- Date / Owner: 2026-10-08 / ruthvikgoud16
- Context: the October 10 demo cannot depend on a vision call. The Drive photos are not in the repo yet. A script that pretends to be Claude would fail the honesty check.
- Options considered: hardcode PASS inside each teammate's agent; wait for photos and risk a timeout on stage; a bus-level script with model.calls 0, and a live switch.
- Decision: `UNIT-001`, `UNIT-002`, and `UNIT-003` return contract-valid records from `orchestration/demo_overrides.py`. The model name is `demo-override` and the call count is 0. `UNIT-001` is CLEAN. `UNIT-002` is BLOCKED / NEEDS_REVIEW because Returns is UNCERTAIN. `UNIT-003` is CLAIM_RECOMMENDED and the Recovery payload flag is CONTRADICTS, citing the Prep and Returns record ids from that same run. `context.live: true`, or any other subject id, calls the real agent. A crashing agent is caught in the orchestrator and stored as UNCERTAIN. The official evidence schema is unchanged: verdict is already PASS, FAIL, or UNCERTAIN, and a content hash is SHA-256, not a tamper proof.
- Why: the contract already rejects a thinner record. Rewriting the four agents to return a private shape would fail validation and the ownership check.
- Consequences: do not quote these three runs as vision accuracy. When the Drive photos arrive, set `live` true or use `TRACER-01` through `TRACER-03`.

### D-010 · The bus seals a real judgment that used a private hash or the word hold
- Date / Owner: 2026-10-08 / ruthvikgoud16
- Context: a live run of PRODUCT-1 through PRODUCT-10 called Claude. Receiving records were stored. Prep, Pack, and Returns records were dropped. Prep's next step was `hold`. Pack and Returns hashed the record with a different canonical form, so `content_hash` did not verify. One Pack check was UNCERTAIN with no `uncertain_reason`.
- Options considered: rewrite the hash inside Prep, Pack, and Returns; keep dropping the envelopes; seal the body on the bus and map `hold` to `review`.
- Decision: `canonicalize_output` runs before validation. `hold` becomes `review`. A missing uncertain reason becomes `insufficient_evidence`. The evidence body is sealed with the official hash, which excludes `content_hash` and `overrides`. The verdict, checks, and call count stay the agent's.
- Why: the judgment was already made. Dropping it made every live workflow FAILED even when Pack had returned PASS. The hash is a content hash, not a tamper seal.
- Consequences: a stored hash can differ from the hash in the agent's own log. A schema error that is not one of these three still becomes a pending UNCERTAIN record.

### D-011 · Optional API key on the orchestrator edge
- Date / Owner: 2026-10-17 / ruthvikgoud16
- Context: ARCHITECTURE.md and api.py stated the HTTP surface had no authentication. A public desk would expose workflow evidence and overrides.
- Options considered: always-open demo; JWT/OAuth; shared API key with public probes.
- Decision: when `ORCH_API_KEY` is set, data routes require `Authorization: Bearer` or `X-API-Key` (constant-time compare). `/health`, `/ready`, `/desk`, `/live`, `/metrics` stay public. Unset key keeps local CI and stub demos open.
- Why: Pod deploy needs a gate without standing up an IdP. Probes and scrapers must not need secrets.
- Consequences: Control Tower must send `VITE_ORCH_API_KEY` when the bus is locked. This is not multi-user RBAC.

### D-012 · SQLite as a first-class store backend
- Date / Owner: 2026-10-17 / ruthvikgoud16
- Context: FileStore is fine for the CLI; ephemeral deploy disks lose JSON under `out/` unless seeded. The store interface already invited a database swap.
- Options considered: keep files only; Postgres; SQLite via `STORE_BACKEND=sqlite`.
- Decision: `SqliteStore` implements the same methods (`list` / `load` / `save` / `get` / `put`) with WAL and evidence immutability. `build_store()` selects file | sqlite | memory.
- Why: one file on the volume, no extra service, same contract tests.
- Consequences: concurrent writers across processes are not a goal; scale-out still wants Postgres later.

### D-013 · Circuit breaker on HTTP agent transport only
- Date / Owner: 2026-10-17 / ruthvikgoud16
- Context: a dead Prep host caused every workflow to burn retries and latency. A bare 422 is not a dead host (D-007).
- Options considered: unlimited retries; breaker on every non-200; breaker on connection/5xx/timeout only.
- Decision: after `CIRCUIT_FAILURE_THRESHOLD` transport failures, open for `CIRCUIT_COOLDOWN_S`. Schema refusals and 4xx rejections do not trip it. Open raises `CircuitOpen` (subclass of `AgentUnavailable`) so resume/`on_error` paths stay unchanged.
- Why: fail fast on outages; never confuse judgment stops with outages.
- Consequences: health payload includes `circuit` for HTTP stages.

### D-014 · Correlation ids and dual metrics surface
- Date / Owner: 2026-10-17 / ruthvikgoud16
- Context: debugging a five-service run needed a shared id at the HTTP edge; ops wanted scrapable counters without a vendor.
- Decision: `RequestIdMiddleware` accepts or mints `X-Request-ID` and echoes it. `GET /metrics` returns JSON by default and Prometheus text when requested. `/ready` checks store only; `/health` still probes agents.
- Why: join logs to a desk poll; scrape without coupling to Datadog.
- Consequences: counters are process-local and reset on restart.

### D-015 · Idempotency-Key on workflow create
- Date / Owner: 2026-10-17 / ruthvikgoud16
- Context: `run_workflow` already advances an existing id, but a client retry after a completed POST still re-enters `advance`.
- Decision: if `Idempotency-Key` is present and the workflow is already terminal (`COMPLETED` / `BLOCKED` / `FAILED` / `RECOVERY_REQUIRED`), return the stored state.
- Why: safe client retries for the intake/create path.
- Consequences: in-progress retries still advance (intentional).

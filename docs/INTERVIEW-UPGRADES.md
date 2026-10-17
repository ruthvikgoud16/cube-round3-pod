# Interview talking points — Pod 4 production upgrades

Use this sheet in interviews. Each item is **real code on this branch**, not a slide claim.

## One-line pitch

> I took our Cube Round 3 multi-agent commerce orchestrator from a demo bus to a deployable integration layer: API auth, correlation IDs, SQLite persistence, circuit breakers for remote agents, and Prometheus-style metrics — without changing the evidence contract.

## What I shipped

| Upgrade | Where | Interview sound bite |
|---|---|---|
| **API key auth** | `orchestration/auth.py` | “The starter said the API had no auth. I added optional Bearer / X-API-Key with constant-time compare, keeping `/health` and `/metrics` public for probes.” |
| **Request correlation IDs** | `orchestration/request_id.py` | “Every HTTP call gets `X-Request-ID` echoed so desk polls, logs, and agent `request_id` can join the same run.” |
| **SQLite store** | `orchestration/store.py` | “Same four-method store interface as FileStore. Evidence immutability stays enforced; deploy survives restart with one volume file.” |
| **Circuit breaker** | `orchestration/clients.py` | “After N transport failures we fail fast for a cooldown. Schema 422 does **not** trip the breaker — that would confuse ‘bad input’ with ‘dead agent’.” |
| **Metrics** | `orchestration/metrics.py` + `GET /metrics` | “In-process counters for workflow outcomes and agent failures, JSON for demos, Prometheus text for scrapers.” |
| **Idempotent create** | `POST /workflows` + `Idempotency-Key` | “Retries of a finished workflow return the stored state instead of inventing a second run.” |
| **Readiness vs health** | `GET /ready` vs `GET /health` | “`/ready` checks the process + store; `/health` probes every stage agent and exposes circuit state.” |
| **Control Tower auth header** | `web/.../orchestrator.ts` | “The UI adapter forwards `VITE_ORCH_API_KEY` when the bus is locked down.” |

## Architecture story (30–60 seconds)

1. **Problem:** Five independently owned agents + one orchestrator. Demo worked on stubs; a public deploy had no auth, file-only state, and cascading retries when one HTTP agent was down.
2. **Constraint:** Round 3 contract is fixed — orchestrator owns workflow state; agents only return evidence; evidence is immutable.
3. **Approach:** Extend the bus at the edges (middleware, store backend, HTTP client) so stage judgment code and schemas stay untouched.
4. **Result:** Same `make test` contract suite still passes; new unit tests cover auth, sqlite, breaker, metrics.

## Tradeoffs I can defend

- **API key vs JWT/OAuth:** Key is enough for a Pod deploy and desk demos; OAuth would be next if multi-tenant operators share one host.
- **SQLite vs Postgres:** Zero extra services on Railway/Render; WAL mode + thread lock is fine for Pod throughput. Swap still goes through `build_store()`.
- **Circuit breaker only on transport:** A completed FAIL or pending envelope is a *judgment*, not an outage. Opening the circuit on 422 would hide real agent answers.
- **Metrics in-process:** Lost on restart; acceptable for demo ops. For production I’d push to OpenTelemetry — the counter names are already stable.

## Demo script (2 minutes)

```sh
make setup
# prove the suite still green
make test

# show auth
ORCH_API_KEY=demo STORE_BACKEND=sqlite make serve
curl -s localhost:8100/ready
curl -s -o /dev/null -w '%{http_code}\n' localhost:8100/workflows          # 401
curl -s -H 'X-API-Key: demo' localhost:8100/workflows                       # 200
curl -s 'localhost:8100/metrics?format=prometheus' | head

# show correlation
curl -sI -H 'X-Request-ID: interview-1' localhost:8100/ready | grep -i x-request-id
```

## Questions I expect — and answers

**“Did you change the agent contract?”**  
No. Auth, store, breaker, and metrics sit outside Agent Input/Output. `canonicalize_output` and rollup are unchanged.

**“What happens if Prep is down?”**  
HTTP failures increment the breaker. After the threshold, later calls get `CircuitOpen` → degraded evidence `agent_unavailable` → workflow `FAILED`/`INCOMPLETE`. Resume works once Prep answers and the cooldown ends.

**“How do you know evidence wasn’t rewritten?”**  
`SqliteStore.put_evidence` / `FileStore.put_evidence` reject a second write of the same `record_id` with a different `content_hash`.

**“What’s still missing?”**  
No JWT/RBAC, no distributed tracing exporter, no Postgres, no end-to-end five-agent vision accuracy number (tracers still need photos). I’d name those as next steps, not pretend they’re done.

## Decisions log

See `docs/decisions.md` entries **D-011 … D-015**.

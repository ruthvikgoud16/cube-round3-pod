# Receiving Manager — integration notes (tomorrow)

## Endpoint
- Base: `http://127.0.0.1:8101` (or Pod host)
- `GET /health` → `{ status, stage: receiving, version, contract_version }`
- `POST /run` → Agent Input → Agent Output (Evidence Contract v1)

## Subject IDs
Use **`UNIT-RCV-01` … `UNIT-RCV-12` only**. These are the **real project deliveries** (dock photos), not mocks.

Photos: `data/input/<UNIT-RCV-NN>/receiving/{01_pallet,02_carton,03_unit}.jpg`

## Env
```bash
RECEIVING_MODE=mock   # CI / offline
RECEIVING_MODE=live   # needs ANTHROPIC_API_KEY
ANTHROPIC_MODEL=claude-sonnet-4-5
```

## Orchestrator glue
1. Call Receiving first in the flow with PO context in `context` or fixture merge (mock).
2. Persist returned `evidence.record_id` (`RCV-*`) and `decision.outcome`.
3. On `pending_review` / UNCERTAIN — route human; do not invent counts downstream.
4. Tenancy: wrong `org_id` → HTTP 404.
5. Fail-open: exceptions return pending Agent Output, never crash the workflow.

## Findings wired
- **F-08** `unit_scope=po_line`
- **F-10** shortfall is supplier-side only (`claim_boundary`)

## UI for demo
- `/` desk · `/evaluation` · `/failures` · `/about`

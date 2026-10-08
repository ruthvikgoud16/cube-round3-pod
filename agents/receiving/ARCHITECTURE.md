# Architecture — Receiving Manager (elite, ~70% without photos)

## Decision: best approach for Round 3

Receiving is **stage 1**. If it invents counts or hides uncertainty, Prep/Pack/Returns/Recovery all inherit lies. Architecture mirrors Returns (Ruthvik) on purpose so the Pod speaks one dialect.

```text
                    ┌─────────────────────────┐
  Agent Input ───▶  │  tenancy gate (404)     │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │  PO context extract     │
                    │  (+ fixture merge mock) │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │  load photos            │
                    │  quality gate           │
                    └───────────┬─────────────┘
                         ┌──────┴──────┐
                         ▼             ▼
              RECEIVING_MODE=live   =mock
              Claude observe×1      fixture observe
              (vision facts only)   (cases.json)
                         └──────┬──────┘
                                ▼
                    ┌─────────────────────────┐
                    │  receiving_policy_v1    │
                    │  6 official check_keys  │
                    │  outcome codes          │
                    └───────────┬─────────────┘
                                ▼
                    ┌─────────────────────────┐
                    │  build_record / seal    │
                    │  RCV-* Evidence v1.0    │
                    │  unit_scope=po_line     │
                    └───────────┬─────────────┘
                                ▼
                         Agent Output
                    (fail-open pending_output
                     on any hard failure)
```

## Why this shape

| Choice | Why |
|---|---|
| Observe ≠ decide | Same as Returns; Recovery can trust checks |
| One model call | Cost/latency; Round 3 eng rule |
| Quality gate first | Bad pixels never become confident grades |
| Mock mode first-class | Build/test to 70% before dock photos |
| Policy holds on any UNCERTAIN | Never reject/accept on incomplete evidence |
| `unit_scope=po_line` | Finding F-08 |
| `shortfall` + `claim_boundary=supplier_side_only` | Finding F-10 |
| Shared `build_record` | Drop into Pod orchestrator without a private A2A |

## Modes

| Env | Behaviour |
|---|---|
| `RECEIVING_MODE=mock` | Fixture observations; placeholders OK; **default for CI** |
| `RECEIVING_MODE=live` | Requires `ANTHROPIC_API_KEY` + real photos |

When photos arrive: drop into `data/input/<UNIT>/receiving/`, set `RECEIVING_MODE=live`, keep the same `handle()`.

## Build status

**Done:** contract spine, policy, 12 mock fixtures, fail-open, tenancy, desk UI, unit tests, **24 staged deliveries** (72 photos), observe-v3 (wrong-SKU harden + count rules), light PII redaction, eval predict/score vs Jaanu+Soanli, path-to-50 plan for 13–24 labels + more dock shoots.

**Left for Pod glue:** push fork, teammate `pod.json` handles, orchestrator e2e, grow labels to ~50.

# Receiving Manager (elite) — Pod 4 · ~70% build

Local Round 3–ready Receiving agent. Photos are **not** required to finish the spine — use `RECEIVING_MODE=mock` until dock photos arrive.

## Architecture (best approach)

```text
Agent Input
  → tenancy (org_demo_alpha|bravo)
  → PO context (+ fixture merge in mock)
  → quality gate
  → ONE observation (Claude live | fixture mock)
  → receiving_policy_v1 → 6 official checks + outcome
  → Evidence RCV-* (unit_scope=po_line, F-10 shortfall boundary)
  → Agent Output (fail-open on errors)
```

Same discipline as Returns: **observe ≠ decide**, one call, UNCERTAIN never upgrades to PASS.

Details: [`ARCHITECTURE.md`](ARCHITECTURE.md)

## Quick start (no photos)

```bash
cd /Users/ruthvikgoud/Downloads/pod4/receiving-elite
source .venv/bin/activate   # or: python3.11 -m venv .venv && pip install -r requirements.txt
export RECEIVING_MODE=mock
PYTHONPATH=. python scripts/run_receiving_demo.py
PYTHONPATH=. pytest tests/unit/test_receiving_policy.py tests/unit/test_receiving_handle.py -q
```

Expected: **12/12** mock fixture paths. Photos staged under `data/input/UNIT-RCV-*/receiving/` (36 JPGs). Live: `RECEIVING_MODE=live` + `python scripts/run_receiving_live.py`.

## HTTP (Pod orchestrator)

```bash
RECEIVING_MODE=mock uvicorn agents.receiving.app:app --port 8101
curl localhost:8101/health
# orchestrator POSTs Agent Input to /run
```

## When photos arrive (~30% left)

1. Put sets under `data/input/UNIT-RCV-0N/receiving/{01_pallet,02_carton,03_unit}.jpg`
2. `export RECEIVING_MODE=live` + `ANTHROPIC_API_KEY`
3. Same `handle()` — no architecture change
4. Copy `agents/receiving/` into Vinay’s Pod fork

See [`PHOTOS-NEEDED.md`](PHOTOS-NEEDED.md).

## Status

| Piece | Status |
|---|---|
| Contract spine + policy | Done |
| Mock fixtures (6 paths) | Done |
| Fail-open / tenancy / idempotent RCV ids | Done |
| Live Claude path | Done (needs photos + key) |
| Real dock photos ×10 | Waiting on you |
| Push to Vinay Pod repo | Waiting on write access |

Owner on push: `@Vinayteja467` · Integration: Ruthvik

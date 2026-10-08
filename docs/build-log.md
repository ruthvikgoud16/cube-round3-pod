# Receiving build log

## 2026-10-07 — photos + live path complete

- Forked Round 3: https://github.com/ruthvikgoud16/cube-round3-pod
- Staged **36** JPGs under `data/input/UNIT-RCV-01..12/receiving/` from Flipkart/Shadowfax carton Drive + RTN headphones for missing-parts.
- Case 06 remapped **water → tears** (no water stain in set).
- Mock: **12/12** expected outcomes.
- Live Claude: sealed dock photos correctly yield `pending_review` when unit counts are not visible (UNCERTAIN ≠ pass).
- Scripts: `stage_receiving_photos.py`, `run_receiving_demo.py`, `run_receiving_live.py`
- Desk: http://127.0.0.1:8101/

## Honest limits

- Most inbound cartons are sealed → live cannot invent unit counts.
- Mock fixtures still exercise accept / reject / exceptions paths for CI and demos.
- Crop PII (addresses, faces) before public submit.

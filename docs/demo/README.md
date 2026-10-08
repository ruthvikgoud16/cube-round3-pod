# Receiving Manager — project set (12 real deliveries)

These are **not mocks**. Photos are real Flipkart/Shadowfax inbound cartons staged under `data/input/UNIT-RCV-01…12`.
Labelers: **Jaanu** and **Soanli**. One Claude observation call per delivery in live mode; disposition from `receiving_policy_v1`.

## Pages

| Page | URL (local :8101) |
|---|---|
| Desk | `/` |
| Evaluation | `/evaluation` |
| Failed cases | `/failures` |
| About / integration | `/about` |
| API docs | `/docs` |

## Commands

```bash
RECEIVING_MODE=mock  uvicorn agents.receiving.app:app --port 8101
RECEIVING_MODE=live  uvicorn agents.receiving.app:app --port 8101
python eval/predict.py && python eval/score.py && python scripts/build_eval_pages.py
```

## Frozen eval

- Soft identity match rate (latest score): see `eval/EVALUATION.md`
- Failed digest: `eval/FAILED-CASES.md`

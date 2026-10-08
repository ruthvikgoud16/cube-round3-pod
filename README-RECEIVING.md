# Receiving Manager (Pod 4) — ready for tomorrow

**Project set = 12 real dock deliveries** (`UNIT-RCV-01`…`12`). Not mocks.

## Quick start
```bash
cd receiving-elite   # or cube-round3-pod after sync
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # set ANTHROPIC_API_KEY for live

# Desk + evaluation UI
RECEIVING_MODE=mock .venv/bin/uvicorn agents.receiving.app:app --port 8101
# open http://127.0.0.1:8101/
```

| URL | Page |
|---|---|
| `/` | Desk — run one or all 12, view photos + checks |
| `/evaluation` | Rates + agent outcomes |
| `/failures` | Agreed-check mismatches |
| `/about` | Integration contract |
| `/docs` | OpenAPI |
| `/eval/report.html` | Printable report → Save as PDF |

## Eval refresh
```bash
.venv/bin/python eval/predict.py
.venv/bin/python eval/score.py
.venv/bin/python scripts/build_eval_pages.py
.venv/bin/python scripts/build_report_html.py
```

## Integration
See [`docs/INTEGRATION.md`](docs/INTEGRATION.md).

# Evaluation Playbook

Operyx AI benchmarks intent extraction against gold annotations using field-level scorers.

## Gold Dataset Format

Store datasets under `eval/datasets/` as JSON:

```json
{
  "name": "sample_gold",
  "entries": [
    {
      "call_id": "uuid-or-null",
      "ground_truth": {
        "side": "BUY",
        "stock_symbol": "RELIANCE",
        "quantity": 100,
        "price": 2500.0,
        "exchange": "NSE"
      },
      "prediction": { "...": "optional for offline scoring" }
    }
  ]
}
```

## Running Evaluations

### API

```bash
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{"dataset_path": "eval/datasets/sample_gold.json", "use_db_annotations": false}'
```

### Dashboard

Open **Evaluations** → **Run sample benchmark**.

### From DB annotations

Set `use_db_annotations: true` to score live extractions against submitted annotations.

## Metrics

| Field | Scorer |
|-------|--------|
| side | Exact match |
| stock_symbol | Exact + Levenshtein ≤ 1 |
| quantity | Numeric normalize |
| price | Numeric normalize (lakhs/crores) |
| exchange | Exact (NSE/BSE) |

Reports are written to `eval/reports/output/{run_id}.html`.

## CI Gate

Prompt changes under `prompts/` should pass regression tests (`tests/prompt/`) and not regress benchmark metrics by more than 2% on the gold set.

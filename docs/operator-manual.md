# Operyx AI — Operator Manual

## Overview

Operyx AI ingests customer call recordings, transcribes them, and extracts structured trading intent (BUY/SELL, stock, quantity, price, exchange) for downstream systems.

## Daily Operations

### Upload calls

- **Single upload**: Dashboard → Calls → Upload, or `POST /api/v1/calls`
- **Batch upload** (up to 100 files): `POST /api/v1/calls/batch` with multipart `files` field

### Review queue

Low-confidence extractions appear in **Reviews**. Operators can:

1. **Approve** — accept the extraction as-is
2. **Correct** — edit fields and save
3. **Reprocess** — re-run the pipeline on the call audio

### Export results

After a batch upload, note the `batch_id` from the response.

- JSON: `GET /api/v1/exports/{batch_id}?format=json`
- Excel: `GET /api/v1/exports/{batch_id}?format=xlsx`

The Reviews dashboard also supports paste-and-export for a batch ID.

### Prompt management

Navigate to **Prompts** to:

- View all prompt versions and content hashes
- Set the active version
- Adjust A/B traffic weights (0.0–1.0 per version)

API: `PATCH /api/v1/prompts/active` with `active_version` and/or `weights`.

### Analytics

The **Analytics** dashboard shows:

- Call volume by status
- Confidence score distribution
- Detected language breakdown

## Authentication (Optional)

Auth is disabled by default. Enable in `config/default.yaml`:

```yaml
auth:
  enabled: true
```

Send a Bearer token (base64-encoded JSON stub for PoC):

```json
{"sub": "operator-1", "roles": ["reviewer"]}
```

### Roles

| Role      | Access                                      |
|-----------|---------------------------------------------|
| annotator | Upload calls, create annotations            |
| reviewer  | Review queue, exports, analytics            |
| admin     | Prompts, evaluations, all reviewer access   |

## Audit Log

All review actions and exports are recorded in the `audit_logs` table with actor, entity, and change payload.

## Evaluation

Run gold-set benchmarks from **Evaluations** or `POST /api/v1/evaluations`. Review per-field accuracy before promoting prompt versions.

## Support Escalation

1. Check API readiness: `GET /api/v1/ready`
2. Inspect worker logs for STT/LLM failures
3. Verify prompt version active in **Prompts**
4. See [k8s-runbook.md](./k8s-runbook.md) for cluster operations

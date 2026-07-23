# URL Ingestion

Ingest call recordings directly from remote URLs (for example Knowlarity `fetchsound` links) without downloading files manually.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/calls/from-url` | Ingest a single recording URL |
| `POST` | `/api/v1/calls/batch/from-urls` | Batch ingest up to 100 URLs per request |

### Single URL

```bash
curl -X POST http://localhost:8000/api/v1/calls/from-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://sr.knowlarity.com/vr/fetchsound/?callid=YOUR_CALL_ID"}'
```

### Batch URLs

```bash
curl -X POST http://localhost:8000/api/v1/calls/batch/from-urls \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/a?callid=1", "https://example.com/b?callid=2"]}'
```

Response fields:

- `batch_id` — UUID grouping the ingested calls
- `call_ids` — list of created call UUIDs
- `total` — successfully ingested count
- `errors` — per-URL failures (partial success is allowed)

When Redis/Celery is unavailable, the API runs STT + intent extraction **inline** in the same request (same DB session). This works for both SQLite dev and Postgres prod.

## SQLite dev vs Postgres prod

| | **SQLite (local dev)** | **Postgres (prod / Docker)** |
|--|------------------------|------------------------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/operyx_dev.db` | `postgresql+asyncpg://…` (see `docker-compose.yml`) |
| Migrations | Optional for dev (`Base.metadata.create_all` on startup) | **Required**: `alembic upgrade head` |
| HTTP batch ingest | Supported; inline processing uses the request session to avoid SQLite locking | Supported; recommended for large batches |
| Celery worker | Optional | Recommended for production throughput |
| Concurrency | Single-writer; use `--limit` for smoke tests | Full concurrent ingest + workers |

### Option A — local dev (SQLite, mock STT)

```bash
# .env
DATABASE_URL=sqlite+aiosqlite:///./data/operyx_dev.db
STT_PROVIDER=mock
LLM_PROVIDER=mock

uvicorn src.api.main:app --reload --port 8000
```

**Mock STT limitation:** `MockSTTAdapter` always reports `detected_language: "en"` regardless of audio content. Language distribution reports and multilingual QA require a real STT provider (see below).

### Option B — Docker (Postgres + Redis + worker)

```bash
docker compose up --build
alembic upgrade head
```

Use this path for production-like ingest, exports, and Celery-backed processing at scale.

## Real STT for multilingual analysis

To detect Hindi, Tamil, or other languages accurately:

1. Set `STT_PROVIDER` in `.env` (e.g. `whisperx` or `google`).
2. Install optional deps if using WhisperX: `pip install -e ".[whisperx]"`.
3. Configure provider block in `config/default.yaml` under `providers.stt`.
4. Restart API (and Celery worker if used).

Example (WhisperX):

```yaml
# config/default.yaml
providers:
  stt:
    default: whisperx
    whisperx:
      model: large-v3
      device: cpu
      compute_type: int8
```

```bash
STT_PROVIDER=whisperx uvicorn src.api.main:app --port 8000
```

After processing, run language analysis:

```bash
python scripts/analyze_languages.py --ingest-metadata eval/reports/ingest_batch.json
```

## CLI: `scripts/ingest_urls.py`

Reads a text file with one URL per line (comments with `#` are ignored). Files with more than 100 URLs are split into multiple API batches automatically.

### Ingest all URLs

```bash
python scripts/ingest_urls.py "C:\Users\natar\Downloads\recording_urls.txt"
```

Outputs:

- `eval/reports/ingest_batch.json` — batch IDs, counts, and any per-URL errors

The API processes each batch inline when Celery is unavailable, so transcripts and intent extractions are ready when the HTTP response returns (no separate finish-up script required).

### Options

| Flag | Description |
|------|-------------|
| `--api-base URL` | API base (default `http://localhost:8000`) |
| `--output PATH` | Ingest metadata JSON path |
| `--analyze` | After ingest, run STT-based language analysis (requires processed calls in DB) |
| `--generate-preview [PATH]` | Write pre-ingest language report from URL metadata |
| `--dry-run` | Parse URLs and print stats without calling the API |
| `--limit N` | Ingest only the first N URLs (smoke test) |

If the API is unreachable, the script automatically writes `eval/reports/language_analysis.json` using URL metadata estimates.

### Offline preview (no API / no STT)

```bash
python scripts/ingest_urls.py recording_urls.txt --generate-preview
```

Report is saved to `eval/reports/language_analysis.json` with `analysis_mode: "url_metadata_estimate"`.

### Manual reprocess (single call)

```bash
python -c "
import asyncio
from uuid import UUID
from src.application.use_cases.process_call import process_call_async
asyncio.run(process_call_async(UUID('YOUR_CALL_ID')))
"
```

Or start the worker: `celery -A src.workers.celery_app worker --loglevel=info`

### Language analysis after processing

```bash
# From ingest metadata (all batches)
python scripts/analyze_languages.py --ingest-metadata eval/reports/ingest_batch.json

# From a single batch
python scripts/analyze_languages.py --batch-id YOUR_BATCH_ID
```

### Processing pipeline

1. **Download** — `AudioDownloader` fetches each URL with retries, rate limiting, and concurrent requests (configurable in `config/default.yaml` under `processing.url_download`).
2. **Filename** — Resolved from `Content-Disposition`, URL path, or `callid` query parameter plus detected format (`wav` / `mp3` / `m4a`).
3. **Store** — Audio is uploaded via `UploadCallUseCase` to local or S3 storage.
4. **Batch** — Successful calls are grouped in `batch_uploads`.
5. **Process** — STT + intent extraction runs inline in the API request (or via Celery when Redis is available).

## URL file format

```
# Optional comment
https://sr.knowlarity.com/vr/fetchsound/?callid=75193f3c-2606-4984-9f34-888c3bf843b7
https://sr.knowlarity.com/vr/fetchsound/?callid=b9e893ed-d66b-4fe3-b640-df7b39f35e5a
```

CSV-style `url,metadata` lines are supported; only the URL column is used.

## Export results

```bash
curl "http://localhost:8000/api/v1/exports/{batch_id}?format=json"
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Connection refused` to Postgres | Set `DATABASE_URL` in `.env` to SQLite for local dev, or start `docker compose` |
| `alembic upgrade head` duplicate heads | Ensure only one `002_batch_audit` migration exists under `alembic/versions/` |
| HTTP 500 during batch ingest (SQLite) | Upgrade to latest code (inline processing uses request session); retry with `--limit 5` smoke test |
| Ingest OK but no transcripts | Confirm API returned 201; check API logs; ensure mock/real STT is configured |
| All languages show as `en` | Expected with `STT_PROVIDER=mock`; switch to WhisperX or Google STT for real detection |
| `HTTP 401` on Knowlarity HEAD | Normal; downloader uses GET |
| Batch > 100 URLs | Script splits into multiple batches automatically |

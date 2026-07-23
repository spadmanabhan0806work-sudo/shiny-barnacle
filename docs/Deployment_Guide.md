# Deployment Guide

## Local Development

### 1. Clone and Setup

```bash
git clone <repo-url>
cd operyx-ai
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Generate Sample Data (if needed)

```bash
python scripts/generate_data.py
```

### 4. Start Backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Verify: http://localhost:8000/api/health

### 5. Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Verify: http://localhost:3000

## Environment Variables

Create `backend/.env`:

```env
AI_PROVIDER=mock
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
DATABASE_URL=sqlite:///./operyx_demo.db
CORS_ORIGINS=http://localhost:3000
```

### Using Real AI Providers

Set `AI_PROVIDER` to `claude`, `openai`, or `gemini` and provide the matching API key:

```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
```

## Production Considerations (Future)

This PoC is designed for local demo. For production deployment:

| Concern | Recommendation |
|---------|---------------|
| Database | Migrate to PostgreSQL |
| Auth | Add OAuth2 / SSO |
| File storage | Use S3 or Azure Blob |
| Hosting | Containerize with Docker |
| HTTPS | Reverse proxy (nginx/Caddy) |
| Secrets | Vault or cloud secret manager |
| CI/CD | GitHub Actions pipeline |

### Example Production Dockerfile (Backend)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Example Production Build (Frontend)

```bash
cd frontend
npm run build
npm start
```

Set `NEXT_PUBLIC_API_URL` to your backend URL.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Check `CORS_ORIGINS` includes frontend URL |
| Empty dashboard | Ensure backend is running and seeded |
| DB locked | Stop duplicate uvicorn instances |
| AI errors | Fall back to `AI_PROVIDER=mock` |
| Port in use | Change port: `--port 8001` |

## Reset Database

```bash
cd backend
rm operyx_demo.db
python -m uvicorn app.main:app --reload --port 8000
```

Database will be recreated and re-seeded on startup.

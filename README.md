# Operyx AI — Intelligent Supply Chain Platform (PoC)

AI-powered supply chain management proof of concept with executive dashboards, demand forecasting, supplier risk intelligence, procurement copilot, logistics control tower, document AI, and executive reporting.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env    # optional — works without API keys in mock mode
python -m uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

### Regenerate Sample Data

```bash
cd backend
python scripts/generate_data.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PROVIDER` | `mock` | `claude`, `openai`, `gemini`, or `mock` |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `GOOGLE_API_KEY` | — | Gemini API key |
| `DATABASE_URL` | `sqlite:///./operyx_demo.db` | SQLite connection |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |

## Demo Flow (10 min)

1. **Executive Dashboard** (`/`) — KPIs, charts, AI insights
2. **Demand Forecast** (`/forecast`) — Select SKU, view forecast + safety stock
3. **Supplier Risk** (`/suppliers`) — Filter high-risk, open detail drawer
4. **Procurement Copilot** (`/copilot`) — Ask "Which suppliers are delayed?"
5. **Logistics** (`/logistics`) — Shipments, warehouses, fleet alerts
6. **Document AI** (`/documents`) — Click sample invoice for extraction
7. **Executive Report** (`/reports`) — Generate full AI summary

## Project Structure

```
operyx-ai/
├── frontend/          # Next.js 14 + TypeScript + Tailwind + shadcn/ui
├── backend/           # FastAPI + SQLite + SQLAlchemy
├── data/              # Sample CSVs, JSON, invoices
├── docs/              # Documentation
└── README.md
```

## Modules

| Module | Route | API |
|--------|-------|-----|
| Executive Dashboard | `/` | `/api/dashboard/*` |
| Demand Forecast | `/forecast` | `/api/forecast/*` |
| Supplier Risk | `/suppliers` | `/api/suppliers/*` |
| Procurement Copilot | `/copilot` | `/api/copilot/chat` |
| Logistics | `/logistics` | `/api/logistics/*` |
| Document AI | `/documents` | `/api/documents/*` |
| Executive Report | `/reports` | `/api/reports/executive` |

## Documentation

- [PoC Business Document](docs/Operyx_AI_Supply_Chain_PoC_Document.md)
- [Project Architecture](docs/Project_Architecture.md)
- [Deployment Guide](docs/Deployment_Guide.md)
- [API Documentation](docs/API_Documentation.md)
- [Demo Script](docs/Demo_Script.md)

## AI Provider

The demo runs fully in **mock mode** without API keys. Mock responses use live database queries for realistic, data-aware answers. Set `AI_PROVIDER` and the corresponding API key to use real LLM providers.

## License

Proof of Concept — Internal Use

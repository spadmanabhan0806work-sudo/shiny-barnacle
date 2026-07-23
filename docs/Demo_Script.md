# Demo Script — Operyx AI Supply Chain PoC

**Duration:** 10–15 minutes  
**Audience:** Supply chain executives, procurement leaders, IT stakeholders  
**Prerequisites:** Backend on port 8000, frontend on port 3000

---

## Opening (1 min)

> "Today I'll show Operyx AI — an intelligent supply chain platform that brings together real-time operations data and AI to help you forecast demand, manage supplier risk, and run your logistics control tower — all in one place."

Open http://localhost:3000

---

## 1. Executive Dashboard (2 min)

**Navigate to:** `/` (home)

**Talking points:**
- "This is your command center — six live KPIs updated from our supply chain database."
- Point out **Delayed Shipments** and **Avg Supplier Risk** — "These are the metrics that need attention today."
- Scroll to charts: "Inventory forecast trend, warehouse utilization by DC, and fleet status distribution."
- Open **AI Insights** panel: "Our AI automatically surfaces risks — delayed shipments, high-risk suppliers, capacity alerts."

**Key message:** Single pane of glass for supply chain health.

---

## 2. AI Demand Forecast (2 min)

**Navigate to:** `/forecast`

**Talking points:**
- "Planners can upload their sales CSV or use our bundled 24-month history across 20 SKUs."
- Select a SKU from dropdown: "Watch the forecast chart — blue is actual, green is projected with confidence bands."
- Point to **Safety Stock** and **Confidence** gauge.
- Show **Recommended Inventory** table: "Per-warehouse replenishment guidance."
- Read **AI Summary**: "The narrative explains what the numbers mean for decision-makers."

**Demo action:** Click "Regenerate Forecast" for a different SKU.

---

## 3. Supplier Risk Intelligence (2 min)

**Navigate to:** `/suppliers`

**Talking points:**
- "15 suppliers scored by delivery performance, quality incidents, and financial health."
- Click **High Risk** filter: "Three suppliers need immediate attention."
- Click **Analyze** on Pacific Metals Corp.
- In the drawer, walk through risk factors, contract expiry, and AI recommendations.

**Key message:** Proactive risk management instead of reactive firefighting.

---

## 4. Procurement Copilot (2 min)

**Navigate to:** `/copilot`

**Talking points:**
- "Your team can ask natural-language questions about the supply chain."
- Click chip: **"Which suppliers are delayed?"**
- Show the data-aware response listing actual shipments.
- Try: **"Show high risk vendors."** or **"Warehouse capacity status?"**

**Key message:** AI assistant grounded in your real operational data.

---

## 5. Logistics Dashboard (2 min)

**Navigate to:** `/logistics`

**Talking points:**
- Red alert banner: "Delayed shipments flagged immediately."
- Shipment table with tracking numbers, routes, ETAs, status badges.
- **Risk Alerts** feed on the right — automated from live data.
- Warehouse utilization chart and **Fleet Status** cards with driver locations.

**Key message:** Control tower visibility without a complex TMS integration.

---

## 6. Document AI (2 min)

**Navigate to:** `/documents`

**Talking points:**
- "Procurement teams spend hours on invoice processing. Watch this."
- Click sample: **invoice_acme_2025_001.txt**
- Show extracted fields: vendor, amount, dates, PO reference with confidence scores.
- Line items table and **AI Summary** on the right.

**Optional:** Upload a TXT file to show the upload flow.

---

## 7. AI Executive Report (1 min)

**Navigate to:** `/reports`

**Talking points:**
- "One click generates a full executive briefing."
- Click **Generate Executive Summary**
- Walk through: Business Summary → Risks → Recommendations → Predicted Issues → Next Actions
- Click **Copy to Clipboard** — "Ready to paste into an email or board deck."

---

## Closing (1 min)

> "Operyx AI runs entirely in demo mode without API keys — but flip one environment variable and it connects to Claude, OpenAI, or Gemini. The architecture is modular and production-ready for PostgreSQL, authentication, and cloud deployment."

**Q&A prompts:**
- "How does mock mode work?" → DB-aware responses from live queries
- "Can we add our own data?" → Upload CSV or replace seed files
- "What's the path to production?" → See Deployment Guide

---

## Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Blank KPIs | Restart backend: `uvicorn app.main:app --reload --port 8000` |
| CORS error | Check backend `.env` has `CORS_ORIGINS=http://localhost:3000` |
| Slow AI response | Confirm `AI_PROVIDER=mock` for instant responses |
| Missing data | Run `python scripts/generate_data.py` and restart backend |

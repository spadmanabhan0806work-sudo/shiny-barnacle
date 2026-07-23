from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Inventory, Order, Shipment, Supplier, Warehouse


class AIService:
    def __init__(self, db: Session | None = None):
        self.db = db
        self.settings = get_settings()
        self.provider = self.settings.ai_provider.lower()

    async def generate(self, prompt: str, context: dict[str, Any] | None = None, system: str = "") -> str:
        context = context or {}
        if self.provider == "mock" or not self._has_api_key():
            return self._mock_response(prompt, context, system)
        if self.provider == "claude":
            return await self._call_claude(prompt, context, system)
        if self.provider == "openai":
            return await self._call_openai(prompt, context, system)
        if self.provider == "gemini":
            return await self._call_gemini(prompt, context, system)
        return self._mock_response(prompt, context, system)

    def _has_api_key(self) -> bool:
        keys = {
            "claude": self.settings.anthropic_api_key,
            "openai": self.settings.openai_api_key,
            "gemini": self.settings.google_api_key,
        }
        return bool(keys.get(self.provider, ""))

    def _build_context_block(self, context: dict[str, Any]) -> str:
        if not context:
            return ""
        lines = ["Supply Chain Context:"]
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _get_db_context_str(self) -> str:
        if not self.db:
            return ""
        try:
            orders = self.db.query(Order).count()
            delayed = self.db.query(Shipment).filter(Shipment.status == "delayed").count()
            suppliers = self.db.query(Supplier).filter(Supplier.risk_level == "high").all()
            supplier_names = ", ".join(s.name for s in suppliers[:3]) if suppliers else "None"
            low_stock = self.db.query(Inventory).filter(Inventory.quantity < Inventory.reorder_point).count()
            return (
                f"\nLive Database Context:\n"
                f"- Active Orders: {orders}\n"
                f"- Delayed Shipments: {delayed}\n"
                f"- High-Risk Suppliers: {len(suppliers)} ({supplier_names})\n"
                f"- Low-Stock Items: {low_stock}\n"
            )
        except Exception:
            return ""

    async def _call_claude(self, prompt: str, context: dict, system: str) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        full_system = f"{system}{self._get_db_context_str()}\n\n{self._build_context_block(context)}".strip()
        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=full_system or "You are an AI supply chain analyst.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def _call_openai(self, prompt: str, context: dict, system: str) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        full_system = f"{system}{self._get_db_context_str()}\n\n{self._build_context_block(context)}".strip()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": full_system or "You are an AI supply chain analyst."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    async def _call_gemini(self, prompt: str, context: dict, system: str) -> str:
        import google.generativeai as genai

        try:
            genai.configure(api_key=self.settings.google_api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            full_prompt = (
                f"System: {system or 'You are an AI supply chain & procurement assistant.'}\n"
                f"{self._get_db_context_str()}\n"
                f"{self._build_context_block(context)}\n\n"
                f"User Question: {prompt}"
            )
            response = await model.generate_content_async(full_prompt)
            return response.text
        except Exception:
            return self._mock_response(prompt, context, system)

    def _mock_response(self, prompt: str, context: dict, system: str) -> str:
        prompt_lower = prompt.lower()
        db = self.db

        if "copilot" in system.lower() or "procurement" in prompt_lower or any(
            k in prompt_lower for k in ["hi", "hello", "hey", "help", "order", "shipment", "supplier", "inventory", "stock", "warehouse", "delay", "risk", "status", "summary", "snapshot"]
        ):
            return self._mock_copilot_response(prompt_lower, db)

        if "forecast" in prompt_lower or "demand" in prompt_lower:
            sku = context.get("sku", "SKU-001")
            return (
                f"Demand forecast analysis for {sku}: Historical data shows seasonal peaks in Q2 and Q4. "
                f"Moving average projects steady growth of 6-8% over the next 6 months. "
                f"Recommend maintaining safety stock at 1.5x average monthly demand. "
                f"Key risk: supplier lead times may extend during peak season."
            )

        if "supplier" in prompt_lower or "risk" in prompt_lower or "vendor" in prompt_lower:
            if db:
                high_risk = db.query(Supplier).filter(Supplier.risk_level == "high").all()
                names = ", ".join(s.name for s in high_risk[:3]) if high_risk else "None"
                return (
                    f"Supplier risk assessment: {len(high_risk)} high-risk suppliers identified "
                    f"({names}). Primary concerns include declining on-time delivery rates, "
                    f"contract expirations within 6 months, and quality incidents. "
                    f"Recommend diversifying sourcing for critical SKUs and initiating contract renegotiations."
                )
            return "Three suppliers flagged as high-risk due to delivery delays and quality incidents."

        if "document" in prompt_lower or "invoice" in prompt_lower:
            vendor = context.get("vendor", "Unknown Vendor")
            amount = context.get("total_amount", "N/A")
            return (
                f"Document analysis complete for {vendor}. Total amount: {amount}. "
                f"Payment terms appear standard (Net 30). No anomalies detected in line items. "
                f"Recommend processing for payment approval within standard workflow."
            )

        if "executive" in prompt_lower or "report" in prompt_lower:
            return self._mock_executive_summary(db)

        if "insight" in prompt_lower or "dashboard" in prompt_lower:
            return self._mock_insights_text(db)

        return self._mock_copilot_response(prompt_lower, db)

    def _mock_copilot_response(self, prompt_lower: str, db: Session | None) -> str:
        if not db:
            return (
                "Hello! I am your Operyx AI Procurement Copilot. "
                "I can answer questions about suppliers, purchase orders, inventory, warehouse utilization, and delayed shipments."
            )

        if any(w in prompt_lower for w in ["hi", "hello", "hey", "who are you", "what can you do"]):
            return (
                "👋 Hello! I am your Operyx AI Procurement Copilot.\n\n"
                "You can ask me questions like:\n"
                "• 'Which shipments are delayed?'\n"
                "• 'Show high-risk suppliers'\n"
                "• 'What inventory is low on stock?'\n"
                "• 'Show recent purchase orders'\n"
                "• 'Warehouse capacity status'"
            )

        if "delayed" in prompt_lower or "delay" in prompt_lower or "shipment" in prompt_lower or "carrier" in prompt_lower:
            delayed = db.query(Shipment).filter(Shipment.status == "delayed").count()
            at_risk = db.query(Shipment).filter(Shipment.status == "at_risk").count()
            shipments = db.query(Shipment).filter(Shipment.status.in_(["delayed", "at_risk"])).limit(5).all()
            if shipments:
                details = "\n".join(f"• {s.tracking_number}: {s.supplier_name} → {s.destination} (ETA: {s.eta or 'TBD'})" for s in shipments)
                return (
                    f"Currently tracking {delayed} delayed and {at_risk} at-risk shipments:\n{details}\n\n"
                    f"Recommendation: Contact carriers for delayed shipments first."
                )
            return "All shipments are currently on schedule with no recorded delays."

        if "high risk" in prompt_lower or "risk" in prompt_lower or "supplier" in prompt_lower or "vendor" in prompt_lower:
            suppliers = db.query(Supplier).filter(Supplier.risk_level == "high").all()
            if suppliers:
                lines = "\n".join(
                    f"• {s.name}: Risk score {s.risk_score}, OTD {s.on_time_delivery_pct}%, "
                    f"{s.quality_incidents} quality incidents"
                    for s in suppliers
                )
                return f"High-risk suppliers ({len(suppliers)}):\n{lines}\n\nConsider backup suppliers for critical components."
            return "No high-risk suppliers detected. All vendors meet performance criteria."

        if "inventory" in prompt_lower or "stock" in prompt_lower or "reorder" in prompt_lower or "sku" in prompt_lower:
            low_stock = db.query(Inventory).filter(Inventory.quantity < Inventory.reorder_point).limit(5).all()
            if low_stock:
                lines = "\n".join(f"• {i.sku} ({i.product_name}): {i.quantity} units at {i.warehouse_name} (Reorder point: {i.reorder_point})" for i in low_stock)
                return f"Low stock alerts ({len(low_stock)} SKUs below reorder point):\n{lines}\n\nRecommend placing replenishment orders within 48 hours."
            return "Inventory levels are within acceptable safety ranges across all warehouses."

        if "order" in prompt_lower or "po" in prompt_lower or "purchase" in prompt_lower:
            pending = db.query(Order).filter(Order.status == "pending").count()
            recent = db.query(Order).order_by(Order.id.desc()).limit(5).all()
            if recent:
                lines = "\n".join(f"• {o.po_number}: {o.supplier_name} - ${o.total_amount:,.2f} ({o.status})" for o in recent)
                return f"There are {pending} pending purchase orders. Recent orders:\n{lines}"
            return "No active purchase orders found in the system."

        if "warehouse" in prompt_lower or "capacity" in prompt_lower or "utilization" in prompt_lower:
            warehouses = db.query(Warehouse).all()
            if warehouses:
                lines = "\n".join(f"• {w.name}: {w.utilization_pct}% utilized ({w.used_units:,}/{w.capacity_units:,} units)" for w in warehouses)
                return f"Warehouse utilization overview:\n{lines}"
            return "No warehouse utilization data available."

        total_orders = db.query(Order).count()
        total_suppliers = db.query(Supplier).count()
        delayed = db.query(Shipment).filter(Shipment.status == "delayed").count()
        high_risk = db.query(Supplier).filter(Supplier.risk_level == "high").count()
        return (
            f"Supply chain overview for your prompt: '{prompt[:60]}...'\n\n"
            f"• Active Purchase Orders: {total_orders}\n"
            f"• Total Suppliers: {total_suppliers} ({high_risk} high-risk)\n"
            f"• Delayed Shipments: {delayed}\n\n"
            f"Try asking specifically about 'delayed shipments', 'high risk suppliers', 'low inventory', or 'purchase orders'."
        )

    def _mock_executive_summary(self, db: Session | None) -> str:
        if not db:
            return "Executive summary: Supply chain operations are stable."
        orders = db.query(Order).count()
        inv_value = sum(i.quantity * i.unit_value for i in db.query(Inventory).all())
        delayed = db.query(Shipment).filter(Shipment.status == "delayed").count()
        high_risk = db.query(Supplier).filter(Supplier.risk_level == "high").count()
        avg_util = sum(w.utilization_pct for w in db.query(Warehouse).all()) / max(db.query(Warehouse).count(), 1)
        return (
            f"Operyx supply chain overview: Managing {orders} purchase orders with "
            f"${inv_value:,.0f} in inventory value. {delayed} shipments are delayed, "
            f"{high_risk} suppliers at high risk. Average warehouse utilization at {avg_util:.1f}%. "
            f"Priority actions: address delayed shipments, renegotiate high-risk supplier contracts, "
            f"and optimize Chicago DC capacity."
        )

    def _mock_insights_text(self, db: Session | None) -> str:
        return self._mock_executive_summary(db)

    async def generate_insights(self) -> list[dict[str, str]]:
        db = self.db
        insights = []
        if db:
            delayed = db.query(Shipment).filter(Shipment.status == "delayed").count()
            if delayed > 0:
                insights.append({
                    "title": "Shipment Delays Detected",
                    "description": f"{delayed} shipments are currently delayed. Review carrier assignments and ETAs.",
                    "severity": "high", "category": "logistics",
                })
            high_risk = db.query(Supplier).filter(Supplier.risk_level == "high").count()
            if high_risk > 0:
                insights.append({
                    "title": "High-Risk Suppliers",
                    "description": f"{high_risk} suppliers flagged for elevated risk. Contract renewals recommended.",
                    "severity": "high", "category": "suppliers",
                })
            warehouses = db.query(Warehouse).filter(Warehouse.utilization_pct > 85).all()
            for w in warehouses:
                insights.append({
                    "title": f"{w.name} Near Capacity",
                    "description": f"Utilization at {w.utilization_pct}%. Consider redistribution or expansion.",
                    "severity": "medium", "category": "warehouses",
                })
            low_stock = db.query(Inventory).filter(Inventory.quantity < Inventory.reorder_point).count()
            if low_stock > 0:
                insights.append({
                    "title": "Low Stock Alerts",
                    "description": f"{low_stock} SKUs below reorder point. Initiate replenishment orders.",
                    "severity": "medium", "category": "inventory",
                })
        if not insights:
            insights.append({
                "title": "Operations Stable",
                "description": "All key metrics within acceptable ranges. Continue monitoring.",
                "severity": "low", "category": "general",
            })
        return insights

    async def generate_executive_report(self) -> dict[str, Any]:
        db = self.db
        summary = self._mock_executive_summary(db)
        risks, recommendations, predicted, actions = [], [], [], []

        if db:
            high_risk = db.query(Supplier).filter(Supplier.risk_level == "high").all()
            for s in high_risk:
                risks.append(f"{s.name}: Risk score {s.risk_score}, contract expires {s.contract_expiry}")
                recommendations.append(f"Initiate backup sourcing plan for {s.name} ({s.category})")

            delayed = db.query(Shipment).filter(Shipment.status.in_(["delayed", "at_risk"])).all()
            for s in delayed[:5]:
                predicted.append(f"Shipment {s.tracking_number} may miss SLA by 3-7 days")
                actions.append(f"Escalate {s.tracking_number} with {s.carrier}")

            warehouses = db.query(Warehouse).filter(Warehouse.utilization_pct > 80).all()
            for w in warehouses:
                predicted.append(f"{w.name} may reach 95% capacity within 30 days")
                actions.append(f"Plan inventory redistribution from {w.name}")

        if not risks:
            risks.append("Moderate geopolitical risk in Asian sourcing regions")
        if not recommendations:
            recommendations.append("Continue quarterly supplier performance reviews")
        if not predicted:
            predicted.append("Seasonal demand increase expected in Q3")
        if not actions:
            actions.append("Schedule weekly supply chain review meeting")

        return {
            "business_summary": summary,
            "risks": risks,
            "recommendations": recommendations,
            "predicted_issues": predicted,
            "next_actions": actions,
            "generated_at": datetime.utcnow().isoformat(),
        }

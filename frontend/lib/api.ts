const getApiBase = () => {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url;
};

const API_BASE = getApiBase();

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `API error ${res.status}`);
  }
  return res.json();
}

export interface KPIs {
  total_orders: number;
  inventory_value: number;
  delayed_shipments: number;
  avg_supplier_risk: number;
  warehouse_utilization: number;
  transportation_active: number;
  transportation_delayed: number;
}

export interface Insight {
  title: string;
  description: string;
  severity: string;
  category: string;
}

export interface DashboardCharts {
  inventory_forecast: { period: string; actual: number; forecast: number }[];
  warehouse_utilization: { name: string; utilization: number; used: number; capacity: number }[];
  transportation_status: { status: string; count: number }[];
}

export interface Supplier {
  id: number;
  name: string;
  country: string;
  category: string;
  risk_score: number;
  risk_level: string;
  contract_expiry: string | null;
  on_time_delivery_pct: number;
  quality_incidents: number;
  financial_health: string;
  delay_count: number;
}

export interface SupplierAnalysis {
  supplier: Supplier;
  risk_factors: string[];
  recommendations: string[];
  ai_analysis: string;
}

export interface Shipment {
  id: number;
  tracking_number: string;
  supplier_name: string;
  origin: string;
  destination: string;
  status: string;
  eta: string | null;
  carrier: string;
  risk_flag: string;
}

export interface Warehouse {
  id: number;
  name: string;
  location: string;
  capacity_units: number;
  used_units: number;
  utilization_pct: number;
  manager: string;
}

export interface Vehicle {
  id: number;
  vehicle_id: string;
  type: string;
  status: string;
  location: string;
  driver: string;
  capacity_tons: number;
  current_load_tons: number;
}

export interface LogisticsAlert {
  id: string;
  severity: string;
  title: string;
  description: string;
  timestamp: string;
}

export interface ForecastResult {
  sku: string;
  product_name: string;
  forecast: { period: string; actual: number | null; forecast: number; lower_bound: number; upper_bound: number }[];
  safety_stock: number;
  confidence: number;
  ai_summary: string;
  recommended_inventory: { warehouse: string; current_stock: number; recommended_stock: number; action: string; gap: number }[];
}

export interface ChatMessage {
  role: string;
  content: string;
}

export interface CopilotResponse {
  reply: string;
  suggested_followups: string[];
}

export interface DocumentExtract {
  document_id: number | null;
  filename: string;
  doc_type: string;
  fields: { field: string; value: string; confidence: number }[];
  line_items: { line: number; description: string; quantity: number; unit_price: number; total: number }[];
  ai_summary: string;
}

export interface ExecutiveReport {
  business_summary: string;
  risks: string[];
  recommendations: string[];
  predicted_issues: string[];
  next_actions: string[];
  generated_at: string;
}

export const api = {
  getKPIs: () => fetchApi<KPIs>("/api/dashboard/kpis"),
  getCharts: () => fetchApi<DashboardCharts>("/api/dashboard/charts"),
  getInsights: () => fetchApi<Insight[]>("/api/dashboard/insights"),
  getSuppliers: (riskLevel?: string) =>
    fetchApi<Supplier[]>(`/api/suppliers${riskLevel ? `?risk_level=${riskLevel}` : ""}`),
  getSupplierAnalysis: (id: number) => fetchApi<SupplierAnalysis>(`/api/suppliers/${id}/analysis`),
  getShipments: (status?: string) =>
    fetchApi<Shipment[]>(`/api/logistics/shipments${status ? `?status=${status}` : ""}`),
  getWarehouses: () => fetchApi<Warehouse[]>("/api/logistics/warehouses"),
  getVehicles: () => fetchApi<Vehicle[]>("/api/logistics/vehicles"),
  getAlerts: () => fetchApi<LogisticsAlert[]>("/api/logistics/alerts"),
  getForecastSkus: () => fetchApi<{ sku: string; product_name: string }[]>("/api/forecast/skus"),
  generateForecast: (sku?: string, horizonMonths = 6) =>
    fetchApi<ForecastResult>("/api/forecast/generate", {
      method: "POST",
      body: JSON.stringify({ sku, horizon_months: horizonMonths }),
    }),
  uploadForecastCsv: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/api/forecast/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  copilotChat: (message: string, history: ChatMessage[] = []) =>
    fetchApi<CopilotResponse>("/api/copilot/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
  uploadDocument: async (file: File, docType = "invoice") => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", docType);
    const res = await fetch(`${API_BASE}/api/documents/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  extractDocument: (documentId?: number, filename?: string) =>
    fetchApi<DocumentExtract>("/api/documents/extract", {
      method: "POST",
      body: JSON.stringify({ document_id: documentId, filename }),
    }),
  getSampleDocuments: () => fetchApi<{ filename: string; path: string }[]>("/api/documents/samples"),
  generateExecutiveReport: () =>
    fetchApi<ExecutiveReport>("/api/reports/executive", { method: "POST", body: JSON.stringify({}) }),
};

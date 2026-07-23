"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Boxes,
  Package,
  ShieldAlert,
  Truck,
  Warehouse,
} from "lucide-react";
import { ForecastAreaChart, TransportPieChart, UtilizationBarChart } from "@/components/charts/chart-components";
import { KPICard } from "@/components/dashboard/kpi-card";
import { PageShell } from "@/components/layout/page-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type DashboardCharts, type Insight, type KPIs } from "@/lib/api";

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getKPIs(), api.getCharts(), api.getInsights()])
      .then(([k, c, i]) => {
        setKpis(k);
        setCharts(c);
        setInsights(i);
      })
      .finally(() => setLoading(false));
  }, []);

  const severityVariant = (s: string) =>
    s === "high" ? "danger" : s === "medium" ? "warning" : "success";

  return (
    <PageShell
      title="Executive Dashboard"
      description="Real-time supply chain KPIs, forecasts, and AI-powered insights"
    >
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : kpis && charts ? (
        <div className="space-y-8">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <KPICard title="Total Orders" value={kpis.total_orders} icon={Package} trend="Active purchase orders" />
            <KPICard title="Inventory Value" value={kpis.inventory_value} format="currency" icon={Boxes} />
            <KPICard title="Delayed Shipments" value={kpis.delayed_shipments} icon={Truck} trend="Requires attention" />
            <KPICard title="Avg Supplier Risk" value={kpis.avg_supplier_risk} format="percent" icon={ShieldAlert} />
            <KPICard title="Warehouse Utilization" value={kpis.warehouse_utilization} format="percent" icon={Warehouse} />
            <KPICard title="Active Transport" value={kpis.transportation_active} icon={Truck} trend={`${kpis.transportation_delayed} delayed`} />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <ForecastAreaChart data={charts.inventory_forecast} />
            </div>
            <TransportPieChart data={charts.transportation_status} />
          </div>

          <UtilizationBarChart data={charts.warehouse_utilization} />

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-primary" />
                AI Insights
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                {insights.map((insight, i) => (
                  <div key={i} className="rounded-lg border border-border/50 bg-muted/30 p-4 animate-slide-up">
                    <div className="flex items-center gap-2">
                      <Badge variant={severityVariant(insight.severity)}>{insight.severity}</Badge>
                      <span className="text-xs text-muted-foreground uppercase">{insight.category}</span>
                    </div>
                    <h4 className="mt-2 font-semibold">{insight.title}</h4>
                    <p className="mt-1 text-sm text-muted-foreground">{insight.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <p className="text-muted-foreground">Failed to load dashboard data. Is the backend running?</p>
      )}
    </PageShell>
  );
}

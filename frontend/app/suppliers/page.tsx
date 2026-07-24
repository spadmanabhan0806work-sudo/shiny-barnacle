"use client";

import { useEffect, useState } from "react";
import { Sparkles, X } from "lucide-react";
import { RiskDistributionChart } from "@/components/charts/chart-components";
import { PageShell } from "@/components/layout/page-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type Supplier, type SupplierAnalysis } from "@/lib/api";

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [allSuppliers, setAllSuppliers] = useState<Supplier[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [selected, setSelected] = useState<Supplier | null>(null);
  const [analysis, setAnalysis] = useState<SupplierAnalysis | null>(null);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  useEffect(() => {
    api.getSuppliers().then(setAllSuppliers);
  }, []);

  useEffect(() => {
    api.getSuppliers(filter === "all" ? undefined : filter).then(setSuppliers);
  }, [filter]);

  const openDetail = async (supplier: Supplier) => {
    setSelected(supplier);
    setLoadingAnalysis(true);
    try {
      const a = await api.getSupplierAnalysis(supplier.id);
      setAnalysis(a);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const riskBadge = (level: string) => {
    if (level === "high") return "danger";
    if (level === "medium") return "warning";
    return "success";
  };

  const riskCounts = {
    high: allSuppliers.filter((s) => s.risk_level === "high").length,
    medium: allSuppliers.filter((s) => s.risk_level === "medium").length,
    low: allSuppliers.filter((s) => s.risk_level === "low").length,
  };

  return (
    <PageShell title="Supplier Risk Intelligence" description="Monitor supplier performance and AI-driven risk analysis">
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <Tabs value={filter} onValueChange={setFilter} className="w-full sm:w-auto">
            <TabsList className="w-full sm:w-auto overflow-x-auto justify-start">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="high">High Risk</TabsTrigger>
              <TabsTrigger value="medium">Medium</TabsTrigger>
              <TabsTrigger value="low">Low Risk</TabsTrigger>
            </TabsList>
          </Tabs>
          <Card className="p-4 w-full sm:w-64">
            <RiskDistributionChart
              data={[
                { name: "High", value: riskCounts.high },
                { name: "Medium", value: riskCounts.medium },
                { name: "Low", value: riskCounts.low },
              ]}
            />
          </Card>
        </div>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Supplier</TableHead>
                  <TableHead>Country</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Risk Score</TableHead>
                  <TableHead>OTD %</TableHead>
                  <TableHead>Quality Incidents</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {suppliers.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell className="font-medium whitespace-nowrap">{s.name}</TableCell>
                    <TableCell className="whitespace-nowrap">{s.country}</TableCell>
                    <TableCell className="whitespace-nowrap">{s.category}</TableCell>
                    <TableCell>{s.risk_score}</TableCell>
                    <TableCell>{s.on_time_delivery_pct}%</TableCell>
                    <TableCell>{s.quality_incidents}</TableCell>
                    <TableCell>
                      <Badge variant={riskBadge(s.risk_level)}>{s.risk_level}</Badge>
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => openDetail(s)}>
                        Analyze
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={() => setSelected(null)}>
          <div
            className="h-full w-full max-w-full sm:max-w-lg overflow-y-auto bg-card border-l border-border p-4 sm:p-6 animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg sm:text-xl font-bold">{selected.name}</h2>
              <Button variant="ghost" size="icon" onClick={() => setSelected(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm">
                <div><span className="text-muted-foreground">Risk Score</span><p className="font-semibold">{selected.risk_score}</p></div>
                <div><span className="text-muted-foreground">Contract Expiry</span><p className="font-semibold">{selected.contract_expiry || "N/A"}</p></div>
                <div><span className="text-muted-foreground">On-Time Delivery</span><p className="font-semibold">{selected.on_time_delivery_pct}%</p></div>
                <div><span className="text-muted-foreground">Financial Health</span><p className="font-semibold">{selected.financial_health}</p></div>
                <div><span className="text-muted-foreground">Delays (12mo)</span><p className="font-semibold">{selected.delay_count}</p></div>
                <div><span className="text-muted-foreground">Quality Incidents</span><p className="font-semibold">{selected.quality_incidents}</p></div>
              </div>

              {loadingAnalysis ? (
                <div className="h-40 animate-pulse rounded-lg bg-muted" />
              ) : analysis ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-xs sm:text-sm">Risk Factors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-xs sm:text-sm">
                        {analysis.risk_factors.map((f, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-red-400">•</span> {f}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-xs sm:text-sm flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-primary" /> AI Recommendations
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2 text-xs sm:text-sm text-muted-foreground">
                        {analysis.recommendations.map((r, i) => (
                          <li key={i}>→ {r}</li>
                        ))}
                      </ul>
                      <p className="mt-4 text-xs sm:text-sm leading-relaxed border-t border-border pt-4">{analysis.ai_analysis}</p>
                    </CardContent>
                  </Card>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}


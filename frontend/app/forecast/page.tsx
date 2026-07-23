"use client";

import { useCallback, useEffect, useState } from "react";
import { Upload, Sparkles, TrendingUp } from "lucide-react";
import { DemandForecastChart } from "@/components/charts/chart-components";
import { PageShell } from "@/components/layout/page-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, type ForecastResult } from "@/lib/api";

export default function ForecastPage() {
  const [skus, setSkus] = useState<{ sku: string; product_name: string }[]>([]);
  const [selectedSku, setSelectedSku] = useState<string>("");
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.getForecastSkus().then((s) => {
      setSkus(s);
      if (s.length) setSelectedSku(s[0].sku);
    });
  }, []);

  const runForecast = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.generateForecast(selectedSku || undefined);
      setResult(data);
    } finally {
      setLoading(false);
    }
  }, [selectedSku]);

  useEffect(() => {
    if (selectedSku) runForecast();
  }, [selectedSku, runForecast]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.uploadForecastCsv(file);
      const s = await api.getForecastSkus();
      setSkus(s);
      if (s.length) setSelectedSku(s[0].sku);
    } finally {
      setUploading(false);
    }
  };

  return (
    <PageShell title="AI Demand Forecast" description="Upload sales data and generate AI-powered demand forecasts">
      <div className="space-y-6">
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border px-6 py-4 hover:bg-muted/30 transition-colors">
            <Upload className="h-5 w-5 text-primary" />
            <span className="text-sm">{uploading ? "Uploading..." : "Upload Sales CSV"}</span>
            <input type="file" accept=".csv" className="hidden" onChange={handleUpload} />
          </label>
          <select
            value={selectedSku}
            onChange={(e) => setSelectedSku(e.target.value)}
            className="h-10 rounded-md border border-border bg-muted/50 px-3 text-sm"
          >
            {skus.map((s) => (
              <option key={s.sku} value={s.sku}>
                {s.sku} — {s.product_name}
              </option>
            ))}
          </select>
          <Button onClick={runForecast} disabled={loading}>
            {loading ? "Generating..." : "Regenerate Forecast"}
          </Button>
        </div>

        {result && (
          <div className="space-y-6 animate-fade-in">
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-muted-foreground">Safety Stock</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">{result.safety_stock}</p>
                  <p className="text-xs text-muted-foreground mt-1">units recommended</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-muted-foreground">Confidence</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">{(result.confidence * 100).toFixed(0)}%</p>
                  <div className="mt-2 h-2 rounded-full bg-muted">
                    <div className="h-2 rounded-full bg-primary" style={{ width: `${result.confidence * 100}%` }} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm text-muted-foreground">Product</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-lg font-bold">{result.sku}</p>
                  <p className="text-sm text-muted-foreground">{result.product_name}</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  Forecast Chart — {result.product_name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DemandForecastChart data={result.forecast} />
              </CardContent>
            </Card>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle>Recommended Inventory</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Warehouse</TableHead>
                        <TableHead>Current</TableHead>
                        <TableHead>Target</TableHead>
                        <TableHead>Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {result.recommended_inventory.map((r, i) => (
                        <TableRow key={i}>
                          <TableCell>{r.warehouse}</TableCell>
                          <TableCell>{r.current_stock}</TableCell>
                          <TableCell>{r.recommended_stock}</TableCell>
                          <TableCell>
                            <Badge variant={r.action === "replenish" ? "warning" : "success"}>{r.action}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    AI Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">{result.ai_summary}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </div>
    </PageShell>
  );
}

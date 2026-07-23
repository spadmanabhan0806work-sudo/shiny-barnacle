"use client";

import { useState } from "react";
import { Check, Copy, Sparkles } from "lucide-react";
import { PageShell } from "@/components/layout/page-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type ExecutiveReport } from "@/lib/api";

export default function ReportsPage() {
  const [report, setReport] = useState<ExecutiveReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const data = await api.generateExecutiveReport();
      setReport(data);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!report) return;
    const text = [
      "OPERYX AI — EXECUTIVE SUPPLY CHAIN REPORT",
      `Generated: ${report.generated_at}`,
      "",
      "BUSINESS SUMMARY",
      report.business_summary,
      "",
      "RISKS",
      ...report.risks.map((r) => `• ${r}`),
      "",
      "RECOMMENDATIONS",
      ...report.recommendations.map((r) => `• ${r}`),
      "",
      "PREDICTED ISSUES",
      ...report.predicted_issues.map((r) => `• ${r}`),
      "",
      "NEXT ACTIONS",
      ...report.next_actions.map((r) => `• ${r}`),
    ].join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <PageShell
      title="AI Executive Report"
      description="One-click comprehensive supply chain executive summary"
      actions={
        <div className="flex gap-2">
          {report && (
            <Button variant="outline" onClick={copyToClipboard}>
              {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
              {copied ? "Copied!" : "Copy to Clipboard"}
            </Button>
          )}
          <Button size="lg" onClick={generate} disabled={loading}>
            <Sparkles className="h-4 w-4 mr-2" />
            {loading ? "Generating..." : "Generate Executive Summary"}
          </Button>
        </div>
      }
    >
      {!report && !loading && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Sparkles className="h-16 w-16 text-primary/50 mb-4" />
          <h2 className="text-xl font-semibold">Ready to Generate</h2>
          <p className="mt-2 text-muted-foreground max-w-md">
            Click the button above to generate a comprehensive AI-powered executive summary of your supply chain operations.
          </p>
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      )}

      {report && !loading && (
        <div className="space-y-6 animate-fade-in print:space-y-4">
          <p className="text-xs text-muted-foreground">Generated: {new Date(report.generated_at).toLocaleString()}</p>

          <Card>
            <CardHeader>
              <CardTitle>Business Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{report.business_summary}</p>
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-red-400">Risks</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {report.risks.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-red-400">⚠</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-emerald-400">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {report.recommendations.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-emerald-400">→</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-amber-400">Predicted Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {report.predicted_issues.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-amber-400">◆</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-primary">Next Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {report.next_actions.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-primary">☐</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PageShell>
  );
}

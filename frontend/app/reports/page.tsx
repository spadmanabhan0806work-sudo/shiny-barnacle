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
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          {report && (
            <Button variant="outline" onClick={copyToClipboard} size="sm" className="w-full sm:w-auto text-xs sm:text-sm">
              {copied ? <Check className="h-4 w-4 mr-2" /> : <Copy className="h-4 w-4 mr-2" />}
              {copied ? "Copied!" : "Copy to Clipboard"}
            </Button>
          )}
          <Button size="sm" onClick={generate} disabled={loading} className="w-full sm:w-auto text-xs sm:text-sm sm:h-10 sm:px-4">
            <Sparkles className="h-4 w-4 mr-2" />
            {loading ? "Generating..." : "Generate Executive Summary"}
          </Button>
        </div>
      }
    >
      {!report && !loading && (
        <div className="flex flex-col items-center justify-center py-16 sm:py-24 text-center px-4">
          <Sparkles className="h-12 w-12 sm:h-16 sm:w-16 text-primary/50 mb-4" />
          <h2 className="text-lg sm:text-xl font-semibold">Ready to Generate</h2>
          <p className="mt-2 text-xs sm:text-sm text-muted-foreground max-w-md">
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
              <CardTitle className="text-base sm:text-lg">Business Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs sm:text-sm leading-relaxed">{report.business_summary}</p>
            </CardContent>
          </Card>

          <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg text-red-400">Risks</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-xs sm:text-sm">
                  {report.risks.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-red-400 shrink-0">⚠</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg text-emerald-400">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-xs sm:text-sm">
                  {report.recommendations.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-emerald-400 shrink-0">→</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg text-amber-400">Predicted Issues</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-xs sm:text-sm">
                  {report.predicted_issues.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-amber-400 shrink-0">◆</span> {r}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base sm:text-lg text-primary">Next Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-xs sm:text-sm">
                  {report.next_actions.map((r, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-primary shrink-0">☐</span> {r}
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


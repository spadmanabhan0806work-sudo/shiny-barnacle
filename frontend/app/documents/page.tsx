"use client";

import { useEffect, useState } from "react";
import { FileText, Sparkles, Upload } from "lucide-react";
import { PageShell } from "@/components/layout/page-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api, type DocumentExtract } from "@/lib/api";

export default function DocumentsPage() {
  const [samples, setSamples] = useState<{ filename: string }[]>([]);
  const [result, setResult] = useState<DocumentExtract | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    api.getSampleDocuments().then(setSamples);
  }, []);

  const extractSample = async (filename: string) => {
    setLoading(true);
    try {
      const data = await api.extractDocument(undefined, filename);
      setResult(data);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const upload = await api.uploadDocument(file);
      const data = await api.extractDocument(upload.document_id);
      setResult(data);
    } finally {
      setUploading(false);
    }
  };

  return (
    <PageShell title="Document AI" description="Upload invoices, POs, and contracts for AI-powered extraction">
      <div className="space-y-6">
        <div className="flex flex-wrap gap-4">
          <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border px-6 py-8 hover:bg-muted/30 transition-colors flex-1 min-w-[200px]">
            <Upload className="h-6 w-6 text-primary" />
            <div>
              <p className="text-sm font-medium">{uploading ? "Processing..." : "Upload Document"}</p>
              <p className="text-xs text-muted-foreground">PDF, PNG, JPG, or TXT</p>
            </div>
            <input type="file" accept=".pdf,.png,.jpg,.jpeg,.txt" className="hidden" onChange={handleUpload} />
          </label>

          <Card className="flex-1 min-w-[200px]">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Sample Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {samples.map((s) => (
                <Button key={s.filename} variant="outline" size="sm" className="w-full justify-start" onClick={() => extractSample(s.filename)} disabled={loading}>
                  <FileText className="h-4 w-4 mr-2" />
                  {s.filename}
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>

        {loading && <div className="h-48 animate-pulse rounded-lg bg-muted" />}

        {result && !loading && (
          <div className="grid gap-6 lg:grid-cols-2 animate-fade-in">
            <Card>
              <CardHeader>
                <CardTitle>Extracted Fields — {result.filename}</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Field</TableHead>
                      <TableHead>Value</TableHead>
                      <TableHead>Confidence</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.fields.map((f, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium capitalize">{f.field.replace("_", " ")}</TableCell>
                        <TableCell>{f.value}</TableCell>
                        <TableCell>{(f.confidence * 100).toFixed(0)}%</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {result.line_items.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold mb-2">Line Items</h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>#</TableHead>
                          <TableHead>Description</TableHead>
                          <TableHead>Qty</TableHead>
                          <TableHead>Total</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.line_items.map((item) => (
                          <TableRow key={item.line}>
                            <TableCell>{item.line}</TableCell>
                            <TableCell>{item.description}</TableCell>
                            <TableCell>{item.quantity}</TableCell>
                            <TableCell>${item.total.toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
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
        )}
      </div>
    </PageShell>
  );
}

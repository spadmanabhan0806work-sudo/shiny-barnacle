"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { EvaluationRun, FieldMetrics, getEvaluation } from "@/lib/api";

const FIELD_ORDER = ["side", "stock_symbol", "quantity", "price", "exchange"];

function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export default function EvaluationDetailPage() {
  const params = useParams();
  const evalId = params.evalId as string;
  const [run, setRun] = useState<EvaluationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getEvaluation(evalId);
      setRun(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load evaluation");
    } finally {
      setLoading(false);
    }
  }, [evalId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <p className="text-gray-500">Loading evaluation...</p>;
  }

  if (error || !run || !run.aggregate_metrics) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || "Evaluation not found"}
      </div>
    );
  }

  const { fields, per_call, summary } = run.aggregate_metrics;

  return (
    <div>
      <Link href="/evaluations" className="text-indigo-600 hover:text-indigo-800 text-sm">
        ← Back to evaluations
      </Link>
      <h1 className="text-2xl font-bold mt-2">Evaluation Detail</h1>
      <p className="text-sm text-gray-500 font-mono mt-1">{run.id}</p>

      <div className="mt-6 grid gap-6 md:grid-cols-3">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-gray-500 text-sm">Macro Accuracy</p>
          <p className="text-2xl font-bold">{formatPct(summary.macro_accuracy)}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-gray-500 text-sm">Perfect Matches</p>
          <p className="text-2xl font-bold">
            {summary.matched_all_fields}/{summary.total}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-gray-500 text-sm">Providers</p>
          <p className="text-sm font-medium mt-1">
            {run.stt_provider} / {run.llm_provider}
          </p>
          <p className="text-xs text-gray-400">{run.prompt_version}</p>
        </div>
      </div>

      <div className="mt-6 bg-white rounded-lg shadow overflow-hidden">
        <h2 className="text-lg font-semibold p-4 border-b">Per-field Metrics</h2>
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Field</th>
              <th className="px-4 py-2 text-left">Accuracy</th>
              <th className="px-4 py-2 text-left">Precision</th>
              <th className="px-4 py-2 text-left">Recall</th>
              <th className="px-4 py-2 text-left">F1</th>
            </tr>
          </thead>
          <tbody>
            {FIELD_ORDER.filter((f) => fields[f]).map((field) => {
              const m: FieldMetrics = fields[field];
              return (
                <tr key={field} className="border-t">
                  <td className="px-4 py-2 font-medium capitalize">
                    {field.replace("_", " ")}
                  </td>
                  <td className="px-4 py-2">{formatPct(m.accuracy)}</td>
                  <td className="px-4 py-2">{formatPct(m.precision)}</td>
                  <td className="px-4 py-2">{formatPct(m.recall)}</td>
                  <td className="px-4 py-2">{formatPct(m.f1)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-6 bg-white rounded-lg shadow overflow-hidden">
        <h2 className="text-lg font-semibold p-4 border-b">Per-call Breakdown</h2>
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left">Call ID</th>
              {FIELD_ORDER.map((f) => (
                <th key={f} className="px-4 py-2 text-left capitalize">
                  {f.replace("_", " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {per_call.map((row, idx) => (
              <tr key={idx} className="border-t">
                <td className="px-4 py-2 font-mono text-xs">
                  {row.call_id?.slice(0, 8) ?? "—"}
                </td>
                {FIELD_ORDER.map((f) => (
                  <td
                    key={f}
                    className={`px-4 py-2 ${row.matches[f] ? "text-green-700" : "text-red-700"}`}
                  >
                    {row.matches[f] ? "✓" : "✗"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  EvaluationRun,
  FieldMetrics,
  listEvaluations,
  runEvaluation,
} from "@/lib/api";

const FIELD_ORDER = ["side", "stock_symbol", "quantity", "price", "exchange"];

function formatPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function MetricBar({ label, metrics }: { label: string; metrics: FieldMetrics }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium capitalize">{label.replace("_", " ")}</span>
        <span className="text-gray-500">
          F1 {formatPct(metrics.f1)} · Acc {formatPct(metrics.accuracy)}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full"
          style={{ width: `${Math.round(metrics.accuracy * 100)}%` }}
        />
      </div>
    </div>
  );
}

function EvaluationCard({ run }: { run: EvaluationRun }) {
  const fields = run.aggregate_metrics?.fields;
  const summary = run.aggregate_metrics?.summary;

  return (
    <Link
      href={`/evaluations/${run.id}`}
      className="block bg-white rounded-lg shadow p-6 hover:ring-2 hover:ring-indigo-200 transition"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-sm text-gray-500">{new Date(run.ran_at).toLocaleString()}</p>
          <p className="font-mono text-xs text-gray-400 mt-1">{run.id}</p>
        </div>
        <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded">
          {run.prompt_version}
        </span>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        STT: {run.stt_provider} · LLM: {run.llm_provider}
      </p>
      {summary && (
        <p className="text-lg font-semibold text-gray-900 mb-4">
          Macro accuracy: {formatPct(summary.macro_accuracy)}
          <span className="text-sm font-normal text-gray-500 ml-2">
            ({summary.matched_all_fields}/{summary.total} perfect)
          </span>
        </p>
      )}
      {fields && (
        <div className="space-y-3">
          {FIELD_ORDER.filter((f) => fields[f]).map((field) => (
            <MetricBar key={field} label={field} metrics={fields[field]} />
          ))}
        </div>
      )}
    </Link>
  );
}

export default function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listEvaluations();
      setEvaluations(data.evaluations);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load evaluations");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      await runEvaluation();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation run failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading evaluations...</p>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Evaluations</h1>
          <p className="text-sm text-gray-500 mt-1">
            Benchmark runs against gold annotations
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {running ? "Running..." : "Run sample benchmark"}
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {evaluations.length === 0 ? (
        <p className="text-gray-500">No evaluation runs yet. Start one above.</p>
      ) : (
        <div className="grid gap-6">
          {evaluations.map((run) => (
            <EvaluationCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}

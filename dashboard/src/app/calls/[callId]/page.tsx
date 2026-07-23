"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  Call,
  confidenceBadgeClass,
  getCall,
  getCallAudioUrl,
  reprocessCall,
} from "@/lib/api";

function statusColor(status: string): string {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800";
    case "review_required":
      return "bg-orange-100 text-orange-800";
    case "processing":
    case "extracting":
    case "transcribed":
      return "bg-blue-100 text-blue-800";
    case "failed":
      return "bg-red-100 text-red-800";
    default:
      return "bg-yellow-100 text-yellow-800";
  }
}

export default function CallDetailPage() {
  const params = useParams();
  const callId = params.callId as string;

  const [call, setCall] = useState<Call | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reprocessing, setReprocessing] = useState(false);

  const loadCall = useCallback(async () => {
    try {
      const data = await getCall(callId);
      setCall(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load call");
    } finally {
      setLoading(false);
    }
  }, [callId]);

  useEffect(() => {
    loadCall();
    const interval = setInterval(() => {
      if (
        call?.status === "pending" ||
        call?.status === "processing" ||
        call?.status === "transcribed" ||
        call?.status === "extracting"
      ) {
        loadCall();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [loadCall, call?.status]);

  async function handleReprocess() {
    setReprocessing(true);
    try {
      const data = await reprocessCall(callId);
      setCall(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reprocess failed");
    } finally {
      setReprocessing(false);
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading call details...</p>;
  }

  if (error || !call) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || "Call not found"}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link href="/calls" className="text-indigo-600 hover:text-indigo-800 text-sm">
          ← Back to calls
        </Link>
        <h1 className="text-2xl font-bold mt-2">Call Detail</h1>
        <p className="text-sm text-gray-500 font-mono mt-1">{call.id}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h2 className="text-lg font-semibold">Metadata</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Status</dt>
              <dd>
                <span
                  className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${statusColor(call.status)}`}
                >
                  {call.status}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Detected Language</dt>
              <dd>{call.detected_language || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Duration</dt>
              <dd>
                {call.duration_sec != null
                  ? `${call.duration_sec.toFixed(1)}s`
                  : "—"}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Storage Key</dt>
              <dd className="font-mono text-xs truncate max-w-[200px]">
                {call.storage_key}
              </dd>
            </div>
          </dl>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Audio</h3>
            <audio controls className="w-full" src={getCallAudioUrl(callId)}>
              Your browser does not support the audio element.
            </audio>
          </div>

          <div className="flex gap-4">
            <Link
              href={`/annotations/${callId}`}
              className="inline-block text-indigo-600 hover:text-indigo-800 text-sm font-medium"
            >
              Annotate this call →
            </Link>
            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
            >
              {reprocessing ? "Reprocessing..." : "Reprocess"}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Transcript</h2>
          {call.transcript ? (
            <div className="space-y-4">
              <div className="text-xs text-gray-500">
                Provider: {call.transcript.stt_provider} · Model:{" "}
                {call.transcript.stt_model}
              </div>
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {call.transcript.full_text}
              </p>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              {["pending", "processing", "transcribed", "extracting"].includes(call.status)
                ? "Transcription in progress..."
                : "No transcript available."}
            </p>
          )}
        </div>
      </div>

      {call.intent_extraction && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Extracted Intent</h2>
            <span
              className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${confidenceBadgeClass(call.intent_extraction.confidence)}`}
            >
              {(call.intent_extraction.confidence * 100).toFixed(0)}% confidence
            </span>
          </div>
          <dl className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Side</dt>
              <dd className="font-medium">{call.intent_extraction.side}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Stock</dt>
              <dd className="font-medium">{call.intent_extraction.stock_symbol}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Quantity</dt>
              <dd className="font-medium">{call.intent_extraction.quantity}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Price</dt>
              <dd className="font-medium">₹{call.intent_extraction.price}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Exchange</dt>
              <dd className="font-medium">{call.intent_extraction.exchange}</dd>
            </div>
            <div>
              <dt className="text-gray-500">LLM</dt>
              <dd className="font-medium">
                {call.intent_extraction.llm_provider} ({call.intent_extraction.prompt_version})
              </dd>
            </div>
          </dl>
          {call.review && (
            <p className="mt-4 text-sm text-orange-700">
              Pending human review —{" "}
              <Link href="/reviews" className="underline">
                open review queue
              </Link>
            </p>
          )}
        </div>
      )}
    </div>
  );
}

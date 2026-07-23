"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Call, listCalls, uploadCall } from "@/lib/api";

function statusColor(status: string): string {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800";
    case "processing":
      return "bg-blue-100 text-blue-800";
    case "failed":
      return "bg-red-100 text-red-800";
    default:
      return "bg-yellow-100 text-yellow-800";
  }
}

export default function CallsPage() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCalls = useCallback(async () => {
    try {
      const data = await listCalls();
      setCalls(data.calls);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load calls");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCalls();
  }, [fetchCalls]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadCall(file);
      await fetchCalls();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Call Recordings</h1>
        <label className="cursor-pointer bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
          {uploading ? "Uploading..." : "Upload Audio"}
          <input
            type="file"
            accept=".wav,.mp3,.m4a"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading calls...</p>
      ) : calls.length === 0 ? (
        <p className="text-gray-500">No calls yet. Upload an audio file to get started.</p>
      ) : (
        <table className="w-full bg-white rounded-lg shadow overflow-hidden">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">ID</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Status</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Language</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Duration</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {calls.map((call) => (
              <tr key={call.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-mono">{call.id.slice(0, 8)}...</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${statusColor(call.status)}`}
                  >
                    {call.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {call.detected_language || "—"}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {call.duration_sec != null ? `${call.duration_sec.toFixed(1)}s` : "—"}
                </td>
                <td className="px-4 py-3 space-x-3">
                  <Link
                    href={`/calls/${call.id}`}
                    className="text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                  >
                    View
                  </Link>
                  <Link
                    href={`/annotations/${call.id}`}
                    className="text-gray-600 hover:text-gray-800 text-sm font-medium"
                  >
                    Annotate
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

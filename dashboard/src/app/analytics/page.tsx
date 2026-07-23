"use client";

import { useCallback, useEffect, useState } from "react";
import { Analytics, getAnalytics } from "@/lib/api";

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setData(await getAnalytics());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return <p className="text-gray-500">Loading analytics...</p>;
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || "No data"}
      </div>
    );
  }

  const maxConf = Math.max(...data.confidence_distribution.map((b) => b.count), 1);
  const maxLang = Math.max(...data.language_breakdown.map((l) => l.count), 1);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-500">Total Calls</p>
          <p className="text-3xl font-bold text-indigo-600">{data.volume.total_calls}</p>
        </div>
        {Object.entries(data.volume.by_status).map(([status, count]) => (
          <div key={status} className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-500 capitalize">{status.replace("_", " ")}</p>
            <p className="text-3xl font-bold">{count}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Confidence Distribution</h2>
          <div className="space-y-3">
            {data.confidence_distribution.map((bucket) => (
              <div key={bucket.range}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{bucket.range}</span>
                  <span className="font-medium">{bucket.count}</span>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${(bucket.count / maxConf) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Language Breakdown</h2>
          {data.language_breakdown.length === 0 ? (
            <p className="text-gray-500 text-sm">No language data yet.</p>
          ) : (
            <div className="space-y-3">
              {data.language_breakdown.map((item) => (
                <div key={item.language}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 uppercase">{item.language}</span>
                    <span className="font-medium">{item.count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${(item.count / maxLang) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

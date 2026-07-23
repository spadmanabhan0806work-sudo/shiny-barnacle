"use client";

import { useState } from "react";
import { exportBatchUrl } from "@/lib/api";

export default function ExportPage() {
  const [batchId, setBatchId] = useState("");

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Export Batch Results</h1>
      <p className="text-gray-600 mb-6">
        Download processed call transcripts and trade intents for a batch upload.
      </p>

      <div className="bg-white rounded-lg shadow p-6 max-w-xl space-y-4">
        <label className="block text-sm font-medium text-gray-700">Batch ID</label>
        <input
          type="text"
          value={batchId}
          onChange={(e) => setBatchId(e.target.value.trim())}
          placeholder="e.g. 22222222-2222-2222-2222-222222222222"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
        />

        <div className="flex gap-3 pt-2">
          <a
            href={batchId ? exportBatchUrl(batchId, "json") : "#"}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              batchId
                ? "bg-indigo-600 text-white hover:bg-indigo-700"
                : "bg-gray-200 text-gray-400 pointer-events-none"
            }`}
          >
            Download JSON
          </a>
          <a
            href={batchId ? exportBatchUrl(batchId, "xlsx") : "#"}
            className={`px-4 py-2 rounded-lg text-sm font-medium border ${
              batchId
                ? "border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                : "border-gray-200 text-gray-400 pointer-events-none"
            }`}
          >
            Download Excel
          </a>
        </div>
      </div>
    </div>
  );
}

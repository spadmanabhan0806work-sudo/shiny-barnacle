"use client";

import { useCallback, useEffect, useState } from "react";
import {
  PromptVersion,
  listPrompts,
  setActivePrompt,
} from "@/lib/api";

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<PromptVersion[]>([]);
  const [activeVersion, setActiveVersion] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listPrompts();
      setPrompts(data.prompts);
      setActiveVersion(data.active_version);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load prompts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSetActive(version: string) {
    setSaving(true);
    setError(null);
    try {
      const data = await setActivePrompt({ active_version: version });
      setPrompts(data.prompts);
      setActiveVersion(data.active_version);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update prompt");
    } finally {
      setSaving(false);
    }
  }

  async function handleWeightChange(version: string, weight: number) {
    setSaving(true);
    setError(null);
    try {
      const data = await setActivePrompt({
        weights: [{ version, ab_weight: weight }],
      });
      setPrompts(data.prompts);
      setActiveVersion(data.active_version);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update weight");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading prompts...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Prompt Manager</h1>
      <p className="text-gray-500 text-sm mb-6">
        Active version: <span className="font-mono text-indigo-600">{activeVersion}</span>
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hash</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">A/B Weight</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {prompts.map((p) => (
              <tr key={p.version}>
                <td className="px-4 py-3 font-mono text-sm">{p.version}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{p.system_prompt_hash}</td>
                <td className="px-4 py-3">
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={p.ab_weight}
                    disabled={saving}
                    onChange={(e) => handleWeightChange(p.version, Number(e.target.value))}
                    className="w-32"
                  />
                  <span className="ml-2 text-sm text-gray-600">{(p.ab_weight * 100).toFixed(0)}%</span>
                </td>
                <td className="px-4 py-3">
                  {p.is_active ? (
                    <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Active</span>
                  ) : (
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">Inactive</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {!p.is_active && (
                    <button
                      onClick={() => handleSetActive(p.version)}
                      disabled={saving}
                      className="px-3 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      Set active
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

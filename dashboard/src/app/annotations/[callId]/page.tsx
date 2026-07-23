"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  Annotation,
  createAnnotation,
  getAnnotation,
  getCall,
  Call,
} from "@/lib/api";

export default function AnnotationPage() {
  const params = useParams();
  const callId = params.callId as string;

  const [call, setCall] = useState<Call | null>(null);
  const [side, setSide] = useState("BUY");
  const [stockSymbol, setStockSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [price, setPrice] = useState("");
  const [exchange, setExchange] = useState("NSE");
  const [annotatorId, setAnnotatorId] = useState("annotator-1");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [callData, annotation] = await Promise.all([
        getCall(callId),
        getAnnotation(callId),
      ]);
      setCall(callData);
      if (annotation) {
        populateForm(annotation);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [callId]);

  const populateForm = (annotation: Annotation) => {
    const gt = annotation.ground_truth;
    setSide(gt.side);
    setStockSymbol(gt.stock_symbol);
    setQuantity(String(gt.quantity));
    setPrice(String(gt.price));
    setExchange(gt.exchange);
    setAnnotatorId(annotation.annotator_id);
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const result = await createAnnotation({
        call_id: callId,
        annotator_id: annotatorId,
        ground_truth: {
          side,
          stock_symbol: stockSymbol,
          quantity: parseInt(quantity, 10),
          price: parseFloat(price),
          exchange,
        },
      });
      populateForm(result);
      setMessage("Annotation saved successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save annotation");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="text-gray-500">Loading...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Annotate Call</h1>
      {call && (
        <p className="text-sm text-gray-500 mb-6 font-mono">
          Call ID: {call.id} · Status: {call.status}
        </p>
      )}

      {message && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {message}
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-4 max-w-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Annotator ID</label>
          <input
            type="text"
            value={annotatorId}
            onChange={(e) => setAnnotatorId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Trade Side</label>
          <select
            value={side}
            onChange={(e) => setSide(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Stock Symbol</label>
          <input
            type="text"
            value={stockSymbol}
            onChange={(e) => setStockSymbol(e.target.value.toUpperCase())}
            placeholder="e.g. RELIANCE"
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            min="1"
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price</label>
          <input
            type="number"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            min="0"
            step="0.01"
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Exchange</label>
          <select
            value={exchange}
            onChange={(e) => setExchange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2"
          >
            <option value="NSE">NSE</option>
            <option value="BSE">BSE</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Annotation"}
        </button>
      </form>
    </div>
  );
}

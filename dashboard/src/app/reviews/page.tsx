"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ReviewItem,
  confidenceBadgeClass,
  exportBatchUrl,
  listReviews,
  reprocessCall,
  updateReview,
} from "@/lib/api";

export default function ReviewsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [form, setForm] = useState({
    side: "BUY",
    stock_symbol: "",
    quantity: 0,
    price: 0,
    exchange: "NSE",
  });

  const loadReviews = useCallback(async () => {
    try {
      const data = await listReviews();
      setReviews(data.reviews);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load reviews");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReviews();
  }, [loadReviews]);

  async function handleApprove(reviewId: string) {
    await updateReview(reviewId, "approve");
    await loadReviews();
  }

  function startCorrect(review: ReviewItem) {
    if (!review.intent) return;
    setEditingId(review.id);
    setForm({
      side: review.intent.side,
      stock_symbol: review.intent.stock_symbol,
      quantity: review.intent.quantity,
      price: review.intent.price,
      exchange: review.intent.exchange,
    });
  }

  async function handleCorrect(reviewId: string) {
    await updateReview(reviewId, "correct", form);
    setEditingId(null);
    await loadReviews();
  }

  async function handleReprocess(callId: string) {
    setError(null);
    try {
      await reprocessCall(callId);
      await loadReviews();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Reprocess failed");
    }
  }

  if (loading) {
    return <p className="text-gray-500">Loading review queue...</p>;
  }

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-2">Review Queue</h1>
          <p className="text-gray-500 text-sm">
            Low-confidence extractions awaiting human approval or correction.
          </p>
        </div>
        {batchId && (
          <div className="flex gap-2">
            <a
              href={exportBatchUrl(batchId, "json")}
              className="px-3 py-2 text-sm bg-gray-100 rounded hover:bg-gray-200"
            >
              Export JSON
            </a>
            <a
              href={exportBatchUrl(batchId, "xlsx")}
              className="px-3 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Export Excel
            </a>
          </div>
        )}
      </div>

      <div className="mb-4">
        <label className="text-sm text-gray-500 mr-2">Batch ID for export:</label>
        <input
          className="border rounded px-2 py-1 text-sm font-mono w-80"
          placeholder="Paste batch UUID from batch upload"
          value={batchId || ""}
          onChange={(e) => setBatchId(e.target.value || null)}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {reviews.length === 0 ? (
        <p className="text-gray-500">No pending reviews.</p>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs text-gray-400 font-mono">{review.id}</p>
                  {review.intent && (
                    <div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                      <div>
                        <span className="text-gray-500">Side</span>
                        <p className="font-medium">{review.intent.side}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Stock</span>
                        <p className="font-medium">{review.intent.stock_symbol}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Qty</span>
                        <p className="font-medium">{review.intent.quantity}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Price</span>
                        <p className="font-medium">₹{review.intent.price}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Exchange</span>
                        <p className="font-medium">{review.intent.exchange}</p>
                      </div>
                    </div>
                  )}
                </div>
                {review.intent && (
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-medium rounded-full shrink-0 ${confidenceBadgeClass(review.intent.confidence)}`}
                  >
                    {(review.intent.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>

              {editingId === review.id ? (
                <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3">
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    value={form.side}
                    onChange={(e) => setForm({ ...form, side: e.target.value })}
                  />
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    value={form.stock_symbol}
                    onChange={(e) => setForm({ ...form, stock_symbol: e.target.value })}
                  />
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    type="number"
                    value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
                  />
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    type="number"
                    value={form.price}
                    onChange={(e) => setForm({ ...form, price: Number(e.target.value) })}
                  />
                  <input
                    className="border rounded px-2 py-1 text-sm"
                    value={form.exchange}
                    onChange={(e) => setForm({ ...form, exchange: e.target.value })}
                  />
                  <div className="col-span-full flex gap-2 mt-2">
                    <button
                      onClick={() => handleCorrect(review.id)}
                      className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                    >
                      Save correction
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-1 text-sm text-gray-600"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    onClick={() => handleApprove(review.id)}
                    className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => startCorrect(review)}
                    className="px-3 py-1 bg-amber-600 text-white text-sm rounded hover:bg-amber-700"
                  >
                    Correct
                  </button>
                  {review.intent && (
                    <>
                      <button
                        onClick={() => handleReprocess(review.intent?.call_id ?? '')}
                        className="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700"
                      >
                        Reprocess
                      </button>
                      <Link
                        href={`/calls/${review.intent.call_id}`}
                        className="px-3 py-1 text-sm text-indigo-600 hover:underline"
                      >
                        View call
                      </Link>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

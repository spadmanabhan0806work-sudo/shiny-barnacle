const getApiBase = () => {
  let url = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }
  return url;
};

const API_URL = getApiBase();

export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  confidence: number | null;
}

export interface Transcript {
  id: string;
  full_text: string;
  segments: TranscriptSegment[];
  stt_provider: string;
  stt_model: string;
}

export interface IntentExtraction {
  id: string;
  call_id?: string;
  side: string;
  stock_symbol: string;
  quantity: number;
  price: number;
  exchange: string;
  confidence: number;
  prompt_version: string;
  llm_provider: string;
}

export interface ReviewStatus {
  id: string;
  status: string;
  corrected_fields?: Record<string, unknown> | null;
}

export interface Call {
  id: string;
  tenant_id: string;
  storage_key: string;
  status: string;
  detected_language: string | null;
  duration_sec: number | null;
  transcript?: Transcript | null;
  intent_extraction?: IntentExtraction | null;
  review?: ReviewStatus | null;
}

export interface GroundTruth {
  side: string;
  stock_symbol: string;
  quantity: number;
  price: number;
  exchange: string;
}

export interface Annotation {
  id: string;
  call_id: string;
  annotator_id: string;
  ground_truth: GroundTruth;
  status: string;
}

export interface ReviewItem {
  id: string;
  extraction_id: string;
  status: string;
  corrected_fields?: Record<string, unknown> | null;
  reviewer_id?: string | null;
  intent?: IntentExtraction | null;
}

export async function listCalls(): Promise<{ calls: Call[]; total: number }> {
  const res = await fetch(`${API_URL}/api/v1/calls`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch calls");
  return res.json();
}

export async function getCall(callId: string): Promise<Call> {
  const res = await fetch(`${API_URL}/api/v1/calls/${callId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch call");
  return res.json();
}

export function getCallAudioUrl(callId: string): string {
  return `${API_URL}/api/v1/calls/${callId}/audio`;
}

export async function reprocessCall(
  callId: string,
  promptVersion?: string
): Promise<Call> {
  const res = await fetch(`${API_URL}/api/v1/calls/${callId}/reprocess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt_version: promptVersion ?? null }),
  });
  if (!res.ok) throw new Error("Failed to reprocess call");
  return res.json();
}

export async function listReviews(): Promise<{ reviews: ReviewItem[]; total: number }> {
  const res = await fetch(`${API_URL}/api/v1/reviews?status=pending`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch reviews");
  return res.json();
}

export async function updateReview(
  reviewId: string,
  action: "approve" | "correct",
  correctedFields?: Record<string, unknown>
): Promise<ReviewItem> {
  const res = await fetch(`${API_URL}/api/v1/reviews/${reviewId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action,
      reviewer_id: "dashboard-operator",
      corrected_fields: correctedFields,
    }),
  });
  if (!res.ok) throw new Error("Failed to update review");
  return res.json();
}

export async function getAnnotation(callId: string): Promise<Annotation | null> {
  const res = await fetch(`${API_URL}/api/v1/annotations/${callId}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Failed to fetch annotation");
  return res.json();
}

export async function createAnnotation(data: {
  call_id: string;
  annotator_id: string;
  ground_truth: GroundTruth;
}): Promise<Annotation> {
  const res = await fetch(`${API_URL}/api/v1/annotations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create annotation");
  }
  return res.json();
}

export async function uploadCall(file: File): Promise<Call> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_URL}/api/v1/calls`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload call");
  }
  return res.json();
}

export function confidenceBadgeClass(confidence: number): string {
  if (confidence >= 0.85) return "bg-green-100 text-green-800";
  if (confidence >= 0.7) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
}

export interface FieldMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  correct: number;
  total: number;
}

export interface EvaluationRun {
  id: string;
  prompt_version: string;
  stt_provider: string;
  llm_provider: string;
  aggregate_metrics: {
    fields: Record<string, FieldMetrics>;
    per_call: Array<{
      call_id: string | null;
      matches: Record<string, boolean>;
    }>;
    summary: {
      total: number;
      matched_all_fields: number;
      macro_accuracy: number;
    };
  } | null;
  ran_at: string;
  report_path?: string | null;
}

export async function listEvaluations(): Promise<{
  evaluations: EvaluationRun[];
  total: number;
}> {
  const res = await fetch(`${API_URL}/api/v1/evaluations`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch evaluations");
  return res.json();
}

export async function getEvaluation(evalId: string): Promise<EvaluationRun> {
  const res = await fetch(`${API_URL}/api/v1/evaluations/${evalId}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch evaluation");
  return res.json();
}

export async function runEvaluation(options?: {
  dataset_path?: string;
  use_db_annotations?: boolean;
  prompt_version?: string;
}): Promise<EvaluationRun> {
  const res = await fetch(`${API_URL}/api/v1/evaluations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_path: options?.dataset_path ?? "eval/datasets/sample_gold.json",
      use_db_annotations: options?.use_db_annotations ?? false,
      prompt_version: options?.prompt_version,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to run evaluation");
  }
  return res.json();
}

export interface BatchUploadResult {
  batch_id: string;
  call_ids: string[];
  total: number;
  errors: string[];
}

export async function batchUploadCalls(files: File[]): Promise<BatchUploadResult> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  const res = await fetch(`${API_URL}/api/v1/calls/batch`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to batch upload");
  }
  return res.json();
}

export function exportBatchUrl(batchId: string, format: "json" | "xlsx" = "json"): string {
  return `${API_URL}/api/v1/exports/${batchId}?format=${format}`;
}

export interface PromptVersion {
  version: string;
  module: string;
  system_prompt_hash: string;
  is_active: boolean;
  ab_weight: number;
}

export async function listPrompts(): Promise<{
  prompts: PromptVersion[];
  active_version: string;
}> {
  const res = await fetch(`${API_URL}/api/v1/prompts`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch prompts");
  return res.json();
}

export async function setActivePrompt(body: {
  active_version?: string;
  weights?: Array<{ version: string; ab_weight: number }>;
}): Promise<{ prompts: PromptVersion[]; active_version: string }> {
  const res = await fetch(`${API_URL}/api/v1/prompts/active`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error("Failed to update prompts");
  return res.json();
}

export interface Analytics {
  volume: { total_calls: number; by_status: Record<string, number> };
  confidence_distribution: Array<{ range: string; count: number }>;
  language_breakdown: Array<{ language: string; count: number }>;
  avg_confidence: number | null;
}

export async function getAnalytics(): Promise<Analytics> {
  const res = await fetch(`${API_URL}/api/v1/analytics`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return res.json();
}

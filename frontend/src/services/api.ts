import type {
  SystemHealth,
  ExecutionPlan,
  ExecutionRunSummary,
  ExecutionTraceView,
} from '../types/api';

export const API_BASE = import.meta.env.VITE_API_BASE_URL ? `${import.meta.env.VITE_API_BASE_URL}/api` : '/api';

export interface WorkflowRunRequestPayload {
  text_query: string;
  session_id?: string;
  target_language?: string;
  location?: {
    place_name?: string;
    latitude?: number;
    longitude?: number;
  };
  inputs?: Array<{
    modality: string;
    filename: string;
    storage_path?: string;
    file_size_bytes?: number;
    checksum_sha256?: string;
    extracted_summary?: string;
  }>;
}

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function previewExecutionPlan(payload: WorkflowRunRequestPayload): Promise<ExecutionPlan> {
  const res = await fetch(`${API_BASE}/v1/workflow/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Plan formulation failed');
  }
  return res.json();
}

export async function executeWorkflow(payload: WorkflowRunRequestPayload): Promise<any> {
  const res = await fetch(`${API_BASE}/v1/workflow/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Workflow execution failed');
  }
  return res.json();
}

export async function uploadMultimodalFile(file: File): Promise<{
  metadata: {
    modality: string;
    filename: string;
    file_size_bytes: number;
    checksum_sha256: string;
    extracted_summary?: string;
  };
  processing_summary: Record<string, unknown>;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/v1/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'File upload failed');
  }
  return res.json();
}

export async function fetchExecutionTrace(traceId: string): Promise<ExecutionTraceView> {
  const res = await fetch(`${API_BASE}/v1/traces/${traceId}`);
  if (!res.ok) throw new Error(`Failed to load trace: ${res.statusText}`);
  return res.json();
}

export async function fetchRunHistory(limit = 20, offset = 0, crop?: string): Promise<{
  count: number;
  runs: ExecutionRunSummary[];
}> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (crop) params.append('crop', crop);

  const res = await fetch(`${API_BASE}/v1/history/runs?${params.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch history: ${res.statusText}`);
  return res.json();
}

export async function submitRunFeedback(
  runId: string,
  rating: number,
  isHelpful: boolean,
  comment?: string
): Promise<{ status: string; feedback_id: string }> {
  const res = await fetch(`${API_BASE}/v1/history/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, rating, is_helpful: isHelpful, comment }),
  });
  if (!res.ok) throw new Error('Feedback submission failed');
  return res.json();
}

export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type RunStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type RunStage =
  | "queued"
  | "briefing"
  | "planning"
  | "developing"
  | "testing"
  | "repairing"
  | "reporting"
  | "complete"
  | "cancelled";

export interface DevelopmentPlan {
  file_name: string;
  test_file_name: string;
  developer_task: string;
  tester_task: string;
}

export interface RunEvent {
  stage: RunStage;
  message: string;
  created_at: string;
}

export interface RunAttempt {
  sequence: number;
  candidate_attempt: number | null;
  status: "passed" | "failed" | "infrastructure";
  failure_kind: string | null;
  repair_target: string | null;
  test_results: string;
  application_code: string;
  test_code: string;
}

export interface RunArtifact {
  path: string;
  kind: string;
  content: string;
}

export interface RetrievedSource {
  chunk_id: string;
  source_id: string;
  library: string;
  library_version: string;
  document_version: string;
  title: string;
  heading: string;
  source_url: string;
  distance: number;
}

export interface RetrievalEvent {
  query: string;
  results: RetrievedSource[];
}

export interface RunSnapshot {
  run_id: string;
  request: string;
  status: RunStatus;
  stage: RunStage;
  attempts_used: number;
  max_attempts: number;
  cancel_requested: boolean;
  created_at: string;
  updated_at: string;
  technical_brief: string | null;
  plan: DevelopmentPlan | null;
  test_results: string | null;
  report: string | null;
  attempts: RunAttempt[];
  events: RunEvent[];
  artifacts: RunArtifact[];
  retrieval_events: RetrievalEvent[];
  error: string | null;
}

export interface BenchmarkTaskResult {
  task_id: string;
  task_version: string;
  difficulty: "easy" | "medium";
  passed: boolean;
  tests_passed: number;
  tests_total: number;
  duration_seconds: number;
  candidate_path: string;
  error: string | null;
}

export interface BenchmarkReport {
  schema_version: string;
  benchmark_version: string;
  evaluator_sha256: string;
  run_id: string;
  model: string;
  sandbox_backend: string;
  started_at: string;
  completed_at: string;
  tasks_passed: number;
  tasks_total: number;
  results: BenchmarkTaskResult[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(payload?.detail ?? `Request failed with ${response.status}.`);
  }
  return (await response.json()) as T;
}

export function checkHealth(signal?: AbortSignal) {
  return request<{ status: string }>("/health", { signal });
}

export function startRun(userRequest: string) {
  return request<RunSnapshot>("/runs", {
    method: "POST",
    body: JSON.stringify({ request: userRequest }),
  });
}

export function getRun(runId: string, signal?: AbortSignal) {
  return request<RunSnapshot>(`/runs/${runId}`, { signal });
}

export function cancelRun(runId: string) {
  return request<RunSnapshot>(`/runs/${runId}/cancel`, { method: "POST" });
}

export function getBenchmarks(signal?: AbortSignal) {
  return request<BenchmarkReport[]>("/benchmarks", { signal });
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const prismApi = {
  createWorker: (payload: { name: string; platform: string; zone: string; working_hours: string }) =>
    fetchJSON("/workers", { method: "POST", body: JSON.stringify(payload) }),

  buyPolicy: (payload: { worker_id: number; week_start: string; week_end: string }) =>
    fetchJSON("/policies", { method: "POST", body: JSON.stringify(payload) }),

  triggerClaim: (payload: {
    worker_id: number;
    policy_id: number;
    expected_income: number;
    actual_income: number;
    trigger_source: string;
    lat: number;
    lon: number;
    activity_score: number;
  }) => fetchJSON("/claims/trigger", { method: "POST", body: JSON.stringify(payload) }),

  workerDashboard: (workerId: number) => fetchJSON(`/dashboard/worker/${workerId}`),
  adminDashboard:  () => fetchJSON("/dashboard/admin"),

  fraudAnalyze: (payload: {
    worker_id: number;
    policy_id: number;
    expected_income: number;
    actual_income: number;
    lat: number;
    lon: number;
    zone: string;
    activity_score: number;
    request_hour?: number;
  }) => fetchJSON("/fraud/analyze", { method: "POST", body: JSON.stringify(payload) }),

  fraudPipelineStatus: () => fetchJSON("/fraud/pipeline-status"),
};

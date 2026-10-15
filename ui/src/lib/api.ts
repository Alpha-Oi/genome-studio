import type { Plan } from "@/types/plan";

const API_BASE = "/api";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchPlan(text: string, projectId?: number): Promise<Plan> {
  const body: { text: string; project_id?: number } = { text };
  if (projectId !== undefined) body.project_id = projectId;

  const resp = await fetch(API_BASE + "/goal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    let detail = "";
    try {
      const b = await resp.json();
      detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b);
    } catch {
      detail = await resp.text();
    }
    throw new ApiError(resp.status, detail || "HTTP " + resp.status);
  }

  const data = (await resp.json()) as { plan: Plan };
  return data.plan;
}
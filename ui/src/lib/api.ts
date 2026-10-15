// API клиент для backend Genome Studio.
// В dev использует Vite proxy (/api -> 127.0.0.1:8000).

import type { Plan } from "@/types/plan";

const API_BASE = "/api";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchPlan(text: string): Promise<Plan> {
  const resp = await fetch(API_BASE + "/goal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!resp.ok) {
    let detail = "";
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body);
    } catch {
      detail = await resp.text();
    }
    throw new ApiError(resp.status, detail || "HTTP " + resp.status);
  }

  const data = (await resp.json()) as { plan: Plan };
  return data.plan;
}
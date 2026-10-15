import type {
  NgsResponse,
  SangerResponse,
  SequencingRequest,
} from "@/types/sequencing";
import { ApiError } from "@/lib/api";

const API_BASE = "/api";

async function postJson<T>(endpoint: string, body: unknown): Promise<T> {
  const r = await fetch(API_BASE + endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let detail = "";
    try {
      const b = await r.json();
      detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b);
    } catch {
      detail = await r.text();
    }
    throw new ApiError(r.status, detail || "HTTP " + r.status);
  }
  return (await r.json()) as T;
}

export async function runSanger(req: SequencingRequest): Promise<SangerResponse> {
  return postJson<SangerResponse>("/simulate/sanger", req);
}

export async function runNgs(req: SequencingRequest): Promise<NgsResponse> {
  return postJson<NgsResponse>("/simulate/ngs", req);
}
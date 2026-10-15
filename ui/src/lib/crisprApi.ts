import type { Guide } from "@/types/guide";
import { ApiError } from "@/lib/api";

const API_BASE = "/api";

export interface CrisprRequest {
  sequence: string;
  topN?: number;
  minScore?: number;
}

export async function designGuides(req: CrisprRequest): Promise<Guide[]> {
  const resp = await fetch(API_BASE + "/crispr/design", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sequence: req.sequence,
      top_n: req.topN ?? 5,
      min_score: req.minScore ?? 0.5,
    }),
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

  const data = (await resp.json()) as { guides: Guide[] };
  return data.guides;
}
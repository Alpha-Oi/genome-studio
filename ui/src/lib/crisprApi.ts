import type { Guide } from "@/types/guide";
import type { OffTargetResult } from "@/types/offtarget";
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

export interface OffTargetRequest {
  guideSpacer: string;
  reference: string;
  maxMismatches?: number;
  referenceLabel?: string;
}

export async function findOffTargets(req: OffTargetRequest): Promise<OffTargetResult> {
  const resp = await fetch(API_BASE + "/crispr/offtarget", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      guide_spacer: req.guideSpacer,
      reference: req.reference,
      max_mismatches: req.maxMismatches ?? 4,
      reference_label: req.referenceLabel ?? "ref",
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

  return (await resp.json()) as OffTargetResult;
}
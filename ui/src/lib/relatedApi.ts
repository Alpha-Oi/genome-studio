const API_BASE = "/api";

export interface RelatedItem {
  experiment_id: number;
  project_id: number;
  project_name: string;
  title: string;
  created_at: string;
  intervention_kind: string | null;
  predicted_effect: number | null;
  off_target_risk: number | null;
  essentiality_risk: number | null;
}

export interface RelatedResult {
  related: RelatedItem[];
  criteria: { gene: string; organism: string; intent: string };
}

export async function fetchRelated(
  gene: string,
  organism: string,
  intent: string,
  limit = 5,
): Promise<RelatedItem[]> {
  const params = new URLSearchParams({
    gene,
    organism,
    intent,
    limit: String(limit),
  });
  const r = await fetch(API_BASE + "/related?" + params.toString());
  if (!r.ok) {
    throw new Error("Failed to fetch related: HTTP " + r.status);
  }
  const data = (await r.json()) as RelatedResult;
  return data.related;
}
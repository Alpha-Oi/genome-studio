const API_BASE = "/api";

export interface BatchSequence {
  name: string;
  sequence: string;
}

export interface BatchGuide {
  spacer: string;
  pam: string;
  position: number;
  strand: string;
  gc_content: number;
  score: number;
  reasons: string[];
  warnings: string[];
}

export interface BatchResult {
  name: string;
  length: number;
  guides: BatchGuide[];
  error: string | null;
}

export async function batchDesign(
  sequences: BatchSequence[],
  topN = 3,
  minScore = 0.0,
): Promise<BatchResult[]> {
  const r = await fetch(API_BASE + "/batch/design", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      sequences,
      top_n: topN,
      min_score: minScore,
    }),
  });
  if (!r.ok) {
    let detail = "";
    try {
      const b = await r.json();
      detail = typeof b.detail === "string" ? b.detail : JSON.stringify(b);
    } catch {
      detail = await r.text();
    }
    throw new Error(detail || "HTTP " + r.status);
  }
  const data = (await r.json()) as { results: BatchResult[] };
  return data.results;
}
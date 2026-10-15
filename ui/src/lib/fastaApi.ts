const API_BASE = "/api";

export interface FastaRecord {
  name: string;
  description: string;
  sequence: string;
  length: number;
  gc_content: number;
}

export async function parseFastaContent(content: string): Promise<FastaRecord[]> {
  const r = await fetch(API_BASE + "/parse/fasta", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
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
  const data = (await r.json()) as { records: FastaRecord[] };
  return data.records;
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(reader.error ?? new Error("file read error"));
    reader.readAsText(file);
  });
}
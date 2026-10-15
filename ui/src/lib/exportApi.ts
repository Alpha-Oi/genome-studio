const API_BASE = "/api";

export interface ExportEditRequest {
  sequence: string;
  gene_name: string;
  kind: "substitution" | "insertion" | "deletion";
  position: number;
  ref: string;
  alt: string;
}

async function downloadFromPost(
  endpoint: string,
  body: ExportEditRequest,
  filename: string,
): Promise<void> {
  const resp = await fetch(API_BASE + endpoint, {
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
    throw new Error(detail || "HTTP " + resp.status);
  }

  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function downloadFasta(req: ExportEditRequest): Promise<void> {
  await downloadFromPost("/export/edit/fasta", req, req.gene_name + "_edited.fasta");
}

export async function downloadVcf(req: ExportEditRequest): Promise<void> {
  await downloadFromPost("/export/edit/vcf", req, req.gene_name + "_edit.vcf");
}

export async function downloadGenbank(req: ExportEditRequest): Promise<void> {
  await downloadFromPost("/export/edit/genbank", req, req.gene_name + "_edited.gb");
}
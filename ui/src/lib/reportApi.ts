const API_BASE = "/api";

export async function downloadProjectReport(projectId: number): Promise<void> {
  const resp = await fetch(API_BASE + "/projects/" + projectId + "/report.pdf");
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
  a.download = "project_" + projectId + "_report.pdf";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
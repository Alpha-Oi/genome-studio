import type { Warning } from "@/types/warning";
import { ApiError } from "@/lib/api";

const API_BASE = "/api";

async function jsonOrError<T>(resp: Response): Promise<T> {
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
  return (await resp.json()) as T;
}

export async function listWarnings(
  projectId: number,
  status?: "open" | "acknowledged",
): Promise<Warning[]> {
  const url = status
    ? API_BASE + "/projects/" + projectId + "/warnings?status=" + status
    : API_BASE + "/projects/" + projectId + "/warnings";
  const r = await fetch(url);
  const data = await jsonOrError<{ warnings: Warning[] }>(r);
  return data.warnings;
}

export async function acknowledgeWarning(
  warningId: number,
  by: string,
  note: string,
): Promise<Warning> {
  const r = await fetch(API_BASE + "/warnings/" + warningId + "/acknowledge", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ by, note }),
  });
  const data = await jsonOrError<{ warning: Warning }>(r);
  return data.warning;
}
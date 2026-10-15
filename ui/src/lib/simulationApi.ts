import type { SimulateEditRequest, SimulateEditResponse } from "@/types/simulation";
import { ApiError } from "@/lib/api";

const API_BASE = "/api";

export async function simulateEdit(
  req: SimulateEditRequest,
): Promise<SimulateEditResponse> {
  const resp = await fetch(API_BASE + "/simulate/edit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
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

  return (await resp.json()) as SimulateEditResponse;
}
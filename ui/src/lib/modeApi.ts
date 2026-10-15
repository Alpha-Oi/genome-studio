const API_BASE = "/api";

export interface ModeInfo {
  mode: "local" | "multi";
  user: {
    id: number;
    email: string;
    name: string;
    is_admin: boolean;
    is_local: boolean;
  };
  available_modes: string[];
  switchable: boolean;
}

export async function fetchMode(): Promise<ModeInfo> {
  const r = await fetch(API_BASE + "/mode");
  if (!r.ok) {
    throw new Error("Failed to fetch mode: HTTP " + r.status);
  }
  return (await r.json()) as ModeInfo;
}
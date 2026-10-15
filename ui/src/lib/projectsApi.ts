import type { Experiment, Project } from "@/types/project";
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

export async function listProjects(): Promise<Project[]> {
  const r = await fetch(API_BASE + "/projects");
  const data = await jsonOrError<{ projects: Project[] }>(r);
  return data.projects;
}

export async function createProject(name: string): Promise<Project> {
  const r = await fetch(API_BASE + "/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await jsonOrError<{ project: Project }>(r);
  return data.project;
}

export async function deleteProject(id: number): Promise<void> {
  const r = await fetch(API_BASE + "/projects/" + id, { method: "DELETE" });
  if (!r.ok) {
    throw new ApiError(r.status, "HTTP " + r.status);
  }
}

export async function listExperiments(projectId: number): Promise<Experiment[]> {
  const r = await fetch(API_BASE + "/projects/" + projectId + "/experiments");
  const data = await jsonOrError<{ experiments: Experiment[] }>(r);
  return data.experiments;
}

export async function createExperiment(
  projectId: number,
  kind: string,
  title: string,
  payload: unknown = {},
): Promise<Experiment> {
  const r = await fetch(API_BASE + "/projects/" + projectId + "/experiments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ kind, title, payload }),
  });
  const data = await jsonOrError<{ experiment: Experiment }>(r);
  return data.experiment;
}
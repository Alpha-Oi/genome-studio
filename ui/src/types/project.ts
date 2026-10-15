export interface Project {
  id: number;
  name: string;
  description: string;
  organism: string;
  created_at: string;
  updated_at: string;
}

export interface Experiment {
  id: number;
  project_id: number;
  kind: string;
  title: string;
  payload: unknown;
  created_at: string;
}
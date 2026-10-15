export interface Warning {
  id: number;
  project_id: number;
  experiment_id: number | null;
  level: string;
  severity: string;
  type: string;
  message: string;
  evidence: string[];
  status: string;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  acknowledgment_note: string;
  created_at: string;
}
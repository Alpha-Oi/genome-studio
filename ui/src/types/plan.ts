// Типы для Plan, приходящего от backend API.

export interface PlanGoal {
  raw_text: string;
  intent: string;
  target: {
    gene: string;
    organism: string;
    cell_line: string | null;
  };
  phenotype_target: {
    metric: string;
    direction: string;
    magnitude: string | null;
  } | null;
  constraints: string[];
  confidence: number;
}

export interface PlanIntervention {
  kind: string;
  target_gene: string;
  rationale: string;
  predicted_effect: number;
  off_target_risk: number;
  essentiality_risk: number;
  complexity: number;
  warnings: string[];
  evidence: string[];
}

export interface PlanStep {
  order: number;
  action: string;
  description: string;
  depends_on: number[];
  warnings: string[];
}

export interface Plan {
  goal: PlanGoal;
  intervention: PlanIntervention;
  steps: PlanStep[];
  notes: string[];
}
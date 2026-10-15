export interface SimulateEditRequest {
  sequence: string;
  gene_name: string;
  kind: "substitution" | "insertion" | "deletion";
  position: number;
  ref: string;
  alt: string;
  project_id?: number;
}

export interface EditEffect {
  effect_type: string;
  ref_protein: string;
  alt_protein: string;
  description: string;
  severity: number;
  evidence: string[];
}

export interface ConsequenceNode {
  node_id: string;
  type: string;
  description: string;
  confidence: number;
  method: string;
  evidence: string[];
  children: ConsequenceNode[];
}

export interface SimulateEditResponse {
  edited_sequence: string;
  effect: EditEffect;
  consequence_tree: ConsequenceNode;
  warning_ids: number[];
}
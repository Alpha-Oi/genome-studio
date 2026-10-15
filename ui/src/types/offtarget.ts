export interface OffTargetHit {
  position: number;
  strand: string;
  mismatches: number;
  spacer: string;
  pam: string;
  locus_label: string;
}

export interface OffTargetSummary {
  total: number;
  perfect: number;
  near: number;
  distant: number;
  risk: number;
}

export interface OffTargetResult {
  hits: OffTargetHit[];
  summary: OffTargetSummary;
}
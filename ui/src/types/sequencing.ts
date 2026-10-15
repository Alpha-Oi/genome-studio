export interface SequencingRequest {
  wt_sequence: string;
  edited_sequence: string;
  edited_fraction: number;
  heterozygote_fraction: number;
  total_reads: number;
  window: number;
}

export interface SangerPeak {
  position: number;
  A: number;
  T: number;
  G: number;
  C: number;
}

export interface AlleleInfo {
  name: string;
  fraction: number;
  sequence: string;
}

export interface SangerResponse {
  wt_sequence: string;
  edited_sequence: string;
  edit_position: number;
  window_start: number;
  window_end: number;
  alleles: AlleleInfo[];
  peaks: SangerPeak[];
}

export interface NgsAllele {
  name: string;
  fraction: number;
  reads: number;
  sequence: string;
}

export interface NgsResponse {
  total_reads: number;
  alleles: NgsAllele[];
}
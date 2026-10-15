import { useState } from "react";
import { designGuides, findOffTargets } from "@/lib/crisprApi";
import { createExperiment } from "@/lib/projectsApi";
import { GuideList } from "@/components/GuideList";
import { OffTargetList } from "@/components/OffTargetList";
import { FastaUploadButton } from "@/components/FastaUploadButton";
import type { Guide } from "@/types/guide";
import type { OffTargetResult } from "@/types/offtarget";

const EXAMPLE =
  "ACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTTACGTACGTACGTACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTTACGTACGT";

const OFF_TARGET_REF =
  "ACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTT" +
  "ACGTACGTACGTACGTTCGTCGGGGGGCCCCGGGGCCCCGGGGAGG" +
  "ACGTACGTACGTACGTACGTAGGTTTTAAAATTTTAAAATTTT";

interface Props {
  projectId: number | null;
  onExperimentSaved?: () => void;
}

export function CrisprPanel({ projectId, onExperimentSaved }: Props) {
  const [sequence, setSequence] = useState(EXAMPLE);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fastaInfo, setFastaInfo] = useState<string | null>(null);

  const [selectedGuide, setSelectedGuide] = useState<string | null>(null);
  const [reference, setReference] = useState(OFF_TARGET_REF);
  const [offTarget, setOffTarget] = useState<OffTargetResult | null>(null);
  const [otLoading, setOtLoading] = useState(false);
  const [otError, setOtError] = useState<string | null>(null);

  async function submit() {
    const seq = sequence.trim();
    if (!seq || loading) return;

    setLoading(true);
    setError(null);
    try {
      const result = await designGuides({ sequence: seq, topN: 5, minScore: 0.0 });
      setGuides(result);
      setSelectedGuide(result[0]?.spacer ?? null);
      setOffTarget(null);

      if (projectId !== null && result.length > 0) {
        try {
          const title = String(result.length) + " gRNAs for " + seq.slice(0, 20) + "...";
          await createExperiment(projectId, "crispr_design", title, { guides: result });
          if (onExperimentSaved) onExperimentSaved();
        } catch (persistErr) {
          console.warn("Failed to save crispr experiment:", persistErr);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setGuides([]);
    } finally {
      setLoading(false);
    }
  }

  function handleFasta(records: { name: string; sequence: string }[]) {
    const first = records[0];
    if (!first) return;

    setSequence(first.sequence);
    setFastaInfo(
      "Loaded " + records.length + " record(s). Using: " + first.name +
      " (" + first.sequence.length + " nt)"
    );

    const second = records[1];
    if (second) {
      setReference(second.sequence);
    }
    setTimeout(() => setFastaInfo(null), 5000);
  }

  async function checkOffTarget() {
    if (!selectedGuide || otLoading) return;
    const ref = reference.trim();
    if (!ref) return;

    setOtLoading(true);
    setOtError(null);
    try {
      const result = await findOffTargets({
        guideSpacer: selectedGuide,
        reference: ref,
        maxMismatches: 4,
        referenceLabel: "ref",
      });
      setOffTarget(result);

      if (projectId !== null) {
        try {
          const title =
            "Off-target for " +
            selectedGuide.slice(0, 10) +
            "... (" +
            String(result.summary.total) +
            " hits)";
          await createExperiment(projectId, "offtarget", title, result);
          if (onExperimentSaved) onExperimentSaved();
        } catch (persistErr) {
          console.warn("Failed to save offtarget experiment:", persistErr);
        }
      }
    } catch (e) {
      setOtError(e instanceof Error ? e.message : "Unknown error");
      setOffTarget(null);
    } finally {
      setOtLoading(false);
    }
  }

  return (
    <div className="crispr-panel">
      <div className="crispr-input">
        <div className="crispr-input-head">
          <label>Target DNA sequence (ACGT):</label>
          <FastaUploadButton onLoad={handleFasta} />
        </div>
        {fastaInfo && <div className="fasta-info">✓ {fastaInfo}</div>}
        <textarea
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
          rows={4}
          disabled={loading}
        />
        <button onClick={() => void submit()} disabled={loading || !sequence.trim()}>
          {loading ? "…" : "Design guides"}
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {guides.length > 0 && (
        <div className="guide-selector">
          <label>Select guide for off-target check:</label>
          <select
            value={selectedGuide ?? ""}
            onChange={(e) => {
              setSelectedGuide(e.target.value);
              setOffTarget(null);
            }}
          >
            {guides.map((g, i) => (
              <option key={i} value={g.spacer}>
                {i + 1}. {g.spacer} ({g.pam}, score {Math.round(g.score * 100)}%)
              </option>
            ))}
          </select>
        </div>
      )}

      <GuideList guides={guides} />

      {guides.length > 0 && (
        <div className="crispr-input">
          <label>Reference sequence for off-target screening:</label>
          <textarea
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            rows={4}
            disabled={otLoading}
          />
          <button
            onClick={() => void checkOffTarget()}
            disabled={otLoading || !selectedGuide || !reference.trim()}
          >
            {otLoading ? "…" : "Check off-targets"}
          </button>
        </div>
      )}

      {otError && <div className="chat-error">Error: {otError}</div>}

      {offTarget && <OffTargetList result={offTarget} />}
    </div>
  );
}
import { useState } from "react";
import { designGuides, findOffTargets } from "@/lib/crisprApi";
import { GuideList } from "@/components/GuideList";
import { OffTargetList } from "@/components/OffTargetList";
import type { Guide } from "@/types/guide";
import type { OffTargetResult } from "@/types/offtarget";

const EXAMPLE =
  "ACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTTACGTACGTACGTACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTTACGTACGT";

const OFF_TARGET_REF =
  "ACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTT" +
  "ACGTACGTACGTACGTTCGTCGGGGGGCCCCGGGGCCCCGGGGA GG".replace(/ /g, "") +
  "ACGTACGTACGTACGTACGTAGGTTTTAAAATTTTAAAATTTT";

export function CrisprPanel() {
  const [sequence, setSequence] = useState(EXAMPLE);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // off-target state
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
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setGuides([]);
    } finally {
      setLoading(false);
    }
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
        <label>Target DNA sequence (ACGT):</label>
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

      {error && <div className="chat-error">Ошибка: {error}</div>}

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

      {otError && <div className="chat-error">Ошибка: {otError}</div>}

      {offTarget && <OffTargetList result={offTarget} />}
    </div>
  );
}
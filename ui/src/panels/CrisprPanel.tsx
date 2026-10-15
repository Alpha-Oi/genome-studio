import { useState } from "react";
import { designGuides } from "@/lib/crisprApi";
import { GuideList } from "@/components/GuideList";
import type { Guide } from "@/types/guide";

const EXAMPLE =
  "ACGTACGTACGTACGTACGTCGGGGGGCCCCGGGGCCCCGGGGAGGTTTTAAAATTTTAAAATTTTACGTACGTACGT";

export function CrisprPanel() {
  const [sequence, setSequence] = useState(EXAMPLE);
  const [guides, setGuides] = useState<Guide[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    const seq = sequence.trim();
    if (!seq || loading) return;

    setLoading(true);
    setError(null);
    try {
      const result = await designGuides({ sequence: seq, topN: 5, minScore: 0.0 });
      setGuides(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setGuides([]);
    } finally {
      setLoading(false);
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

      <GuideList guides={guides} />
    </div>
  );
}
import { useState } from "react";
import { runNgs, runSanger } from "@/lib/sequencingApi";
import { Chromatogram } from "@/components/Chromatogram";
import type { NgsResponse, SangerResponse } from "@/types/sequencing";

const WT = "ATG" + "GCT".repeat(20) + "TAA";
const EDITED = "ATG" + "GCT".repeat(20) + "TAG"; // last base changed

interface Props {
  projectId: number | null;
}

export function SequencingPanel({ projectId: _projectId }: Props) {
  const [wtSeq, setWtSeq] = useState(WT);
  const [editedSeq, setEditedSeq] = useState(EDITED);
  const [editedFraction, setEditedFraction] = useState(0.5);
  const [hetFraction, setHetFraction] = useState(0.0);
  const [totalReads, setTotalReads] = useState(1000);
  const [window_, setWindow] = useState(40);

  const [sanger, setSanger] = useState<SangerResponse | null>(null);
  const [ngs, setNgs] = useState<NgsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const req = {
        wt_sequence: wtSeq.trim(),
        edited_sequence: editedSeq.trim(),
        edited_fraction: editedFraction,
        heterozygote_fraction: hetFraction,
        total_reads: totalReads,
        window: window_,
      };
      const [s, n] = await Promise.all([runSanger(req), runNgs(req)]);
      setSanger(s);
      setNgs(n);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setSanger(null);
      setNgs(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="crispr-panel">
      <h3>Sequencing simulation (Sanger / NGS)</h3>

      <div className="crispr-input">
        <label>WT sequence:</label>
        <textarea
          value={wtSeq}
          onChange={(e) => setWtSeq(e.target.value)}
          rows={2}
        />
      </div>

      <div className="crispr-input">
        <label>Edited sequence (same length):</label>
        <textarea
          value={editedSeq}
          onChange={(e) => setEditedSeq(e.target.value)}
          rows={2}
        />
      </div>

      <div className="sim-grid">
        <label>
          Edited fraction
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={editedFraction}
            onChange={(e) => setEditedFraction(parseFloat(e.target.value) || 0)}
          />
        </label>
        <label>
          Heterozygote fraction
          <input
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={hetFraction}
            onChange={(e) => setHetFraction(parseFloat(e.target.value) || 0)}
          />
        </label>
        <label>
          Reads
          <input
            type="number"
            min={10}
            step={100}
            value={totalReads}
            onChange={(e) => setTotalReads(parseInt(e.target.value) || 1000)}
          />
        </label>
        <label>
          Window
          <input
            type="number"
            min={5}
            step={5}
            value={window_}
            onChange={(e) => setWindow(parseInt(e.target.value) || 40)}
          />
        </label>
      </div>

      <div className="crispr-input">
        <button onClick={() => void run()} disabled={loading}>
          {loading ? "…" : "Simulate sequencing"}
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {sanger && (
        <div className="sim-result">
          <h4>Sanger chromatogram</h4>
          <div className="allele-chips">
            {sanger.alleles.map((a) => (
              <span key={a.name} className="allele-chip">
                {a.name}: {Math.round(a.fraction * 100)}%
              </span>
            ))}
          </div>
          <Chromatogram
            peaks={sanger.peaks}
            editPosition={sanger.edit_position}
          />
        </div>
      )}

      {ngs && (
        <div className="sim-result">
          <h4>NGS read distribution ({ngs.total_reads} reads)</h4>
          <table className="guide-table">
            <thead>
              <tr>
                <th>Allele</th>
                <th>Fraction</th>
                <th>Reads</th>
              </tr>
            </thead>
            <tbody>
              {ngs.alleles.map((a) => (
                <tr key={a.name}>
                  <td>{a.name}</td>
                  <td>{Math.round(a.fraction * 100)}%</td>
                  <td>{a.reads}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
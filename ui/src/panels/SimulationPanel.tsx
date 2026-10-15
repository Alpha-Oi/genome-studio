import { useState } from "react";
import { simulateEdit } from "@/lib/simulationApi";
import { createExperiment } from "@/lib/projectsApi";
import { downloadFasta, downloadGenbank, downloadVcf } from "@/lib/exportApi";
import { ConsequenceTree } from "@/components/ConsequenceTree";
import type { SimulateEditResponse } from "@/types/simulation";

const EXAMPLE_SEQ = "ATG" + "GCT".repeat(20) + "TAA";

interface Props {
  projectId: number | null;
  onSimulated?: () => void;
  onExperimentSaved?: () => void;
}

export function SimulationPanel({ projectId, onSimulated, onExperimentSaved }: Props) {
  const [sequence, setSequence] = useState(EXAMPLE_SEQ);
  const [geneName, setGeneName] = useState("testGene");
  const [kind, setKind] = useState<"substitution" | "insertion" | "deletion">(
    "substitution",
  );
  const [position, setPosition] = useState(5);
  const [ref, setRef] = useState("T");
  const [alt, setAlt] = useState("C");
  const [result, setResult] = useState<SimulateEditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);

  function currentExportReq() {
    return {
      sequence: sequence.trim(),
      gene_name: geneName,
      kind,
      position,
      ref: kind === "insertion" ? "" : ref,
      alt: kind === "deletion" ? "" : alt,
    };
  }

  async function submit() {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const r = await simulateEdit({
        ...currentExportReq(),
        project_id: projectId ?? undefined,
      });
      setResult(r);
      if (projectId !== null) {
        if (onSimulated) onSimulated();
        try {
          const title =
            geneName +
            ": " +
            r.effect.effect_type +
            " at pos " +
            String(position);
          await createExperiment(projectId, "simulation", title, r);
          if (onExperimentSaved) onExperimentSaved();
        } catch (persistErr) {
          console.warn("Failed to save simulation experiment:", persistErr);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  async function doExport(kindName: "fasta" | "vcf" | "genbank") {
    setExporting(kindName);
    setError(null);
    try {
      const req = currentExportReq();
      if (kindName === "fasta") await downloadFasta(req);
      else if (kindName === "vcf") await downloadVcf(req);
      else await downloadGenbank(req);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="crispr-panel">
      <h3>Simulate edit</h3>

      <div className="crispr-input">
        <label>DNA sequence:</label>
        <textarea
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
          rows={3}
        />
      </div>

      <div className="sim-grid">
        <label>
          Gene name
          <input value={geneName} onChange={(e) => setGeneName(e.target.value)} />
        </label>
        <label>
          Kind
          <select value={kind} onChange={(e) => setKind(e.target.value as typeof kind)}>
            <option value="substitution">substitution</option>
            <option value="insertion">insertion</option>
            <option value="deletion">deletion</option>
          </select>
        </label>
        <label>
          Position
          <input
            type="number"
            value={position}
            onChange={(e) => setPosition(parseInt(e.target.value) || 0)}
          />
        </label>
        <label>
          Ref
          <input
            value={ref}
            onChange={(e) => setRef(e.target.value)}
            disabled={kind === "insertion"}
          />
        </label>
        <label>
          Alt
          <input
            value={alt}
            onChange={(e) => setAlt(e.target.value)}
            disabled={kind === "deletion"}
          />
        </label>
      </div>

      <div className="sim-actions">
        <button onClick={() => void submit()} disabled={loading}>
          {loading ? "…" : "Simulate"}
        </button>
        <span className="sim-actions-label">Export:</span>
        <button
          className="export-btn"
          onClick={() => void doExport("fasta")}
          disabled={exporting !== null}
        >
          {exporting === "fasta" ? "…" : "FASTA"}
        </button>
        <button
          className="export-btn"
          onClick={() => void doExport("vcf")}
          disabled={exporting !== null}
        >
          {exporting === "vcf" ? "…" : "VCF"}
        </button>
        <button
          className="export-btn"
          onClick={() => void doExport("genbank")}
          disabled={exporting !== null}
        >
          {exporting === "genbank" ? "…" : "GenBank"}
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {result && (
        <div className="sim-result">
          <div className="plan-metrics">
            <span className="metric">
              effect <b>{result.effect.effect_type}</b>
            </span>
            <span className="metric">
              severity <b>{Math.round(result.effect.severity * 100)}%</b>
            </span>
          </div>
          <p className="plan-rationale">{result.effect.description}</p>
          <details>
            <summary>Edited sequence</summary>
            <pre className="seq-mono">{result.edited_sequence}</pre>
          </details>
          <h4>Consequence tree</h4>
          <ConsequenceTree node={result.consequence_tree} />
        </div>
      )}
    </div>
  );
}
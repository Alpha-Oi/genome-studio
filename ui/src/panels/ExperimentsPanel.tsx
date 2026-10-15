import { useEffect, useState } from "react";
import {
  createExperiment,
  deleteExperiment,
  listExperiments,
} from "@/lib/projectsApi";
import { downloadProjectReport } from "@/lib/reportApi";
import type { Experiment } from "@/types/project";

interface Props {
  projectId: number | null;
  refreshKey?: number;
  onExperimentSaved?: () => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const isToday =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate();
  const time = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (isToday) return time;
  const date = d.toLocaleDateString([], { month: "short", day: "numeric" });
  return date + " " + time;
}

export function ExperimentsPanel({ projectId, refreshKey = 0, onExperimentSaved }: Props) {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [duplicating, setDuplicating] = useState<number | null>(null);

  async function refresh() {
    if (projectId === null) {
      setExperiments([]);
      return;
    }
    setError(null);
    try {
      const items = await listExperiments(projectId);
      setExperiments(items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshKey]);

  async function remove(id: number) {
    if (!confirm("Delete experiment?")) return;
    try {
      await deleteExperiment(id);
      setExperiments((prev) => prev.filter((e) => e.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  async function duplicate(exp: Experiment) {
    if (projectId === null || duplicating !== null) return;
    setDuplicating(exp.id);
    setError(null);
    try {
      const title = exp.title + " (copy)";
      const created = await createExperiment(projectId, exp.kind, title, exp.payload);
      setExperiments((prev) => [created, ...prev]);
      if (onExperimentSaved) onExperimentSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setDuplicating(null);
    }
  }

  async function download() {
    if (projectId === null) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadProjectReport(projectId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setDownloading(false);
    }
  }

  if (projectId === null) {
    return (
      <div className="panel">
        <h2>Experiments</h2>
        <p>Select a project to see its experiments.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="exp-panel-head">
        <h2>Experiments ({experiments.length})</h2>
        <button
          className="pdf-btn"
          onClick={() => void download()}
          disabled={downloading}
          title="Download PDF report"
        >
          {downloading ? "…" : "PDF"}
        </button>
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {experiments.length === 0 ? (
        <p>No experiments yet.</p>
      ) : (
        <ul className="experiment-list">
          {experiments.map((e) => (
            <li key={e.id} className="experiment-item">
              <div className="experiment-head">
                <span className="badge exp-kind">{e.kind}</span>
                <span className="exp-time">{formatDate(e.created_at)}</span>
                <button
                  className="exp-action"
                  onClick={() => void duplicate(e)}
                  disabled={duplicating === e.id}
                  title="Duplicate"
                >
                  {duplicating === e.id ? "…" : "⎘"}
                </button>
                <button
                  className="exp-delete"
                  onClick={() => void remove(e.id)}
                  title="Delete"
                >
                  ×
                </button>
              </div>
              <div className="experiment-title">{e.title || "(no title)"}</div>
              <details className="experiment-details">
                <summary>payload</summary>
                <pre className="seq-mono">
                  {JSON.stringify(e.payload, null, 2)}
                </pre>
              </details>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
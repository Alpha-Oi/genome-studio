import { useEffect, useState } from "react";
import { acknowledgeWarning, listWarnings } from "@/lib/warningsApi";
import type { Warning } from "@/types/warning";

interface Props {
  projectId: number | null;
}

export function WarningsPanel({ projectId }: Props) {
  const [warnings, setWarnings] = useState<Warning[]>([]);
  const [filter, setFilter] = useState<"all" | "open" | "acknowledged">("open");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  async function refresh() {
    if (projectId === null) {
      setWarnings([]);
      return;
    }
    setError(null);
    try {
      const status = filter === "all" ? undefined : filter;
      const items = await listWarnings(projectId, status);
      setWarnings(items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, filter]);

  async function ack(id: number) {
    const note = prompt("Reason for acknowledging this warning:");
    if (!note || !note.trim()) return;
    setBusyId(id);
    setError(null);
    try {
      await acknowledgeWarning(id, "ui-user", note.trim());
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setBusyId(null);
    }
  }

  if (projectId === null) {
    return (
      <div className="panel">
        <h2>Warnings</h2>
        <p>Select a project to see its warnings.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2>Warnings</h2>

      <div className="warnings-filter">
        {(["open", "acknowledged", "all"] as const).map((f) => (
          <button
            key={f}
            className={filter === f ? "active" : ""}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {error && <div className="chat-error">Error: {error}</div>}

      {warnings.length === 0 ? (
        <p>No warnings.</p>
      ) : (
        <ul className="warning-list">
          {warnings.map((w) => (
            <li key={w.id} className="warning-item">
              <div className="warning-head">
                <span className={"badge wsev-" + w.severity}>{w.severity}</span>
                <span className="badge wtype">{w.type}</span>
                <span className="badge wlevel">{w.level}</span>
              </div>
              <div className="warning-msg">{w.message}</div>
              {w.evidence.length > 0 && (
                <ul className="warning-evidence">
                  {w.evidence.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              )}
              {w.status === "open" ? (
                <button
                  className="warning-ack"
                  onClick={() => void ack(w.id)}
                  disabled={busyId === w.id}
                >
                  {busyId === w.id ? "…" : "Acknowledge"}
                </button>
              ) : (
                <div className="warning-ack-info">
                  ✓ {w.acknowledged_by}: {w.acknowledgment_note}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
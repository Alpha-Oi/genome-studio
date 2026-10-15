import type { RelatedItem } from "@/lib/relatedApi";

interface Props {
  items: RelatedItem[];
  criteria: { gene: string; organism: string; intent: string } | null;
  onOpenProject: (projectId: number) => void;
}

function pct(x: number | null): string {
  if (x === null || x === undefined) return "—";
  return Math.round(x * 100) + "%";
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

export function RelatedHistory({ items, criteria, onOpenProject }: Props) {
  if (items.length === 0 || !criteria) return null;

  return (
    <div className="related-history">
      <h3>
        Related history ({items.length}) — {criteria.gene} / {criteria.organism} /{" "}
        {criteria.intent}
      </h3>
      <ul className="related-list">
        {items.map((it) => (
          <li key={it.experiment_id} className="related-item">
            <div className="related-head">
              <span className="badge related-project">{it.project_name}</span>
              <span className="related-time">{formatDate(it.created_at)}</span>
            </div>
            <div className="related-title">{it.title}</div>
            <div className="related-metrics">
              <span className="metric">
                intervention <b>{it.intervention_kind ?? "?"}</b>
              </span>
              <span className="metric">
                effect <b>{pct(it.predicted_effect)}</b>
              </span>
              <span className="metric">
                off-target <b>{pct(it.off_target_risk)}</b>
              </span>
              <span className="metric">
                essentiality <b>{pct(it.essentiality_risk)}</b>
              </span>
            </div>
            <button
              className="related-open"
              onClick={() => onOpenProject(it.project_id)}
            >
              Open project →
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
import type { Plan } from "@/types/plan";

interface Props {
  plan: Plan;
}

function pct(x: number): string {
  return Math.round(x * 100) + "%";
}

export function PlanCard({ plan }: Props) {
  const { goal, intervention, steps, notes } = plan;

  return (
    <div className="plan-card">
      <header className="plan-header">
        <span className="badge badge-intent">{goal.intent}</span>
        <span className="badge badge-gene">{goal.target.gene}</span>
        <span className="badge badge-organism">{goal.target.organism}</span>
      </header>

      <div className="plan-rationale">
        <strong>{intervention.kind}</strong> — {intervention.rationale}
      </div>

      <div className="plan-metrics">
        <span className="metric">
          effect <b>{pct(intervention.predicted_effect)}</b>
        </span>
        <span className="metric">
          off-target <b>{pct(intervention.off_target_risk)}</b>
        </span>
        <span className="metric">
          essentiality <b>{pct(intervention.essentiality_risk)}</b>
        </span>
        <span className="metric">
          complexity <b>{intervention.complexity}/5</b>
        </span>
      </div>

      {intervention.warnings.length > 0 && (
        <ul className="plan-warnings">
          {intervention.warnings.map((w, i) => (
            <li key={i}>⚠ {w}</li>
          ))}
        </ul>
      )}

      <ol className="plan-steps">
        {steps.map((s) => (
          <li key={s.order} className="plan-step">
            <span className="step-order">{s.order}.</span>
            <span className="step-action">{s.action}</span>
            <span className="step-desc">{s.description}</span>
          </li>
        ))}
      </ol>

      {notes.length > 0 && (
        <div className="plan-notes">
          {notes.map((n, i) => (
            <div key={i}>ℹ {n}</div>
          ))}
        </div>
      )}
    </div>
  );
}
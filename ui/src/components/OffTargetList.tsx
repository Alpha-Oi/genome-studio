import type { OffTargetResult } from "@/types/offtarget";

interface Props {
  result: OffTargetResult;
}

function riskClass(risk: number): string {
  if (risk < 0.2) return "score-good";
  if (risk < 0.5) return "score-mid";
  return "score-bad";
}

export function OffTargetList({ result }: Props) {
  const { hits, summary } = result;

  return (
    <div className="offtarget-list">
      <h3>
        Off-targets: {summary.total} hits&nbsp;
        <span className={riskClass(summary.risk)}>
          risk {Math.round(summary.risk * 100)}%
        </span>
      </h3>

      <div className="offtarget-summary">
        <span>perfect <b>{summary.perfect}</b></span>
        <span>near (1-2 mm) <b>{summary.near}</b></span>
        <span>distant (≥3 mm) <b>{summary.distant}</b></span>
      </div>

      {hits.length === 0 ? (
        <p className="offtarget-empty">No off-targets found with given criteria.</p>
      ) : (
        <table className="guide-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Locus</th>
              <th>Strand</th>
              <th>MM</th>
              <th>Spacer</th>
              <th>PAM</th>
            </tr>
          </thead>
          <tbody>
            {hits.slice(0, 50).map((h, i) => (
              <tr key={i} className={h.mismatches === 0 ? "row-perfect" : ""}>
                <td>{i + 1}</td>
                <td className="mono">{h.locus_label}</td>
                <td>{h.strand}</td>
                <td className={h.mismatches <= 2 ? "score-bad" : h.mismatches <= 3 ? "score-mid" : ""}>
                  {h.mismatches}
                </td>
                <td className="mono">{h.spacer}</td>
                <td className="mono">{h.pam}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {hits.length > 50 && (
        <p className="offtarget-empty">Showing first 50 of {hits.length} hits.</p>
      )}
    </div>
  );
}
import type { BatchResult } from "@/lib/batchApi";

interface Props {
  results: BatchResult[];
}

function scoreClass(score: number): string {
  if (score >= 0.75) return "score-good";
  if (score >= 0.5) return "score-mid";
  return "score-bad";
}

export function BatchResultsTable({ results }: Props) {
  if (results.length === 0) return null;

  return (
    <div className="batch-results">
      <h3>Batch design: {results.length} sequence(s)</h3>
      <table className="guide-table">
        <thead>
          <tr>
            <th>Sequence</th>
            <th>Length</th>
            <th>#</th>
            <th>Top spacer</th>
            <th>PAM</th>
            <th>Strand</th>
            <th>GC</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, ri) => {
            if (r.guides.length === 0) {
              return (
                <tr key={ri} className="row-error">
                  <td>{r.name}</td>
                  <td>{r.length}</td>
                  <td colSpan={6} className="score-bad">
                    {r.error || "no guides"}
                  </td>
                </tr>
              );
            }
            return r.guides.map((g, gi) => (
              <tr key={ri + "-" + gi}>
                {gi === 0 && (
                  <>
                    <td rowSpan={r.guides.length}>{r.name}</td>
                    <td rowSpan={r.guides.length}>{r.length}</td>
                  </>
                )}
                <td>{gi + 1}</td>
                <td className="mono">{g.spacer}</td>
                <td className="mono">{g.pam}</td>
                <td>{g.strand}</td>
                <td>{Math.round(g.gc_content * 100)}%</td>
                <td className={scoreClass(g.score)}>
                  {Math.round(g.score * 100)}%
                </td>
              </tr>
            ));
          })}
        </tbody>
      </table>
    </div>
  );
}
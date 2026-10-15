import type { Guide } from "@/types/guide";

interface Props {
  guides: Guide[];
}

function pct(x: number): string {
  return Math.round(x * 100) + "%";
}

function scoreClass(score: number): string {
  if (score >= 0.75) return "score-good";
  if (score >= 0.5) return "score-mid";
  return "score-bad";
}

export function GuideList({ guides }: Props) {
  if (guides.length === 0) return null;

  return (
    <div className="guide-list">
      <h3>Top {guides.length} guides (SpCas9, NGG PAM)</h3>
      <table className="guide-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Spacer (5'→3')</th>
            <th>PAM</th>
            <th>Pos</th>
            <th>Strand</th>
            <th>GC</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {guides.map((g, i) => (
            <tr key={i}>
              <td>{i + 1}</td>
              <td className="mono">{g.spacer}</td>
              <td className="mono">{g.pam}</td>
              <td>{g.position}</td>
              <td>{g.strand}</td>
              <td>{pct(g.gc_content)}</td>
              <td className={scoreClass(g.score)}>{pct(g.score)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {guides[0] && guides[0].warnings.length > 0 && (
        <ul className="guide-warnings">
          {guides[0].warnings.map((w, i) => (
            <li key={i}>⚠ {w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
import type { SangerPeak } from "@/types/sequencing";

interface Props {
  peaks: SangerPeak[];
  editPosition: number;
}

const COLORS: Record<string, string> = {
  A: "#7cd47c", // green
  T: "#e88080", // red
  G: "#333333", // black
  C: "#6090e0", // blue
};

const ORDER = ["A", "T", "G", "C"] as const;

export function Chromatogram({ peaks, editPosition }: Props) {
  if (peaks.length === 0) return null;

  const cellW = 12;
  const height = 140;
  const width = peaks.length * cellW + 60;
  const baseline = height - 10;

  return (
    <div className="chromatogram-wrap">
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="chromatogram"
      >
        {peaks.map((p, i) => {
          const x = 60 + i * cellW;
          const isEdit = p.position === editPosition;
          return (
            <g key={i}>
              {isEdit && (
                <rect
                  x={x}
                  y={0}
                  width={cellW}
                  height={height}
                  fill="rgba(255,200,100,0.12)"
                />
              )}
              {ORDER.map((base) => {
                const h = (p[base] as number) * (baseline - 20);
                return (
                  <rect
                    key={base}
                    x={x + 1}
                    y={baseline - h}
                    width={cellW - 2}
                    height={h}
                    fill={COLORS[base]}
                    opacity={0.85}
                  />
                );
              })}
              {i % 5 === 0 && (
                <text
                  x={x + cellW / 2}
                  y={height - 1}
                  textAnchor="middle"
                  fontSize="8"
                  fill="#666"
                >
                  {p.position}
                </text>
              )}
            </g>
          );
        })}

        <g transform="translate(6, 16)">
          {ORDER.map((base, baseIdx) => (
            <g key={base} transform={`translate(0, ${baseIdx * 16})`}>
              <rect width={10} height={10} fill={COLORS[base]} />
              <text x={14} y={9} fontSize="10" fill="#ccc">
                {base}
              </text>
            </g>
          ))}
        </g>
      </svg>
      <p className="chromatogram-note">
        Yellow column = edit position {editPosition + 1} (1-based).
        Overlapping bars = heterozygous / mixed population.
      </p>
    </div>
  );
}
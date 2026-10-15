import type { ConsequenceNode } from "@/types/simulation";

interface Props {
  node: ConsequenceNode;
  depth?: number;
}

function confidenceClass(c: number): string {
  if (c >= 0.75) return "score-good";
  if (c >= 0.5) return "score-mid";
  return "score-bad";
}

export function ConsequenceTree({ node, depth = 0 }: Props) {
  const indent = depth * 16;
  return (
    <div className="consequence-node" style={{ marginLeft: indent }}>
      <div className="consequence-row">
        <span className={"ctype ctype-" + node.type}>{node.type}</span>
        <span className="cdesc">{node.description || "\u00a0"}</span>
        <span className={"cconf " + confidenceClass(node.confidence)}>
          {Math.round(node.confidence * 100)}%
        </span>
      </div>
      {node.children.map((c) => (
        <ConsequenceTree key={c.node_id} node={c} depth={depth + 1} />
      ))}
    </div>
  );
}
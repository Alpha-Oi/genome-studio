interface Props {
  onPick: (text: string) => void;
}

interface Template {
  label: string;
  text: string;
}

const TEMPLATES: Template[] = [
  { label: "Knockout", text: "knockout gene lacZ in E. coli" },
  { label: "Increase", text: "increase expression of gene lacZ in E. coli" },
  { label: "Decrease", text: "downregulate gene lacZ in E. coli" },
  { label: "Knock-in", text: "knock-in of gene GFP in CHO, stable integration" },
];

export function GoalTemplates({ onPick }: Props) {
  return (
    <div className="goal-templates">
      <span className="goal-templates-label">Templates:</span>
      {TEMPLATES.map((t) => (
        <button
          key={t.label}
          className="goal-template-btn"
          onClick={() => onPick(t.text)}
          title={t.text}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
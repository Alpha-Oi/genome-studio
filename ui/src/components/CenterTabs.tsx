import { useState, type ReactNode } from "react";

export type CenterTab = "browser" | "crispr" | "simulation" | "sequencing";

interface Props {
  browser: ReactNode;
  crispr: ReactNode;
  simulation: ReactNode;
  sequencing: ReactNode;
}

const TABS: { id: CenterTab; label: string }[] = [
  { id: "browser", label: "Browser" },
  { id: "crispr", label: "CRISPR" },
  { id: "simulation", label: "Simulation" },
  { id: "sequencing", label: "Sequencing" },
];

export function CenterTabs(props: Props) {
  const [active, setActive] = useState<CenterTab>("browser");

  return (
    <div className="center-tabs">
      <nav className="tabs-bar">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={active === t.id ? "tab active" : "tab"}
            onClick={() => setActive(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="tabs-body">
        {active === "browser" && props.browser}
        {active === "crispr" && props.crispr}
        {active === "simulation" && props.simulation}
        {active === "sequencing" && props.sequencing}
      </div>
    </div>
  );
}
import { type ComponentType, type ReactNode } from "react";
import {
  BrowserIcon,
  CrisprIcon,
  SequencingIcon,
  SimulationIcon,
} from "@/components/icons/TabsIcons";

export type CenterTab = "browser" | "crispr" | "simulation" | "sequencing";

interface Props {
  browser: ReactNode;
  crispr: ReactNode;
  simulation: ReactNode;
  sequencing: ReactNode;
  active: CenterTab;
  onChange: (tab: CenterTab) => void;
}

interface TabDef {
  id: CenterTab;
  label: string;
  Icon: ComponentType<{ size?: number }>;
}

const TABS: TabDef[] = [
  { id: "browser", label: "Browser", Icon: BrowserIcon },
  { id: "crispr", label: "CRISPR", Icon: CrisprIcon },
  { id: "simulation", label: "Simulation", Icon: SimulationIcon },
  { id: "sequencing", label: "Sequencing", Icon: SequencingIcon },
];

export function CenterTabs(props: Props) {
  const { active, onChange } = props;

  return (
    <div className="center-tabs">
      <nav className="tabs-bar">
        {TABS.map((t) => {
          const Icon = t.Icon;
          return (
            <button
              key={t.id}
              className={active === t.id ? "tab active" : "tab"}
              onClick={() => onChange(t.id)}
            >
              <Icon />
              <span className="tab-label">{t.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="tabs-body">
        <div style={{ display: active === "browser" ? "block" : "none" }}>
          {props.browser}
        </div>
        <div style={{ display: active === "crispr" ? "block" : "none" }}>
          {props.crispr}
        </div>
        <div style={{ display: active === "simulation" ? "block" : "none" }}>
          {props.simulation}
        </div>
        <div style={{ display: active === "sequencing" ? "block" : "none" }}>
          {props.sequencing}
        </div>
      </div>
    </div>
  );
}
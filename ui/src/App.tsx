import { useEffect, useState } from "react";
import {
  BrowserPanel,
  ChatPanel,
  CrisprPanel,
  DevPanel,
  ExperimentsPanel,
  ProjectsPanel,
  SequencingPanel,
  SimulationPanel,
  WarningsPanel,
} from "@/panels";
import { CenterTabs, type CenterTab } from "@/components/CenterTabs";
import { getBuildInfo } from "@/lib/build-info";
import { fetchMode } from "@/lib/modeApi";
import "./App.css";

export function App() {
  const build = getBuildInfo();
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [sideRefreshKey, setSideRefreshKey] = useState(0);
  const [appMode, setAppMode] = useState<"local" | "multi" | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<CenterTab>("browser");

  function bump(message?: string) {
    setSideRefreshKey((k) => k + 1);
    if (message) {
      setToast(message);
      window.setTimeout(() => setToast(null), 2000);
    }
  }

  useEffect(() => {
    void fetchMode()
      .then((m) => setAppMode(m.mode))
      .catch(() => setAppMode(null));
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Genome Studio</h1>
        <span className="build-badge">{build.mode}</span>
        {appMode && (
          <span className={"mode-badge mode-" + appMode}>
            {appMode === "local" ? "LOCAL" : "SERVER"}
          </span>
        )}
        {selectedProjectId !== null && (
          <span className="project-badge">project #{selectedProjectId}</span>
        )}
      </header>

      <main className="app-main">
        <aside className="app-sidebar">
          <ProjectsPanel
            selectedId={selectedProjectId}
            onSelect={setSelectedProjectId}
          />
          <ExperimentsPanel
            projectId={selectedProjectId}
            refreshKey={sideRefreshKey}
            onExperimentSaved={() => bump()}
          />
        </aside>

        <section className="app-center">
          <CenterTabs
            active={activeTab}
            onChange={setActiveTab}
            browser={<BrowserPanel />}
            crispr={
              <CrisprPanel
                projectId={selectedProjectId}
                onExperimentSaved={() => bump("CRISPR design saved")}
              />
            }
            simulation={
              <SimulationPanel
                projectId={selectedProjectId}
                onSimulated={() => bump()}
                onExperimentSaved={() => bump("Simulation saved")}
              />
            }
            sequencing={
              <SequencingPanel
                projectId={selectedProjectId}
                onExperimentSaved={() => bump("Sequencing saved")}
              />
            }
          />
        </section>

        <aside className="app-right">
          <ChatPanel
            projectId={selectedProjectId}
            onPlanCreated={() => bump()}
            onExperimentSaved={() => bump("Plan saved")}
          />
          <WarningsPanel
            projectId={selectedProjectId}
            refreshKey={sideRefreshKey}
          />
          <DevPanel />
        </aside>
      </main>

      {toast && <div className="toast">✓ {toast}</div>}

      <footer className="app-footer">
        <span>v0.0.1</span>
      </footer>
    </div>
  );
}
import { useState } from "react";
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
import { getBuildInfo } from "@/lib/build-info";
import "./App.css";

export function App() {
  const build = getBuildInfo();
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [sideRefreshKey, setSideRefreshKey] = useState(0);

  function bump() {
    setSideRefreshKey((k) => k + 1);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Genome Studio</h1>
        <span className="build-badge">{build.mode}</span>
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
          />
        </aside>

        <section className="app-center">
          <BrowserPanel />
          <CrisprPanel
            projectId={selectedProjectId}
            onExperimentSaved={bump}
          />
          <SimulationPanel
            projectId={selectedProjectId}
            onSimulated={bump}
            onExperimentSaved={bump}
          />
          <SequencingPanel
            projectId={selectedProjectId}
            onExperimentSaved={bump}
          />
        </section>

        <aside className="app-right">
          <ChatPanel
            projectId={selectedProjectId}
            onPlanCreated={bump}
            onExperimentSaved={bump}
          />
          <WarningsPanel
            projectId={selectedProjectId}
            refreshKey={sideRefreshKey}
          />
          <DevPanel />
        </aside>
      </main>

      <footer className="app-footer">
        <span>v0.0.1</span>
      </footer>
    </div>
  );
}
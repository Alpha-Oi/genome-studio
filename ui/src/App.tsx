import { useState } from "react";
import {
  BrowserPanel,
  ChatPanel,
  CrisprPanel,
  DevPanel,
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
  const [warningsRefreshKey, setWarningsRefreshKey] = useState(0);

  function bumpWarnings() {
    setWarningsRefreshKey((k) => k + 1);
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
        </aside>

        <section className="app-center">
          <BrowserPanel />
          <CrisprPanel />
          <SimulationPanel
            projectId={selectedProjectId}
            onSimulated={bumpWarnings}
          />
          <SequencingPanel projectId={selectedProjectId} />
        </section>

        <aside className="app-right">
          <ChatPanel
            projectId={selectedProjectId}
            onPlanCreated={bumpWarnings}
          />
          <WarningsPanel
            projectId={selectedProjectId}
            refreshKey={warningsRefreshKey}
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
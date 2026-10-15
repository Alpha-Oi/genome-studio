import {
  BrowserPanel,
  ChatPanel,
  CrisprPanel,
  DevPanel,
  ProjectsPanel,
  SimulationPanel,
  WarningsPanel,
} from "@/panels";
import { getBuildInfo } from "@/lib/build-info";
import "./App.css";

export function App() {
  const build = getBuildInfo();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Genome Studio</h1>
        <span className="build-badge">{build.mode}</span>
      </header>

      <main className="app-main">
        <aside className="app-sidebar">
          <ProjectsPanel />
        </aside>

        <section className="app-center">
          <BrowserPanel />
          <CrisprPanel />
          <SimulationPanel />
        </section>

        <aside className="app-right">
          <ChatPanel />
          <WarningsPanel />
          <DevPanel />
        </aside>
      </main>

      <footer className="app-footer">
        <span>v0.0.1</span>
      </footer>
    </div>
  );
}
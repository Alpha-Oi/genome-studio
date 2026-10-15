import { getBuildInfo } from "@/lib/build-info";

// DevPanel виден ТОЛЬКО в dev-сборке.
// В prod-сборке компонент не рендерится.
export function DevPanel() {
  const info = getBuildInfo();

  if (!info.devPanelAvailable) {
    return null;
  }

  return (
    <div className="panel dev-panel">
      <h2>DEV PANEL</h2>
      <p>ВСЕ ФИЛЬТРЫ ОТКЛЮЧЕНЫ</p>
      <ul>
        <li>T0 Essentiality</li>
        <li>T0 Off-target</li>
        <li>T0 Toxicity</li>
        <li>T1 DURC</li>
        <li>T1 Pathogen</li>
        <li>T2 Legal</li>
        <li>T2 Export</li>
      </ul>
    </div>
  );
}

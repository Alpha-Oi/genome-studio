// Информация о сборке UI.
//
// __APP_MODE__ задаётся в vite.config.ts.
// В prod-сборке dev_panel недоступна.

export type BuildMode = "development" | "production";

export interface BuildInfo {
  mode: BuildMode;
  devPanelAvailable: boolean;
}

export function getBuildInfo(): BuildInfo {
  const mode = (__APP_MODE__ as BuildMode) ?? "production";
  return {
    mode,
    devPanelAvailable: mode === "development",
  };
}

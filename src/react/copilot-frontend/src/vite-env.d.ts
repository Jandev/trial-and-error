/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * URL of the .NET AG-UI endpoint (e.g. "https://localhost:7123/agui").
   * Injected by the Aspire AppHost in dev; required at module load.
   */
  readonly VITE_AGUI_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

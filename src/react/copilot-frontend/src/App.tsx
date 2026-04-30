import { useMemo } from "react";
import { CopilotKitProvider, CopilotChat } from "@copilotkit/react-core/v2";
import { HttpAgent } from "@ag-ui/client";

import { useShowToastAction } from "./tools/useShowToastAction";
import { useAskUserConfirmationAction } from "./tools/useAskUserConfirmationAction";
import { useShowWeatherAction } from "./tools/useShowWeatherAction";
import "./App.css";

/**
 * Read the AG-UI endpoint URL from Vite env at build time.
 *
 * In dev this is injected by the Aspire AppHost (see AppHost.cs subtask 09)
 * via `VITE_AGUI_URL=<apiservice https endpoint>/agui`. For standalone
 * `npm run dev` runs, copy `.env.example` -> `.env.local` and edit.
 */
const AGUI_URL = import.meta.env.VITE_AGUI_URL;

if (!AGUI_URL) {
  // Fail fast at module load so the dev experience is obvious.
  throw new Error(
    "VITE_AGUI_URL is not set. Run via the Aspire AppHost (which injects it) " +
      "or copy .env.example to .env.local and set the value.",
  );
}

/**
 * The agent name MUST match the first arg passed to `app.MapAGUI(...)` on the
 * .NET side (subtask 03). We use "frontend_demo" everywhere.
 */
const AGENT_NAME = "frontend_demo";

function App() {
  // useMemo so React StrictMode's double-render in dev doesn't open two
  // SSE connections per mount.
  const agent = useMemo(
    () =>
      new HttpAgent({
        url: AGUI_URL,
      }),
    [],
  );

  return (
    <CopilotKitProvider
      // `agents__unsafe_dev_only` registers a browser-side AbstractAgent so the
      // CopilotKit core treats it as a "local agent" and skips the runtime-url
      // requirement (CopilotKitProvider.tsx line 412: `!hasLocalAgents` check).
      // The HttpAgent below POSTs RunAgentInput directly to our .NET MapAGUI
      // endpoint — no Node sidecar needed. The "unsafe" naming is about
      // exposing credentials in the browser, which is not relevant here since
      // /agui is unauthenticated in dev.
      agents__unsafe_dev_only={{ [AGENT_NAME]: agent }}
    >
      <FrontendTools />
      <main className="app-shell">
        <header className="app-header">
          <h1>AspireTrial · CopilotKit + AG-UI demo</h1>
          <p>
            Chat with a Microsoft Agent Framework agent hosted in the .NET API.
            Try: <em>"show me a toast"</em>,{" "}
            <em>"what's the weather in Amsterdam?"</em>, or{" "}
            <em>"delete my files"</em> (HITL).
          </p>
        </header>
        <section className="chat-pane">
          <CopilotChat
            agentId={AGENT_NAME}
            labels={{
              welcomeMessageText: "Hi! Ask me to call a frontend tool.",
              chatInputPlaceholder: "Message the demo agent…",
            }}
          />
        </section>
      </main>
    </CopilotKitProvider>
  );
}

export default App;

/**
 * Mounts the three frontend-tool hooks. Must live INSIDE the
 * <CopilotKitProvider> so the hooks can register against the active context.
 * Renders nothing.
 */
function FrontendTools() {
  useShowToastAction();
  useAskUserConfirmationAction();
  useShowWeatherAction();
  return null;
}

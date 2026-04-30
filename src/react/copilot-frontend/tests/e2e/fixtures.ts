import { test as base, expect, type Page } from "@playwright/test";

/**
 * Shared Playwright fixtures + helpers for the copilot-frontend e2e suite.
 *
 * Test strategy
 * -------------
 * The React app talks to two external systems at runtime:
 *   1. The .NET AG-UI endpoint at VITE_AGUI_URL (POST /agui, SSE response).
 *   2. The Open-Meteo geocoding + forecast HTTPS APIs (used by showWeather).
 *
 * For deterministic e2e runs we mock both via page.route() in individual specs.
 * This fixture file exposes:
 *   - the default `page` fixture (re-exported for convenience)
 *   - sendChatMessage(page, text) helper that types into the CopilotKit chat
 *     input and submits it via Enter.
 *
 * Selectors prefer role-based queries; fall back to data-testid hooks added in
 * our own components (e.g. ConfirmationDialog, WeatherCard).
 */

export const test = base;
export { expect };

/**
 * Type a message into the CopilotKit chat input and submit via Enter.
 *
 * CopilotKit's <CopilotChat /> renders a textarea (role="textbox") with the
 * placeholder "Type a message..." by default. We match by role to stay
 * resilient to copy changes in our wrapper.
 */
export async function sendChatMessage(page: Page, text: string): Promise<void> {
  const input = page.getByRole("textbox").first();
  await input.click();
  await input.fill(text);
  await input.press("Enter");
}

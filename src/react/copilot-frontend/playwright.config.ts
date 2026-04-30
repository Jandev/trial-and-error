import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config for the copilot-frontend e2e suite.
 *
 * baseURL is read from PLAYWRIGHT_BASE_URL so the same suite can run against:
 *  - the local Vite dev server (default http://localhost:5173)
 *  - the URL allocated by Aspire AppHost when running `aspire run`
 *
 * Tests are expected to mock the AG-UI endpoint and Open-Meteo via page.route()
 * (see tests/e2e/fixtures.ts), so no live backend is required by default.
 */
export default defineConfig({
  testDir: "tests/e2e",
  retries: 1,
  reporter: "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

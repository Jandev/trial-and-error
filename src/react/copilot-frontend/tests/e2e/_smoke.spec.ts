import { test, expect } from "./fixtures";

/**
 * Sanity check: confirms the Playwright runner is wired up correctly
 * before the real specs land in subtasks 11–13.
 *
 * This test does not hit the app — it just verifies the test harness
 * itself loads and executes. Safe to keep alongside the real specs.
 */
test("playwright harness boots", () => {
  expect(1 + 1).toBe(2);
});

import { useFrontendTool } from "@copilotkit/react-core/v2";
import toast from "react-hot-toast";
import { z } from "zod";

const LEVEL_SCHEMA = z.enum(["success", "error", "info"]);
type ToastLevel = z.infer<typeof LEVEL_SCHEMA>;

const PARAMS_SCHEMA = z.object({
  level: LEVEL_SCHEMA.describe("One of: success, error, info"),
  message: z.string().describe("The text to display in the toast"),
});

function showToast(level: ToastLevel, message: string): void {
  switch (level) {
    case "success":
      toast.success(message);
      return;
    case "error":
      toast.error(message);
      return;
    case "info":
      toast(message);
      return;
  }
}

/**
 * Registers the `showToast` frontend tool. The agent calls this with
 * `{ level, message }`; we display a `react-hot-toast` notification and
 * return a short confirmation string back to the agent.
 *
 * Mount this hook anywhere under the <CopilotKitProvider>. It contributes
 * to `RunAgentInput.tools` on every request.
 */
export function useShowToastAction(): void {
  useFrontendTool({
    name: "showToast",
    description:
      "Display a transient toast notification in the user's browser. " +
      "Use for short status updates, acknowledgements, or to surface tool " +
      "results visually. Do NOT use this for confirmations.",
    parameters: PARAMS_SCHEMA,
    handler: async ({ level, message }) => {
      showToast(level, message);
      return `Displayed ${level} toast: "${message}"`;
    },
  });
}

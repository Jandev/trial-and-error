import { useHumanInTheLoop } from "@copilotkit/react-core/v2";
import { ToolCallStatus } from "@copilotkit/core";
import { z } from "zod";

import { ConfirmationDialog, type ConfirmationResponse } from "./ConfirmationDialog";

const PARAMS_SCHEMA = z.object({
  question: z.string().describe("The yes/no question to display to the user"),
});

/**
 * Registers the `askUserConfirmation` HITL frontend tool.
 *
 * The agent run pauses when the model calls this tool; CopilotKit renders
 * the {@link ConfirmationDialog}, and the run resumes when the user clicks
 * Yes or No. The literal string "yes" or "no" is sent back as the
 * tool result via the `respond` callback (only available in the
 * `Executing` status).
 */
export function useAskUserConfirmationAction(): void {
  useHumanInTheLoop({
    name: "askUserConfirmation",
    description:
      "Ask the user a yes/no question and wait for their answer. Use BEFORE " +
      "performing any action the user might want to reject (destructive " +
      "changes, sending data, calling tools with side-effects). " +
      "Returns 'yes' or 'no'.",
    parameters: PARAMS_SCHEMA,
    render: ({ args, status, respond }) => {
      const question =
        typeof args?.question === "string" && args.question.trim().length > 0
          ? args.question
          : "Are you sure?";
      const isExecuting = status === ToolCallStatus.Executing;
      return (
        <ConfirmationDialog
          question={question}
          disabled={!isExecuting}
          onRespond={(value: ConfirmationResponse) => {
            // `respond` is only defined when status === Executing.
            void respond?.(value);
          }}
        />
      );
    },
  });
}

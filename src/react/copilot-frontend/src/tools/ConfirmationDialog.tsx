import { useCallback, useEffect, useRef } from "react";

export type ConfirmationResponse = "yes" | "no";

interface ConfirmationDialogProps {
  question: string;
  /** Called with the user's choice. */
  onRespond: (response: ConfirmationResponse) => void;
  /** Whether the dialog can still accept input (false after a choice is made). */
  disabled?: boolean;
}

/**
 * Modal yes/no confirmation dialog.
 *
 * Keyboard:
 * - Enter  -> "yes"
 * - Escape -> "no"
 *
 * Focus is trapped inside the dialog while open; focus is moved to the
 * "Yes" button on mount.
 */
export function ConfirmationDialog({
  question,
  onRespond,
  disabled = false,
}: ConfirmationDialogProps) {
  const yesButtonRef = useRef<HTMLButtonElement | null>(null);
  const noButtonRef = useRef<HTMLButtonElement | null>(null);

  // Focus "Yes" on mount so keyboard users land in the dialog.
  useEffect(() => {
    yesButtonRef.current?.focus();
  }, []);

  const respond = useCallback(
    (value: ConfirmationResponse) => {
      if (disabled) return;
      onRespond(value);
    },
    [disabled, onRespond],
  );

  // Global key handling: Enter -> yes, Escape -> no.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (disabled) return;
      if (e.key === "Enter") {
        e.preventDefault();
        respond("yes");
      } else if (e.key === "Escape") {
        e.preventDefault();
        respond("no");
      } else if (e.key === "Tab") {
        // Trap focus between the two buttons.
        const active = document.activeElement;
        if (active === yesButtonRef.current && e.shiftKey === false) {
          e.preventDefault();
          noButtonRef.current?.focus();
        } else if (active === noButtonRef.current && e.shiftKey === true) {
          e.preventDefault();
          yesButtonRef.current?.focus();
        }
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [disabled, respond]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-dialog-question"
      data-testid="confirmation-dialog"
      style={{
        border: "1px solid #d1d5db",
        borderRadius: 8,
        padding: 16,
        margin: "8px 0",
        background: "#fff",
        boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
        maxWidth: 440,
      }}
    >
      <p id="confirmation-dialog-question" style={{ margin: "0 0 12px" }}>
        {question}
      </p>
      <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
        <button
          ref={noButtonRef}
          type="button"
          onClick={() => respond("no")}
          disabled={disabled}
          data-testid="confirmation-no"
        >
          No
        </button>
        <button
          ref={yesButtonRef}
          type="button"
          onClick={() => respond("yes")}
          disabled={disabled}
          data-testid="confirmation-yes"
          style={{ fontWeight: 600 }}
        >
          Yes
        </button>
      </div>
    </div>
  );
}

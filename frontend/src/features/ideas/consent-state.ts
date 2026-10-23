export type ConsentAction = { type: "accept"; key: string } | { type: "revoke" } | { type: "handoff"; from: string; to: string };
/** Creation-scoped consent is deliberately ephemeral; no browser persistence. */
export function consentReducer(accepted: string | null, action: ConsentAction): string | null {
  if (action.type === "accept") return action.key;
  if (action.type === "revoke") return null;
  return accepted === action.from ? action.to : accepted;
}

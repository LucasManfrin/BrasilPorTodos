"use client";
import { createContext, useContext, useReducer } from "react";
import { consentReducer } from "./consent-state";
import type { ConsentAction } from "./consent-state";
import type { ReactNode } from "react";

const ConsentContext = createContext<{ accepted: string | null; dispatch: (action: ConsentAction) => void } | null>(null);
/** In-memory only, scoped to this creation. AuthGate unmount clears consent at sign-out. */
export function GuidanceConsentProvider({ children }: { children: ReactNode }) {
  const [accepted, dispatch] = useReducer(consentReducer, null);
  return <ConsentContext.Provider value={{ accepted, dispatch }}>{children}</ConsentContext.Provider>;
}
export function useCreationConsent(key: string) {
  const session = useContext(ConsentContext);
  if (!session) throw new Error("Consentimento requer o painel autenticado.");
  const consent = session.accepted === key;
  return { consent, accept: () => session.dispatch({ type: "accept", key }), revoke: () => session.dispatch({ type: "revoke" }),
    handoff: (savedId: string) => { session.dispatch({ type: "handoff", from: key, to: savedId }); } };
}

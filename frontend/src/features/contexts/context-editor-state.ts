import type { ContextReviewInput } from "./types.ts";

/** Every reopened/saved target must be checked anew; never carry a previous attestation. */
export function blankReview(): Omit<ContextReviewInput, "expected_revision" | "decision"> {
  return {rationale:"",references_checked:false,scopes_checked:false,alternatives_checked:false,limitations_checked:false};
}

/** SPA navigation bypasses beforeunload. Same-page fragments and other tabs keep the editor. */
export function internalDestination(href: string, currentUrl: string, target = ""): string | null {
  if (target && target !== "_self") return null;
  try {
    const current = new URL(currentUrl), destination = new URL(href, current);
    if (destination.origin !== current.origin || destination.username || destination.password) return null;
    if (destination.pathname === current.pathname && destination.search === current.search) return null;
    return destination.pathname + destination.search + destination.hash;
  } catch { return null; }
}

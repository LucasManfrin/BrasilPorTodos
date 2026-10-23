import type { Envelope } from "../../lib/types";
import type { GraphRecord, GraphSummary } from "./types";

/** A valid exact record is independent of directory availability. Missing public
 * data never silently becomes a teaching scene on a requested version route. */
export function initialGraphState(initial: Envelope<GraphSummary[]> | null, validatedRecord: GraphRecord | null, id?: string, revision?: number) {
  if (validatedRecord) return { mode: "published" as const, record: validatedRecord, busy: false, error: "", target: { id: validatedRecord.id, revision: validatedRecord.revision } };
  if (id) return { mode: "published" as const, record: null, busy: true, error: "", target: { id, revision } };
  if (!initial) return { mode: "published" as const, record: null, busy: false, error: "Não foi possível consultar os mapas publicados.", target: null };
  if (initial.data.length) return { mode: "published" as const, record: null, busy: true, error: "", target: { id: initial.data[0].id, revision: initial.data[0].revision } };
  return { mode: "demo" as const, record: null, busy: false, error: "", target: null };
}

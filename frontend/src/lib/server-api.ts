import "server-only";
import type { Envelope } from "./types";

export async function serverApi<T>(path: string): Promise<Envelope<T> | null> {
  try {
    const base = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
    const response = await fetch(`${base}/api/v1/${path}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

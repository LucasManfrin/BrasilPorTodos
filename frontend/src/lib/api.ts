import type { Envelope } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

export async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<Envelope<T>> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  let response: Response;
  try {
    response = await fetch(`/api/v1/${path}`, {
      ...options,
      headers,
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      503,
      "API_UNAVAILABLE",
      "Não foi possível conectar. Tente novamente.",
    );
  }
  const body = await response.json();
  if (!response.ok)
    throw new ApiError(
      response.status,
      body.error?.code ?? "REQUEST_FAILED",
      body.error?.message ?? "Não foi possível concluir.",
    );
  return body;
}

export function csrfCookie() {
  return (
    document.cookie
      .split("; ")
      .find((item) => item.startsWith("bpt_csrf="))
      ?.split("=")
      .slice(1)
      .join("=") ?? ""
  );
}

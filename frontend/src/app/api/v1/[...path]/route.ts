import type { NextRequest } from "next/server";
import { proxyTimeoutMs } from "@/lib/proxy-timeout";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (path.some((part) => part === "." || part === ".." || part.includes("/")))
    return Response.json(
      { error: { code: "INVALID_PATH", message: "Caminho inválido." } },
      { status: 400 },
    );
  const base = process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000";
  const url = `${base}/api/v1/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const headers = new Headers();
  for (const name of [
    "Authorization",
    "Cookie",
    "Content-Type",
    "Origin",
    "X-CSRF-Token",
  ]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const upstream = await fetch(url, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method)
        ? undefined
        : await request.arrayBuffer(),
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(proxyTimeoutMs(request.method, path)),
    });
    const outputHeaders = new Headers({ "Cache-Control": "no-store" });
    for (const name of [
      "Content-Type",
      "X-Request-ID",
      "WWW-Authenticate",
      "Retry-After",
    ]) {
      const value = upstream.headers.get(name);
      if (value) outputHeaders.set(name, value);
    }
    for (const cookie of upstream.headers.getSetCookie())
      outputHeaders.append("Set-Cookie", cookie);
    return new Response(upstream.body, {
      status: upstream.status,
      headers: outputHeaders,
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "API_UNAVAILABLE",
          message:
            "O serviço está temporariamente indisponível. Tente novamente.",
        },
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};

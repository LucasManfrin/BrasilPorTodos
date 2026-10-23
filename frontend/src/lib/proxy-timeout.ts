// Keep the proxy budget above the maximum provider timeout (45s), plus API overhead.
export function proxyTimeoutMs(method: string, path: readonly string[]): number {
  return method === "POST" && path.length === 2 && path[0] === "guidance" && path[1] === "organize"
    ? 60_000
    : 15_000;
}

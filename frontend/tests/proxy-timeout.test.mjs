import test from "node:test";
import assert from "node:assert/strict";
import { proxyTimeoutMs } from "../src/lib/proxy-timeout.ts";

test("guidance proxy leaves time for the largest supported provider budget and API cleanup", () => {
  assert.ok(proxyTimeoutMs("POST", ["guidance", "organize"]) >= 45_000 + 10_000);
});

test("long guidance requests do not relax budgets for reads or unrelated writes", () => {
  for (const [method, path] of [["GET",["guidance","organize"]],["POST",["guidance","history"]],["POST",["ideas"]],["POST",["guidance","organize","extra"]]]) {
    assert.equal(proxyTimeoutMs(method,path),15_000);
  }
});

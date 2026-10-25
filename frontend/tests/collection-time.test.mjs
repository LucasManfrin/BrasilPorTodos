import test from "node:test";
import assert from "node:assert/strict";
import { collectionTimestamp } from "../src/lib/collection-time.ts";
import { date } from "../src/lib/format.ts";

test("collection timestamps use Sao Paulo, including the previous local day", () => {
  assert.equal(collectionTimestamp("2026-10-15T02:47:43.719981+00:00"), "14/10/2026 às 23:47 (São Paulo)");
});
test("a midnight Sao Paulo collection is midnight, without 24-hour notation", () => {
  assert.equal(collectionTimestamp("2026-10-25T03:00:00Z"), "25/10/2026 às 00:00 (São Paulo)");
});
test("an explicit equivalent offset represents the same collection instant", () => {
  assert.equal(collectionTimestamp("2026-10-14T23:47:00-03:00"), collectionTimestamp("2026-10-15T02:47:00Z"));
});
test("bad timestamps and unknown timezones fail softly", () => {
  assert.equal(collectionTimestamp("invalid"), "horário indisponível");
  assert.equal(collectionTimestamp("2026-10-25T03:00:00Z", "Invalid/Timezone"), "horário indisponível");
});
test("calendar reference dates keep their original date rather than shifting timezone", () => {
  assert.equal(date("2026-08-01"), "01/08/2026");
});

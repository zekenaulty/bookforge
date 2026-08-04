import assert from "node:assert/strict";
import test from "node:test";
import { normalizeReaderTurn, readerTurnNumbers, resolveReaderNavigation } from "../lib/reader-navigation.ts";

const turns = [{ turnNumber: 5 }, { turnNumber: 1 }, { turnNumber: 3 }, { turnNumber: 3 }];

test("normalizes reader positions against real section numbers", () => {
  assert.deepEqual(readerTurnNumbers(turns), [1, 3, 5]);
  assert.equal(normalizeReaderTurn(turns, 4), 3);
  assert.equal(normalizeReaderTurn(turns, 0), 1);
});

test("resolves first, previous, next, and last through one navigation path", () => {
  assert.deepEqual(resolveReaderNavigation(turns, 3, "first", true), { kind: "move", turnNumber: 1 });
  assert.deepEqual(resolveReaderNavigation(turns, 3, "previous", true), { kind: "move", turnNumber: 1 });
  assert.deepEqual(resolveReaderNavigation(turns, 3, "next", true), { kind: "move", turnNumber: 5 });
  assert.deepEqual(resolveReaderNavigation(turns, 3, "last", true), { kind: "move", turnNumber: 5 });
});

test("next and last write only at the current active edge", () => {
  assert.deepEqual(resolveReaderNavigation(turns, 5, "next", true), { kind: "write", turnNumber: 5 });
  assert.deepEqual(resolveReaderNavigation(turns, 5, "last", true), { kind: "write", turnNumber: 5 });
  assert.deepEqual(resolveReaderNavigation(turns, 5, "next", false), { kind: "stay", turnNumber: 5 });
  assert.deepEqual(resolveReaderNavigation([{ turnNumber: 1 }], 1, "last", true), { kind: "write", turnNumber: 1 });
});

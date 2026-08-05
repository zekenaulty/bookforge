import assert from "node:assert/strict";
import test from "node:test";
import { regenerationTargetsCurrentTurn, storyTailMatches } from "../lib/story-revision.ts";

test("a regeneration candidate is valid only for the exact source turn revision", () => {
  const intent = { intendedTurnNumber: 12, regenerationOfTurnId: "turn-12-a" };
  assert.equal(regenerationTargetsCurrentTurn(intent, { id: "turn-12-a", turnNumber: 12 }), true);
  assert.equal(regenerationTargetsCurrentTurn(intent, { id: "turn-12-b", turnNumber: 12 }), false);
  assert.equal(regenerationTargetsCurrentTurn(intent, { id: "turn-13", turnNumber: 13 }), false);
  assert.equal(regenerationTargetsCurrentTurn({}, { id: "turn-12-a", turnNumber: 12 }), false);
});

test("a writer predecessor check binds to both tail number and immutable turn id", () => {
  const expected = { turnNumber: 12, turnId: "turn-12-a" };
  assert.equal(storyTailMatches(expected, { turnNumber: 12, turnId: "turn-12-a" }), true);
  assert.equal(storyTailMatches(expected, { turnNumber: 12, turnId: "turn-12-regenerated" }), false);
  assert.equal(storyTailMatches(expected, { turnNumber: 13, turnId: "turn-13" }), false);
});

import assert from "node:assert/strict";
import test from "node:test";

import { splitLocalNarration } from "../lib/local-voice-types.ts";

test("local narration chunks preserve sequence, punctuation, and source offsets", () => {
  const text = "Dr. Vale waited.  Then she whispered: this door remembers every visitor, even the ones we forgot.\n\nNo one answered.";
  const chunks = splitLocalNarration(text);

  assert.ok(chunks.length >= 3);
  assert.deepEqual(chunks.map((chunk) => chunk.sequence), chunks.map((_, index) => index));
  for (const chunk of chunks) {
    assert.equal(text.slice(chunk.start, chunk.end), chunk.text);
    assert.ok(chunk.text.length <= 260);
  }
  assert.ok(chunks[0].text.includes("Dr. Vale"), "honorifics must not become isolated chunks");
  assert.ok(chunks.some((chunk) => chunk.text.endsWith(".")), "sentence punctuation must remain available to Kokoro");
});

test("local narration uses bounded clause chunks for long prose", () => {
  const text = `${"A quiet corridor stretched beyond them, ".repeat(12)}and at last it ended.`;
  const chunks = splitLocalNarration(text);

  assert.ok(chunks.length > 1);
  assert.ok(chunks.every((chunk) => chunk.text.length <= 260));
  assert.equal(chunks.map((chunk) => chunk.text).join(" ").replace(/\s+/g, " "), text.replace(/\s+/g, " "));
});

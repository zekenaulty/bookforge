import assert from "node:assert/strict";
import test from "node:test";
import { artAttemptObjectKey } from "../lib/art-storage.ts";

test("art storage keys are immutable per model and owning lease", () => {
  const base = { storyId: "story", assetId: "cover", renderVersion: "cover" };
  const first = artAttemptObjectKey({ ...base, model: "gemini-3-pro-image", lease: "lease-a" });
  const otherModel = artAttemptObjectKey({ ...base, model: "gemini-3.1-flash-image", lease: "lease-a" });
  const otherLease = artAttemptObjectKey({ ...base, model: "gemini-3-pro-image", lease: "lease-b" });
  assert.notEqual(first, otherModel);
  assert.notEqual(first, otherLease);
  assert.match(first, /gemini-3-pro-image\/lease-a\/image$/);
});

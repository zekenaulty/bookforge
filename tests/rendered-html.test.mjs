import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("server-renders the private living-fiction library", async () => {
  const [page, client, layout] = await Promise.all([
    readFile(new URL("app/page.tsx", root), "utf8"),
    readFile(new URL("app/KotobaApp.tsx", root), "utf8"),
    readFile(new URL("app/layout.tsx", root), "utf8"),
  ]);
  assert.match(page, /<KotobaApp/);
  assert.match(client, /kotoba-no-kaijiba/);
  assert.match(client, /Stories waiting for you/);
  assert.match(client, /New story/);
  assert.match(layout, /private living-fiction library/i);
  assert.doesNotMatch(`${page}${client}${layout}`, /codex-preview|react-loading-skeleton|Starter Project/);
});

test("keeps runtime writing and persistence wired", async () => {
  const [route, hosting, page, layout, client] = await Promise.all([
    readFile(new URL("app/api/app/route.ts", root), "utf8"),
    readFile(new URL(".openai/hosting.json", root), "utf8"),
    readFile(new URL("app/page.tsx", root), "utf8"),
    readFile(new URL("app/layout.tsx", root), "utf8"),
    readFile(new URL("app/KotobaApp.tsx", root), "utf8"),
  ]);
  assert.match(hosting, /"d1":\s*"DB"/);
  assert.match(route, /action === "continueStory"/);
  assert.match(route, /generation_jobs/);
  assert.match(route, /maybeCheckpoint/);
  assert.match(client, /Auto write next/i);
  assert.match(client, /Note to the author/i);
  assert.match(page, /<KotobaApp/);
  assert.match(layout, /private living-fiction library/i);
  assert.doesNotMatch(client, /chat bubble|chat message/i);
});

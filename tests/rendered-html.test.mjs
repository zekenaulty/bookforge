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
  const [route, hosting, page, layout, client, ai, database, pdf] = await Promise.all([
    readFile(new URL("app/api/app/route.ts", root), "utf8"),
    readFile(new URL(".openai/hosting.json", root), "utf8"),
    readFile(new URL("app/page.tsx", root), "utf8"),
    readFile(new URL("app/layout.tsx", root), "utf8"),
    readFile(new URL("app/KotobaApp.tsx", root), "utf8"),
    readFile(new URL("lib/ai.ts", root), "utf8"),
    readFile(new URL("lib/app-db.ts", root), "utf8"),
    readFile(new URL("lib/story-pdf.ts", root), "utf8"),
  ]);
  assert.match(hosting, /"d1":\s*"DB"/);
  assert.match(hosting, /"r2":\s*"ART"/);
  assert.match(route, /action === "continueStory"/);
  assert.match(route, /generation_jobs/);
  assert.match(route, /runBackgroundJob/);
  assert.match(route, /context_reconcile/);
  assert.match(route, /queueArt/);
  assert.match(database, /operation_logs/);
  assert.match(database, /background_jobs/);
  assert.match(database, /context_snapshots/);
  assert.match(database, /art_assets/);
  assert.match(ai, /MAX_ATTEMPTS = 3/);
  assert.match(ai, /TRANSPORT_TIMEOUT_MS = 10 \* 60 \* 1000/);
  assert.match(ai, /category: "parser"|"parser", true/);
  assert.match(pdf, /%PDF-1\.4/);
  assert.match(pdf, /DCTDecode/);
  assert.match(client, /Auto write next/i);
  assert.match(client, /High-quality local voice/i);
  assert.match(client, /device voice instead/i);
  assert.match(client, /Note to the author/i);
  assert.match(client, /Story gallery/i);
  assert.match(client, /Download illustrated PDF/i);
  assert.match(client, /Generation log/i);
  assert.match(page, /<KotobaApp/);
  assert.match(layout, /private living-fiction library/i);
  assert.doesNotMatch(client, /chat bubble|chat message/i);
});

test("keeps neural narration local, lazy, and off the UI thread", async () => {
  const [client, player, worker, voiceTypes, manifest, vite] = await Promise.all([
    readFile(new URL("app/KotobaApp.tsx", root), "utf8"),
    readFile(new URL("lib/local-voice.ts", root), "utf8"),
    readFile(new URL("lib/local-voice-worker.ts", root), "utf8"),
    readFile(new URL("lib/local-voice-types.ts", root), "utf8"),
    readFile(new URL("package.json", root), "utf8"),
    readFile(new URL("vite.config.ts", root), "utf8"),
  ]);
  assert.match(manifest, /"kokoro-js": "1\.2\.1"/);
  assert.match(client, /kotoba-high-quality-local-voice/);
  assert.match(client, /Kokoro 82M q8/);
  assert.match(client, /Local voice · English/);
  assert.match(client, /speechSynthesis/);
  assert.match(player, /voice: LocalVoiceId/);
  assert.match(voiceTypes, /English \(US\)/);
  assert.match(voiceTypes, /English \(UK\)/);
  assert.match(voiceTypes, /bf_emma/);
  assert.match(player, /new Worker\(new URL/);
  assert.match(player, /navigator\.storage\.persist/);
  assert.match(worker, /KokoroTTS\.from_pretrained/);
  assert.match(worker, /dtype: "q8"/);
  assert.match(worker, /"webgpu"/);
  assert.match(worker, /"wasm"/);
  assert.match(worker, /useBrowserCache = true/);
  assert.match(worker, /wasmPaths = ORT_WASM_CDN/);
  assert.match(vite, /omit-pinned-onnx-wasm/);
  assert.doesNotMatch(worker, /API[_ -]?key/i);
  assert.doesNotMatch(worker, /\.onnx["']/i);
});

test("generates resumable story art with selectable Google Nano Banana models", async () => {
  const [client, route, generator, models, hosting] = await Promise.all([
    readFile(new URL("app/KotobaApp.tsx", root), "utf8"),
    readFile(new URL("app/api/app/route.ts", root), "utf8"),
    readFile(new URL("lib/google-image.ts", root), "utf8"),
    readFile(new URL("lib/image-models.ts", root), "utf8"),
    readFile(new URL(".openai/hosting.json", root), "utf8"),
  ]);
  assert.match(client, /Google image model/);
  assert.match(client, /Google Nano Banana generates art/);
  assert.match(models, /gemini-3\.1-flash-image/);
  assert.match(models, /gemini-3\.1-flash-lite-image/);
  assert.match(models, /gemini-3-pro-image/);
  assert.match(models, /gemini-2\.5-flash-image/);
  assert.match(generator, /:generateContent/);
  assert.match(generator, /responseModalities: \["IMAGE"\]/);
  assert.match(generator, /responseFormat/);
  assert.match(generator, /TRANSPORT_TIMEOUT_MS = 10 \* 60 \* 1000/);
  assert.match(route, /bucket\.put/);
  assert.match(route, /status='Ready'/);
  assert.match(route, /GoogleImageFailure/);
  assert.match(hosting, /"r2":\s*"ART"/);
  assert.doesNotMatch(generator, /Buffer\.from/);
});

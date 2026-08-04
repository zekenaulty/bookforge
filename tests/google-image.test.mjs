import assert from "node:assert/strict";
import test from "node:test";
import { generateGoogleImage, GoogleImageFailure } from "../lib/google-image.ts";

const originalFetch = globalThis.fetch;
const originalKey = process.env.GEMINI_API_KEY;
const originalUrl = process.env.GEMINI_IMAGE_API_URL;
const originalGenericUrl = process.env.GEMINI_API_URL;
process.env.GEMINI_API_KEY = "test-key-not-a-secret";
process.env.GEMINI_IMAGE_API_URL = "https://gemini.invalid/v1";

test.after(() => {
  globalThis.fetch = originalFetch;
  if (originalKey == null) delete process.env.GEMINI_API_KEY; else process.env.GEMINI_API_KEY = originalKey;
  if (originalUrl == null) delete process.env.GEMINI_IMAGE_API_URL; else process.env.GEMINI_IMAGE_API_URL = originalUrl;
  if (originalGenericUrl == null) delete process.env.GEMINI_API_URL; else process.env.GEMINI_API_URL = originalGenericUrl;
});

test("sends the selected Nano Banana model and requested aspect ratio", async () => {
  globalThis.fetch = async (url, init) => {
    assert.equal(url, "https://gemini.invalid/v1/models/gemini-3-pro-image:generateContent");
    assert.equal(init.headers["x-goog-api-key"], "test-key-not-a-secret");
    const body = JSON.parse(init.body);
    assert.deepEqual(body.generationConfig.responseFormat, { image: { aspectRatio: "2:3", imageSize: "1K" } });
    return Response.json({ candidates: [{ content: { parts: [{ inlineData: { data: btoa("cover"), mimeType: "image/jpeg" } }] } }] });
  };
  const image = await generateGoogleImage({ prompt: "cover", model: "gemini-3-pro-image", aspectRatio: "2:3" });
  assert.equal(new TextDecoder().decode(image.bytes), "cover");
  assert.equal(image.model, "gemini-3-pro-image");
});

test("falls back when an endpoint rejects the responseFormat aspect-ratio schema", async () => {
  let attempts = 0;
  globalThis.fetch = async (_url, init) => {
    attempts += 1;
    const body = JSON.parse(init.body);
    if (attempts === 1) {
      assert.deepEqual(body.generationConfig.responseFormat, { image: { aspectRatio: "2:3", imageSize: "1K" } });
      return new Response(JSON.stringify({ error: {
        status: "INVALID_ARGUMENT",
        message: `Invalid value at 'generation_config.response_format.image.aspect_ratio' (type.googleapis.com/google.ai.generativelanguage.v1beta.ImageResponseFormat.AspectRatio), "2:3" Invalid value at 'generation_config.response_format'.`,
      } }), { status: 400 });
    }
    assert.equal(body.generationConfig.responseFormat, undefined);
    assert.deepEqual(body.generationConfig.imageConfig, { aspectRatio: "2:3", imageSize: "1K" });
    return Response.json({ candidates: [{ content: { parts: [{ inlineData: { data: btoa("compatible"), mimeType: "image/png" } }] } }] });
  };
  const image = await generateGoogleImage({ prompt: "cover", model: "gemini-3.1-flash-image", aspectRatio: "2:3" });
  assert.equal(attempts, 2);
  assert.equal(new TextDecoder().decode(image.bytes), "compatible");
});

test("keeps image generation on the documented v1 endpoint when text uses v1beta", async () => {
  delete process.env.GEMINI_IMAGE_API_URL;
  process.env.GEMINI_API_URL = "https://text-only.invalid/v1beta";
  try {
    globalThis.fetch = async (url) => {
      assert.equal(url, "https://generativelanguage.googleapis.com/v1/models/gemini-3.1-flash-image:generateContent");
      return Response.json({ candidates: [{ content: { parts: [{ inlineData: { data: btoa("v1"), mimeType: "image/png" } }] } }] });
    };
    const image = await generateGoogleImage({ prompt: "cover", aspectRatio: "2:3" });
    assert.equal(new TextDecoder().decode(image.bytes), "v1");
  } finally {
    process.env.GEMINI_IMAGE_API_URL = "https://gemini.invalid/v1";
    if (originalGenericUrl == null) delete process.env.GEMINI_API_URL; else process.env.GEMINI_API_URL = originalGenericUrl;
  }
});

test("retries a recoverable parser failure inside one ten-minute request window", async () => {
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    if (attempts === 1) return new Response("not-json", { status: 200 });
    return Response.json({ candidates: [{ content: { parts: [{ inlineData: { data: btoa("retry"), mimeType: "image/png" } }] } }] });
  };
  const image = await generateGoogleImage({ prompt: "cover", aspectRatio: "2:3" });
  assert.equal(attempts, 2);
  assert.equal(new TextDecoder().decode(image.bytes), "retry");
});

test("ignores thought images and saves the last final image", async () => {
  globalThis.fetch = async () => Response.json({ candidates: [{ content: { parts: [
    { thought: true, inlineData: { data: btoa("thought"), mimeType: "image/jpeg" } },
    { inlineData: { data: btoa("first"), mimeType: "image/jpeg" } },
    { inlineData: { data: btoa("last"), mimeType: "image/webp" } },
  ] } }] });
  const image = await generateGoogleImage({ prompt: "scene", aspectRatio: "16:9" });
  assert.equal(new TextDecoder().decode(image.bytes), "last");
  assert.equal(image.mimeType, "image/webp");
});

test("rejects unsupported image formats and redacts provider credentials", async () => {
  globalThis.fetch = async () => Response.json({ candidates: [{ content: { parts: [{ inlineData: { data: btoa("x"), mimeType: "image/gif" } }] } }] });
  await assert.rejects(() => generateGoogleImage({ prompt: "cover", aspectRatio: "2:3" }), (error) => error instanceof GoogleImageFailure && error.category === "image_mime");

  globalThis.fetch = async () => new Response(JSON.stringify({ error: { status: "INVALID_ARGUMENT", message: "token=super-secret malformed request" } }), { status: 400 });
  await assert.rejects(() => generateGoogleImage({ prompt: "cover", aspectRatio: "2:3" }), (error) => {
    assert.equal(error.category, "http_400");
    assert.match(error.message, /token=\[redacted\]/);
    assert.doesNotMatch(error.message, /super-secret/);
    return true;
  });
});

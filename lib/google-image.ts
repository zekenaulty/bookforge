import { DEFAULT_GOOGLE_IMAGE_MODEL, isGoogleImageModel, type GoogleImageModel } from "./image-models";

const TRANSPORT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_BASE64_LENGTH = 40 * 1024 * 1024;
const SUPPORTED_MIME_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

type GenerateContentPayload = {
  promptFeedback?: { blockReason?: unknown };
  candidates?: Array<{
    finishReason?: unknown;
    content?: { parts?: Array<{ inlineData?: { data?: unknown; mimeType?: unknown } }> };
  }>;
};

export class GoogleImageFailure extends Error {
  constructor(message: string, public category: string, public recoverable: boolean, public retryAfterMs = 0) {
    super(message);
  }
}

export function selectedGoogleImageModel(value: unknown): GoogleImageModel {
  if (isGoogleImageModel(value)) return value;
  if (isGoogleImageModel(process.env.GOOGLE_IMAGE_MODEL)) return process.env.GOOGLE_IMAGE_MODEL;
  return DEFAULT_GOOGLE_IMAGE_MODEL;
}

export async function generateGoogleImage(input: { prompt: string; model?: unknown; aspectRatio: "2:3" | "16:9" }) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new GoogleImageFailure("Google image generation is not configured.", "configuration", false);
  const model = selectedGoogleImageModel(input.model);
  const base = (process.env.GEMINI_IMAGE_API_URL || process.env.GEMINI_API_URL || "https://generativelanguage.googleapis.com/v1beta").replace(/\/$/, "");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TRANSPORT_TIMEOUT_MS);

  try {
    const responseFormat = model === "gemini-2.5-flash-image"
      ? { image: { aspectRatio: input.aspectRatio } }
      : { image: { aspectRatio: input.aspectRatio, imageSize: "1K" } };
    const response = await fetch(`${base}/models/${encodeURIComponent(model)}:generateContent`, {
      method: "POST",
      signal: controller.signal,
      headers: { "content-type": "application/json", "x-goog-api-key": apiKey },
      body: JSON.stringify({
        contents: [{ parts: [{ text: input.prompt }] }],
        generationConfig: { responseModalities: ["IMAGE"], responseFormat },
      }),
    });
    if (!response.ok) throw imageHttpFailure(response);
    const payload = await response.json() as GenerateContentPayload;
    const inline = payload.candidates?.flatMap((candidate) => candidate.content?.parts || [])
      .map((part) => part.inlineData).find((item) => typeof item?.data === "string");
    if (!inline || typeof inline.data !== "string") {
      const blockReason = payload.promptFeedback?.blockReason || payload.candidates?.find((candidate) => candidate.finishReason)?.finishReason;
      if (typeof blockReason === "string" && /safety|block|prohibited/i.test(blockReason)) {
        throw new GoogleImageFailure("Google declined this art brief under its safety policy.", "safety", false);
      }
      throw new GoogleImageFailure("Google returned no image for this art brief.", "empty_image", true);
    }
    const mimeType = typeof inline.mimeType === "string" && SUPPORTED_MIME_TYPES.has(inline.mimeType) ? inline.mimeType : "image/jpeg";
    return { bytes: decodeImageData(inline.data), mimeType, model };
  } catch (error) {
    if (error instanceof GoogleImageFailure) throw error;
    if (controller.signal.aborted) throw new GoogleImageFailure("The Google image request timed out after ten minutes.", "timeout", true);
    throw new GoogleImageFailure(error instanceof Error ? error.message : "The Google image transport was interrupted.", "transport", true);
  } finally {
    clearTimeout(timeout);
  }
}

function decodeImageData(value: string) {
  const clean = value.replace(/^data:image\/[a-z0-9.+-]+;base64,/i, "").replace(/\s/g, "");
  if (!clean || clean.length > MAX_BASE64_LENGTH || !/^[A-Za-z0-9+/]*={0,2}$/.test(clean)) {
    throw new GoogleImageFailure("Google returned invalid or oversized image data.", "image_payload", true);
  }
  try {
    const binary = atob(clean);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
    if (!bytes.length) throw new Error("empty");
    return bytes;
  } catch {
    throw new GoogleImageFailure("Google returned unreadable image data.", "image_payload", true);
  }
}

function imageHttpFailure(response: Response) {
  const recoverable = [408, 409, 425, 429, 500, 502, 503, 504].includes(response.status);
  const retryAfter = Number(response.headers.get("retry-after") || 0);
  return new GoogleImageFailure(`Google image generation returned HTTP ${response.status}.`, `http_${response.status}`, recoverable,
    Number.isFinite(retryAfter) ? Math.min(retryAfter * 1000, 60_000) : 0);
}

import { DEFAULT_GOOGLE_IMAGE_MODEL, isGoogleImageModel, type GoogleImageModel } from "./image-models.ts";

const TRANSPORT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_HTTP_ATTEMPTS = 3;
const MAX_BASE64_LENGTH = 40 * 1024 * 1024;
const SUPPORTED_MIME_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

type GenerateContentPayload = {
  promptFeedback?: { blockReason?: unknown };
  candidates?: Array<{
    finishReason?: unknown;
    content?: { parts?: Array<{ inlineData?: { data?: unknown; mimeType?: unknown }; thought?: unknown }> };
  }>;
};

export type GoogleImage = { bytes: Uint8Array; mimeType: string; model: GoogleImageModel };

export class GoogleImageFailure extends Error {
  category: string;
  recoverable: boolean;
  retryAfterMs: number;
  restartRequired: boolean;

  constructor(message: string, category: string, recoverable: boolean, retryAfterMs = 0, restartRequired = false) {
    super(message);
    this.name = "GoogleImageFailure";
    this.category = category;
    this.recoverable = recoverable;
    this.retryAfterMs = retryAfterMs;
    this.restartRequired = restartRequired;
  }
}

export function selectedGoogleImageModel(value: unknown): GoogleImageModel {
  if (isGoogleImageModel(value)) return value;
  if (isGoogleImageModel(process.env.GOOGLE_IMAGE_MODEL)) return process.env.GOOGLE_IMAGE_MODEL;
  return DEFAULT_GOOGLE_IMAGE_MODEL;
}

export async function generateGoogleImage(input: { prompt: string; model?: unknown; aspectRatio: "2:3" | "16:9" }): Promise<GoogleImage> {
  const model = selectedGoogleImageModel(input.model);
  const responseFormat = model === "gemini-2.5-flash-image"
    ? { image: { aspectRatio: input.aspectRatio } }
    : { image: { aspectRatio: input.aspectRatio, imageSize: "1K" } };
  const url = `${googleBase()}/models/${encodeURIComponent(model)}:generateContent`;
  const request = (legacyImageConfig = false) => googleJson<GenerateContentPayload>(url, {
    method: "POST",
    headers: googleHeaders(),
    body: JSON.stringify({
      contents: [{ parts: [{ text: input.prompt }] }],
      generationConfig: legacyImageConfig
        ? { responseModalities: ["IMAGE"], imageConfig: responseFormat.image }
        : { responseModalities: ["IMAGE"], responseFormat },
    }),
  }, TRANSPORT_TIMEOUT_MS, "generate_content");
  let payload: GenerateContentPayload;
  try {
    payload = await request();
  } catch (error) {
    // v1beta briefly exposed responseFormat with enum-shaped fields while imageConfig
    // retained string ratios. Keep this narrow compatibility retry for configured
    // proxies/endpoints that have not yet adopted the v1 responseFormat schema.
    if (!(error instanceof GoogleImageFailure) || error.category !== "http_400"
      || !/generation_config\.response_format|response[_ ]format.*aspect[_ ]ratio/i.test(error.message)) throw error;
    console.warn("[kotoba-google-image] responseFormat was rejected; retrying with the compatible imageConfig schema.");
    payload = await request(true);
  }
  const images = payload.candidates?.flatMap((candidate) => candidate.content?.parts || [])
    .filter((part) => part.thought !== true)
    .map((part) => part.inlineData)
    .filter((item): item is { data: string; mimeType?: unknown } => typeof item?.data === "string") || [];
  const inline = images.at(-1);
  if (!inline) {
    const blockReason = payload.promptFeedback?.blockReason || payload.candidates?.find((candidate) => candidate.finishReason)?.finishReason;
    if (typeof blockReason === "string" && /safety|block|prohibited/i.test(blockReason)) {
      throw new GoogleImageFailure("Google declined this art brief under its safety policy.", "safety", false);
    }
    throw new GoogleImageFailure("Google returned no final image for this art brief.", "empty_image", true);
  }
  return decodeGoogleImage(inline.data, inline.mimeType, model);
}

function decodeGoogleImage(data: string, rawMimeType: unknown, model: GoogleImageModel): GoogleImage {
  const mimeType = typeof rawMimeType === "string" && rawMimeType ? rawMimeType : "image/jpeg";
  if (!SUPPORTED_MIME_TYPES.has(mimeType)) {
    throw new GoogleImageFailure(`Google returned an unsupported image format (${safeMimeType(mimeType)}).`, "image_mime", true);
  }
  return { bytes: decodeImageData(data), mimeType, model };
}

async function googleJson<T>(url: string, init: RequestInit, timeoutMs: number, operation: string): Promise<T> {
  const deadline = Date.now() + timeoutMs;
  let lastFailure: GoogleImageFailure | null = null;
  for (let attempt = 1; attempt <= MAX_HTTP_ATTEMPTS; attempt += 1) {
    const remaining = deadline - Date.now();
    if (remaining <= 0) break;
    const controller = new AbortController();
    const attemptsLeft = MAX_HTTP_ATTEMPTS - attempt + 1;
    const attemptTimeout = Math.max(1_000, Math.floor(remaining / attemptsLeft));
    const timeout = setTimeout(() => controller.abort(), attemptTimeout);
    try {
      const response = await fetch(url, { ...init, signal: controller.signal });
      if (!response.ok) throw await imageHttpFailure(response);
      try {
        return await response.json() as T;
      } catch {
        throw new GoogleImageFailure("Google returned an unreadable image response.", `${operation}_parser`, true);
      }
    } catch (error) {
      const failure = error instanceof GoogleImageFailure ? error : controller.signal.aborted
        ? new GoogleImageFailure("The Google image request timed out within its ten-minute request window.", `${operation}_timeout`, true)
        : new GoogleImageFailure("The Google image transport was interrupted.", `${operation}_transport`, true);
      lastFailure = failure;
      if (!failure.recoverable || attempt === MAX_HTTP_ATTEMPTS) throw failure;
      console.warn(`[kotoba-google-image] ${operation} attempt ${attempt} will retry after ${failure.category}.`);
      const delay = Math.max(failure.retryAfterMs, 500 * 2 ** (attempt - 1));
      if (Date.now() + delay >= deadline) throw failure;
      await new Promise((resolve) => setTimeout(resolve, delay));
    } finally {
      clearTimeout(timeout);
    }
  }
  throw lastFailure || new GoogleImageFailure("The Google image request timed out.", `${operation}_timeout`, true);
}

function googleBase() {
  // Image generation's documented responseFormat contract is on v1. Do not
  // inherit GEMINI_API_URL: that setting may intentionally keep text models on
  // v1beta and caused valid portrait ratios to be parsed as response enums.
  return (process.env.GEMINI_IMAGE_API_URL || "https://generativelanguage.googleapis.com/v1").replace(/\/$/, "");
}

function googleHeaders() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) throw new GoogleImageFailure("Google image generation is not configured.", "configuration", false);
  return { "content-type": "application/json", "x-goog-api-key": apiKey };
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

async function imageHttpFailure(response: Response) {
  const recoverable = [408, 409, 425, 429, 500, 502, 503, 504].includes(response.status);
  const retryAfter = Number(response.headers.get("retry-after") || 0);
  let provider = "";
  try {
    const text = (await response.text()).slice(0, 4096);
    const parsed = JSON.parse(text) as { error?: unknown };
    provider = safeProviderError(parsed.error);
  } catch { /* status and category remain sufficient */ }
  const detail = provider ? `: ${provider}` : ".";
  return new GoogleImageFailure(`Google image generation returned HTTP ${response.status}${detail}`, `http_${response.status}`, recoverable,
    Number.isFinite(retryAfter) ? Math.min(retryAfter * 1000, 60_000) : 0);
}

function safeProviderError(value: unknown) {
  const raw = typeof value === "string" ? value : value && typeof value === "object"
    ? (() => {
      const error = value as { code?: unknown; status?: unknown; message?: unknown };
      const code = typeof error.status === "string" ? error.status : typeof error.code === "string" ? error.code : "";
      const message = typeof error.message === "string" ? error.message : "";
      return `${code}${code && message ? " - " : ""}${message}`;
    })()
    : "";
  return raw.replace(/(key|token|secret)\s*[=:]\s*[^\s,;]+/gi, "$1=[redacted]").replace(/\s+/g, " ").trim().slice(0, 240);
}

function safeMimeType(value: string) {
  return /^[a-z0-9.+-]+\/[a-z0-9.+-]+$/i.test(value) ? value : "unknown";
}

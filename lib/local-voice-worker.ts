/// <reference lib="webworker" />

import { env as transformersEnv } from "@huggingface/transformers";
import { KokoroTTS } from "kokoro-js";
import { isLocalVoiceId, type LocalNarrationChunk, type LocalVoiceBackend, type LocalVoiceRequest, type LocalVoiceResponse } from "./local-voice-types";

const MODEL_ID = "onnx-community/Kokoro-82M-v1.0-ONNX";
const ORT_WASM_CDN = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0-dev.20250409-89f8206ba4/dist/";
const MODEL_CACHE = "transformers-cache";
const VOICE_CACHE = "kokoro-voices";
const GENERATION_ATTEMPTS = 2;
const scope = self as DedicatedWorkerGlobalScope;

function isKokoroAssetUrl(url: string) {
  try {
    return decodeURIComponent(url).includes("onnx-community/Kokoro-82M-v1.0-ONNX");
  } catch {
    return url.includes("onnx-community/Kokoro-82M-v1.0-ONNX");
  }
}

type ProductionJob = {
  id: string;
  chunks: LocalNarrationChunk[];
  voice: Extract<LocalVoiceRequest, { type: "speak" }>["voice"];
  speed: number;
  nextIndex: number;
  producing: boolean;
};

let engine: KokoroTTS | null = null;
let backend: LocalVoiceBackend | undefined;
let preparing: Promise<KokoroTTS> | null = null;
let activeJob: ProductionJob | null = null;
let pumpPromise: Promise<void> | null = null;
let wakeProducer: (() => void) | null = null;

transformersEnv.allowLocalModels = false;
transformersEnv.allowRemoteModels = true;
transformersEnv.useBrowserCache = true;
const wasmBackend = transformersEnv.backends.onnx.wasm;
if (wasmBackend) wasmBackend.wasmPaths = ORT_WASM_CDN;

// Sites responses are not cross-origin isolated, so ORT cannot use shared-memory
// threading. Inference stays responsive because this entire module is a worker.
if (wasmBackend) wasmBackend.numThreads = 1;

function post(message: LocalVoiceResponse, transfer: Transferable[] = []) {
  scope.postMessage(message, transfer);
}

function progressDetail(value: unknown) {
  if (!value || typeof value !== "object") return {};
  const item = value as { status?: unknown; progress?: unknown; file?: unknown };
  return {
    progress: typeof item.progress === "number" ? Math.max(0, Math.min(100, item.progress)) : undefined,
    detail: typeof item.file === "string" ? item.file.split("/").at(-1) : typeof item.status === "string" ? item.status : undefined,
  };
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Local voice generation failed.";
}

async function canUseWebGpu() {
  const gpu = (navigator as Navigator & { gpu?: { requestAdapter: () => Promise<unknown> } }).gpu;
  if (!gpu) return false;
  try {
    return Boolean(await gpu.requestAdapter());
  } catch {
    return false;
  }
}

async function clearDownloadedAssets() {
  if (!("caches" in scope)) return;
  const clearMatchingEntries = async (cacheName: string) => {
    const names = await caches.keys();
    if (!names.includes(cacheName)) return;
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    await Promise.allSettled(requests
      .filter((request) => isKokoroAssetUrl(request.url))
      .map((request) => cache.delete(request)));
  };
  // Transformers.js shares its cache with any other local Hugging Face model.
  // Remove only Kokoro repository entries, never the entire site/model cache.
  await Promise.allSettled([clearMatchingEntries(MODEL_CACHE), clearMatchingEntries(VOICE_CACHE)]);
}

async function prefetchVoice(voice: ProductionJob["voice"]) {
  if (!("caches" in scope)) return false;
  const url = `https://huggingface.co/${MODEL_ID}/resolve/main/voices/${voice}.bin`;
  let cache: Cache;
  try {
    cache = await caches.open(VOICE_CACHE);
  } catch {
    return false;
  }
  if (await cache.match(url)) return true;

  post({ type: "status", phase: "loading", backend, detail: `Downloading the ${voice} voice` });
  let lastError: unknown;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Voice download returned HTTP ${response.status}.`);
      try {
        await cache.put(url, response);
        return true;
      } catch {
        // The model remains usable when storage is full; Kokoro will fetch the
        // small voice file on demand and can still benefit from the HTTP cache.
        return false;
      }
    } catch (error) {
      lastError = error;
      if (attempt < 3) await new Promise((resolve) => setTimeout(resolve, 300 * attempt));
    }
  }
  throw lastError;
}

async function loadEngine(preferWebGpu: boolean, forceDownload = false, announceReady = true) {
  if (engine && !forceDownload) return engine;
  if (preparing) return preparing;

  preparing = (async () => {
    if (forceDownload) {
      const previousEngine = engine;
      engine = null;
      backend = undefined;
      await previousEngine?.model.dispose().catch(() => {});
      post({ type: "status", phase: "loading", detail: "Clearing the previous local voice download" });
      await clearDownloadedAssets();
    }

    const requestedBackend: LocalVoiceBackend = preferWebGpu && await canUseWebGpu() ? "webgpu" : "wasm";
    const load = async (device: LocalVoiceBackend) => {
      post({ type: "status", phase: "loading", backend: device, detail: device === "webgpu" ? "Preparing WebGPU" : "Preparing WebAssembly" });
      return KokoroTTS.from_pretrained(MODEL_ID, {
        dtype: "q8",
        device,
        progress_callback: (value) => post({ type: "status", phase: "loading", backend: device, ...progressDetail(value) }),
      });
    };

    try {
      engine = await load(requestedBackend);
      backend = requestedBackend;
    } catch (error) {
      if (requestedBackend !== "webgpu") throw error;
      post({ type: "status", phase: "loading", backend: "wasm", detail: "WebGPU unavailable for this model; using WebAssembly" });
      engine = await load("wasm");
      backend = "wasm";
    }
    if (announceReady) post({ type: "status", phase: "ready", backend, detail: "Model ready on this device" });
    return engine;
  })();

  try {
    return await preparing;
  } finally {
    preparing = null;
  }
}

async function replaceFailedWebGpuEngine(jobId: string) {
  const previousEngine = engine;
  engine = null;
  backend = undefined;
  post({ type: "status", jobId, phase: "loading", backend: "wasm", detail: "WebGPU inference failed; recovering with WebAssembly" });
  await previousEngine?.model.dispose().catch(() => {});
  // The narration job remains active while the backend is replaced. Avoid a
  // jobless "ready" status here, which could briefly make the UI look idle
  // before generation resumes on WASM.
  return loadEngine(false, false, false);
}

function wake() {
  wakeProducer?.();
  wakeProducer = null;
}

function waitForDemand(job: ProductionJob) {
  if (job.producing || activeJob !== job) return Promise.resolve();
  return new Promise<void>((resolve) => { wakeProducer = resolve; });
}

async function generateChunk(tts: KokoroTTS, job: ProductionJob, chunk: LocalNarrationChunk) {
  let lastError: unknown;
  for (let attempt = 1; attempt <= GENERATION_ATTEMPTS; attempt += 1) {
    if (activeJob !== job) return null;
    const startedAt = performance.now();
    try {
      const audio = await tts.generate(chunk.text, { voice: job.voice, speed: job.speed });
      const generationMs = performance.now() - startedAt;
      const durationSeconds = audio.audio.length / audio.sampling_rate;
      return {
        samples: audio.audio,
        sampleRate: audio.sampling_rate,
        durationSeconds,
        generationMs,
        realTimeFactor: durationSeconds > 0 ? generationMs / 1000 / durationSeconds : 0,
      };
    } catch (error) {
      lastError = error;
      if (attempt < GENERATION_ATTEMPTS && activeJob === job) {
        await new Promise((resolve) => setTimeout(resolve, 200 * attempt));
      }
    }
  }
  throw lastError;
}

async function pump() {
  while (activeJob) {
    const job = activeJob;
    await waitForDemand(job);
    if (activeJob !== job) continue;

    if (job.nextIndex >= job.chunks.length) {
      post({ type: "done", jobId: job.id, totalChunks: job.chunks.length });
      if (activeJob === job) activeJob = null;
      continue;
    }

    try {
      const tts = await loadEngine(true);
      if (activeJob !== job) continue;
      const chunk = job.chunks[job.nextIndex];
      post({ type: "status", jobId: job.id, phase: "generating", backend, detail: `Generating audio ${chunk.sequence + 1} of ${job.chunks.length}` });
      const chunkStartedAt = performance.now();
      let result;
      try {
        result = await generateChunk(tts, job, chunk);
      } catch (error) {
        if (backend !== "webgpu" || activeJob !== job) throw error;
        const fallback = await replaceFailedWebGpuEngine(job.id);
        if (activeJob !== job) continue;
        result = await generateChunk(fallback, job, chunk);
      }
      if (!result || activeJob !== job) continue;
      result.generationMs = performance.now() - chunkStartedAt;
      result.realTimeFactor = result.durationSeconds > 0 ? result.generationMs / 1000 / result.durationSeconds : 0;
      job.nextIndex += 1;
      post({ type: "audio", jobId: job.id, ...chunk, ...result, backend }, [result.samples.buffer]);
      // Let cancellation, replacement, and flow-control messages run between inferences.
      await new Promise((resolve) => setTimeout(resolve, 0));
    } catch (error) {
      if (activeJob !== job) continue;
      post({ type: "error", jobId: job.id, message: errorMessage(error) });
      activeJob = null;
    }
  }
}

function ensurePump() {
  if (pumpPromise) return;
  pumpPromise = pump().finally(() => {
    pumpPromise = null;
    if (activeJob) ensurePump();
  });
}

scope.addEventListener("message", (event: MessageEvent<LocalVoiceRequest>) => {
  const request = event.data;
  if (request.type === "cancel") {
    if (!request.jobId || request.jobId === activeJob?.id) activeJob = null;
    wake();
    return;
  }
  if (request.type === "flow") {
    if (activeJob?.id === request.jobId) {
      activeJob.producing = request.producing;
      if (request.producing) wake();
    }
    return;
  }
  if (request.type === "prepare") {
    void (async () => {
      await loadEngine(request.preferWebGpu, request.forceDownload, false);
      const voiceCached = request.voice ? await prefetchVoice(request.voice) : false;
      post({ type: "status", phase: "ready", backend, detail: request.voice && voiceCached ? "Model and selected voice ready on this device" : "Model ready on this device" });
    })().catch((error) => post({ type: "error", message: errorMessage(error) }));
    return;
  }
  if (!isLocalVoiceId(request.voice)) {
    post({ type: "error", jobId: request.jobId, message: "That English local voice is unavailable." });
    return;
  }
  activeJob = {
    id: request.jobId,
    chunks: request.chunks,
    voice: request.voice,
    speed: request.speed,
    nextIndex: 0,
    producing: true,
  };
  wake();
  ensurePump();
});

export {};

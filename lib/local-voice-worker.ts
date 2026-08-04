/// <reference lib="webworker" />

import { env as transformersEnv } from "@huggingface/transformers";
import { KokoroTTS } from "kokoro-js";
import { isLocalVoiceId, type LocalVoiceBackend, type LocalVoiceRequest, type LocalVoiceResponse } from "./local-voice-types";

const MODEL_ID = "onnx-community/Kokoro-82M-v1.0-ONNX";
const ORT_WASM_CDN = "https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0-dev.20250409-89f8206ba4/dist/";
const scope = self as DedicatedWorkerGlobalScope;

let engine: KokoroTTS | null = null;
let backend: LocalVoiceBackend | undefined;
let preparing: Promise<KokoroTTS> | null = null;
let activeJobId: string | null = null;

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

async function canUseWebGpu() {
  const gpu = (navigator as Navigator & { gpu?: { requestAdapter: () => Promise<unknown> } }).gpu;
  if (!gpu) return false;
  try {
    return Boolean(await gpu.requestAdapter());
  } catch {
    return false;
  }
}

async function loadEngine(preferWebGpu: boolean) {
  if (engine) return engine;
  if (preparing) return preparing;

  preparing = (async () => {
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
    post({ type: "status", phase: "ready", backend, detail: "Model ready on this device" });
    return engine;
  })();

  try {
    return await preparing;
  } finally {
    preparing = null;
  }
}

async function speak(request: Extract<LocalVoiceRequest, { type: "speak" }>) {
  activeJobId = request.jobId;
  try {
    if (!isLocalVoiceId(request.voice)) throw new Error("That English local voice is unavailable.");
    const tts = await loadEngine(true);
    if (activeJobId !== request.jobId) return;
    post({ type: "status", phase: "generating", backend, detail: "Generating sentence audio" });
    let cursor = 0;
    for await (const chunk of tts.stream(request.text, { voice: request.voice, speed: request.speed })) {
      if (activeJobId !== request.jobId) return;
      const found = request.text.indexOf(chunk.text, cursor);
      const start = found >= 0 ? found : cursor;
      const end = Math.min(request.text.length, start + chunk.text.length);
      cursor = end;
      const samples = chunk.audio.audio;
      post({ type: "audio", jobId: request.jobId, text: chunk.text, start, end, samples, sampleRate: chunk.audio.sampling_rate }, [samples.buffer]);
      // Yield between sentence chunks so cancellation and navigation messages run.
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
    if (activeJobId === request.jobId) post({ type: "done", jobId: request.jobId });
  } catch (error) {
    if (activeJobId === request.jobId) post({ type: "error", jobId: request.jobId, message: error instanceof Error ? error.message : "Local voice generation failed." });
  }
}

scope.addEventListener("message", (event: MessageEvent<LocalVoiceRequest>) => {
  const request = event.data;
  if (request.type === "cancel") {
    if (!request.jobId || request.jobId === activeJobId) activeJobId = null;
    return;
  }
  if (request.type === "prepare") {
    void loadEngine(request.preferWebGpu).catch((error) => post({ type: "error", message: error instanceof Error ? error.message : "The local voice model could not be prepared." }));
    return;
  }
  void speak(request);
});

export {};

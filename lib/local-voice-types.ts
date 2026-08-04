export type LocalVoiceBackend = "webgpu" | "wasm";

export type LocalVoiceProgress = {
  phase: "idle" | "loading" | "ready" | "generating" | "playing" | "paused" | "error";
  backend?: LocalVoiceBackend;
  progress?: number;
  detail?: string;
};

export type LocalVoiceRequest =
  | { type: "prepare"; preferWebGpu: boolean }
  | { type: "speak"; jobId: string; text: string; voice: "af_heart"; speed: number }
  | { type: "cancel"; jobId?: string };

export type LocalVoiceResponse =
  | { type: "status"; phase: "loading" | "ready" | "generating"; backend?: LocalVoiceBackend; progress?: number; detail?: string }
  | { type: "audio"; jobId: string; text: string; start: number; end: number; samples: Float32Array; sampleRate: number }
  | { type: "done"; jobId: string }
  | { type: "error"; jobId?: string; message: string };

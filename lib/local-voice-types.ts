export type LocalVoiceBackend = "webgpu" | "wasm";

export const LOCAL_VOICE_OPTIONS = [
  { id: "af_heart", label: "Heart", locale: "English (US)", gender: "Female" },
  { id: "af_bella", label: "Bella", locale: "English (US)", gender: "Female" },
  { id: "af_nicole", label: "Nicole", locale: "English (US)", gender: "Female" },
  { id: "af_nova", label: "Nova", locale: "English (US)", gender: "Female" },
  { id: "af_sarah", label: "Sarah", locale: "English (US)", gender: "Female" },
  { id: "am_fenrir", label: "Fenrir", locale: "English (US)", gender: "Male" },
  { id: "am_michael", label: "Michael", locale: "English (US)", gender: "Male" },
  { id: "am_puck", label: "Puck", locale: "English (US)", gender: "Male" },
  { id: "bf_emma", label: "Emma", locale: "English (UK)", gender: "Female" },
  { id: "bf_isabella", label: "Isabella", locale: "English (UK)", gender: "Female" },
  { id: "bm_george", label: "George", locale: "English (UK)", gender: "Male" },
  { id: "bm_fable", label: "Fable", locale: "English (UK)", gender: "Male" },
] as const;

export type LocalVoiceId = typeof LOCAL_VOICE_OPTIONS[number]["id"];

export function isLocalVoiceId(value: unknown): value is LocalVoiceId {
  return LOCAL_VOICE_OPTIONS.some((voice) => voice.id === value);
}

export type LocalVoiceProgress = {
  phase: "idle" | "loading" | "ready" | "generating" | "playing" | "paused" | "error";
  backend?: LocalVoiceBackend;
  progress?: number;
  detail?: string;
};

export type LocalVoiceRequest =
  | { type: "prepare"; preferWebGpu: boolean }
  | { type: "speak"; jobId: string; text: string; voice: LocalVoiceId; speed: number }
  | { type: "cancel"; jobId?: string };

export type LocalVoiceResponse =
  | { type: "status"; phase: "loading" | "ready" | "generating"; backend?: LocalVoiceBackend; progress?: number; detail?: string }
  | { type: "audio"; jobId: string; text: string; start: number; end: number; samples: Float32Array; sampleRate: number }
  | { type: "done"; jobId: string }
  | { type: "error"; jobId?: string; message: string };

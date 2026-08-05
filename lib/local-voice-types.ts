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

/** A source-text chunk whose offsets are relative to the narration request. */
export type LocalNarrationChunk = {
  sequence: number;
  text: string;
  start: number;
  end: number;
};

export type LocalVoiceMetrics = {
  backend?: LocalVoiceBackend;
  generatedChunks: number;
  playedChunks: number;
  generationMs: number;
  audioDurationSeconds: number;
  realTimeFactor?: number;
  lastGenerationMs?: number;
  lastAudioDurationSeconds?: number;
  lastRealTimeFactor?: number;
  queueDepth: number;
  bufferedSeconds: number;
  underruns: number;
  producerPaused: boolean;
};

export const LOCAL_VOICE_DOWNLOAD_ESTIMATE = {
  modelWeightsMegabytes: 92.4,
  selectedVoiceMegabytes: 0.52,
  estimatedFirstDownloadMegabytes: { minimum: 100, maximum: 120 },
} as const;

export type LocalVoiceProgress = {
  phase: "idle" | "loading" | "ready" | "generating" | "buffering" | "playing" | "paused" | "error";
  backend?: LocalVoiceBackend;
  progress?: number;
  detail?: string;
  metrics?: LocalVoiceMetrics;
};

export type LocalVoiceRequest =
  | { type: "prepare"; preferWebGpu: boolean; forceDownload?: boolean; voice?: LocalVoiceId }
  | { type: "speak"; jobId: string; chunks: LocalNarrationChunk[]; voice: LocalVoiceId; speed: number }
  | { type: "flow"; jobId: string; producing: boolean }
  | { type: "cancel"; jobId?: string };

export type LocalVoiceResponse =
  | { type: "status"; jobId?: string; phase: "loading" | "ready" | "generating"; backend?: LocalVoiceBackend; progress?: number; detail?: string }
  | ({
      type: "audio";
      jobId: string;
      samples: Float32Array;
      sampleRate: number;
      durationSeconds: number;
      generationMs: number;
      realTimeFactor: number;
      backend?: LocalVoiceBackend;
    } & LocalNarrationChunk)
  | { type: "done"; jobId: string; totalChunks: number }
  | { type: "error"; jobId?: string; message: string };

const ABBREVIATIONS = new Set([
  "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs", "etc", "inc", "ltd",
  "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
]);

const MIN_CLAUSE_CHARACTERS = 72;
const COMMA_CLAUSE_CHARACTERS = 132;
const MAX_CHUNK_CHARACTERS = 260;

function isSentenceBoundary(text: string, punctuationIndex: number) {
  const mark = text[punctuationIndex];
  if (mark !== "." && mark !== "!" && mark !== "?" && mark !== "\u2026") return false;
  if (mark === "." && /\d/.test(text[punctuationIndex - 1] || "") && /\d/.test(text[punctuationIndex + 1] || "")) return false;
  if (mark === ".") {
    const prefix = text.slice(0, punctuationIndex);
    const word = prefix.match(/([A-Za-z]+)$/)?.[1]?.toLowerCase();
    if (word && (ABBREVIATIONS.has(word) || word.length === 1)) return false;
  }
  let next = punctuationIndex + 1;
  while (next < text.length && /[.!?\u2026"'\u2019\u201d)\]}\u00bb]/.test(text[next])) next += 1;
  return next >= text.length || /\s/.test(text[next]);
}

/**
 * Split prose into bounded sentence/clause-sized work units without rewriting it.
 * Punctuation remains in the generated text so Kokoro keeps its natural pauses,
 * and every chunk retains exact offsets into the original request.
 */
export function splitLocalNarration(text: string): LocalNarrationChunk[] {
  const chunks: LocalNarrationChunk[] = [];
  let cursor = 0;

  while (cursor < text.length) {
    while (cursor < text.length && /\s/.test(text[cursor])) cursor += 1;
    if (cursor >= text.length) break;

    const hardEnd = Math.min(text.length, cursor + MAX_CHUNK_CHARACTERS);
    let sentenceEnd = -1;
    let clauseEnd = -1;
    let commaEnd = -1;

    for (let index = cursor; index < hardEnd; index += 1) {
      const mark = text[index];
      if (isSentenceBoundary(text, index)) {
        let end = index + 1;
        while (end < hardEnd && /[.!?\u2026"'\u2019\u201d)\]}\u00bb]/.test(text[end])) end += 1;
        sentenceEnd = end;
        break;
      }
      const length = index - cursor + 1;
      if ((mark === ";" || mark === ":" || mark === "\u2014" || mark === "\u2013" || mark === "\n") && length >= MIN_CLAUSE_CHARACTERS) clauseEnd = index + 1;
      if (mark === "," && length >= COMMA_CLAUSE_CHARACTERS) commaEnd = index + 1;
    }

    let end = sentenceEnd > 0 ? sentenceEnd : clauseEnd > 0 ? clauseEnd : commaEnd > 0 ? commaEnd : hardEnd;
    if (end === hardEnd && hardEnd < text.length) {
      const candidate = text.slice(cursor, hardEnd).search(/\s\S*$/);
      if (candidate > MIN_CLAUSE_CHARACTERS) end = cursor + candidate;
    }
    while (end > cursor && /\s/.test(text[end - 1])) end -= 1;
    if (end <= cursor) end = Math.min(text.length, cursor + MAX_CHUNK_CHARACTERS);

    chunks.push({ sequence: chunks.length, text: text.slice(cursor, end), start: cursor, end });
    cursor = end;
  }

  return chunks;
}

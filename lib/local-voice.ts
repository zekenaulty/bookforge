import {
  splitLocalNarration,
  type LocalVoiceId,
  type LocalVoiceMetrics,
  type LocalVoiceProgress,
  type LocalVoiceRequest,
  type LocalVoiceResponse,
} from "./local-voice-types";

type AudioChunk = Extract<LocalVoiceResponse, { type: "audio" }> & { buffer: AudioBuffer };
type ScheduledChunk = {
  chunk: AudioChunk;
  source: AudioBufferSourceNode;
  startTime: number;
  endTime: number;
};

export type LocalNarrationCallbacks = {
  onState: (state: LocalVoiceProgress) => void;
  onPosition: (character: number) => void;
  onEnd: () => void;
  onError: (error: Error) => void;
  onMetrics?: (metrics: LocalVoiceMetrics) => void;
};

export type LocalVoicePlayerOptions = {
  /** Audio required before playback begins. Defaults to seven seconds. */
  prebufferSeconds?: number;
  /** Restart worker generation when remaining audio falls below this value. */
  lowWaterSeconds?: number;
  /** Pause worker generation when remaining audio reaches this value. */
  highWaterSeconds?: number;
};

export type LocalVoiceCacheInfo = {
  modelCached: boolean;
  voiceCached: boolean;
  selectedVoiceCached?: boolean;
  modelEntries: number;
  voiceEntries: number;
  storageUsage?: number;
  storageQuota?: number;
  persistent: boolean;
};

const START_LEAD_SECONDS = 0.045;
const MONITOR_INTERVAL_MS = 100;

function isKokoroAssetUrl(url: string) {
  try {
    return decodeURIComponent(url).includes("onnx-community/Kokoro-82M-v1.0-ONNX");
  } catch {
    return url.includes("onnx-community/Kokoro-82M-v1.0-ONNX");
  }
}

function decodedAssetUrl(url: string) {
  try { return decodeURIComponent(url); } catch { return url; }
}

function emptyMetrics(): LocalVoiceMetrics {
  return {
    generatedChunks: 0,
    playedChunks: 0,
    generationMs: 0,
    audioDurationSeconds: 0,
    queueDepth: 0,
    bufferedSeconds: 0,
    underruns: 0,
    producerPaused: false,
  };
}

export class LocalVoicePlayer {
  private callbacks: LocalNarrationCallbacks;
  private worker: Worker;
  private audioContext: AudioContext | null = null;
  private queue = new Map<number, AudioChunk>();
  private scheduled = new Map<number, ScheduledChunk>();
  private activeJobId: string | null = null;
  private startAt = 0;
  private generationDone = false;
  private stopped = true;
  private paused = false;
  private playbackStarted = false;
  private waitingAfterUnderrun = false;
  private modelReady = false;
  private nextSequence = 0;
  private totalChunks = 0;
  private nextScheduleTime = 0;
  private producerEnabled = true;
  private monitorId: number | null = null;
  private lastPositionSequence = -1;
  private lastMetricsAt = 0;
  private metrics = emptyMetrics();
  private state: LocalVoiceProgress = { phase: "idle" };
  private readonly prebufferSeconds: number;
  private readonly lowWaterSeconds: number;
  private readonly highWaterSeconds: number;

  constructor(callbacks: LocalNarrationCallbacks, options: LocalVoicePlayerOptions = {}) {
    this.callbacks = callbacks;
    this.prebufferSeconds = Math.max(1, options.prebufferSeconds ?? 7);
    this.lowWaterSeconds = Math.max(1, Math.min(options.lowWaterSeconds ?? 5, this.prebufferSeconds));
    this.highWaterSeconds = Math.max(this.prebufferSeconds, options.highWaterSeconds ?? 14);
    this.worker = this.createWorker();
  }

  /** Load/cache the model without starting narration. Safe to call repeatedly. */
  prepare(voice?: LocalVoiceId) {
    this.send({ type: "prepare", preferWebGpu: "gpu" in navigator, voice });
  }

  /** Explicit UI-facing alias for the initial model download button. */
  download(voice?: LocalVoiceId) {
    this.prepare(voice);
  }

  /**
   * Cancel narration, discard the in-memory model and browser cache, then fetch
   * a fresh copy. Progress is delivered through onState.
   */
  redownload(voice?: LocalVoiceId) {
    this.stop();
    this.resetWorker();
    this.modelReady = false;
    this.setState({ phase: "loading", detail: "Starting a fresh local voice download" });
    this.send({ type: "prepare", preferWebGpu: "gpu" in navigator, forceDownload: true, voice });
  }

  getMetrics() {
    return { ...this.metrics, ...this.liveQueueMetrics() };
  }

  getStatus() {
    return { ...this.state, metrics: this.getMetrics() };
  }

  speak(text: string, startAt: number, speed: number, voice: LocalVoiceId) {
    this.stop();
    this.stopped = false;
    this.paused = false;
    this.startAt = Math.max(0, Math.min(startAt, text.length));
    this.activeJobId = crypto.randomUUID();
    this.generationDone = false;
    this.playbackStarted = false;
    this.waitingAfterUnderrun = false;
    this.queue.clear();
    this.scheduled.clear();
    this.nextSequence = 0;
    this.nextScheduleTime = 0;
    this.producerEnabled = true;
    this.lastPositionSequence = -1;
    this.metrics = emptyMetrics();

    const chunks = splitLocalNarration(text.slice(this.startAt));
    this.totalChunks = chunks.length;
    let context: AudioContext;
    try {
      context = this.getAudioContext();
    } catch (error) {
      this.fail(error instanceof Error ? error : new Error("Web Audio is unavailable on this device."));
      return;
    }
    void context.resume()
      .then(() => this.scheduleAvailable())
      .catch(() => {
        if (this.activeJobId) this.setState({ ...this.state, phase: "paused", detail: "Tap play to allow local audio" });
      });
    this.startMonitor();
    this.setState({ phase: "loading", detail: "Preparing local voice", metrics: this.getMetrics() });
    this.send({ type: "speak", jobId: this.activeJobId, chunks, voice, speed });
  }

  async pause() {
    if (!this.audioContext || !this.activeJobId || this.paused) return;
    this.paused = true;
    await this.audioContext.suspend();
    this.setState({ ...this.state, phase: "paused", detail: "Local narration paused", metrics: this.getMetrics() });
  }

  async resume() {
    if (!this.audioContext || !this.activeJobId) return;
    await this.audioContext.resume();
    this.paused = false;
    this.scheduleAvailable();
    this.setState({ ...this.state, phase: this.playbackStarted ? "playing" : "buffering", metrics: this.getMetrics() });
  }

  stop() {
    this.stopped = true;
    this.paused = false;
    if (this.activeJobId) this.send({ type: "cancel", jobId: this.activeJobId });
    this.activeJobId = null;
    this.queue.clear();
    this.generationDone = false;
    this.playbackStarted = false;
    this.totalChunks = 0;
    this.cancelScheduledAudio();
    this.stopMonitor();
  }

  destroy() {
    this.stop();
    this.detachWorker();
    this.worker.terminate();
    if (this.audioContext) {
      this.audioContext.onstatechange = null;
      void this.audioContext.close();
    }
    this.audioContext = null;
  }

  private createWorker() {
    const worker = new Worker(new URL("./local-voice-worker.ts", import.meta.url), { type: "module", name: "kotoba-local-voice" });
    worker.addEventListener("message", this.onMessage);
    worker.addEventListener("error", this.onWorkerError);
    return worker;
  }

  private detachWorker() {
    this.worker.removeEventListener("message", this.onMessage);
    this.worker.removeEventListener("error", this.onWorkerError);
  }

  private resetWorker() {
    this.detachWorker();
    this.worker.terminate();
    this.worker = this.createWorker();
  }

  private getAudioContext() {
    if (this.audioContext?.state === "closed") this.audioContext = null;
    if (!this.audioContext) {
      const AudioContextConstructor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextConstructor) throw new Error("Web Audio is unavailable on this device.");
      this.audioContext = new AudioContextConstructor();
      this.audioContext.onstatechange = () => {
        if (!this.audioContext || !this.activeJobId || this.paused) return;
        const state = this.audioContext.state as string;
        if (state === "suspended" || state === "interrupted") {
          void this.audioContext.resume().catch(() => {
            this.paused = true;
            this.setState({ ...this.state, phase: "paused", detail: "Tap play to resume local audio", metrics: this.getMetrics() });
          });
        }
      };
    }
    return this.audioContext;
  }

  private send(message: LocalVoiceRequest) {
    this.worker.postMessage(message);
  }

  private setState(state: LocalVoiceProgress) {
    this.state = state;
    this.callbacks.onState(state);
  }

  private onMessage = (event: MessageEvent<LocalVoiceResponse>) => {
    const message = event.data;
    if (message.type === "status") {
      if (message.jobId && message.jobId !== this.activeJobId) return;
      if (message.phase === "ready") this.modelReady = true;
      const phase = message.phase === "generating" && this.activeJobId
        ? this.paused ? "paused" : this.playbackStarted ? "playing" : "buffering"
        : message.phase;
      const detail = message.phase === "generating" && this.playbackStarted ? "Playing while local voice prefetches" : message.detail;
      this.setState({ phase, backend: message.backend, progress: message.progress, detail, metrics: this.getMetrics() });
      return;
    }
    if (message.type === "error") {
      if (message.jobId && message.jobId !== this.activeJobId) return;
      this.fail(new Error(message.message));
      return;
    }
    if (message.jobId !== this.activeJobId) return;
    if (message.type === "audio") {
      this.acceptAudio(message);
      return;
    }
    this.generationDone = true;
    this.totalChunks = message.totalChunks;
    this.scheduleAvailable();
    this.finishIfComplete();
  };

  private onWorkerError = () => {
    const shouldReset = Boolean(this.activeJobId) || this.modelReady;
    this.fail(new Error("The local voice worker stopped."));
    if (shouldReset) {
      this.resetWorker();
      this.modelReady = false;
    }
  };

  private acceptAudio(message: Extract<LocalVoiceResponse, { type: "audio" }>) {
    if (!this.audioContext || this.queue.has(message.sequence) || this.scheduled.has(message.sequence)) return;
    let buffer: AudioBuffer;
    try {
      buffer = this.audioContext.createBuffer(1, message.samples.length, message.sampleRate);
      buffer.getChannelData(0).set(message.samples);
    } catch {
      this.fail(new Error("The device could not allocate a local narration audio buffer."));
      return;
    }
    this.queue.set(message.sequence, { ...message, buffer });
    this.metrics.backend = message.backend ?? this.metrics.backend;
    this.metrics.generatedChunks += 1;
    this.metrics.generationMs += message.generationMs;
    this.metrics.audioDurationSeconds += message.durationSeconds;
    this.metrics.realTimeFactor = this.metrics.audioDurationSeconds > 0
      ? this.metrics.generationMs / 1000 / this.metrics.audioDurationSeconds
      : undefined;
    this.metrics.lastGenerationMs = message.generationMs;
    this.metrics.lastAudioDurationSeconds = message.durationSeconds;
    this.metrics.lastRealTimeFactor = message.realTimeFactor;

    const contiguousSeconds = this.contiguousQueuedSeconds();
    if (!this.playbackStarted && (contiguousSeconds >= this.prebufferSeconds || this.metrics.generatedChunks === this.totalChunks)) {
      this.playbackStarted = true;
    }
    this.scheduleAvailable();
    this.rebalanceProducer();
    this.reportMetrics(true);
  }

  private contiguousQueuedSeconds() {
    let duration = 0;
    for (let sequence = this.nextSequence; ; sequence += 1) {
      const chunk = this.queue.get(sequence);
      if (!chunk) break;
      duration += chunk.durationSeconds;
    }
    return duration;
  }

  private scheduleAvailable() {
    if (this.stopped || this.paused || !this.playbackStarted || !this.activeJobId || !this.audioContext || this.audioContext.state !== "running") return;
    const jobId = this.activeJobId;
    while (this.queue.has(this.nextSequence)) {
      const chunk = this.queue.get(this.nextSequence)!;
      this.queue.delete(this.nextSequence);
      const source = this.audioContext.createBufferSource();
      source.buffer = chunk.buffer;
      source.connect(this.audioContext.destination);

      const earliestStart = this.audioContext.currentTime + START_LEAD_SECONDS;
      let startTime = this.nextScheduleTime || earliestStart;
      if (startTime < earliestStart) {
        if (this.nextSequence > 0 && !this.waitingAfterUnderrun) this.metrics.underruns += 1;
        startTime = earliestStart;
      }
      const endTime = startTime + chunk.buffer.duration;
      const scheduled: ScheduledChunk = { chunk, source, startTime, endTime };
      this.scheduled.set(chunk.sequence, scheduled);
      this.nextScheduleTime = endTime;
      this.nextSequence += 1;
      this.waitingAfterUnderrun = false;

      source.onended = () => {
        if (this.activeJobId !== jobId || this.scheduled.get(chunk.sequence)?.source !== source) return;
        source.disconnect();
        this.scheduled.delete(chunk.sequence);
        this.metrics.playedChunks += 1;
        if (this.lastPositionSequence <= chunk.sequence) this.callbacks.onPosition(this.startAt + chunk.end);
        this.rebalanceProducer();
        this.reportMetrics(true);
        this.finishIfComplete();
      };
      try {
        source.start(startTime);
      } catch {
        source.onended = null;
        source.disconnect();
        this.scheduled.delete(chunk.sequence);
        this.fail(new Error("The device could not schedule the next local narration buffer."));
        return;
      }
    }
    this.setState({ ...this.state, phase: "playing", detail: "Buffered local narration", metrics: this.getMetrics() });
  }

  private liveQueueMetrics() {
    const now = this.audioContext?.currentTime ?? 0;
    let bufferedSeconds = 0;
    for (const item of this.scheduled.values()) {
      bufferedSeconds += Math.max(0, item.endTime - Math.max(now, item.startTime));
    }
    for (const item of this.queue.values()) bufferedSeconds += item.durationSeconds;
    return { queueDepth: this.scheduled.size + this.queue.size, bufferedSeconds };
  }

  private rebalanceProducer() {
    if (!this.activeJobId || this.generationDone) return;
    const { bufferedSeconds } = this.liveQueueMetrics();
    if (this.producerEnabled && bufferedSeconds >= this.highWaterSeconds) {
      this.producerEnabled = false;
      this.metrics.producerPaused = true;
      this.send({ type: "flow", jobId: this.activeJobId, producing: false });
    } else if (!this.producerEnabled && bufferedSeconds <= this.lowWaterSeconds) {
      this.producerEnabled = true;
      this.metrics.producerPaused = false;
      this.send({ type: "flow", jobId: this.activeJobId, producing: true });
    }
  }

  private startMonitor() {
    this.stopMonitor();
    this.monitorId = window.setInterval(() => {
      if (!this.activeJobId || !this.audioContext) return;
      const now = this.audioContext.currentTime;
      const current = [...this.scheduled.values()].find((item) => item.startTime <= now && now < item.endTime);
      if (current && current.chunk.sequence !== this.lastPositionSequence) {
        this.lastPositionSequence = current.chunk.sequence;
        this.callbacks.onPosition(this.startAt + current.chunk.start);
      }

      const hasFutureAudio = [...this.scheduled.values()].some((item) => item.endTime > now) || this.queue.size > 0;
      if (this.playbackStarted && !this.paused && !this.generationDone && !hasFutureAudio && !this.waitingAfterUnderrun) {
        this.waitingAfterUnderrun = true;
        this.metrics.underruns += 1;
        this.setState({ ...this.state, phase: "buffering", detail: "Recovering the local audio buffer", metrics: this.getMetrics() });
      }
      this.rebalanceProducer();
      this.reportMetrics();
    }, MONITOR_INTERVAL_MS);
  }

  private stopMonitor() {
    if (this.monitorId != null) window.clearInterval(this.monitorId);
    this.monitorId = null;
  }

  private reportMetrics(force = false) {
    const now = performance.now();
    if (!force && now - this.lastMetricsAt < 500) return;
    this.lastMetricsAt = now;
    const live = this.liveQueueMetrics();
    this.metrics.queueDepth = live.queueDepth;
    this.metrics.bufferedSeconds = live.bufferedSeconds;
    this.callbacks.onMetrics?.({ ...this.metrics });
  }

  private cancelScheduledAudio() {
    for (const item of this.scheduled.values()) {
      item.source.onended = null;
      try { item.source.stop(); } catch { /* already stopped */ }
      item.source.disconnect();
    }
    this.scheduled.clear();
    this.nextScheduleTime = 0;
  }

  private finishIfComplete() {
    if (!this.generationDone || this.scheduled.size || this.queue.size || !this.activeJobId) return;
    this.activeJobId = null;
    this.stopMonitor();
    this.setState({ phase: "ready", backend: this.metrics.backend, detail: "Model ready on this device", metrics: this.getMetrics() });
    this.callbacks.onEnd();
  }

  private fail(error: Error) {
    if (!this.activeJobId && this.state.phase === "error") return;
    const hadNarration = Boolean(this.activeJobId);
    this.activeJobId = null;
    this.queue.clear();
    this.cancelScheduledAudio();
    this.stopMonitor();
    this.setState({ ...this.state, phase: "error", detail: error.message, metrics: this.getMetrics() });
    // Preparation failures also need to reach the UI so device speech can remain
    // the explicit fallback even when narration has not started yet.
    if (hadNarration || !this.modelReady) this.callbacks.onError(error);
  }
}

export async function getLocalVoiceCacheInfo(selectedVoice?: LocalVoiceId): Promise<LocalVoiceCacheInfo> {
  let modelCached = false;
  let voiceCached = false;
  let selectedVoiceCached: boolean | undefined;
  let modelEntries = 0;
  let voiceEntries = 0;
  try {
    if (typeof caches !== "undefined") {
      const names = await caches.keys();
      if (names.includes("transformers-cache")) {
        const requests = await (await caches.open("transformers-cache")).keys();
        const entries = requests.filter((request) => isKokoroAssetUrl(request.url));
        modelEntries = entries.length;
        modelCached = entries.some((request) => /\/onnx\/model_quantized\.onnx(?:\?|$)/i.test(decodedAssetUrl(request.url)));
      }
      if (names.includes("kokoro-voices")) {
        const requests = await (await caches.open("kokoro-voices")).keys();
        const entries = requests.filter((request) => isKokoroAssetUrl(request.url));
        voiceEntries = entries.length;
        voiceCached = entries.some((request) => /\/voices\/[^/]+\.bin(?:\?|$)/i.test(decodedAssetUrl(request.url)));
        selectedVoiceCached = selectedVoice
          ? entries.some((request) => decodedAssetUrl(request.url).includes(`/voices/${selectedVoice}.bin`))
          : undefined;
      }
    }
  } catch {
    // Cache inspection is advisory; private browsing can deny Cache Storage.
  }
  const storage = typeof navigator !== "undefined" ? navigator.storage : undefined;
  const [estimate, persistent] = await Promise.all([
    storage?.estimate?.().catch(() => undefined),
    storage?.persisted?.().catch(() => false) ?? false,
  ]);
  return {
    modelCached,
    voiceCached,
    selectedVoiceCached,
    modelEntries,
    voiceEntries,
    storageUsage: estimate?.usage,
    storageQuota: estimate?.quota,
    persistent,
  };
}

export async function requestPersistentVoiceStorage() {
  if (typeof navigator === "undefined" || !navigator.storage?.persist) return false;
  try {
    // Called directly from the feature-toggle gesture so browsers may grant it.
    return navigator.storage.persist();
  } catch {
    return false;
  }
}

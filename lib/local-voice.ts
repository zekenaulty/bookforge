import type { LocalVoiceProgress, LocalVoiceRequest, LocalVoiceResponse } from "./local-voice-types";

type Chunk = Extract<LocalVoiceResponse, { type: "audio" }>;

export type LocalNarrationCallbacks = {
  onState: (state: LocalVoiceProgress) => void;
  onPosition: (character: number) => void;
  onEnd: () => void;
  onError: (error: Error) => void;
};

export class LocalVoicePlayer {
  private worker: Worker;
  private audioContext: AudioContext | null = null;
  private source: AudioBufferSourceNode | null = null;
  private queue: Chunk[] = [];
  private activeJobId: string | null = null;
  private startAt = 0;
  private generationDone = false;
  private stopped = false;
  private state: LocalVoiceProgress = { phase: "idle" };

  constructor(private callbacks: LocalNarrationCallbacks) {
    this.worker = new Worker(new URL("./local-voice-worker.ts", import.meta.url), { type: "module", name: "kotoba-local-voice" });
    this.worker.addEventListener("message", this.onMessage);
    this.worker.addEventListener("error", this.onWorkerError);
  }

  prepare() {
    this.send({ type: "prepare", preferWebGpu: "gpu" in navigator });
  }

  speak(text: string, startAt: number, speed: number) {
    this.stop();
    this.stopped = false;
    this.startAt = startAt;
    this.activeJobId = crypto.randomUUID();
    this.generationDone = false;
    this.queue = [];
    this.audioContext ||= new AudioContext();
    void this.audioContext.resume();
    this.setState({ phase: "loading", detail: "Preparing local voice" });
    this.send({ type: "speak", jobId: this.activeJobId, text: text.slice(startAt), voice: "af_heart", speed });
  }

  async pause() {
    if (!this.audioContext || !this.activeJobId) return;
    await this.audioContext.suspend();
    this.setState({ ...this.state, phase: "paused" });
  }

  async resume() {
    if (!this.audioContext || !this.activeJobId) return;
    await this.audioContext.resume();
    this.setState({ ...this.state, phase: this.source ? "playing" : "generating" });
    this.playNext();
  }

  stop() {
    this.stopped = true;
    if (this.activeJobId) this.send({ type: "cancel", jobId: this.activeJobId });
    this.activeJobId = null;
    this.queue = [];
    this.generationDone = false;
    if (this.source) {
      this.source.onended = null;
      try { this.source.stop(); } catch { /* already stopped */ }
      this.source.disconnect();
      this.source = null;
    }
  }

  destroy() {
    this.stop();
    this.worker.removeEventListener("message", this.onMessage);
    this.worker.removeEventListener("error", this.onWorkerError);
    this.worker.terminate();
    void this.audioContext?.close();
    this.audioContext = null;
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
      this.setState({ phase: message.phase, backend: message.backend, progress: message.progress, detail: message.detail });
      return;
    }
    if (message.type === "error") {
      if (message.jobId && message.jobId !== this.activeJobId) return;
      this.setState({ ...this.state, phase: "error", detail: message.message });
      this.callbacks.onError(new Error(message.message));
      return;
    }
    if (message.jobId !== this.activeJobId) return;
    if (message.type === "audio") {
      this.queue.push(message);
      this.playNext();
      return;
    }
    this.generationDone = true;
    this.finishIfComplete();
  };

  private onWorkerError = () => {
    this.setState({ ...this.state, phase: "error", detail: "The local voice worker stopped." });
    this.callbacks.onError(new Error("The local voice worker stopped."));
  };

  private playNext() {
    if (this.stopped || this.source || !this.activeJobId || !this.audioContext || this.audioContext.state === "suspended") return;
    const chunk = this.queue.shift();
    if (!chunk) { this.finishIfComplete(); return; }
    const buffer = this.audioContext.createBuffer(1, chunk.samples.length, chunk.sampleRate);
    buffer.copyToChannel(chunk.samples, 0);
    const source = this.audioContext.createBufferSource();
    source.buffer = buffer;
    source.connect(this.audioContext.destination);
    source.onended = () => {
      if (this.source !== source) return;
      this.callbacks.onPosition(this.startAt + chunk.end);
      source.disconnect();
      this.source = null;
      this.playNext();
    };
    this.source = source;
    this.callbacks.onPosition(this.startAt + chunk.start);
    this.setState({ ...this.state, phase: "playing" });
    source.start();
  }

  private finishIfComplete() {
    if (!this.generationDone || this.source || this.queue.length || !this.activeJobId) return;
    this.activeJobId = null;
    this.setState({ ...this.state, phase: "ready" });
    this.callbacks.onEnd();
  }
}

export async function requestPersistentVoiceStorage() {
  if (!navigator.storage?.persist) return false;
  try {
    // Called directly from the feature-toggle gesture so browsers may grant it.
    return navigator.storage.persist();
  } catch {
    return false;
  }
}

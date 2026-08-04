"use client";
/* eslint-disable @next/next/no-img-element -- private R2-backed art is served through the authenticated app route. */

import { useCallback, useEffect, useRef, useState } from "react";
import { DEFAULT_GOOGLE_IMAGE_MODEL, GOOGLE_IMAGE_MODELS, type GoogleImageModel, isGoogleImageModel } from "../lib/image-models";
import { LocalVoicePlayer, requestPersistentVoiceStorage } from "../lib/local-voice";
import { isLocalVoiceId, LOCAL_VOICE_OPTIONS, type LocalVoiceId, type LocalVoiceProgress } from "../lib/local-voice-types";
import { normalizeReaderTurn, readerTurnNumbers, resolveReaderNavigation, type ReaderNavigationIntent } from "../lib/reader-navigation";
import type { ArtAsset, AuthorProfile, BackgroundJob, CastMember, OperationLog, Story, Turn, TurnResult } from "../lib/types";

type View = "library" | "authors" | "archived" | "settings" | "reader" | "author";
type LibraryPayload = { authors: AuthorProfile[]; stories: Story[]; logs: OperationLog[] };
class BackgroundJobStopped extends Error {}
const HTTP_TIMEOUT_MS = 10 * 60 * 1000;

const genres = ["Fantasy", "Science fiction", "Romance", "Mystery", "Horror", "Historical", "Literary", "Adventure", "Cozy", "Gothic", "Progression", "Speculative"];

async function api<T>(body?: Record<string, unknown>, storyId?: string, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort(signal?.reason);
  if (signal?.aborted) abort(); else signal?.addEventListener("abort", abort, { once: true });
  const timeout = window.setTimeout(() => { timedOut = true; controller.abort(); }, HTTP_TIMEOUT_MS);
  try {
    const response = await fetch(storyId ? `/api/app?storyId=${encodeURIComponent(storyId)}` : "/api/app", body ? {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), signal: controller.signal,
    } : { cache: "no-store", signal: controller.signal });
    const payload = await response.json() as T & { error?: string };
    if (!response.ok) throw new Error(payload.error || "The library could not complete that request.");
    return payload;
  } catch (error) {
    if (timedOut) throw new Error("The request did not complete within ten minutes. Your saved story data is unchanged; try again when the connection is steadier.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
    signal?.removeEventListener("abort", abort);
  }
}

async function drainBackgroundJobs(storyId: string, onStory?: (story: Story) => void, jobId = "", signal?: AbortSignal) {
  let processed = false;
  for (let pass = 0; pass < 6; pass += 1) {
    signal?.throwIfAborted();
    const result = await api<{ processed: boolean; more: boolean }>({ action: "runBackgroundJob", storyId, ...(jobId ? { jobId } : {}) }, undefined, signal);
    processed ||= result.processed;
    if (!result.more) break;
  }
  if (processed || jobId) {
    const story = (await api<{ story: Story }>(undefined, storyId, signal)).story;
    signal?.throwIfAborted();
    onStory?.(story);
    return story;
  }
}

function abortableDelay(milliseconds: number, signal: AbortSignal) {
  if (signal.aborted) return Promise.reject(signal.reason || new DOMException("Aborted", "AbortError"));
  return new Promise<void>((resolve, reject) => {
    const onAbort = () => { window.clearTimeout(timer); reject(signal.reason || new DOMException("Aborted", "AbortError")); };
    const timer = window.setTimeout(() => { signal.removeEventListener("abort", onAbort); resolve(); }, milliseconds);
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

async function waitForBackgroundJob(storyId: string, jobId: string, onStory: (story: Story) => void, signal: AbortSignal) {
  const deadline = Date.now() + 10 * 60 * 1000;
  let failures = 0;
  while (Date.now() < deadline) {
    signal.throwIfAborted();
    try {
      const applyStory = (story: Story) => { if (!signal.aborted) onStory(story); };
      let story = await drainBackgroundJobs(storyId, applyStory, jobId);
      signal.throwIfAborted();
      if (!story) story = (await api<{ story: Story }>(undefined, storyId)).story;
      signal.throwIfAborted();
      const job = story.jobs?.find((item) => item.id === jobId);
      if (!job) throw new Error("The artwork job could not be found.");
      if (job.status === "completed") return story;
      if (["failed", "unsupported"].includes(job.status)) throw new BackgroundJobStopped(job.lastError || "Artwork generation stopped. Review the saved diagnostics and retry.");
      failures = 0;
    } catch (error) {
      if (error instanceof BackgroundJobStopped) throw error;
      if (signal.aborted) throw signal.reason || new DOMException("Aborted", "AbortError");
      failures += 1;
      if (failures >= 3) throw error;
    }
    await abortableDelay(5_000, signal);
  }
  throw new Error("Artwork is still running in the background. You can close the gallery and return later without losing it.");
}

export default function KotobaApp() {
  const [library, setLibrary] = useState<LibraryPayload>({ authors: [], stories: [], logs: [] });
  const [view, setView] = useState<View>("library");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [selectedAuthor, setSelectedAuthor] = useState<AuthorProfile | null>(null);
  const [authorOpen, setAuthorOpen] = useState(false);
  const [storyOpen, setStoryOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await api<LibraryPayload>();
      setLibrary(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "The library could not be opened.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const saved = localStorage.getItem("kotoba-theme");
    const next = saved === "dark" || (!saved && matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    const themeFrame = requestAnimationFrame(() => setTheme(next));
    const refreshFrame = requestAnimationFrame(() => void refresh());
    return () => { cancelAnimationFrame(themeFrame); cancelAnimationFrame(refreshFrame); };
  }, [refresh]);

  function changeTheme(next: "light" | "dark") {
    setTheme(next); localStorage.setItem("kotoba-theme", next); document.documentElement.dataset.theme = next;
  }

  async function openStory(story: Story) {
    setError(""); setLoading(true);
    try {
      const result = await api<{ story: Story }>(undefined, story.id);
      setSelectedStory(result.story); setView("reader");
      void drainBackgroundJobs(story.id, (next) => setSelectedStory((current) => current?.id === next.id ? next : current)).catch(() => {});
    } catch (err) { setError(message(err)); }
    finally { setLoading(false); }
  }

  function openAuthor(author: AuthorProfile) { setSelectedAuthor(author); setView("author"); }
  function navigate(next: View) { window.speechSynthesis?.cancel(); setView(next); setSelectedStory(null); }
  const updateSelectedStory = useCallback((next: Story) => setSelectedStory((current) => current?.id === next.id ? next : current), []);

  return <div className="app-shell">
    <header className="topbar">
      <button className="brand" onClick={() => navigate("library")} aria-label="Open library">
        <span className="brand-mark" aria-hidden="true"><span /></span>
        <span>kotoba-no-kaijiba</span>
      </button>
      <nav aria-label="Primary navigation">
        <button className={view === "library" ? "active" : ""} onClick={() => navigate("library")}>Library</button>
        <button className={view === "authors" || view === "author" ? "active" : ""} onClick={() => navigate("authors")}>Authors</button>
        <button className={view === "archived" ? "active" : ""} onClick={() => navigate("archived")}>Archive</button>
        <button className={view === "settings" ? "active" : ""} onClick={() => navigate("settings")}>Settings</button>
      </nav>
      <button className="theme-button" onClick={() => changeTheme(theme === "light" ? "dark" : "light")} aria-label={`Use ${theme === "light" ? "dark" : "light"} mode`}>
        {theme === "light" ? "☾" : "☀"}
      </button>
    </header>

    {error && <div className="error-banner" role="alert"><span>{error}</span><button onClick={() => setError("")}>Dismiss</button></div>}
    {loading && <div className="quiet-loading" aria-live="polite"><span className="ink-dot" /> Opening your library…</div>}

    <main>
      {view === "library" && <LibraryView stories={library.stories.filter((story) => story.status !== "Archived")} authors={library.authors} onNew={() => setStoryOpen(true)} onOpen={openStory} onAuthor={openAuthor} />}
      {view === "archived" && <ArchiveView stories={library.stories.filter((story) => story.status === "Archived")} onOpen={openStory} onRestore={async (story) => { await api({ action: "setStoryStatus", storyId: story.id, status: "Active" }); await refresh(); }} />}
      {view === "authors" && <AuthorsView authors={library.authors.filter((author) => !author.archived)} stories={library.stories} onNew={() => { setSelectedAuthor(null); setAuthorOpen(true); }} onOpen={openAuthor} />}
      {view === "author" && selectedAuthor && <AuthorView author={selectedAuthor} stories={library.stories.filter((story) => story.selectedAuthorId === selectedAuthor.id)} onStory={openStory} onCreate={() => setStoryOpen(true)} onEdit={() => setAuthorOpen(true)} onArchive={async () => {
        try {
          const first = await api<{ requiresConfirmation: boolean; storyCount: number }>({ action: "archiveAuthor", authorId: selectedAuthor.id });
          if (confirm(`${selectedAuthor.displayName} is used by ${first.storyCount} ${first.storyCount === 1 ? "story" : "stories"}. Existing stories will keep their pinned author voice. Archive this reusable author?`)) {
            await api({ action: "archiveAuthor", authorId: selectedAuthor.id, confirm: true }); await refresh(); navigate("authors");
          }
        } catch (err) { setError(message(err)); }
      }} />}
      {view === "settings" && <SettingsView theme={theme} onTheme={changeTheme} logs={library.logs} />}
      {view === "reader" && selectedStory && <Reader story={selectedStory} onStory={updateSelectedStory} onBack={() => { navigate("library"); void refresh(); }} onAuthor={openAuthor} onError={setError} />}
    </main>

    {authorOpen && <AuthorDialog existing={selectedAuthor} onClose={() => setAuthorOpen(false)} onSaved={async (author) => { setAuthorOpen(false); setSelectedAuthor(author); await refresh(); setView("author"); }} />}
    {storyOpen && <StoryDialog authors={library.authors.filter((author) => !author.archived)} preferredAuthor={view === "author" ? selectedAuthor : null} onNeedAuthor={() => { setStoryOpen(false); setSelectedAuthor(null); setAuthorOpen(true); }} onClose={() => setStoryOpen(false)} onCreated={async (story) => { setStoryOpen(false); setSelectedStory(story); await refresh(); setView("reader"); void drainBackgroundJobs(story.id, updateSelectedStory).catch(() => {}); }} />}
  </div>;
}

function LibraryView({ stories, authors, onNew, onOpen, onAuthor }: { stories: Story[]; authors: AuthorProfile[]; onNew: () => void; onOpen: (story: Story) => void; onAuthor: (author: AuthorProfile) => void }) {
  return <section className="page library-page">
    <div className="page-heading"><div><p className="eyebrow">Your living-fiction library</p><h1>Stories waiting for you</h1><p>Read what has been written. Invite the author to continue when you reach the edge.</p></div><button className="primary" onClick={onNew}>New story</button></div>
    <div className="story-grid">
      <NewStoryCard onClick={onNew} />
      {stories.map((story, index) => <StoryCard key={story.id} story={story} index={index} author={authors.find((author) => author.id === story.selectedAuthorId)} onOpen={() => onOpen(story)} onAuthor={onAuthor} />)}
    </div>
    {!stories.length && <p className="empty-note">Your shelves are quiet. Begin with an unwritten page.</p>}
  </section>;
}

function NewStoryCard({ onClick }: { onClick: () => void }) {
  return <button className="new-story-card" onClick={onClick}>
    <span className="blank-book" aria-hidden="true"><i /><b>＋</b></span>
    <strong>New story</strong><span>Give a fictional author an idea.</span>
  </button>;
}

function StoryCard({ story, index, author, onOpen, onAuthor }: { story: Story; index: number; author?: AuthorProfile; onOpen: () => void; onAuthor: (author: AuthorProfile) => void }) {
  const cover = story.art?.find((asset) => asset.type === "cover" && asset.status === "Ready");
  return <article className="story-card">
    <button className={`cover cover-${index % 5}`} onClick={onOpen} aria-label={`Open ${story.title}`}>
      {cover && <img src={`/api/app?assetId=${encodeURIComponent(cover.id)}`} alt="" />}
      <span className="cover-rule" /><strong>{story.title}</strong><em>{author?.displayName || story.authorSnapshot.displayName}</em><span className="cover-mark">⌁</span>
    </button>
    <div className="story-card-body">
      <div className="story-meta"><span>{story.status}</span><span>Section {story.latestAcceptedTurnNumber}</span></div>
      <h2>{story.title}</h2><p>{story.shortDescription}</p>
      <button className="author-link" onClick={() => author && onAuthor(author)}>by {author?.displayName || story.authorSnapshot.displayName}</button>
      <button className="text-action" onClick={onOpen}>{story.latestAcceptedTurnNumber ? "Continue reading" : "Begin reading"} <span>→</span></button>
    </div>
  </article>;
}

function AuthorsView({ authors, stories, onNew, onOpen }: { authors: AuthorProfile[]; stories: Story[]; onNew: () => void; onOpen: (author: AuthorProfile) => void }) {
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">The atelier</p><h1>Fictional authors</h1><p>Reusable voices, each with their own instincts and craft.</p></div><button className="primary" onClick={onNew}>Create author</button></div>
    <div className="author-grid">
      {authors.map((author) => <button key={author.id} className="author-card" onClick={() => onOpen(author)}><span className="author-monogram">{initials(author.displayName)}</span><div><h2>{author.displayName}</h2><p>{author.shortDescription}</p><div className="tag-row">{author.selectedGenres.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div><small>{stories.filter((story) => story.selectedAuthorId === author.id).length} stories</small></div></button>)}
    </div>
    {!authors.length && <div className="center-empty"><div className="nib" /><h2>No authors yet</h2><p>Create a storyteller from a few genres and a short description.</p><button className="primary" onClick={onNew}>Create your first author</button></div>}
  </section>;
}

function AuthorView({ author, stories, onStory, onCreate, onEdit, onArchive }: { author: AuthorProfile; stories: Story[]; onStory: (story: Story) => void; onCreate: () => void; onEdit: () => void; onArchive: () => void }) {
  return <section className="page author-profile-page">
    <div className="author-hero"><span className="author-monogram large">{initials(author.displayName)}</span><div><p className="eyebrow">Fictional author</p><h1>{author.displayName}</h1><p>{author.shortDescription}</p><div className="tag-row">{[...author.selectedGenres, ...author.tone].slice(0, 7).map((tag) => <span key={tag}>{tag}</span>)}</div></div></div>
    <div className="profile-actions"><button className="primary" onClick={onCreate}>Create story with this author</button><button className="secondary" onClick={onEdit}>Revise author</button><button className="ghost danger" onClick={onArchive}>Archive author</button></div>
    <div className="profile-columns"><article><p className="eyebrow">Voice</p><h2>How the prose moves</h2><p>{author.voice}</p><dl><dt>Pacing</dt><dd>{author.pacing}</dd><dt>Point of view</dt><dd>{author.preferredPointOfView}</dd><dt>Tense</dt><dd>{author.preferredTense}</dd><dt>Texture</dt><dd>{author.proseDensity}</dd></dl></article><article><p className="eyebrow">Principles</p><h2>What guides the work</h2><ul>{author.writingRules.map((rule) => <li key={rule}>{rule}</li>)}</ul><p className="eyebrow minor">Avoids</p><ul className="muted-list">{author.thingsToAvoid.map((rule) => <li key={rule}>{rule}</li>)}</ul></article></div>
    <div className="subsection-heading"><h2>Stories by {author.displayName}</h2></div><div className="compact-story-list">{stories.map((story) => <button key={story.id} onClick={() => onStory(story)}><span className="mini-cover">{story.title.slice(0, 1)}</span><span><strong>{story.title}</strong><small>Section {story.latestAcceptedTurnNumber} · {story.status}</small></span><b>→</b></button>)}</div>
  </section>;
}

function ArchiveView({ stories, onOpen, onRestore }: { stories: Story[]; onOpen: (story: Story) => void; onRestore: (story: Story) => void }) {
  return <section className="page"><div className="page-heading"><div><p className="eyebrow">Shelved for now</p><h1>Archived stories</h1><p>Nothing is lost. Return any story to the active library.</p></div></div>
    <div className="archive-list">{stories.map((story) => <article key={story.id}><div className="mini-cover">{story.title.slice(0, 1)}</div><div><h2>{story.title}</h2><p>{story.shortDescription}</p><small>{story.authorSnapshot.displayName} · {story.latestAcceptedTurnNumber} sections</small></div><div><button className="secondary" onClick={() => onOpen(story)}>Read</button><button className="ghost" onClick={() => onRestore(story)}>Restore</button></div></article>)}</div>
    {!stories.length && <div className="center-empty"><h2>No archived stories</h2><p>Your active shelves hold everything.</p></div>}
  </section>;
}

function SettingsView({ theme, onTheme, logs }: { theme: string; onTheme: (theme: "light" | "dark") => void; logs: OperationLog[] }) {
  return <section className="page settings-page"><div className="page-heading"><div><p className="eyebrow">Reading room</p><h1>Settings</h1><p>A few quiet choices for your private library.</p></div></div>
    <div className="settings-card"><div><h2>Appearance</h2><p>Choose a comfortable reading surface.</p></div><div className="segmented"><button className={theme === "light" ? "active" : ""} onClick={() => onTheme("light")}>Warm paper</button><button className={theme === "dark" ? "active" : ""} onClick={() => onTheme("dark")}>Night ink</button></div></div>
    <div className="settings-card"><div><h2>Private by design</h2><p>Your authors, stories, cast, reading place, and continuity records live in this private application. There is no public profile or story discovery.</p></div><span className="privacy-seal">Private</span></div>
    <div className="settings-card"><div><h2>Narration</h2><p>Device speech remains the instant, zero-download default. Readers can optionally enable a private local neural voice; its model is downloaded and cached by the browser, with no API key or server audio.</p></div></div>
    <div className="settings-card log-settings"><div><h2>Generation log</h2><p>Recoverable transport and parser failures get up to three attempts per request. Each request may wait up to ten minutes; failures that escape request-level recovery and every resumable background attempt are recorded here for diagnosis.</p></div></div>
    <div className="operation-log">{logs.length ? logs.map((log) => <article key={log.id}><span className={`status-pill ${log.status}`}>{log.status}</span><div><strong>{humanJobName(log.operation)}</strong><p>{log.message}</p><small>{new Date(log.createdAt).toLocaleString()} · {log.category} · attempt {log.attempt}</small></div></article>) : <p className="empty-note">No generation failures or retries have been logged.</p>}</div>
  </section>;
}

function Reader({ story, onStory, onBack, onAuthor, onError }: { story: Story; onStory: (story: Story) => void; onBack: () => void; onAuthor: (author: AuthorProfile) => void; onError: (error: string) => void }) {
  const [turnNumber, setTurnNumber] = useState(() => normalizeReaderTurn(story.turns, story.readingTurnNumber || story.latestAcceptedTurnNumber));
  const [writing, setWriting] = useState(false);
  const [note, setNote] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [gallery, setGallery] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);
  const [rate, setRate] = useState(story.playbackRate || 1);
  const [voiceId, setVoiceId] = useState(story.defaultNarrationVoice || "");
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [autoRead, setAutoRead] = useState(story.autoReadNext);
  const [autoWrite, setAutoWrite] = useState(story.autoWriteNext);
  const [highQuality, setHighQuality] = useState(false);
  const [localVoiceId, setLocalVoiceId] = useState<LocalVoiceId>("af_heart");
  const [localVoice, setLocalVoice] = useState<LocalVoiceProgress>({ phase: "idle" });
  const [voiceStoragePersistent, setVoiceStoragePersistent] = useState(false);
  const [regen, setRegen] = useState<{ candidate: TurnResult; original: Turn } | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const storyRef = useRef(story); const turnRef = useRef(turnNumber); const autoReadRef = useRef(autoRead); const autoWriteRef = useRef(autoWrite); const noteRef = useRef(note); const writingRef = useRef(false);
  const speechCharRef = useRef(0); const speechTextRef = useRef(""); const narrationActiveRef = useRef(false); const activeNarratorRef = useRef<"local" | "device" | null>(null);
  const activeNarrationTurnRef = useRef<number | null>(null); const narrationSequenceRef = useRef(0);
  const autoAdvanceTimeoutRef = useRef<number | null>(null); const autoAdvanceIntervalRef = useRef<number | null>(null);
  const highQualityRef = useRef(false); const localVoiceIdRef = useRef<LocalVoiceId>("af_heart"); const localPlayerRef = useRef<LocalVoicePlayer | null>(null);
  const preferenceWriteRef = useRef<Promise<unknown>>(Promise.resolve());
  const narrationFinishedRef = useRef<(target: number) => void>(() => {}); const deviceFallbackRef = useRef<(target: number, startAt: number, sequence: number) => void>(() => {});
  const speakTurnRef = useRef<(target: number, startAt?: number) => void>(() => {});
  const readerPageRef = useRef<HTMLElement | null>(null);
  const normalizedTurnNumber = normalizeReaderTurn(story.turns, turnNumber);
  const current = story.turns?.find((turn) => turn.turnNumber === normalizedTurnNumber);

  useEffect(() => {
    storyRef.current = story;
    turnRef.current = normalizedTurnNumber;
    autoReadRef.current = autoRead;
    autoWriteRef.current = autoWrite;
    noteRef.current = note;
  }, [story, normalizedTurnNumber, autoRead, autoWrite, note]);

  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: "auto" }); }, [story.id]);

  useEffect(() => {
    const timer = window.setInterval(() => void drainBackgroundJobs(story.id, (next) => { storyRef.current = next; onStory(next); }).catch(() => {}), 60_000);
    return () => window.clearInterval(timer);
  }, [onStory, story.id]);

  useEffect(() => {
    const loadVoices = () => setVoices(window.speechSynthesis?.getVoices() || []);
    loadVoices(); window.speechSynthesis?.addEventListener("voiceschanged", loadVoices);
    return () => {
      narrationSequenceRef.current += 1;
      if (autoAdvanceTimeoutRef.current != null) window.clearTimeout(autoAdvanceTimeoutRef.current);
      if (autoAdvanceIntervalRef.current != null) window.clearInterval(autoAdvanceIntervalRef.current);
      window.speechSynthesis?.removeEventListener("voiceschanged", loadVoices); window.speechSynthesis?.cancel(); localPlayerRef.current?.destroy(); localPlayerRef.current = null;
    };
  }, []);

  const persist = useCallback((nextTurn = turnRef.current, nextRate = rate, nextAutoRead = autoReadRef.current, nextAutoWrite = autoWriteRef.current, nextVoice = voiceId) => {
    const preference = { action: "updatePreferences", storyId: storyRef.current.id, readingTurnNumber: nextTurn, playbackRate: nextRate,
      autoReadNext: nextAutoRead, autoWriteNext: nextAutoWrite, voiceId: nextVoice };
    preferenceWriteRef.current = preferenceWriteRef.current.catch(() => {}).then(() => api(preference)).catch(() => {});
  }, [rate, voiceId]);

  const revealSection = useCallback(() => {
    window.requestAnimationFrame(() => readerPageRef.current?.scrollIntoView({
      block: "start",
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
    }));
  }, []);

  const continueWriting = useCallback(async (background = false) => {
    if (writingRef.current) return;
    if (storyRef.current.status !== "Active") return;
    const latest = storyRef.current.latestAcceptedTurnNumber;
    if (background && turnRef.current !== latest) return;
    const originTurn = turnRef.current;
    writingRef.current = true; setWriting(true);
    const direction = noteRef.current;
    try {
      const result = await api<{ story: Story }>({ action: "continueStory", storyId: storyRef.current.id, note: direction, expectedLatestTurnNumber: latest });
      storyRef.current = result.story; onStory(result.story);
      void drainBackgroundJobs(result.story.id, (next) => { storyRef.current = next; onStory(next); }).catch(() => {});
      if (direction && noteRef.current === direction) { noteRef.current = ""; setNote(""); }
      if (!background && turnRef.current === originTurn) {
        const nextTurn = result.story.latestAcceptedTurnNumber;
        setTurnNumber(nextTurn); turnRef.current = nextTurn; persist(nextTurn); revealSection();
      }
    } catch (err) { onError(message(err)); }
    finally { writingRef.current = false; setWriting(false); }
  }, [onError, onStory, persist, revealSection]);

  const clearAutoAdvance = useCallback(() => {
    if (autoAdvanceTimeoutRef.current != null) window.clearTimeout(autoAdvanceTimeoutRef.current);
    if (autoAdvanceIntervalRef.current != null) window.clearInterval(autoAdvanceIntervalRef.current);
    autoAdvanceTimeoutRef.current = null;
    autoAdvanceIntervalRef.current = null;
  }, []);

  const narrationFinished = useCallback((target: number) => {
    if (activeNarrationTurnRef.current !== target) return;
    narrationActiveRef.current = false; activeNarratorRef.current = null; activeNarrationTurnRef.current = null;
    setSpeaking(false); setPaused(false);
    clearAutoAdvance();
    const sequence = narrationSequenceRef.current;
    const latestStory = storyRef.current;
    const nextDecision = resolveReaderNavigation(latestStory.turns, target, "next", false);
    if (autoReadRef.current && nextDecision.kind === "move") {
      autoAdvanceTimeoutRef.current = window.setTimeout(() => {
        if (autoReadRef.current && sequence === narrationSequenceRef.current && turnRef.current === target) speakTurnRef.current(nextDecision.turnNumber);
      }, 100);
    } else if (autoReadRef.current && writingRef.current) {
      const expected = latestStory.latestAcceptedTurnNumber + 1;
      autoAdvanceIntervalRef.current = window.setInterval(() => {
        if (!autoReadRef.current || sequence !== narrationSequenceRef.current || turnRef.current !== target) { clearAutoAdvance(); return; }
        if (storyRef.current.turns?.some((turn) => turn.turnNumber === expected)) { clearAutoAdvance(); speakTurnRef.current(expected); }
        else if (!writingRef.current) clearAutoAdvance();
      }, 500);
    }
  }, [clearAutoAdvance]);

  useEffect(() => { narrationFinishedRef.current = narrationFinished; }, [narrationFinished]);

  const speakWithDevice = useCallback((target: number, startAt = 0, sequence = narrationSequenceRef.current) => {
    const synth = window.speechSynthesis;
    const item = storyRef.current.turns?.find((turn) => turn.turnNumber === target);
    if (!synth || !item) { narrationActiveRef.current = false; activeNarratorRef.current = null; setSpeaking(false); return; }
    activeNarratorRef.current = "device";
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(item.prose.slice(startAt));
    utterance.rate = rate;
    const chosen = voices.find((voice) => voice.voiceURI === voiceId || voice.name === voiceId);
    if (chosen) utterance.voice = chosen;
    utterance.onboundary = (event) => { speechCharRef.current = startAt + event.charIndex; };
    utterance.onend = () => {
      if (sequence !== narrationSequenceRef.current || !narrationActiveRef.current) return;
      narrationFinishedRef.current(target);
    };
    utterance.onerror = () => {
      if (sequence !== narrationSequenceRef.current || !narrationActiveRef.current) return;
      narrationActiveRef.current = false; activeNarratorRef.current = null; activeNarrationTurnRef.current = null;
      setSpeaking(false); setPaused(false); onError("Narration stopped. The prose is safe, and you can try playing it again.");
    };
    synth.speak(utterance);
  }, [onError, rate, voiceId, voices]);

  useEffect(() => { deviceFallbackRef.current = speakWithDevice; }, [speakWithDevice]);

  const ensureLocalPlayer = useCallback(() => {
    if (localPlayerRef.current) return localPlayerRef.current;
    const player = new LocalVoicePlayer({
      onState: (state) => {
        setLocalVoice(state);
        if (narrationActiveRef.current && ["loading", "generating", "playing"].includes(state.phase)) { setSpeaking(true); setPaused(false); }
        if (state.phase === "paused") setPaused(true);
      },
      onPosition: (character) => { speechCharRef.current = character; },
      onEnd: () => { const target = activeNarrationTurnRef.current; if (target != null) narrationFinishedRef.current(target); },
      onError: () => {
        if (!narrationActiveRef.current) return;
        localPlayerRef.current?.stop();
        activeNarratorRef.current = "device";
        onError("The high-quality local voice could not continue. Using your device voice instead.");
        const target = activeNarrationTurnRef.current;
        if (target != null) deviceFallbackRef.current(target, speechCharRef.current, narrationSequenceRef.current);
      },
    });
    localPlayerRef.current = player;
    return player;
  }, [onError]);

  useEffect(() => {
    const enabled = window.localStorage.getItem("kotoba-high-quality-local-voice") === "true";
    const savedVoice = window.localStorage.getItem("kotoba-local-voice");
    const nextVoice = isLocalVoiceId(savedVoice) ? savedVoice : "af_heart";
    const timer = window.setTimeout(() => {
      highQualityRef.current = enabled;
      localVoiceIdRef.current = nextVoice;
      setHighQuality(enabled);
      setLocalVoiceId(nextVoice);
      if (enabled) ensureLocalPlayer().prepare();
    }, 0);
    void navigator.storage?.persisted?.().then(setVoiceStoragePersistent).catch(() => {});
    return () => window.clearTimeout(timer);
  }, [ensureLocalPlayer]);

  const speakTurn = useCallback((target: number, startAt = 0) => {
    const item = storyRef.current.turns?.find((turn) => turn.turnNumber === target);
    if (!item) return;
    const changedSection = target !== turnRef.current;
    clearAutoAdvance();
    const sequence = ++narrationSequenceRef.current;
    window.speechSynthesis?.cancel();
    localPlayerRef.current?.stop();
    speechTextRef.current = item.prose; speechCharRef.current = startAt; narrationActiveRef.current = true; activeNarrationTurnRef.current = target;
    setTurnNumber(target); turnRef.current = target; setSpeaking(true); setPaused(false);
    if (highQualityRef.current) { activeNarratorRef.current = "local"; ensureLocalPlayer().speak(item.prose, startAt, rate, localVoiceIdRef.current); }
    else { activeNarratorRef.current = "device"; speakWithDevice(target, startAt, sequence); }
    persist(target);
    if (changedSection) revealSection();
    if (autoWriteRef.current && storyRef.current.status === "Active" && target === storyRef.current.latestAcceptedTurnNumber) void continueWriting(true);
  }, [clearAutoAdvance, continueWriting, ensureLocalPlayer, persist, rate, revealSection, speakWithDevice]);

  useEffect(() => { speakTurnRef.current = speakTurn; }, [speakTurn]);

  function togglePlay() {
    const synth = window.speechSynthesis;
    if (!current || (!synth && !highQualityRef.current)) return;
    if (speaking && !paused) { if (activeNarratorRef.current === "local") void localPlayerRef.current?.pause(); else synth?.pause(); setPaused(true); return; }
    if (speaking && paused) { if (activeNarratorRef.current === "local") void localPlayerRef.current?.resume(); else synth?.resume(); setPaused(false); return; }
    speakTurn(current.turnNumber);
  }

  function stopAudio() {
    clearAutoAdvance(); narrationSequenceRef.current += 1; narrationActiveRef.current = false; activeNarratorRef.current = null; activeNarrationTurnRef.current = null;
    localPlayerRef.current?.stop(); window.speechSynthesis?.cancel(); setSpeaking(false); setPaused(false);
  }
  function skipNarration(seconds: number) {
    if (!speaking || !speechTextRef.current) return;
    const next = Math.max(0, Math.min(speechTextRef.current.length - 1, speechCharRef.current + seconds * 18));
    speakTurn(turnRef.current, next);
  }
  function move(target: number) {
    const normalized = normalizeReaderTurn(storyRef.current.turns, target);
    if (normalized === turnRef.current) return;
    stopAudio(); setTurnNumber(normalized); turnRef.current = normalized; persist(normalized); revealSection();
  }
  function navigateReader(intent: ReaderNavigationIntent) {
    const decision = resolveReaderNavigation(storyRef.current.turns, turnRef.current, intent, storyRef.current.status === "Active");
    if (decision.kind === "move") move(decision.turnNumber);
    else if (decision.kind === "write") { stopAudio(); void continueWriting(false); }
  }
  function toggleAutoRead(next: boolean) {
    setAutoRead(next); autoReadRef.current = next;
    if (!next) {
      clearAutoAdvance();
      if (autoWriteRef.current) { setAutoWrite(false); autoWriteRef.current = false; }
    }
    persist(turnRef.current, rate, next, next ? autoWriteRef.current : false, voiceId);
  }
  function toggleAutoWrite(next: boolean) {
    if (next && storyRef.current.status !== "Active") return;
    setAutoWrite(next); autoWriteRef.current = next;
    if (next) { setAutoRead(true); autoReadRef.current = true; }
    persist(turnRef.current, rate, autoReadRef.current, next, voiceId);
  }
  async function toggleHighQuality(next: boolean) {
    stopAudio();
    highQualityRef.current = next; setHighQuality(next);
    window.localStorage.setItem("kotoba-high-quality-local-voice", String(next));
    if (next) {
      setVoiceStoragePersistent(await requestPersistentVoiceStorage());
      ensureLocalPlayer().prepare();
    } else {
      localPlayerRef.current?.destroy(); localPlayerRef.current = null; setLocalVoice({ phase: "idle" });
    }
  }
  function changeLocalVoice(next: LocalVoiceId) {
    stopAudio();
    localVoiceIdRef.current = next; setLocalVoiceId(next);
    window.localStorage.setItem("kotoba-local-voice", next);
  }

  if (!current) return <div className="quiet-loading">The first page is being prepared…</div>;
  const paragraphs = current.prose.split(/\n\s*\n/).filter(Boolean);
  const sectionArt = story.art?.find((asset) => asset.turnNumber === current.turnNumber && asset.type !== "cover" && asset.status === "Ready");
  const localProgress = typeof localVoice.progress === "number" ? ` ${Math.round(localVoice.progress)}%` : "";
  const localBackend = localVoice.backend === "webgpu" ? "WebGPU" : localVoice.backend === "wasm" ? "WebAssembly" : "local";
  const narrationStatus = writing ? "The author is writing the next section…" : highQuality
    ? localVoice.phase === "loading" ? `Downloading or loading ${localBackend}${localProgress}`
      : localVoice.phase === "generating" ? `Generating on ${localBackend}`
        : localVoice.phase === "error" ? (speaking ? "Narrating with device fallback" : "Local voice unavailable · device fallback ready")
          : speaking ? (paused ? "Local narration paused" : `Narrating on ${localBackend}`)
             : localVoice.phase === "ready" ? `${localBackend} ready${voiceStoragePersistent ? " · persistent cache" : " · browser cache"}` : "Local voice enabled · about 116 MB first download"
    : speaking ? (paused ? "Narration paused" : "Narrating") : "Ready to listen";
  const availableTurnNumbers = readerTurnNumbers(story.turns);
  const firstTurnNumber = availableTurnNumbers[0] || current.turnNumber;
  const lastTurnNumber = availableTurnNumbers.at(-1) || current.turnNumber;
  const atFirst = current.turnNumber === firstTurnNumber;
  const atLast = current.turnNumber === lastTurnNumber;
  const canWrite = story.status === "Active";
  const nextLabel = atLast ? (canWrite ? "Write next section" : "No next section") : "Next section";
  const lastLabel = atLast ? (canWrite ? "Write next section from the current last section" : "Already at the last section") : "Last section";
  return <section className="reader-shell">
    <div className="reader-top"><button className="reader-back" onClick={() => { stopAudio(); onBack(); }}>← Library</button><div><strong>{story.title}</strong><button onClick={() => onAuthor(story.authorSnapshot)}>by {story.authorSnapshot.displayName}</button></div><div className="reader-tools"><button className="secondary small" onClick={() => setGallery(true)}>Gallery</button><button className="secondary small" onClick={() => setDrawer(true)}>Cast &amp; story</button></div></div>
    <article className="reader-page" ref={readerPageRef}><p className="section-label">Section {current.turnNumber} of {story.latestAcceptedTurnNumber}</p><h1>{story.title}</h1><button className="reader-author" onClick={() => onAuthor(story.authorSnapshot)}>{story.authorSnapshot.displayName}</button>{sectionArt && <figure className="section-art"><img src={`/api/app?assetId=${encodeURIComponent(sectionArt.id)}`} alt={sectionArt.caption || sectionArt.title} /><figcaption>{sectionArt.caption}</figcaption></figure>}<div className="prose">{paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div></article>
    <div className="reader-actions"><button className="ghost" disabled={atFirst} onClick={() => navigateReader("previous")}>← Previous section</button>
      {!atLast ? <button className="secondary" onClick={() => navigateReader("next")}>Next section →</button> : <button className="continue-button" disabled={writing || !canWrite} onClick={() => navigateReader("next")}>{writing ? <><span className="ink-dot" /> The author is writing…</> : canWrite ? "Continue writing →" : "End of story"}</button>}
    </div>
    <div className="note-panel"><button onClick={() => setNoteOpen(!noteOpen)}><span>Note to the author</span><small>Optional direction for one section</small><b>{noteOpen ? "−" : "+"}</b></button>{noteOpen && <div><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={500} placeholder="Stay with this character. Slow the scene down. Reveal what is behind the door…" /><p>{writing ? `The current draft is already underway. This note will wait for Section ${story.latestAcceptedTurnNumber + 2}.` : "Clears automatically after the next section is written."}</p></div>}</div>
    <div className="reader-secondary"><a className="secondary pdf-link" href={`/api/app?storyId=${encodeURIComponent(story.id)}&format=pdf`} download>Download illustrated PDF</a><button className="ghost danger" disabled={regenerating || writing || current.turnNumber !== story.latestAcceptedTurnNumber} onClick={async () => {
      if (!confirm("Prepare a new version of the latest section? The original will remain until you choose.")) return;
      setRegenerating(true); try { setRegen(await api({ action: "regenerateLatest", storyId: story.id, note })); } catch (err) { onError(message(err)); } finally { setRegenerating(false); }
    }}>{regenerating ? "Preparing another version…" : "Regenerate latest section"}</button></div>

    <div className="audio-dock" aria-label="Reader playhead and narration controls">
      <div className="audio-overview" aria-live="polite" aria-busy={writing}><div className="audio-title"><strong>Section {current.turnNumber} of {story.latestAcceptedTurnNumber}</strong><span>{narrationStatus}</span></div></div>
      <div className="playhead-controls" role="group" aria-label="Story playhead">
        <button className="playhead-button" disabled={atFirst} onClick={() => navigateReader("first")} aria-label="First section" title="First section">↤</button>
        <button className="playhead-button" disabled={atFirst} onClick={() => navigateReader("previous")} aria-label="Previous section" title="Previous section">←</button>
        <button className="play-button" onClick={togglePlay} aria-label={speaking && !paused ? "Pause narration" : "Play narration"} title={speaking && !paused ? "Pause narration" : "Play narration"}>{speaking && !paused ? "Ⅱ" : "▶"}</button>
        <button className="playhead-button" disabled={(atLast && !canWrite) || (atLast && writing)} onClick={() => navigateReader("next")} aria-label={nextLabel} title={nextLabel}>→</button>
        <button className="playhead-button" disabled={(atLast && !canWrite) || (atLast && writing)} onClick={() => navigateReader("last")} aria-label={lastLabel} title={lastLabel}>↦</button>
      </div>
      <details className="audio-settings">
        <summary>Voice &amp; autoplay</summary>
        <div className="audio-options">
          <div className="narration-skips" role="group" aria-label="Narration position"><button className="skip" onClick={() => skipNarration(-10)} aria-label="Skip narration backward ten seconds">−10</button><button className="skip" onClick={() => skipNarration(10)} aria-label="Skip narration forward ten seconds">+10</button></div>
          <label>Speed<select value={rate} onChange={(event) => { const next = Number(event.target.value); setRate(next); persist(current.turnNumber, next); }}><option value="0.8">0.8×</option><option value="1">1×</option><option value="1.2">1.2×</option><option value="1.5">1.5×</option><option value="1.8">1.8×</option></select></label>
          <label>{highQuality ? "Fallback voice" : "Device voice"}<select value={voiceId} onChange={(event) => { setVoiceId(event.target.value); persist(current.turnNumber, rate, autoRead, autoWrite, event.target.value); }}><option value="">Device default</option>{voices.map((voice) => <option key={voice.voiceURI} value={voice.voiceURI}>{voice.name}</option>)}</select></label>
          <label title="Device speech is instant. Kokoro runs locally in a browser worker and downloads about 116 MB the first time.">High-quality local voice<select value={highQuality ? "kokoro-q8" : "device"} onChange={(event) => void toggleHighQuality(event.target.value === "kokoro-q8")}><option value="device">Off · device speech</option><option value="kokoro-q8">On · Kokoro 82M q8</option></select></label>
          {highQuality && <label title="Kokoro's local model supports English narration. Choose an American or British English voice.">Local voice · English<select value={localVoiceId} onChange={(event) => isLocalVoiceId(event.target.value) && changeLocalVoice(event.target.value)}>{LOCAL_VOICE_OPTIONS.map((voice) => <option key={voice.id} value={voice.id}>{voice.label} · {voice.locale.replace("English ", "")}</option>)}</select></label>}
          <label className="switch-label"><input type="checkbox" checked={autoRead} onChange={(event) => toggleAutoRead(event.target.checked)} /><span />Auto read next</label>
          <label className="switch-label"><input type="checkbox" checked={autoWrite && canWrite} disabled={!canWrite || typeof window === "undefined" || (!("speechSynthesis" in window) && !highQuality)} onChange={(event) => toggleAutoWrite(event.target.checked)} /><span />Auto write next</label>
        </div>
      </details>
    </div>

    {drawer && <StoryDrawer story={story} onClose={() => setDrawer(false)} />}
    {gallery && <StoryGallery story={story} currentTurn={current.turnNumber} onClose={() => setGallery(false)} onStory={(next) => { storyRef.current = next; onStory(next); }} onError={onError} />}
    {regen && <RegenerationDialog data={regen} onClose={() => setRegen(null)} onAccept={async () => { try { const result = await api<{ story: Story }>({ action: "acceptRegeneration", storyId: story.id, candidate: regen.candidate }); onStory(result.story); storyRef.current = result.story; setRegen(null); void drainBackgroundJobs(result.story.id, (next) => { storyRef.current = next; onStory(next); }).catch(() => {}); } catch (err) { onError(message(err)); } }} />}
  </section>;
}

function StoryDrawer({ story, onClose }: { story: Story; onClose: () => void }) {
  return <div className="drawer-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><aside className="story-drawer"><div className="drawer-heading"><div><p className="eyebrow">Cast &amp; story</p><h2>{story.title}</h2></div><button onClick={onClose}>×</button></div><p>{story.shortDescription}</p><dl className="story-facts"><dt>Where</dt><dd>{story.storyState?.currentLocation}</dd><dt>Now</dt><dd>{story.storyState?.currentScene}</dd><dt>Story pressure</dt><dd>{story.storyState?.currentNarrativePressure}</dd><dt>Context</dt><dd>{story.contextSnapshot ? `Reconciled through Section ${story.contextSnapshot.throughTurnNumber}` : "Queued for background reconciliation"}</dd></dl><h3>Known cast</h3><div className="cast-list">{story.cast?.map((member: CastMember) => <article key={member.id}><span>{initials(member.name)}</span><div><h4>{member.name}</h4><small>{member.narrativeRole} · {member.pronouns}</small><p>{member.readerKnownSummary || member.physicalDescription}</p><em>{member.currentStatus} · {member.currentLocation}</em></div></article>)}</div><h3>Background work</h3><div className="job-list">{story.jobs?.slice(0, 12).map((job) => <JobRow key={job.id} job={job} />)}</div><h3>Recent diagnostics</h3><div className="drawer-logs">{story.logs?.slice(0, 8).map((log) => <p key={log.id}><strong>{log.status}</strong> {log.message}</p>)}{!story.logs?.length && <p>No retries or failures logged for this story.</p>}</div></aside></div>;
}

function StoryGallery({ story, currentTurn, onClose, onStory, onError }: { story: Story; currentTurn: number; onClose: () => void; onStory: (story: Story) => void; onError: (error: string) => void }) {
  const [category, setCategory] = useState<ArtAsset["category"]>("Cover");
  const [working, setWorking] = useState<{ jobId: string; type: "cover" | "scene" | "retry" } | null>(null);
  const [imageModel, setImageModel] = useState<GoogleImageModel>(() => {
    if (typeof window === "undefined") return DEFAULT_GOOGLE_IMAGE_MODEL;
    const saved = window.localStorage.getItem("kotoba-google-image-model");
    return isGoogleImageModel(saved) ? saved : DEFAULT_GOOGLE_IMAGE_MODEL;
  });
  const requestControllerRef = useRef<AbortController | null>(null);
  useEffect(() => () => requestControllerRef.current?.abort(), []);
  const assets = (story.art || []).filter((asset) => asset.category === category);
  const profiles = (story.visualProfiles || []).filter((profile) => category === "Characters" ? profile.kind === "character" : category === "Locations" ? profile.kind === "location" : false);
  const activeArtJobs = (story.jobs || []).filter((job) => ["pending", "running", "retrying"].includes(job.status) && job.jobType.startsWith("art_"));
  const hasReadyCover = (story.art || []).some((asset) => asset.type === "cover" && asset.status === "Ready");
  function chooseImageModel(model: GoogleImageModel) {
    setImageModel(model);
    window.localStorage.setItem("kotoba-google-image-model", model);
  }
  async function queue(type: "cover" | "scene", turnNumber?: number) {
    requestControllerRef.current?.abort();
    const controller = new AbortController();
    requestControllerRef.current = controller;
    setWorking({ jobId: `queue:${type}`, type });
    try {
      const result = await api<{ story: Story; jobId: string; queued: boolean; model: GoogleImageModel }>({ action: "queueArt", storyId: story.id, type, turnNumber, model: imageModel });
      controller.signal.throwIfAborted();
      onStory(result.story);
      setWorking({ jobId: result.jobId, type });
      if (!result.queued && result.model !== imageModel) onError(`Artwork was already running with ${googleImageModelLabel(result.model)}. Your selected model will apply to the next regeneration.`);
      await waitForBackgroundJob(story.id, result.jobId, onStory, controller.signal);
    } catch (error) { if (!controller.signal.aborted) onError(message(error)); }
    finally { if (!controller.signal.aborted) setWorking(null); }
  }
  async function retry(job: BackgroundJob) {
    requestControllerRef.current?.abort();
    const controller = new AbortController();
    requestControllerRef.current = controller;
    setWorking({ jobId: job.id, type: "retry" });
    try {
      const result = await api<{ story: Story; jobId: string }>({ action: "retryBackgroundJob", jobId: job.id, model: imageModel });
      controller.signal.throwIfAborted();
      onStory(result.story);
      await waitForBackgroundJob(story.id, result.jobId, onStory, controller.signal);
    }
    catch (error) { if (!controller.signal.aborted) onError(message(error)); }
    finally { if (!controller.signal.aborted) setWorking(null); }
  }
  function closeGallery() { requestControllerRef.current?.abort(); onClose(); }
  return <Modal onClose={closeGallery} wide><div className="dialog-heading"><p className="eyebrow">Story gallery</p><h1>Visual continuity</h1><p>Google Nano Banana generates art in a persisted app job without blocking the reader. Requests may remain connected for up to ten minutes; interrupted work stays safely retryable. Missing or disliked pieces can always be regenerated.</p></div>
    <div className="gallery-tabs">{(["Cover", "Scenes", "Characters", "Locations"] as const).map((item) => <button key={item} className={category === item ? "active" : ""} onClick={() => setCategory(item)}>{item}</button>)}</div>
    <div className="gallery-actions"><label>Google image model<select value={imageModel} disabled={Boolean(working)} onChange={(event) => isGoogleImageModel(event.target.value) && chooseImageModel(event.target.value)}>{GOOGLE_IMAGE_MODELS.map((model) => <option key={model.id} value={model.id}>{model.label} · {model.detail}</option>)}</select></label>{category === "Cover" && <button className="primary" disabled={Boolean(working)} onClick={() => void queue("cover")}>{working?.type === "cover" ? "Generating cover…" : hasReadyCover ? "Regenerate cover" : "Generate cover"}</button>}{category === "Scenes" && <button className="primary" disabled={Boolean(working)} onClick={() => void queue("scene", currentTurn)}>{working?.type === "scene" ? "Generating illustration…" : `Illustrate Section ${currentTurn}`}</button>}</div>
    {activeArtJobs.length > 0 && <div className="art-progress" role="status" aria-live="polite"><span className="ink-dot" /><div><strong>{working ? "Artwork is running" : "Artwork continues in the background"}</strong><small>You may keep reading or close this gallery. Interrupted requests retain their saved brief, model, asset, retry state, and diagnostics.</small></div></div>}
    <div className="gallery-grid">{assets.map((asset) => <article key={asset.id} className="gallery-card">{asset.status === "Ready" ? <img src={`/api/app?assetId=${encodeURIComponent(asset.id)}`} alt={asset.caption || asset.title} /> : <div className="art-placeholder"><span>{asset.type === "cover" ? story.title.slice(0, 1) : asset.turnNumber || "✦"}</span><small>{asset.status}</small></div>}<div><span className={`status-pill ${asset.status.toLowerCase()}`}>{asset.status}</span><h2>{asset.title}</h2><p>{asset.caption}</p>{asset.promptSummary && <details><summary>Saved art brief</summary><p>{asset.promptSummary}</p></details>}</div></article>)}{profiles.map((profile) => <article key={profile.id} className="gallery-card profile-card"><div className="art-placeholder"><span>{profile.name.slice(0, 1)}</span><small>Continuity profile</small></div><div><span className="status-pill completed">Tracked</span><h2>{profile.name}</h2><p>{profile.visualDescription || [profile.bodyType, profile.hair, profile.clothing, profile.architecture, profile.atmosphere].filter(Boolean).join(" · ")}</p><details><summary>Current visual details</summary><p>{[...(profile.currentVisualChanges || []), ...(profile.distinctiveMarkings || []), ...(profile.importantLandmarks || [])].join(" · ") || `Updated through Section ${profile.lastUpdatedTurn}`}</p></details></div></article>)}</div>
    {!assets.length && !profiles.length && <div className="gallery-empty"><p>No {category.toLowerCase()} art has been prepared yet.</p>{(category === "Characters" || category === "Locations") && <small>Visual profiles appear after a background context reconciliation discovers stable subjects.</small>}</div>}
    {story.jobs?.some((job) => ["failed", "unsupported"].includes(job.status) && job.jobType.startsWith("art_")) && <div className="retry-panel"><h3>Art jobs needing attention</h3>{story.jobs.filter((job) => ["failed", "unsupported"].includes(job.status) && job.jobType.startsWith("art_")).slice(0, 8).map((job) => <div key={job.id}><JobRow job={job} /><button className="secondary small" disabled={Boolean(working)} onClick={() => void retry(job)}>Retry with selected model</button></div>)}</div>}
  </Modal>;
}

function JobRow({ job }: { job: BackgroundJob }) {
  return <article className="job-row"><span className={`status-pill ${job.status}`}>{job.status}</span><div><strong>{humanJobName(job.jobType)}</strong><small>{job.turnNumber ? `Section ${job.turnNumber} · ` : ""}attempt {job.attempts}/{job.maxAttempts}</small>{job.lastError && <p>{job.lastError}</p>}</div></article>;
}

function humanJobName(value: string) {
  return ({ context_reconcile: "Context and motives", checkpoint_reconcile: "Continuity checkpoint", art_cover: "Cover art", art_scene: "Scene art", story_foundation: "Story opening", story_continuation: "Story continuation", story_repair: "Continuity repair" } as Record<string, string>)[value] || value.replace(/_/g, " ");
}

function googleImageModelLabel(value: GoogleImageModel) {
  return GOOGLE_IMAGE_MODELS.find((model) => model.id === value)?.label || value;
}

function AuthorDialog({ existing, onClose, onSaved }: { existing: AuthorProfile | null; onClose: () => void; onSaved: (author: AuthorProfile) => void }) {
  const [selected, setSelected] = useState<string[]>(existing?.selectedGenres || []); const [name, setName] = useState(existing?.displayName || "");
  const [description, setDescription] = useState(existing?.shortDescription || ""); const [profile, setProfile] = useState<AuthorProfile | null>(existing);
  const [revision, setRevision] = useState(""); const [working, setWorking] = useState(false); const [error, setError] = useState("");
  async function generate() { setWorking(true); setError(""); try { const result = await api<{ profile: AuthorProfile }>({ action: "previewAuthor", genres: selected, name, description, revision }); setProfile({ ...result.profile, id: existing?.id || "", createdAt: existing?.createdAt }); setRevision(""); } catch (err) { setError(message(err)); } finally { setWorking(false); } }
  async function save() { if (!profile) return; setWorking(true); try { const result = await api<{ author: AuthorProfile }>({ action: "saveAuthor", profile }); onSaved(result.author); } catch (err) { setError(message(err)); } finally { setWorking(false); } }
  return <Modal onClose={onClose} wide><div className="dialog-heading"><p className="eyebrow">{existing ? "Revise a voice" : "A new voice"}</p><h1>{profile ? profile.displayName : "Create a fictional author"}</h1><p>{profile ? "Read the profile, then save it or ask for one small change." : "A few choices are enough. The rest of the craft belongs to the author."}</p></div>
    {!profile ? <><fieldset className="genre-field"><legend>What do they write?</legend><div className="genre-grid">{genres.map((genre) => <button type="button" key={genre} className={selected.includes(genre) ? "selected" : ""} onClick={() => setSelected(selected.includes(genre) ? selected.filter((item) => item !== genre) : [...selected, genre])}>{genre}</button>)}</div></fieldset><label className="field"><span>Author name <em>optional</em></span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Leave blank for a fitting pen name" /></label><label className="field"><span>Describe the kind of storyteller you want.</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Quiet science fiction focused on memory and identity." /></label><div className="example-list"><span>Try:</span><button onClick={() => setDescription("Fast progression fantasy with dry observational humor.")}>Fast progression fantasy with dry observational humor.</button><button onClick={() => setDescription("Intimate gothic romance without purple prose.")}>Intimate gothic romance without purple prose.</button></div><button className="primary full" disabled={working || !selected.length || !description.trim()} onClick={() => void generate()}>{working ? "Shaping the voice…" : "Create author preview"}</button></> : <><div className="author-preview"><div className="preview-top"><span className="author-monogram large">{initials(profile.displayName)}</span><div><h2>{profile.displayName}</h2><p>{profile.shortDescription}</p><div className="tag-row">{[...profile.selectedGenres, ...profile.tone].slice(0, 6).map((tag) => <span key={tag}>{tag}</span>)}</div></div></div><section><h3>Voice</h3><p>{profile.voice}</p></section><div className="preview-columns"><section><h3>Pacing &amp; form</h3><p>{profile.pacing}</p><small>{profile.preferredPointOfView} · {profile.preferredTense}</small></section><section><h3>Writing principles</h3><ul>{profile.writingRules.slice(0, 5).map((item) => <li key={item}>{item}</li>)}</ul></section><section><h3>Avoids</h3><ul>{profile.thingsToAvoid.slice(0, 5).map((item) => <li key={item}>{item}</li>)}</ul></section></div></div><label className="field revision"><span>Ask for a small revision <em>optional</em></span><input value={revision} onChange={(event) => setRevision(event.target.value)} placeholder="Make the voice warmer and the pacing slightly quicker." /></label><div className="dialog-actions"><button className="ghost" onClick={() => setProfile(null)}>Start over</button><button className="secondary" disabled={working} onClick={() => void generate()}>{working ? "Revising…" : revision ? "Make revision" : "Regenerate"}</button><button className="primary" disabled={working} onClick={() => void save()}>Save author</button></div></>}
    {error && <p className="form-error">{error}</p>}
  </Modal>;
}

function StoryDialog({ authors, preferredAuthor, onNeedAuthor, onClose, onCreated }: { authors: AuthorProfile[]; preferredAuthor: AuthorProfile | null; onNeedAuthor: () => void; onClose: () => void; onCreated: (story: Story) => void }) {
  const [authorId, setAuthorId] = useState(preferredAuthor?.id || authors[0]?.id || ""); const [title, setTitle] = useState(""); const [idea, setIdea] = useState(""); const [working, setWorking] = useState(false); const [error, setError] = useState("");
  async function create() { setWorking(true); setError(""); try { const result = await api<{ story: Story }>({ action: "createStory", authorId, title, idea }); onCreated(result.story); } catch (err) { setError(message(err)); } finally { setWorking(false); } }
  return <Modal onClose={working ? () => {} : onClose} wide><div className="dialog-heading"><p className="eyebrow">An unwritten book</p><h1>{working ? "The author is beginning…" : "Create a new story"}</h1><p>{working ? "The foundation and opening section are being written. Only Section 1 will be created." : "Choose a voice, then tell the author what kind of story you want."}</p></div>
    {working ? <div className="writing-state"><span className="book-loader"><i /><i /><i /></span><p>Finding the opening situation, cast, and the first meaningful turn of the story.</p></div> : <><fieldset className="author-choice"><legend>Choose an author</legend>{authors.map((author) => <label key={author.id} className={authorId === author.id ? "selected" : ""}><input type="radio" name="author" checked={authorId === author.id} onChange={() => setAuthorId(author.id)} /><span className="author-monogram">{initials(author.displayName)}</span><span><strong>{author.displayName}</strong><small>{author.shortDescription}</small></span></label>)}<button className="create-inline" onClick={onNeedAuthor}>＋ Create a new author</button></fieldset><label className="field"><span>Story title <em>optional</em></span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="The author can name it" /></label><label className="field story-idea"><span>Tell the author what kind of story you want.</span><textarea value={idea} onChange={(event) => setIdea(event.target.value)} placeholder="A retired cartographer discovers that a coastline erased from every map still appears in her dreams…" /><small>A sentence or several detailed paragraphs both work.</small></label><button className="primary full" disabled={!authorId || !idea.trim()} onClick={() => void create()}>Begin the story</button></>}
    {error && <p className="form-error">{error}</p>}
  </Modal>;
}

function RegenerationDialog({ data, onClose, onAccept }: { data: { candidate: TurnResult; original: Turn }; onClose: () => void; onAccept: () => void }) {
  return <Modal onClose={onClose} wide><div className="dialog-heading"><p className="eyebrow">Another telling</p><h1>Choose the latest section</h1><p>The original is still safe. Only one version can become part of continuity.</p></div><div className="version-compare"><article><span>Current version</span><p>{data.original.prose.slice(0, 1100)}{data.original.prose.length > 1100 ? "…" : ""}</p></article><article><span>New version</span><p>{data.candidate.prose.slice(0, 1100)}{data.candidate.prose.length > 1100 ? "…" : ""}</p></article></div><div className="dialog-actions"><button className="secondary" onClick={onClose}>Keep original</button><button className="primary" onClick={onAccept}>Use new version</button></div></Modal>;
}

function Modal({ children, onClose, wide = false }: { children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  useEffect(() => { const handler = (event: KeyboardEvent) => event.key === "Escape" && onClose(); window.addEventListener("keydown", handler); return () => window.removeEventListener("keydown", handler); }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className={`modal ${wide ? "wide" : ""}`} role="dialog" aria-modal="true"><button className="modal-close" onClick={onClose} aria-label="Close">×</button>{children}</section></div>;
}

function initials(name: string) { return name.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
function message(error: unknown) { return error instanceof Error ? error.message : "Something interrupted the library."; }

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { AuthorProfile, CastMember, Story, Turn, TurnResult } from "../lib/types";

type View = "library" | "authors" | "archived" | "settings" | "reader" | "author";
type LibraryPayload = { authors: AuthorProfile[]; stories: Story[] };

const genres = ["Fantasy", "Science fiction", "Romance", "Mystery", "Horror", "Historical", "Literary", "Adventure", "Cozy", "Gothic", "Progression", "Speculative"];

async function api<T>(body?: Record<string, unknown>, storyId?: string): Promise<T> {
  const response = await fetch(storyId ? `/api/app?storyId=${encodeURIComponent(storyId)}` : "/api/app", body ? {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
  } : { cache: "no-store" });
  const payload = await response.json() as T & { error?: string };
  if (!response.ok) throw new Error(payload.error || "The library could not complete that request.");
  return payload;
}

export default function KotobaApp() {
  const [library, setLibrary] = useState<LibraryPayload>({ authors: [], stories: [] });
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
    } catch (err) { setError(message(err)); }
    finally { setLoading(false); }
  }

  function openAuthor(author: AuthorProfile) { setSelectedAuthor(author); setView("author"); }
  function navigate(next: View) { window.speechSynthesis?.cancel(); setView(next); setSelectedStory(null); }

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
      {view === "settings" && <SettingsView theme={theme} onTheme={changeTheme} />}
      {view === "reader" && selectedStory && <Reader story={selectedStory} onStory={setSelectedStory} onBack={async () => { await refresh(); navigate("library"); }} onAuthor={openAuthor} onError={setError} />}
    </main>

    {authorOpen && <AuthorDialog existing={selectedAuthor} onClose={() => setAuthorOpen(false)} onSaved={async (author) => { setAuthorOpen(false); setSelectedAuthor(author); await refresh(); setView("author"); }} />}
    {storyOpen && <StoryDialog authors={library.authors.filter((author) => !author.archived)} preferredAuthor={view === "author" ? selectedAuthor : null} onNeedAuthor={() => { setStoryOpen(false); setSelectedAuthor(null); setAuthorOpen(true); }} onClose={() => setStoryOpen(false)} onCreated={async (story) => { setStoryOpen(false); setSelectedStory(story); await refresh(); setView("reader"); }} />}
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
  return <article className="story-card">
    <button className={`cover cover-${index % 5}`} onClick={onOpen} aria-label={`Open ${story.title}`}>
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

function SettingsView({ theme, onTheme }: { theme: string; onTheme: (theme: "light" | "dark") => void }) {
  return <section className="page settings-page"><div className="page-heading"><div><p className="eyebrow">Reading room</p><h1>Settings</h1><p>A few quiet choices for your private library.</p></div></div>
    <div className="settings-card"><div><h2>Appearance</h2><p>Choose a comfortable reading surface.</p></div><div className="segmented"><button className={theme === "light" ? "active" : ""} onClick={() => onTheme("light")}>Warm paper</button><button className={theme === "dark" ? "active" : ""} onClick={() => onTheme("dark")}>Night ink</button></div></div>
    <div className="settings-card"><div><h2>Private by design</h2><p>Your authors, stories, cast, reading place, and continuity records live in this private application. There is no public profile or story discovery.</p></div><span className="privacy-seal">Private</span></div>
    <div className="settings-card"><div><h2>Narration</h2><p>Voices come from your browser or device. Your preferred voice and speed are remembered per story.</p></div></div>
  </section>;
}

function Reader({ story, onStory, onBack, onAuthor, onError }: { story: Story; onStory: (story: Story) => void; onBack: () => void; onAuthor: (author: AuthorProfile) => void; onError: (error: string) => void }) {
  const [turnNumber, setTurnNumber] = useState(Math.min(story.readingTurnNumber || story.latestAcceptedTurnNumber, story.latestAcceptedTurnNumber));
  const [writing, setWriting] = useState(false);
  const [note, setNote] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [paused, setPaused] = useState(false);
  const [rate, setRate] = useState(story.playbackRate || 1);
  const [voiceId, setVoiceId] = useState(story.defaultNarrationVoice || "");
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [autoRead, setAutoRead] = useState(story.autoReadNext);
  const [autoWrite, setAutoWrite] = useState(story.autoWriteNext);
  const [regen, setRegen] = useState<{ candidate: TurnResult; original: Turn } | null>(null);
  const [regenerating, setRegenerating] = useState(false);
  const storyRef = useRef(story); const turnRef = useRef(turnNumber); const autoReadRef = useRef(autoRead); const autoWriteRef = useRef(autoWrite); const noteRef = useRef(note); const writingRef = useRef(false);
  const speechCharRef = useRef(0); const speechTextRef = useRef(""); const manualCancelRef = useRef(false);
  const speakTurnRef = useRef<(target: number, startAt?: number) => void>(() => {});
  const current = story.turns?.find((turn) => turn.turnNumber === turnNumber) || story.turns?.at(-1);

  useEffect(() => {
    storyRef.current = story;
    turnRef.current = turnNumber;
    autoReadRef.current = autoRead;
    autoWriteRef.current = autoWrite;
    noteRef.current = note;
  }, [story, turnNumber, autoRead, autoWrite, note]);

  useEffect(() => {
    const loadVoices = () => setVoices(window.speechSynthesis?.getVoices() || []);
    loadVoices(); window.speechSynthesis?.addEventListener("voiceschanged", loadVoices);
    return () => { window.speechSynthesis?.removeEventListener("voiceschanged", loadVoices); window.speechSynthesis?.cancel(); };
  }, []);

  const persist = useCallback((nextTurn = turnRef.current, nextRate = rate, nextAutoRead = autoReadRef.current, nextAutoWrite = autoWriteRef.current, nextVoice = voiceId) => {
    void api({ action: "updatePreferences", storyId: storyRef.current.id, readingTurnNumber: nextTurn, playbackRate: nextRate, autoReadNext: nextAutoRead, autoWriteNext: nextAutoWrite, voiceId: nextVoice }).catch(() => {});
  }, [rate, voiceId]);

  const continueWriting = useCallback(async (background = false) => {
    if (writingRef.current) return;
    const latest = storyRef.current.latestAcceptedTurnNumber;
    if (background && turnRef.current !== latest) return;
    writingRef.current = true; setWriting(true);
    const direction = noteRef.current;
    try {
      const result = await api<{ story: Story }>({ action: "continueStory", storyId: storyRef.current.id, note: direction });
      storyRef.current = result.story; onStory(result.story);
      if (direction && noteRef.current === direction) { noteRef.current = ""; setNote(""); }
      if (!background) { setTurnNumber(result.story.latestAcceptedTurnNumber); turnRef.current = result.story.latestAcceptedTurnNumber; }
    } catch (err) { onError(message(err)); }
    finally { writingRef.current = false; setWriting(false); }
  }, [onError, onStory]);

  const speakTurn = useCallback((target: number, startAt = 0) => {
    const synth = window.speechSynthesis;
    const item = storyRef.current.turns?.find((turn) => turn.turnNumber === target);
    if (!synth || !item) return;
    manualCancelRef.current = true; synth.cancel(); manualCancelRef.current = false;
    speechTextRef.current = item.prose; speechCharRef.current = startAt;
    setTurnNumber(target); turnRef.current = target; setSpeaking(true); setPaused(false);
    const utterance = new SpeechSynthesisUtterance(item.prose.slice(startAt));
    utterance.rate = rate;
    const chosen = voices.find((voice) => voice.voiceURI === voiceId || voice.name === voiceId);
    if (chosen) utterance.voice = chosen;
    utterance.onboundary = (event) => { speechCharRef.current = startAt + event.charIndex; };
    utterance.onend = () => {
      if (manualCancelRef.current) return;
      setSpeaking(false); setPaused(false);
      const latestStory = storyRef.current;
      const next = target + 1;
      if (autoReadRef.current && latestStory.turns?.some((turn) => turn.turnNumber === next)) {
        window.setTimeout(() => speakTurnRef.current(next), 30);
      } else if (autoReadRef.current && writingRef.current) {
        const wait = window.setInterval(() => {
          if (storyRef.current.turns?.some((turn) => turn.turnNumber === next)) { clearInterval(wait); speakTurnRef.current(next); }
          else if (!writingRef.current) clearInterval(wait);
        }, 400);
      }
    };
    utterance.onerror = () => { setSpeaking(false); setPaused(false); onError("Narration stopped. The prose is safe, and you can try playing it again."); };
    synth.speak(utterance);
    persist(target);
    if (autoWriteRef.current && target === storyRef.current.latestAcceptedTurnNumber) void continueWriting(true);
  }, [continueWriting, onError, persist, rate, voiceId, voices]);

  useEffect(() => { speakTurnRef.current = speakTurn; }, [speakTurn]);

  function togglePlay() {
    const synth = window.speechSynthesis;
    if (!synth || !current) return;
    if (speaking && !paused) { synth.pause(); setPaused(true); return; }
    if (speaking && paused) { synth.resume(); setPaused(false); return; }
    speakTurn(current.turnNumber);
  }

  function stopAudio() { manualCancelRef.current = true; window.speechSynthesis?.cancel(); manualCancelRef.current = false; setSpeaking(false); setPaused(false); }
  function skipNarration(seconds: number) {
    if (!speaking || !speechTextRef.current) return;
    const next = Math.max(0, Math.min(speechTextRef.current.length - 1, speechCharRef.current + seconds * 18));
    speakTurn(turnRef.current, next);
  }
  function move(target: number) { stopAudio(); setTurnNumber(target); turnRef.current = target; persist(target); }
  function toggleAutoWrite(next: boolean) { setAutoWrite(next); autoWriteRef.current = next; if (next) { setAutoRead(true); autoReadRef.current = true; } persist(turnNumber, rate, next ? true : autoRead, next, voiceId); }

  if (!current) return <div className="quiet-loading">The first page is being prepared…</div>;
  const paragraphs = current.prose.split(/\n\s*\n/).filter(Boolean);
  return <section className="reader-shell">
    <div className="reader-top"><button className="reader-back" onClick={onBack}>← Library</button><div><strong>{story.title}</strong><button onClick={() => onAuthor(story.authorSnapshot)}>by {story.authorSnapshot.displayName}</button></div><button className="secondary small" onClick={() => setDrawer(true)}>Cast &amp; story</button></div>
    <article className="reader-page"><p className="section-label">Section {current.turnNumber} of {story.latestAcceptedTurnNumber}</p><h1>{story.title}</h1><button className="reader-author" onClick={() => onAuthor(story.authorSnapshot)}>{story.authorSnapshot.displayName}</button><div className="prose">{paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div></article>
    <div className="reader-actions"><button className="ghost" disabled={turnNumber <= 1} onClick={() => move(turnNumber - 1)}>← Previous section</button>
      {turnNumber < story.latestAcceptedTurnNumber ? <button className="secondary" onClick={() => move(turnNumber + 1)}>Next section →</button> : <button className="continue-button" disabled={writing} onClick={() => void continueWriting(false)}>{writing ? <><span className="ink-dot" /> The author is writing…</> : "Continue writing →"}</button>}
    </div>
    <div className="note-panel"><button onClick={() => setNoteOpen(!noteOpen)}><span>Note to the author</span><small>Optional direction for one section</small><b>{noteOpen ? "−" : "+"}</b></button>{noteOpen && <div><textarea value={note} onChange={(event) => setNote(event.target.value)} maxLength={500} placeholder="Stay with this character. Slow the scene down. Reveal what is behind the door…" /><p>{writing ? `The current draft is already underway. This note will wait for Section ${story.latestAcceptedTurnNumber + 2}.` : "Clears automatically after the next section is written."}</p></div>}</div>
    <div className="reader-secondary"><button className="ghost danger" disabled={regenerating || writing || turnNumber !== story.latestAcceptedTurnNumber} onClick={async () => {
      if (!confirm("Prepare a new version of the latest section? The original will remain until you choose.")) return;
      setRegenerating(true); try { setRegen(await api({ action: "regenerateLatest", storyId: story.id, note })); } catch (err) { onError(message(err)); } finally { setRegenerating(false); }
    }}>{regenerating ? "Preparing another version…" : "Regenerate latest section"}</button></div>

    <div className="audio-dock" aria-label="Narration controls"><button className="play-button" onClick={togglePlay} aria-label={speaking && !paused ? "Pause narration" : "Play narration"}>{speaking && !paused ? "Ⅱ" : "▶"}</button><div className="audio-title"><strong>Section {turnNumber}</strong><span>{writing && autoWrite ? "The author is writing the next section…" : speaking ? (paused ? "Narration paused" : "Narrating") : "Ready to listen"}</span></div><button className="skip" onClick={() => skipNarration(-10)} aria-label="Skip narration backward ten seconds">−10</button><button className="skip" onClick={() => skipNarration(10)} aria-label="Skip narration forward ten seconds">+10</button><label>Speed<select value={rate} onChange={(event) => { const next = Number(event.target.value); setRate(next); persist(turnNumber, next); }}><option value="0.8">0.8×</option><option value="1">1×</option><option value="1.2">1.2×</option><option value="1.5">1.5×</option><option value="1.8">1.8×</option></select></label><label>Voice<select value={voiceId} onChange={(event) => { setVoiceId(event.target.value); persist(turnNumber, rate, autoRead, autoWrite, event.target.value); }}><option value="">Device default</option>{voices.map((voice) => <option key={voice.voiceURI} value={voice.voiceURI}>{voice.name}</option>)}</select></label><label className="switch-label"><input type="checkbox" checked={autoRead} onChange={(event) => { setAutoRead(event.target.checked); autoReadRef.current = event.target.checked; if (!event.target.checked && autoWrite) toggleAutoWrite(false); else persist(turnNumber, rate, event.target.checked, autoWrite); }} /><span />Auto read next</label><label className="switch-label"><input type="checkbox" checked={autoWrite} disabled={typeof window === "undefined" || !("speechSynthesis" in window)} onChange={(event) => toggleAutoWrite(event.target.checked)} /><span />Auto write next</label></div>

    {drawer && <StoryDrawer story={story} onClose={() => setDrawer(false)} />}
    {regen && <RegenerationDialog data={regen} onClose={() => setRegen(null)} onAccept={async () => { try { const result = await api<{ story: Story }>({ action: "acceptRegeneration", storyId: story.id, candidate: regen.candidate }); onStory(result.story); storyRef.current = result.story; setRegen(null); } catch (err) { onError(message(err)); } }} />}
  </section>;
}

function StoryDrawer({ story, onClose }: { story: Story; onClose: () => void }) {
  return <div className="drawer-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><aside className="story-drawer"><div className="drawer-heading"><div><p className="eyebrow">Cast &amp; story</p><h2>{story.title}</h2></div><button onClick={onClose}>×</button></div><p>{story.shortDescription}</p><dl className="story-facts"><dt>Where</dt><dd>{story.storyState?.currentLocation}</dd><dt>Now</dt><dd>{story.storyState?.currentScene}</dd><dt>Story pressure</dt><dd>{story.storyState?.currentNarrativePressure}</dd></dl><h3>Known cast</h3><div className="cast-list">{story.cast?.map((member: CastMember) => <article key={member.id}><span>{initials(member.name)}</span><div><h4>{member.name}</h4><small>{member.narrativeRole} · {member.pronouns}</small><p>{member.readerKnownSummary || member.physicalDescription}</p><em>{member.currentStatus} · {member.currentLocation}</em></div></article>)}</div></aside></div>;
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

import { createAuthorProfile, createCheckpoint, createStoryFoundation, continueStory, repairTurn, validationIssues } from "../../../lib/ai";
import { ensureDatabase, getD1, json, now, words } from "../../../lib/app-db";
import type { AuthorProfile, CastMember, Story, StoryFoundation, StoryState, Turn, TurnResult } from "../../../lib/types";

export const dynamic = "force-dynamic";

type Row = Record<string, string | number | null>;

export async function GET(request: Request) {
  try {
    await ensureDatabase();
    const url = new URL(request.url);
    const storyId = url.searchParams.get("storyId");
    if (storyId) {
      const story = await loadStory(storyId, true);
      if (!story) return Response.json({ error: "Story not found." }, { status: 404 });
      return Response.json({ story });
    }
    return Response.json(await loadLibrary());
  } catch (error) {
    return routeError(error);
  }
}

export async function POST(request: Request) {
  try {
    await ensureDatabase();
    const body = await request.json() as Record<string, unknown>;
    const action = String(body.action || "");

    if (action === "previewAuthor") {
      const genres = stringList(body.genres);
      const description = String(body.description || "").trim();
      if (!genres.length || !description) return bad("Choose at least one genre and describe your storyteller.");
      const profile = await createAuthorProfile({
        genres,
        name: String(body.name || "").trim(),
        description,
        revision: String(body.revision || "").trim(),
      });
      return Response.json({ profile });
    }

    if (action === "saveAuthor") {
      const incoming = body.profile as AuthorProfile;
      if (!incoming?.displayName || !incoming?.shortDescription) return bad("The author preview is incomplete.");
      const db = getD1();
      const stamp = now();
      const profile = { ...incoming, id: incoming.id || crypto.randomUUID(), createdAt: incoming.createdAt || stamp, updatedAt: stamp, archived: false };
      await db.prepare(`INSERT INTO authors (id, display_name, short_description, profile_json, archived, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        ON CONFLICT(id) DO UPDATE SET display_name=excluded.display_name, short_description=excluded.short_description,
        profile_json=excluded.profile_json, updated_at=excluded.updated_at`).bind(
        profile.id, profile.displayName, profile.shortDescription, JSON.stringify(profile), profile.createdAt, profile.updatedAt,
      ).run();
      return Response.json({ author: profile });
    }

    if (action === "archiveAuthor") {
      const authorId = String(body.authorId || "");
      const db = getD1();
      const used = await db.prepare("SELECT COUNT(*) AS count FROM stories WHERE selected_author_id = ?").bind(authorId).first<Row>();
      if (!body.confirm) return Response.json({ requiresConfirmation: true, storyCount: Number(used?.count || 0) });
      await db.prepare("UPDATE authors SET archived = 1, updated_at = ? WHERE id = ?").bind(now(), authorId).run();
      return Response.json({ ok: true });
    }

    if (action === "createStory") return await handleCreateStory(body);
    if (action === "continueStory") return await handleContinue(body);
    if (action === "regenerateLatest") return await handleRegenerate(body);
    if (action === "acceptRegeneration") return await handleAcceptRegeneration(body);

    if (action === "updatePreferences") {
      const storyId = String(body.storyId || "");
      const readingTurnNumber = Math.max(1, Number(body.readingTurnNumber || 1));
      const playbackRate = Math.round(Math.max(0.7, Math.min(2, Number(body.playbackRate || 1))) * 100);
      await getD1().prepare(`UPDATE stories SET reading_turn_number=?, playback_rate=?, auto_read_next=?, auto_write_next=?,
        default_narration_voice=COALESCE(?, default_narration_voice), updated_at=? WHERE id=?`).bind(
        readingTurnNumber, playbackRate, body.autoReadNext ? 1 : 0, body.autoWriteNext ? 1 : 0,
        String(body.voiceId || "") || null, now(), storyId,
      ).run();
      return Response.json({ ok: true });
    }

    if (action === "setStoryStatus") {
      const status = String(body.status || "");
      if (!["Active", "Finished", "Archived"].includes(status)) return bad("Unknown story status.");
      await getD1().prepare("UPDATE stories SET status=?, updated_at=? WHERE id=?").bind(status, now(), String(body.storyId || "")).run();
      return Response.json({ ok: true });
    }

    return bad("Unknown library action.");
  } catch (error) {
    return routeError(error);
  }
}

async function loadLibrary() {
  const db = getD1();
  const [authorResult, storyResult] = await Promise.all([
    db.prepare("SELECT * FROM authors ORDER BY archived ASC, updated_at DESC").all<Row>(),
    db.prepare("SELECT * FROM stories ORDER BY CASE status WHEN 'Active' THEN 0 WHEN 'Finished' THEN 1 ELSE 2 END, updated_at DESC").all<Row>(),
  ]);
  return {
    authors: authorResult.results.map(authorFromRow),
    stories: storyResult.results.map(storyFromRow),
  };
}

async function handleCreateStory(body: Record<string, unknown>) {
  const authorId = String(body.authorId || "");
  const idea = String(body.idea || "").trim();
  const title = String(body.title || "").trim();
  if (!authorId || !idea) return bad("Choose an author and tell them what kind of story you want.");
  const db = getD1();
  const authorRow = await db.prepare("SELECT * FROM authors WHERE id = ? AND archived = 0").bind(authorId).first<Row>();
  if (!authorRow) return bad("That author is no longer available.");
  const author = authorFromRow(authorRow);
  const generated = await createStoryFoundation({ author, idea, title });
  let firstTurn = generated.firstTurn;
  let issues = validationIssues(firstTurn);
  if (issues.length) {
    firstTurn = await repairTurn({
      draft: firstTurn, issues, author, foundation: generated.foundation,
      state: generated.initialState, cast: generated.foundation.initialCast, nextTurnNumber: 1,
    });
    issues = validationIssues(firstTurn);
  }
  if (issues.length) throw new Error(`The opening section did not pass continuity review: ${issues.join("; ")}. Please try again.`);

  const storyId = crypto.randomUUID();
  const turnId = crypto.randomUUID();
  const narration = makeNarration(storyId, turnId, firstTurn.narrationVoiceHint, 1);
  const stamp = now();
  const stateDelta = {
    ...firstTurn.stateDelta,
    priorState: generated.initialState,
    nextStoryState: firstTurn.nextStoryState,
    priorCast: generated.foundation.initialCast,
    turnIntent: firstTurn.turnIntent,
  };
  const statements = [
    db.prepare(`INSERT INTO stories (id,title,short_description,selected_author_id,author_snapshot_json,original_idea,
      foundation_json,status,latest_accepted_turn_number,latest_checkpoint_turn_number,default_narration_voice,
      main_viewpoint_character_id,reading_turn_number,playback_rate,auto_read_next,auto_write_next,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,'Active',1,0,?,?,1,100,0,0,?,?)`).bind(
      storyId, generated.foundation.title, generated.foundation.shortDescription, authorId, JSON.stringify(author), idea,
      JSON.stringify(generated.foundation), firstTurn.narrationVoiceHint, generated.foundation.mainViewpointCharacterId, stamp, stamp,
    ),
    db.prepare(`INSERT INTO turns (id,story_id,turn_number,prose,word_count,direction_used,state_delta_json,narration_json,generation_status,validation_status,created_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(
      turnId, storyId, 1, firstTurn.prose, words(firstTurn.prose), "", JSON.stringify(stateDelta), JSON.stringify(narration),
      "Accepted", issues.length ? "Accepted after repair" : "Passed", stamp,
    ),
    db.prepare("INSERT INTO narrations (id,story_id,turn_id,voice_id,voice_presentation,playback_rate,status,audio_reference,created_at) VALUES (?,?,?,?,?,100,'Ready','browser-speech-synthesis',?)").bind(
      narration.id, storyId, turnId, narration.voiceId, narration.voicePresentation, stamp,
    ),
    db.prepare("INSERT INTO story_states (story_id,state_json,last_updated_turn) VALUES (?,?,1)").bind(storyId, JSON.stringify(firstTurn.nextStoryState)),
    db.prepare("INSERT INTO checkpoints (id,story_id,through_turn_number,checkpoint_json,created_at) VALUES (?,?,0,?,?)").bind(
      crypto.randomUUID(), storyId, JSON.stringify({
        throughTurnNumber: 0, compactStorySummary: generated.foundation.openingSituation,
        canonicalCast: generated.foundation.initialCast, canonicalWorldFacts: generated.foundation.initialWorldFacts,
        currentLocation: generated.initialState.currentLocation, activeThreads: generated.foundation.initialOpenPlotThreads,
        factsThatMustRemainTrue: generated.foundation.factsThatMustRemainTrue,
      }), stamp,
    ),
  ];
  for (const member of mergeCast(generated.foundation.initialCast, firstTurn.castUpdates, 1)) statements.push(castUpsert(db, storyId, member, 1));
  await db.batch(statements);
  const story = await loadStory(storyId, true);
  return Response.json({ story }, { status: 201 });
}

async function handleContinue(body: Record<string, unknown>) {
  const storyId = String(body.storyId || "");
  const note = String(body.note || "").trim();
  const story = await loadStory(storyId, true);
  if (!story) return Response.json({ error: "Story not found." }, { status: 404 });
  if (story.status !== "Active") return bad("Only active stories can be continued.");
  const db = getD1();
  const nextTurnNumber = story.latestAcceptedTurnNumber + 1;
  const key = `${storyId}:${nextTurnNumber}`;
  const existing = await db.prepare("SELECT status FROM generation_jobs WHERE idempotency_key=?").bind(key).first<Row>();
  if (existing?.status === "generating") return Response.json({ error: "The author is already writing this section." }, { status: 409 });
  if (existing?.status === "completed") {
    const refreshed = await loadStory(storyId, true);
    return Response.json({ story: refreshed, alreadyCompleted: true });
  }
  await db.prepare(`INSERT INTO generation_jobs (idempotency_key,story_id,turn_number,status,updated_at) VALUES (?,?,?,'generating',?)
    ON CONFLICT(idempotency_key) DO UPDATE SET status='generating', error=NULL, updated_at=excluded.updated_at`).bind(key, storyId, nextTurnNumber, now()).run();

  try {
    const checkpointRow = await db.prepare("SELECT checkpoint_json FROM checkpoints WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(storyId).first<Row>();
    const recent = (story.turns || []).slice(-3).map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, stateDelta: turn.stateDelta }));
    const priorCast = story.cast || [];
    let result = await continueStory({
      author: story.authorSnapshot, foundation: story.foundation, checkpoint: json(String(checkpointRow?.checkpoint_json || ""), {}),
      state: story.storyState!, cast: priorCast, recentTurns: recent, nextTurnNumber, note,
    });
    let issues = validationIssues(result, recent.at(-1)?.prose || "");
    if (issues.length) {
      result = await repairTurn({ draft: result, issues, author: story.authorSnapshot, foundation: story.foundation,
        state: story.storyState!, cast: priorCast, nextTurnNumber });
      issues = validationIssues(result, recent.at(-1)?.prose || "");
    }
    if (issues.length) throw new Error(`The section did not pass continuity review: ${issues.join("; ")}. Your existing story is unchanged.`);
    const latest = await db.prepare("SELECT latest_accepted_turn_number FROM stories WHERE id=?").bind(storyId).first<Row>();
    if (Number(latest?.latest_accepted_turn_number) !== nextTurnNumber - 1) throw new Error("A newer section arrived first. This late draft was safely discarded.");
    const turnId = crypto.randomUUID();
    const narration = makeNarration(storyId, turnId, result.narrationVoiceHint, nextTurnNumber);
    const stateDelta = { ...result.stateDelta, priorState: story.storyState, nextStoryState: result.nextStoryState, priorCast, turnIntent: result.turnIntent };
    const mergedCast = mergeCast(priorCast, result.castUpdates, nextTurnNumber);
    const stamp = now();
    const statements = [
      db.prepare(`INSERT INTO turns (id,story_id,turn_number,prose,word_count,direction_used,state_delta_json,narration_json,generation_status,validation_status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(turnId, storyId, nextTurnNumber, result.prose, words(result.prose), note,
        JSON.stringify(stateDelta), JSON.stringify(narration), "Accepted", issues.length ? "Accepted after repair" : "Passed", stamp),
      db.prepare("INSERT INTO narrations (id,story_id,turn_id,voice_id,voice_presentation,playback_rate,status,audio_reference,created_at) VALUES (?,?,?,?,?,100,'Ready','browser-speech-synthesis',?)").bind(
        narration.id, storyId, turnId, narration.voiceId, narration.voicePresentation, stamp),
      db.prepare("UPDATE story_states SET state_json=?, last_updated_turn=? WHERE story_id=?").bind(JSON.stringify(result.nextStoryState), nextTurnNumber, storyId),
      db.prepare("UPDATE stories SET latest_accepted_turn_number=?, updated_at=? WHERE id=?").bind(nextTurnNumber, stamp, storyId),
      db.prepare("UPDATE generation_jobs SET status='completed', updated_at=? WHERE idempotency_key=?").bind(stamp, key),
    ];
    for (const member of mergedCast) statements.push(castUpsert(db, storyId, member, nextTurnNumber));
    await db.batch(statements);
    await maybeCheckpoint(storyId, nextTurnNumber, result.stateDelta);
    return Response.json({ story: await loadStory(storyId, true) });
  } catch (error) {
    await db.prepare("UPDATE generation_jobs SET status='failed', error=?, updated_at=? WHERE idempotency_key=?").bind(message(error), now(), key).run();
    throw error;
  }
}

async function handleRegenerate(body: Record<string, unknown>) {
  const story = await loadStory(String(body.storyId || ""), true);
  if (!story?.turns?.length) return bad("There is no latest section to regenerate.");
  const latest = story.turns.at(-1)!;
  const delta = latest.stateDelta as { priorState?: StoryState; priorCast?: CastMember[] };
  const priorState = delta.priorState || story.storyState!;
  const priorCast = Array.isArray(delta.priorCast) ? delta.priorCast : story.cast || [];
  const previousTurns = story.turns.slice(0, -1).slice(-3);
  let candidate = await continueStory({
    author: story.authorSnapshot, foundation: story.foundation, checkpoint: {}, state: priorState, cast: priorCast,
    recentTurns: previousTurns.map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, stateDelta: turn.stateDelta })),
    nextTurnNumber: latest.turnNumber, note: String(body.note || latest.directionUsed || ""),
  });
  let issues = validationIssues(candidate, previousTurns.at(-1)?.prose || "");
  if (issues.length) {
    candidate = await repairTurn({ draft: candidate, issues, author: story.authorSnapshot, foundation: story.foundation,
      state: priorState, cast: priorCast, nextTurnNumber: latest.turnNumber });
    issues = validationIssues(candidate, previousTurns.at(-1)?.prose || "");
  }
  if (issues.length) throw new Error(`The new version did not pass continuity review: ${issues.join("; ")}. The original remains unchanged.`);
  return Response.json({ candidate, validationStatus: issues.length ? "Accepted after repair" : "Passed", original: latest });
}

async function handleAcceptRegeneration(body: Record<string, unknown>) {
  const storyId = String(body.storyId || "");
  const candidate = body.candidate as TurnResult;
  const story = await loadStory(storyId, true);
  if (!story?.turns?.length || !candidate?.prose || !candidate?.nextStoryState) return bad("The replacement draft is incomplete.");
  const latest = story.turns.at(-1)!;
  const delta = latest.stateDelta as { priorState?: StoryState; priorCast?: CastMember[] };
  const priorCast = Array.isArray(delta.priorCast) ? delta.priorCast : story.cast || [];
  const mergedCast = mergeCast(priorCast, candidate.castUpdates || [], latest.turnNumber);
  const db = getD1();
  const previousCheckpoint = await db.prepare("SELECT MAX(through_turn_number) AS turn_number FROM checkpoints WHERE story_id=? AND through_turn_number<?").bind(storyId, latest.turnNumber).first<Row>();
  const previousCheckpointTurn = Number(previousCheckpoint?.turn_number || 0);
  const turnId = crypto.randomUUID();
  const narration = makeNarration(storyId, turnId, candidate.narrationVoiceHint, latest.turnNumber);
  const stateDelta = { ...candidate.stateDelta, priorState: delta.priorState, nextStoryState: candidate.nextStoryState, priorCast, turnIntent: candidate.turnIntent };
  const stamp = now();
  const statements = [
    db.prepare("DELETE FROM narrations WHERE turn_id=?").bind(latest.id),
    db.prepare("DELETE FROM turns WHERE id=? AND story_id=? AND turn_number=?").bind(latest.id, storyId, latest.turnNumber),
    db.prepare(`INSERT INTO turns (id,story_id,turn_number,prose,word_count,direction_used,state_delta_json,narration_json,generation_status,validation_status,created_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(turnId, storyId, latest.turnNumber, candidate.prose, words(candidate.prose), latest.directionUsed,
      JSON.stringify(stateDelta), JSON.stringify(narration), "Accepted", "Regenerated", stamp),
    db.prepare("INSERT INTO narrations (id,story_id,turn_id,voice_id,voice_presentation,playback_rate,status,audio_reference,created_at) VALUES (?,?,?,?,?,100,'Ready','browser-speech-synthesis',?)").bind(
      narration.id, storyId, turnId, narration.voiceId, narration.voicePresentation, stamp),
    db.prepare("UPDATE story_states SET state_json=?, last_updated_turn=? WHERE story_id=?").bind(JSON.stringify(candidate.nextStoryState), latest.turnNumber, storyId),
    db.prepare("DELETE FROM cast_members WHERE story_id=?").bind(storyId),
    db.prepare("DELETE FROM checkpoints WHERE story_id=? AND through_turn_number>=?").bind(storyId, latest.turnNumber),
    db.prepare("UPDATE stories SET latest_checkpoint_turn_number=?, updated_at=? WHERE id=?").bind(previousCheckpointTurn, stamp, storyId),
  ];
  for (const member of mergedCast) statements.push(castUpsert(db, storyId, member, latest.turnNumber));
  await db.batch(statements);
  if (story.latestCheckpointTurnNumber >= latest.turnNumber) await maybeCheckpoint(storyId, latest.turnNumber, candidate.stateDelta, true);
  return Response.json({ story: await loadStory(storyId, true) });
}

async function maybeCheckpoint(storyId: string, throughTurnNumber: number, stateDelta?: unknown, force = false) {
  try {
    const db = getD1();
    const story = await loadStory(storyId, true);
    if (!story) return;
    const delta = stateDelta && typeof stateDelta === "object" ? stateDelta as Record<string, unknown> : {};
    const checkpointRecommended = delta.checkpointRecommended === true;
    const intervalDue = throughTurnNumber - story.latestCheckpointTurnNumber >= 12;
    if (!force && !intervalDue && !checkpointRecommended) return;
    const previousRow = await db.prepare("SELECT checkpoint_json, through_turn_number FROM checkpoints WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(storyId).first<Row>();
    const after = Number(previousRow?.through_turn_number || 0);
    const turns = (story.turns || []).filter((turn) => turn.turnNumber > after).map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, delta: turn.stateDelta }));
    const checkpoint = await createCheckpoint({ previous: json(String(previousRow?.checkpoint_json || ""), {}), turns,
      state: story.storyState!, cast: story.cast || [], throughTurnNumber });
    const stamp = now();
    await db.batch([
      db.prepare("INSERT OR REPLACE INTO checkpoints (id,story_id,through_turn_number,checkpoint_json,created_at) VALUES (?,?,?,?,?)").bind(
        crypto.randomUUID(), storyId, throughTurnNumber, JSON.stringify(checkpoint), stamp),
      db.prepare("UPDATE stories SET latest_checkpoint_turn_number=?, updated_at=? WHERE id=?").bind(throughTurnNumber, stamp, storyId),
    ]);
  } catch {
    // Accepted prose and per-turn deltas remain authoritative; reconciliation can be retried later.
  }
}

async function loadStory(storyId: string, includeDetails: boolean): Promise<Story | null> {
  const db = getD1();
  const row = await db.prepare("SELECT * FROM stories WHERE id=?").bind(storyId).first<Row>();
  if (!row) return null;
  const story = storyFromRow(row);
  if (!includeDetails) return story;
  const [turnRows, castRows, stateRow] = await Promise.all([
    db.prepare("SELECT * FROM turns WHERE story_id=? ORDER BY turn_number ASC").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM cast_members WHERE story_id=? ORDER BY name ASC").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM story_states WHERE story_id=?").bind(storyId).first<Row>(),
  ]);
  story.turns = turnRows.results.map(turnFromRow);
  story.cast = castRows.results.map((cast: Row) => json<CastMember>(String(cast.canonical_json || ""), {} as CastMember));
  story.storyState = json<StoryState>(String(stateRow?.state_json || ""), {} as StoryState);
  return story;
}

function authorFromRow(row: Row): AuthorProfile {
  return { ...json<AuthorProfile>(String(row.profile_json || ""), {} as AuthorProfile), id: String(row.id),
    archived: Boolean(row.archived), createdAt: String(row.created_at), updatedAt: String(row.updated_at) };
}

function storyFromRow(row: Row): Story {
  return {
    id: String(row.id), title: String(row.title), shortDescription: String(row.short_description),
    selectedAuthorId: String(row.selected_author_id), authorSnapshot: json(String(row.author_snapshot_json || ""), {} as AuthorProfile),
    originalIdea: String(row.original_idea), foundation: json(String(row.foundation_json || ""), {} as StoryFoundation),
    status: String(row.status) as Story["status"], latestAcceptedTurnNumber: Number(row.latest_accepted_turn_number),
    latestCheckpointTurnNumber: Number(row.latest_checkpoint_turn_number), defaultNarrationVoice: String(row.default_narration_voice || ""),
    mainViewpointCharacterId: String(row.main_viewpoint_character_id || ""), readingTurnNumber: Number(row.reading_turn_number || 1),
    playbackRate: Number(row.playback_rate || 100) / 100, autoReadNext: Boolean(row.auto_read_next), autoWriteNext: Boolean(row.auto_write_next),
    createdAt: String(row.created_at), updatedAt: String(row.updated_at),
  };
}

function turnFromRow(row: Row): Turn {
  return {
    id: String(row.id), storyId: String(row.story_id), turnNumber: Number(row.turn_number), prose: String(row.prose),
    wordCount: Number(row.word_count), createdAt: String(row.created_at), directionUsed: String(row.direction_used || ""),
    stateDelta: json(String(row.state_delta_json || ""), {}), narration: json(String(row.narration_json || ""), {}),
    generationStatus: String(row.generation_status), validationStatus: String(row.validation_status),
  };
}

function makeNarration(storyId: string, turnId: string, hint: string, turnNumber: number) {
  return { id: crypto.randomUUID(), storyId, turnId, voiceId: hint || "neutral", voicePresentation: hint || "Neutral",
    playbackRate: 1, status: "Ready", audioReference: "browser-speech-synthesis", duration: null, turnNumber, createdAt: now() };
}

function mergeCast(existing: CastMember[], updates: CastMember[], turn: number) {
  const map = new Map(existing.map((member) => [member.id, member]));
  for (const update of updates) map.set(update.id, { ...(map.get(update.id) || {}), ...update, lastUpdatedTurn: turn } as CastMember);
  return [...map.values()];
}

function castUpsert(db: D1Database, storyId: string, member: CastMember, turn: number) {
  const dbId = `${storyId}:${member.id}`;
  const visible = { id: member.id, name: member.name, pronouns: member.pronouns, narrativeRole: member.narrativeRole,
    readerKnownSummary: member.readerKnownSummary, importantRelationships: member.importantRelationships,
    currentStatus: member.currentStatus, currentLocation: member.currentLocation };
  return db.prepare(`INSERT INTO cast_members (id,story_id,name,visible_json,canonical_json,last_updated_turn) VALUES (?,?,?,?,?,?)
    ON CONFLICT(id) DO UPDATE SET name=excluded.name,visible_json=excluded.visible_json,canonical_json=excluded.canonical_json,last_updated_turn=excluded.last_updated_turn`).bind(
      dbId, storyId, member.name, JSON.stringify(visible), JSON.stringify(member), turn,
    );
}

function stringList(value: unknown) { return Array.isArray(value) ? value.map(String).map((item) => item.trim()).filter(Boolean) : []; }
function bad(error: string) { return Response.json({ error }, { status: 400 }); }
function message(error: unknown) { return error instanceof Error ? error.message : "Something interrupted the author."; }
function routeError(error: unknown) { return Response.json({ error: message(error) }, { status: 500 }); }

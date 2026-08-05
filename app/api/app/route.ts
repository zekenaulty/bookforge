import { AiFailure, createAuthorProfile, createCheckpoint, createContextReconciliation, createStoryFoundation, continueStory, repairTurn, validationIssues } from "../../../lib/ai";
import { ensureDatabase, getArtBucket, getD1, json, now, words } from "../../../lib/app-db";
import { generateGoogleImage, GoogleImageFailure, selectedGoogleImageModel } from "../../../lib/google-image";
import { isGoogleImageModel } from "../../../lib/image-models";
import { recordOperationLog } from "../../../lib/operation-log";
import { buildStoryPdf } from "../../../lib/story-pdf";
import { mergeEntityAppearanceGuides, nextReconciliationThrough, observationsFromGuides, seedEntityAppearanceGuides } from "../../../lib/entity-continuity";
import { regenerationTargetsCurrentTurn, storyTailMatches } from "../../../lib/story-revision";
import { artAttemptObjectKey } from "../../../lib/art-storage";
import type { ArtAsset, AuthorProfile, BackgroundJob, CastMember, ContextSnapshot, EntityAppearanceGuide, EntityAppearanceObservation, OperationLog, Story, StoryArtProfile, StoryFoundation, StoryState, Turn, TurnResult, VisualProfile, WritingJob } from "../../../lib/types";

export const dynamic = "force-dynamic";

type Row = Record<string, string | number | null>;
const WRITER_LEASE_MS = 12 * 60_000;
const TEXT_BACKGROUND_LEASE_MS = 12 * 60_000;
const CONTEXT_RECONCILE_INTERVAL = 12;

class ApiRouteFailure extends Error {
  restartRequired = false;
  constructor(message: string, public category: string, public recoverable: boolean, public retryAfterMs = 0) { super(message); }
}

export async function GET(request: Request) {
  let storyId = "";
  let operation = "load_library";
  try {
    await ensureDatabase();
    const url = new URL(request.url);
    const assetId = url.searchParams.get("assetId");
    if (assetId) { operation = "load_art_asset"; return await serveArtAsset(assetId); }
    storyId = url.searchParams.get("storyId") || "";
    if (storyId) {
      operation = url.searchParams.get("format") === "pdf" ? "compile_story_pdf" : "load_story";
      const story = await loadStory(storyId, true);
      if (!story) return Response.json({ error: "Story not found." }, { status: 404 });
      if (url.searchParams.get("format") === "pdf") {
        const bytes = await buildStoryPdf(story);
        const filename = `${story.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "") || "living-story"}.pdf`;
        return new Response(bytes as BodyInit, { headers: { "content-type": "application/pdf", "content-disposition": `attachment; filename="${filename}"`, "cache-control": "private, no-store" } });
      }
      return Response.json({ story });
    }
    if (url.searchParams.get("logs") === "1") return Response.json({ logs: await loadLogs() });
    return Response.json(await loadLibrary());
  } catch (error) {
    return routeError(error, { storyId, operation });
  }
}

export async function POST(request: Request) {
  let action = "api_post";
  let storyId = "";
  let turnNumber: number | undefined;
  try {
    await ensureDatabase();
    const body = await request.json() as Record<string, unknown>;
    action = String(body.action || "api_post");
    storyId = String(body.storyId || "");
    turnNumber = Number.isFinite(Number(body.turnNumber)) ? Number(body.turnNumber) : undefined;

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
    if (action === "runBackgroundJob") return await handleRunBackgroundJob(body);
    if (action === "retryBackgroundJob") return await handleRetryBackgroundJob(body);
    if (action === "queueArt") return await handleQueueArt(body);

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
    return routeError(error, { storyId, turnNumber, operation: action });
  }
}

async function loadLibrary() {
  const db = getD1();
  const [authorResult, storyResult, artResult, coverJobResult] = await Promise.all([
    db.prepare("SELECT * FROM authors ORDER BY archived ASC, updated_at DESC").all<Row>(),
    db.prepare("SELECT * FROM stories ORDER BY CASE status WHEN 'Active' THEN 0 WHEN 'Finished' THEN 1 ELSE 2 END, updated_at DESC").all<Row>(),
    db.prepare("SELECT * FROM art_assets WHERE type='cover' ORDER BY created_at DESC").all<Row>(),
    db.prepare("SELECT * FROM background_jobs WHERE job_type='art_cover' ORDER BY updated_at DESC").all<Row>(),
  ]);
  const covers = new Map<string, ArtAsset[]>();
  for (const row of artResult.results) {
    const asset = artFromRow(row);
    const current = covers.get(asset.storyId) || [];
    current.push(asset);
    covers.set(asset.storyId, current);
  }
  const coverJobs = new Map<string, BackgroundJob[]>();
  for (const row of coverJobResult.results) {
    const job = jobFromRow(row);
    const current = coverJobs.get(job.storyId) || [];
    current.push(job);
    coverJobs.set(job.storyId, current);
  }
  return {
    authors: authorResult.results.map(authorFromRow),
    stories: storyResult.results.map((row) => ({
      ...storyFromRow(row),
      art: covers.get(String(row.id)) || [],
      jobs: coverJobs.get(String(row.id)) || [],
    })),
    logs: await loadLogs(20),
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
  const storyId = crypto.randomUUID();
  const generated = await createStoryFoundation({ author, idea, title, storyId });
  let firstTurn = generated.firstTurn;
  let issues = validationIssues(firstTurn);
  if (issues.length) {
    firstTurn = await repairTurn({
      storyId, draft: firstTurn, issues, author, foundation: generated.foundation,
      state: generated.initialState, cast: generated.foundation.initialCast, nextTurnNumber: 1,
    });
    issues = validationIssues(firstTurn);
  }
  if (issues.length) throw new Error(`The opening section did not pass continuity review: ${issues.join("; ")}. Please try again.`);

  const turnId = crypto.randomUUID();
  const narration = makeNarration(storyId, turnId, firstTurn.narrationVoiceHint, 1);
  const openingCast = mergeCast(generated.foundation.initialCast, firstTurn.castUpdates, 1);
  const stamp = now();
  const stateDelta = {
    ...firstTurn.stateDelta,
    priorState: generated.initialState,
    nextStoryState: firstTurn.nextStoryState,
    priorCast: generated.foundation.initialCast,
    nextCast: openingCast,
    turnIntent: firstTurn.turnIntent,
  };
  const artProfile = initialArtProfile(generated.foundation);
  const entityGuides = seedEntityAppearanceGuides({ ...generated.foundation, initialCast: openingCast }, 1);
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
    db.prepare("INSERT INTO story_art_profiles (story_id,profile_json,last_updated_turn,updated_at) VALUES (?,?,1,?)").bind(
      storyId, JSON.stringify(artProfile), stamp,
    ),
  ];
  const coverAssetId = crypto.randomUUID();
  statements.push(db.prepare(`INSERT INTO art_assets (id,story_id,turn_id,turn_number,type,category,title,caption,prompt_summary,status,created_at,updated_at)
    VALUES (?,?,?,1,'cover','Cover',?,?,?,'Placeholder',?,?)`).bind(
    coverAssetId, storyId, turnId, `${generated.foundation.title} cover`, `Cover for ${generated.foundation.title}`, coverPromptSummary(generated.foundation, artProfile, entityGuides), stamp, stamp,
  ));
  statements.push(enqueueJobStatement(db, { id: `art_cover:${storyId}:1`, storyId, turnNumber: 1, jobType: "art_cover", input: { assetId: coverAssetId, briefReady: true } }));
  statements.push(enqueueJobStatement(db, { id: `context_reconcile:${storyId}:1`, storyId, turnNumber: 1, jobType: "context_reconcile", input: { reason: "initial visual and character context" } }));
  for (const member of openingCast) statements.push(castUpsert(db, storyId, member, 1));
  for (const guide of entityGuides) statements.push(entityAppearanceGuideUpsert(db, storyId, guide, stamp));
  for (const observation of observationsFromGuides(storyId, entityGuides, 1, 0, "", stamp)) statements.push(entityAppearanceObservationUpsert(db, observation));
  await db.batch(statements);
  const story = await loadStory(storyId, true);
  return Response.json({ story }, { status: 201 });
}

async function handleContinue(body: Record<string, unknown>) {
  const storyId = String(body.storyId || "");
  const note = String(body.note || "").trim();
  const story = await loadStory(storyId, true);
  if (!story) return Response.json({ error: "Story not found." }, { status: 404 });
  const requestedLatest = Number(body.expectedLatestTurnNumber);
  const expectedLatest = Number.isSafeInteger(requestedLatest) && requestedLatest >= 0
    ? requestedLatest
    : story.latestAcceptedTurnNumber;
  if (story.latestAcceptedTurnNumber > expectedLatest) {
    return Response.json({ story, alreadyCompleted: true });
  }
  if (story.latestAcceptedTurnNumber < expectedLatest) {
    return Response.json({ error: "This reader is ahead of the saved story. Refresh before writing another section." }, { status: 409 });
  }
  if (story.status !== "Active") return bad("Only active stories can be continued.");
  const db = getD1();
  const nextTurnNumber = expectedLatest + 1;
  const predecessorTurnId = story.turns?.at(-1)?.id || "";
  const key = `${storyId}:${nextTurnNumber}`;
  const existing = await db.prepare("SELECT status,error,updated_at FROM generation_jobs WHERE idempotency_key=?").bind(key).first<Row>();
  const generationUpdatedAt = Date.parse(String(existing?.updated_at || ""));
  const staleGeneration = existing?.status === "generating"
    && (!Number.isFinite(generationUpdatedAt) || generationUpdatedAt < Date.now() - WRITER_LEASE_MS);
  if (existing?.status === "generating" && !staleGeneration) return Response.json({
    error: "The author is already writing this section.", category: "writer_lease", recoverable: true, retryAfterMs: 2_000,
  }, { status: 409 });
  if (staleGeneration) await recordOperationLog({ storyId, turnNumber: nextTurnNumber, operation: "continue_story", category: "stale_generation_resume",
    attempt: 1, status: "recovered", message: "Resumed writing after an interrupted request left a stale generation lock." });
  if (existing?.status === "completed") {
    const refreshed = await loadStory(storyId, true);
    return Response.json({ story: refreshed, alreadyCompleted: true });
  }
  const generationLease = `lease:${crypto.randomUUID()}`;
  const claimStamp = now();
  if (!existing) {
    await db.prepare("INSERT OR IGNORE INTO generation_jobs (idempotency_key,story_id,turn_number,status,error,updated_at) VALUES (?,?,?,'generating',?,?)")
      .bind(key, storyId, nextTurnNumber, generationLease, claimStamp).run();
  } else {
    await db.prepare(`UPDATE generation_jobs SET status='generating',error=?,updated_at=? WHERE idempotency_key=? AND COALESCE(error,'')=?
      AND ((status='failed' AND updated_at=?) OR (status='generating' AND updated_at=?))`).bind(
      generationLease, claimStamp, key, String(existing.error || ""), String(existing.updated_at || ""), String(existing.updated_at || ""),
    ).run();
  }
  const claimedGeneration = await db.prepare("SELECT status,error FROM generation_jobs WHERE idempotency_key=?").bind(key).first<Row>();
  if (String(claimedGeneration?.status || "") === "completed") return Response.json({ story: await loadStory(storyId, true), alreadyCompleted: true });
  if (String(claimedGeneration?.error || "") !== generationLease) {
    return Response.json({ error: "The author is already writing this section.", category: "writer_lease", recoverable: true, retryAfterMs: 2_000 }, { status: 409 });
  }

  try {
    const checkpointRow = await db.prepare("SELECT checkpoint_json FROM checkpoints WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(storyId).first<Row>();
    const contextRow = await db.prepare("SELECT snapshot_json FROM context_snapshots WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(storyId).first<Row>();
    const recent = (story.turns || []).slice(-3).map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, stateDelta: turn.stateDelta }));
    const priorCast = story.cast || [];
    let result = await continueStory({
      storyId, author: story.authorSnapshot, foundation: story.foundation, checkpoint: json(String(checkpointRow?.checkpoint_json || ""), {}),
      state: story.storyState!, cast: priorCast, recentTurns: recent, nextTurnNumber, note,
      managedContext: { ...json<Record<string, unknown>>(String(contextRow?.snapshot_json || ""), {}), entityAppearanceGuides: story.entityAppearanceGuides || [] },
    });
    await refreshGenerationLease(db, key, generationLease);
    let issues = validationIssues(result, recent.at(-1)?.prose || "");
    if (issues.length) {
      result = await repairTurn({ storyId, draft: result, issues, author: story.authorSnapshot, foundation: story.foundation,
        state: story.storyState!, cast: priorCast, nextTurnNumber });
      await refreshGenerationLease(db, key, generationLease);
      issues = validationIssues(result, recent.at(-1)?.prose || "");
    }
    if (issues.length) throw new Error(`The section did not pass continuity review: ${issues.join("; ")}. Your existing story is unchanged.`);
    const [latest, latestTurn] = await Promise.all([
      db.prepare("SELECT latest_accepted_turn_number FROM stories WHERE id=?").bind(storyId).first<Row>(),
      db.prepare("SELECT id FROM turns WHERE story_id=? ORDER BY turn_number DESC LIMIT 1").bind(storyId).first<Row>(),
    ]);
    if (!storyTailMatches({ turnNumber: nextTurnNumber - 1, turnId: predecessorTurnId }, {
      turnNumber: latest?.latest_accepted_turn_number, turnId: latestTurn?.id,
    })) {
      throw new ApiRouteFailure("The preceding section changed while this draft was being written. The late draft was safely discarded.",
        "writer_predecessor_changed", true);
    }
    const ownedGeneration = await db.prepare("SELECT idempotency_key FROM generation_jobs WHERE idempotency_key=? AND status='generating' AND error=?").bind(key, generationLease).first<Row>();
    if (!ownedGeneration) throw new Error("A resumed writing request replaced this late draft, so it was safely discarded.");
    const turnId = crypto.randomUUID();
    const narration = makeNarration(storyId, turnId, result.narrationVoiceHint, nextTurnNumber);
    const mergedCast = mergeCast(priorCast, result.castUpdates, nextTurnNumber);
    const stateDelta = { ...result.stateDelta, priorState: story.storyState, nextStoryState: result.nextStoryState, priorCast, nextCast: mergedCast, turnIntent: result.turnIntent };
    const stamp = now();
    const mutationGuardId = `writer:${key}:${crypto.randomUUID()}`;
    const statements = [
      writerMutationGuardStatement(db, {
        id: mutationGuardId, storyId, expectedTurnNumber: nextTurnNumber - 1, expectedTurnId: predecessorTurnId,
        generationKey: key, generationLease, stamp,
      }),
      db.prepare(`INSERT INTO turns (id,story_id,turn_number,prose,word_count,direction_used,state_delta_json,narration_json,generation_status,validation_status,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)`).bind(turnId, storyId, nextTurnNumber, result.prose, words(result.prose), note,
        JSON.stringify(stateDelta), JSON.stringify(narration), "Accepted", issues.length ? "Accepted after repair" : "Passed", stamp),
      db.prepare("INSERT INTO narrations (id,story_id,turn_id,voice_id,voice_presentation,playback_rate,status,audio_reference,created_at) VALUES (?,?,?,?,?,100,'Ready','browser-speech-synthesis',?)").bind(
        narration.id, storyId, turnId, narration.voiceId, narration.voicePresentation, stamp),
      db.prepare("UPDATE story_states SET state_json=?, last_updated_turn=? WHERE story_id=?").bind(JSON.stringify(result.nextStoryState), nextTurnNumber, storyId),
      db.prepare("UPDATE stories SET latest_accepted_turn_number=?, updated_at=? WHERE id=?").bind(nextTurnNumber, stamp, storyId),
      db.prepare("UPDATE generation_jobs SET status='completed',error=NULL,updated_at=? WHERE idempotency_key=? AND status='generating' AND error=?").bind(stamp, key, generationLease),
    ];
    for (const member of mergedCast) statements.push(castUpsert(db, storyId, member, nextTurnNumber));
    for (const statement of automaticJobStatements(db, story, nextTurnNumber, result.stateDelta, turnId)) statements.push(statement);
    statements.push(mutationGuardReleaseStatement(db, mutationGuardId));
    try {
      await db.batch(statements);
    } catch (error) {
      if (isMutationGuardFailure(error)) throw new ApiRouteFailure(
        "The preceding section changed while this draft was being written. The late draft was safely discarded.",
        "writer_predecessor_changed", true,
      );
      throw error;
    }
    return Response.json({ story: await loadStory(storyId, true) });
  } catch (error) {
    const failure = writingFailure(error);
    await db.prepare("UPDATE generation_jobs SET status='failed', error=?, updated_at=? WHERE idempotency_key=? AND status='generating' AND error=?")
      .bind(JSON.stringify(failure), now(), key, generationLease).run();
    throw new ApiRouteFailure(failure.message, failure.category, failure.recoverable, failure.retryAfterMs);
  }
}

async function handleRegenerate(body: Record<string, unknown>) {
  const story = await loadStory(String(body.storyId || ""), true);
  if (!story?.turns?.length) return bad("There is no latest section to regenerate.");
  const latest = story.turns.at(-1)!;
  const delta = latest.stateDelta as { priorState?: StoryState; priorCast?: CastMember[] };
  const priorState = delta.priorState || story.storyState!;
  const priorCast = Array.isArray(delta.priorCast) ? delta.priorCast : story.cast || [];
  const previousTurns = story.turns.slice(0, -1).slice(-12);
  const db = getD1();
  const [previousContextRow, previousCheckpointRow] = await Promise.all([
    db.prepare("SELECT snapshot_json FROM context_snapshots WHERE story_id=? AND through_turn_number<? ORDER BY through_turn_number DESC LIMIT 1")
      .bind(story.id, latest.turnNumber).first<Row>(),
    db.prepare("SELECT checkpoint_json FROM checkpoints WHERE story_id=? AND through_turn_number<? ORDER BY through_turn_number DESC LIMIT 1")
      .bind(story.id, latest.turnNumber).first<Row>(),
  ]);
  const previousContext = json<ContextSnapshot | undefined>(String(previousContextRow?.snapshot_json || ""), undefined);
  const previousGuides = previousContext?.entityAppearanceGuides || [];
  const preSectionGuides = mergeEntityAppearanceGuides(previousGuides, seedEntityAppearanceGuides({
    ...story.foundation, setting: previousGuides.length ? "" : story.foundation.setting, initialCast: priorCast,
  }, Math.max(1, latest.turnNumber - 1)), Math.max(1, latest.turnNumber - 1));
  let candidate = await continueStory({
    storyId: story.id, author: story.authorSnapshot, foundation: story.foundation,
    checkpoint: json(String(previousCheckpointRow?.checkpoint_json || ""), {}), state: priorState, cast: priorCast,
    recentTurns: previousTurns.map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, stateDelta: turn.stateDelta })),
    nextTurnNumber: latest.turnNumber, note: String(body.note || latest.directionUsed || ""),
    managedContext: { ...(previousContext || {}), entityAppearanceGuides: preSectionGuides },
  });
  let issues = validationIssues(candidate, previousTurns.at(-1)?.prose || "");
  if (issues.length) {
    candidate = await repairTurn({ storyId: story.id, draft: candidate, issues, author: story.authorSnapshot, foundation: story.foundation,
      state: priorState, cast: priorCast, nextTurnNumber: latest.turnNumber });
    issues = validationIssues(candidate, previousTurns.at(-1)?.prose || "");
  }
  if (issues.length) throw new Error(`The new version did not pass continuity review: ${issues.join("; ")}. The original remains unchanged.`);
  candidate.turnIntent = { ...candidate.turnIntent, intendedTurnNumber: latest.turnNumber, regenerationOfTurnId: latest.id };
  return Response.json({ candidate, validationStatus: issues.length ? "Accepted after repair" : "Passed", original: latest });
}

async function handleAcceptRegeneration(body: Record<string, unknown>) {
  const storyId = String(body.storyId || "");
  const candidate = body.candidate as TurnResult;
  const story = await loadStory(storyId, true);
  if (!story?.turns?.length || !candidate?.prose || !candidate?.nextStoryState) return bad("The replacement draft is incomplete.");
  const latest = story.turns.at(-1)!;
  if (!regenerationTargetsCurrentTurn(candidate.turnIntent, latest)) {
    return Response.json({ error: "The story changed after this replacement was drafted. Regenerate the current latest section again.",
      category: "stale_regeneration", recoverable: false, retryAfterMs: 0 }, { status: 409 });
  }
  const delta = latest.stateDelta as { priorState?: StoryState; priorCast?: CastMember[] };
  const priorCast = Array.isArray(delta.priorCast) ? delta.priorCast : story.cast || [];
  const mergedCast = mergeCast(priorCast, candidate.castUpdates || [], latest.turnNumber);
  const db = getD1();
  const [previousCheckpoint, previousContextRow] = await Promise.all([
    db.prepare("SELECT MAX(through_turn_number) AS turn_number FROM checkpoints WHERE story_id=? AND through_turn_number<?").bind(storyId, latest.turnNumber).first<Row>(),
    db.prepare("SELECT snapshot_json,through_turn_number FROM context_snapshots WHERE story_id=? AND through_turn_number<? ORDER BY through_turn_number DESC LIMIT 1")
      .bind(storyId, latest.turnNumber).first<Row>(),
  ]);
  const previousCheckpointTurn = Number(previousCheckpoint?.turn_number || 0);
  const previousContext = json<ContextSnapshot | undefined>(String(previousContextRow?.snapshot_json || ""), undefined);
  const rollbackTurn = Math.max(1, latest.turnNumber - 1);
  const rollbackSeed = seedEntityAppearanceGuides({
    ...story.foundation,
    setting: previousContext?.entityAppearanceGuides?.length ? "" : story.foundation.setting,
    initialCast: priorCast,
  }, rollbackTurn);
  const rollbackGuides = mergeEntityAppearanceGuides(previousContext?.entityAppearanceGuides || [], rollbackSeed, rollbackTurn);
  const rollbackArtProfile = previousContext?.storyArtProfile || initialArtProfile(story.foundation);
  const writerGuardKey = `${storyId}:${latest.turnNumber + 1}`;
  const writerGuardLease = `lease:regeneration:${crypto.randomUUID()}`;
  if (!await claimGenerationGuard(db, writerGuardKey, storyId, latest.turnNumber + 1, writerGuardLease)) {
    return Response.json({ error: "The next section is already being written or the story advanced. Wait for it to finish, then regenerate the latest section again.",
      category: "writer_lease", recoverable: true, retryAfterMs: 2_000 }, { status: 409 });
  }
  const turnId = crypto.randomUUID();
  const narration = makeNarration(storyId, turnId, candidate.narrationVoiceHint, latest.turnNumber);
  const stateDelta = { ...candidate.stateDelta, priorState: delta.priorState, nextStoryState: candidate.nextStoryState, priorCast, nextCast: mergedCast, turnIntent: candidate.turnIntent };
  const stamp = now();
  const mutationGuardId = `regeneration:${storyId}:${latest.turnNumber}:${crypto.randomUUID()}`;
  const statements = [
    regenerationMutationGuardStatement(db, {
      id: mutationGuardId, storyId, expectedTurnNumber: latest.turnNumber, expectedTurnId: latest.id,
      generationKey: writerGuardKey, generationLease: writerGuardLease, stamp,
    }),
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
    db.prepare("DELETE FROM context_snapshots WHERE story_id=? AND through_turn_number>=?").bind(storyId, latest.turnNumber),
    db.prepare("DELETE FROM entity_appearance_observations WHERE story_id=? AND turn_number>=?").bind(storyId, latest.turnNumber),
    db.prepare("DELETE FROM entity_appearance_guides WHERE story_id=?").bind(storyId),
    db.prepare("DELETE FROM visual_profiles WHERE story_id=?").bind(storyId),
    db.prepare(`INSERT INTO story_art_profiles (story_id,profile_json,last_updated_turn,updated_at) VALUES (?,?,?,?)
      ON CONFLICT(story_id) DO UPDATE SET profile_json=excluded.profile_json,last_updated_turn=excluded.last_updated_turn,updated_at=excluded.updated_at`).bind(
      storyId, JSON.stringify(rollbackArtProfile), rollbackTurn, stamp),
    db.prepare(`UPDATE background_jobs SET status='failed',last_error='Superseded by regenerated section',locked_at=NULL,updated_at=? WHERE story_id=?
      AND ((job_type IN ('context_reconcile','checkpoint_reconcile') AND COALESCE(turn_number,0)>=? AND status IN ('pending','retrying'))
        OR (job_type='art_scene' AND turn_number=? AND status IN ('pending','running','retrying')))`)
      .bind(stamp, storyId, latest.turnNumber, latest.turnNumber),
    db.prepare("UPDATE generation_jobs SET status='failed',error=?,updated_at=? WHERE idempotency_key=? AND status='generating' AND error=?").bind(
      JSON.stringify({ message: "The preceding section was regenerated; the in-flight draft must restart from the accepted replacement.",
        category: "writer_predecessor_changed", recoverable: true, retryAfterMs: 0 }), stamp, writerGuardKey, writerGuardLease),
    db.prepare("UPDATE art_assets SET status='Failed',caption='Superseded by regenerated section',updated_at=? WHERE story_id=? AND turn_number=? AND type<>'cover'").bind(stamp, storyId, latest.turnNumber),
    db.prepare("UPDATE stories SET latest_checkpoint_turn_number=?, updated_at=? WHERE id=?").bind(previousCheckpointTurn, stamp, storyId),
  ];
  for (const member of mergedCast) statements.push(castUpsert(db, storyId, member, latest.turnNumber));
  for (const guide of rollbackGuides) statements.push(entityAppearanceGuideUpsert(db, storyId, guide, stamp));
  statements.push(enqueueJobStatement(db, { id: `context_reconcile:${storyId}:${latest.turnNumber}:regen:${turnId}`, storyId, turnNumber: latest.turnNumber, jobType: "context_reconcile", input: { reason: "latest section regenerated", force: true, rebuildFromTurn: latest.turnNumber } }));
  if (story.latestCheckpointTurnNumber >= latest.turnNumber) statements.push(enqueueJobStatement(db, { id: `checkpoint_reconcile:${storyId}:${latest.turnNumber}:regen:${turnId}`, storyId, turnNumber: latest.turnNumber, jobType: "checkpoint_reconcile", input: { force: true } }));
  statements.push(mutationGuardReleaseStatement(db, mutationGuardId));
  try {
    await db.batch(statements);
  } catch (error) {
    await db.prepare("UPDATE generation_jobs SET status='failed',error=?,updated_at=? WHERE idempotency_key=? AND status='generating' AND error=?")
      .bind(JSON.stringify({ message: "The regeneration did not commit; the next writing attempt may safely resume.", category: "regeneration_commit", recoverable: true, retryAfterMs: 0 }),
        now(), writerGuardKey, writerGuardLease).run();
    if (isMutationGuardFailure(error)) {
      return Response.json({ error: "The story changed before this replacement could be saved. Regenerate the current latest section again.",
        category: "stale_regeneration", recoverable: false, retryAfterMs: 0 }, { status: 409 });
    }
    throw error;
  }
  return Response.json({ story: await loadStory(storyId, true) });
}

type JobType = BackgroundJob["jobType"];

function enqueueJobStatement(db: D1Database, job: { id: string; storyId: string; turnNumber?: number; jobType: JobType; input?: Record<string, unknown> }) {
  const stamp = now();
  const maxAttempts = job.jobType.startsWith("art_") ? 2 : 3;
  return db.prepare(`INSERT OR IGNORE INTO background_jobs
    (id,story_id,turn_number,job_type,status,attempts,max_attempts,run_after,input_json,result_json,created_at,updated_at)
    VALUES (?,?,?,?,'pending',0,?,?,?,'{}',?,?)`).bind(
    job.id, job.storyId, job.turnNumber ?? null, job.jobType, maxAttempts, stamp, JSON.stringify(job.input || {}), stamp, stamp,
  );
}

function enqueueReusableJobStatement(db: D1Database, job: { id: string; storyId: string; turnNumber?: number; jobType: JobType; input?: Record<string, unknown> }) {
  const stamp = now();
  const maxAttempts = job.jobType.startsWith("art_") ? 2 : 3;
  return db.prepare(`INSERT INTO background_jobs
    (id,story_id,turn_number,job_type,status,attempts,max_attempts,run_after,input_json,result_json,last_error,locked_at,created_at,updated_at)
    VALUES (?,?,?,?,'pending',0,?,?,?,'{}',NULL,NULL,?,?)
    ON CONFLICT(id) DO UPDATE SET story_id=excluded.story_id,turn_number=excluded.turn_number,job_type=excluded.job_type,
      status='pending',attempts=0,max_attempts=excluded.max_attempts,run_after=excluded.run_after,input_json=excluded.input_json,result_json='{}',
      last_error=NULL,locked_at=NULL,updated_at=excluded.updated_at
    WHERE background_jobs.status IN ('completed','failed','unsupported')`).bind(
    job.id, job.storyId, job.turnNumber ?? null, job.jobType, maxAttempts, stamp, JSON.stringify(job.input || {}), stamp, stamp,
  );
}

function automaticJobStatements(db: D1Database, story: Story, turnNumber: number, stateDelta: Record<string, unknown>, turnId: string) {
  const statements: D1PreparedStatement[] = [];
  const majorChange = stateDelta?.checkpointRecommended === true;
  if (turnNumber % CONTEXT_RECONCILE_INTERVAL === 0 || majorChange) statements.push(enqueueJobStatement(db, {
    id: `context_reconcile:${story.id}:${turnNumber}`, storyId: story.id, turnNumber, jobType: "context_reconcile",
    input: { reason: majorChange ? stateDelta.checkpointReason || "major story change" : "periodic twelve-section refresh" },
  }));
  const checkpointTarget = story.latestCheckpointTurnNumber + 12;
  if (turnNumber >= checkpointTarget || majorChange) statements.push(enqueueJobStatement(db, {
    id: majorChange ? `checkpoint_reconcile:${story.id}:${turnNumber}:major:${turnId}` : `checkpoint_reconcile:${story.id}:${checkpointTarget}`,
    storyId: story.id, turnNumber, jobType: "checkpoint_reconcile",
    input: { reason: majorChange ? stateDelta.checkpointReason || "major story change" : "twelve-section reconciliation" },
  }));
  if (turnNumber % 4 === 0 || majorChange) statements.push(enqueueJobStatement(db, {
    id: `art_scene:${story.id}:${turnNumber}`, storyId: story.id, turnNumber, jobType: "art_scene", input: { turnId },
  }));
  return statements;
}

async function handleQueueArt(body: Record<string, unknown>) {
  const storyId = String(body.storyId || "");
  const type = body.type === "scene" ? "scene" : "cover";
  const story = await loadStory(storyId, true);
  if (!story) return Response.json({ error: "Story not found." }, { status: 404 });
  const turnNumber = type === "scene" ? Math.max(1, Number(body.turnNumber || story.latestAcceptedTurnNumber)) : 1;
  const turn = story.turns?.find((item) => item.turnNumber === turnNumber);
  if (type === "scene" && !turn) return bad("That section is unavailable.");
  if (body.model != null && !isGoogleImageModel(body.model)) return bad("Choose a supported Google image model.");
  const model = selectedGoogleImageModel(body.model);
  const db = getD1();
  await failExhaustedJobs(db, storyId);
  const jobType: JobType = type === "cover" ? "art_cover" : "art_scene";
  await reconcileActiveArtJobs(db, storyId, jobType, turnNumber);
  const jobId = `${jobType}:${storyId}:${turnNumber}`;
  const active = await db.prepare(`SELECT id,input_json FROM background_jobs WHERE story_id=? AND job_type=? AND turn_number=?
    AND (status='running' OR (status IN ('pending','retrying') AND attempts<max_attempts)) ORDER BY updated_at DESC LIMIT 1`).bind(storyId, jobType, turnNumber).first<Row>();
  if (active) {
    const activeInput = json<Record<string, unknown>>(String(active.input_json || ""), {});
    return Response.json({ story: await loadStory(storyId, true), jobId: String(active.id), queued: false, model: selectedGoogleImageModel(activeInput.model) });
  }

  const stamp = now();
  const assetId = crypto.randomUUID();
  const title = type === "cover" ? `${story.title} cover` : `Section ${turnNumber} illustration`;
  const artStory = type === "scene" ? await storyForArtTurn(db, story, turnNumber) : story;
  const promptSummary = type === "cover" ? coverPromptSummary(story.foundation, initialArtProfile(story.foundation), seedEntityAppearanceGuides(story.foundation, 1)) : scenePromptSummary(artStory, turn!);
  await db.batch([
    db.prepare(`INSERT INTO art_assets (id,story_id,turn_id,turn_number,type,category,title,caption,prompt_summary,status,created_at,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,'Queued',?,?)`).bind(
      assetId, storyId, turn?.id || null, turnNumber, type, type === "cover" ? "Cover" : "Scenes", title,
      type === "cover" ? `Cover for ${story.title}` : `Illustration for Section ${turnNumber}`, promptSummary, stamp, stamp,
    ),
    enqueueReusableJobStatement(db, { id: jobId, storyId, turnNumber, jobType,
      input: { assetId, turnId: turn?.id, requestedByUser: true, model, briefReady: true, briefVersion: 2 } }),
  ]);
  const claimed = await db.prepare("SELECT input_json FROM background_jobs WHERE id=?").bind(jobId).first<Row>();
  const claimedInput = json<Record<string, unknown>>(String(claimed?.input_json || ""), {});
  if (String(claimedInput.assetId || "") !== assetId) await db.prepare("DELETE FROM art_assets WHERE id=? AND status='Queued'").bind(assetId).run();
  return Response.json({ story: await loadStory(storyId, true), jobId, queued: String(claimedInput.assetId || "") === assetId,
    model: selectedGoogleImageModel(claimedInput.model) });
}

async function handleRetryBackgroundJob(body: Record<string, unknown>) {
  const jobId = String(body.jobId || "");
  if (body.model != null && !isGoogleImageModel(body.model)) return bad("Choose a supported Google image model.");
  const db = getD1();
  const row = await db.prepare("SELECT * FROM background_jobs WHERE id=?").bind(jobId).first<Row>();
  if (!row) return Response.json({ error: "That background job no longer exists." }, { status: 404 });
  if (!["failed", "retrying", "unsupported"].includes(String(row.status))) {
    return Response.json({ error: "That background job is already active or complete." }, { status: 409 });
  }
  const input = json<Record<string, unknown>>(String(row.input_json || ""), {});
  delete input.interactionId;
  if (body.model != null) {
    const nextModel = selectedGoogleImageModel(body.model);
    if (input.model && input.model !== nextModel) { delete input.objectKey; delete input.objectKeyLock; }
    input.model = nextModel;
  }
  const jobType = String(row.job_type) as JobType;
  const storyId = String(row.story_id);
  const turnNumber = Number(row.turn_number || 0);
  const activeOther = await db.prepare(`SELECT id FROM background_jobs WHERE story_id=? AND job_type=? AND turn_number=? AND id<>?
    AND (status='running' OR (status IN ('pending','retrying') AND attempts<max_attempts)) ORDER BY updated_at DESC LIMIT 1`)
    .bind(storyId, jobType, turnNumber, jobId).first<Row>();
  if (activeOther) return Response.json({ ok: true, jobId: String(activeOther.id), story: await loadStory(storyId, true), queued: false });
  let refreshedTurnId = "";
  if (jobType === "art_scene") {
    const currentTurn = await db.prepare("SELECT id FROM turns WHERE story_id=? AND turn_number=?").bind(storyId, turnNumber).first<Row>();
    if (currentTurn && String(currentTurn.id) !== String(input.turnId || "")) {
      refreshedTurnId = String(currentTurn.id);
      input.turnId = refreshedTurnId;
      input.refreshBrief = true;
      input.briefReady = false;
      delete input.objectKey;
      delete input.objectKeyLock;
    }
  }
  const stamp = now();
  const retried = await db.prepare(`UPDATE background_jobs SET status='pending',attempts=0,run_after=?,input_json=?,last_error=NULL,locked_at=NULL,updated_at=?
    WHERE id=? AND status=? AND COALESCE(updated_at,'')=? AND COALESCE(locked_at,'')=?`).bind(
    stamp, JSON.stringify(input), stamp, jobId, String(row.status), String(row.updated_at || ""), String(row.locked_at || ""),
  ).run();
  if (Number(retried.meta.changes || 0) < 1) {
    const current = await db.prepare("SELECT status FROM background_jobs WHERE id=?").bind(jobId).first<Row>();
    if (current && ["pending", "running", "retrying"].includes(String(current.status))) {
      return Response.json({ ok: true, jobId, story: await loadStory(storyId, true), queued: false });
    }
    return Response.json({ error: "That background job changed while it was being retried. Refresh its status and try again." }, { status: 409 });
  }
  if (refreshedTurnId && input.assetId) await db.prepare("UPDATE art_assets SET turn_id=?,status='Queued',caption='Queued after the section changed',prompt_summary='',updated_at=? WHERE id=? AND status<>'Ready'")
    .bind(refreshedTurnId, stamp, String(input.assetId)).run();
  if (input.assetId) await db.prepare("UPDATE art_assets SET status='Queued',updated_at=? WHERE id=? AND status<>'Ready'").bind(stamp, String(input.assetId)).run();
  return Response.json({ ok: true, jobId, story: await loadStory(storyId, true) });
}

async function handleRunBackgroundJob(body: Record<string, unknown>) {
  const db = getD1();
  const storyId = String(body.storyId || "");
  const requestedJobId = String(body.jobId || "");
  const runningRows = await db.prepare("SELECT * FROM background_jobs WHERE status='running'").all<Row>();
  const staleRows = runningRows.results.filter((row) => {
    const artJob = ["art_cover", "art_scene"].includes(String(row.job_type));
    const leaseMs = artJob ? 12 * 60_000 : TEXT_BACKGROUND_LEASE_MS;
    const updatedAt = Date.parse(String(row.updated_at || ""));
    return !Number.isFinite(updatedAt) || updatedAt < Date.now() - leaseMs;
  });
  for (const row of staleRows) {
    const exhausted = Number(row.attempts || 0) >= Number(row.max_attempts || 3);
    const stamp = now();
    const staleMessage = exhausted ? "Interrupted job exhausted its retry limit." : "Interrupted job resumed after a stale lock.";
    const staleTransition = await db.prepare(`UPDATE background_jobs SET status=?,locked_at=NULL,run_after=?,last_error=?,updated_at=?
      WHERE id=? AND status='running' AND locked_at=?`).bind(
      exhausted ? "failed" : "retrying", stamp, staleMessage, stamp, String(row.id), String(row.locked_at || ""),
    ).run();
    if (exhausted && Number(staleTransition.meta.changes || 0) > 0) {
      const staleInput = json<Record<string, unknown>>(String(row.input_json || ""), {});
      if (staleInput.assetId) await db.prepare("UPDATE art_assets SET status='Failed',updated_at=? WHERE id=? AND status IN ('Queued','Preparing')")
        .bind(stamp, String(staleInput.assetId)).run();
      await recordOperationLog({ storyId: String(row.story_id), turnNumber: Number(row.turn_number || 0), operation: String(row.job_type),
        category: "stale_job_exhausted", attempt: Number(row.attempts || 1), status: "failed", message: staleMessage });
    }
  }
  if (storyId) await ensureBaselineJobs(db, storyId);
  const jobRow = await db.prepare(`SELECT * FROM background_jobs WHERE status IN ('pending','retrying') AND attempts<max_attempts AND run_after<=?
    AND (?='' OR story_id=?) AND (?='' OR id=?)
    ORDER BY CASE job_type WHEN 'art_cover' THEN 0 WHEN 'art_scene' THEN 1 ELSE 2 END,run_after ASC,created_at ASC LIMIT 1`)
    .bind(now(), storyId, storyId, requestedJobId, requestedJobId).first<Row>();
  if (!jobRow) return Response.json({ processed: false, more: false, waiting: Boolean(requestedJobId) });
  const lock = crypto.randomUUID();
  await db.prepare(`UPDATE background_jobs SET status='running',attempts=attempts+1,locked_at=?,updated_at=?
    WHERE id=? AND status IN ('pending','retrying') AND attempts<max_attempts AND run_after<=?`).bind(lock, now(), String(jobRow.id), now()).run();
  const claimed = await db.prepare("SELECT * FROM background_jobs WHERE id=? AND status='running' AND locked_at=?").bind(String(jobRow.id), lock).first<Row>();
  if (!claimed) return Response.json({ processed: false, more: true });
  const job = jobFromRow(claimed);
  const input = json<Record<string, unknown>>(String(claimed.input_json || ""), {});
  try {
    const outcome = await processBackgroundJob(job, input, lock);
    if (outcome.deferred) {
      const runAfter = new Date(Date.now() + Math.max(2_000, outcome.runAfterMs || 5_000)).toISOString();
      await db.prepare(`UPDATE background_jobs SET status='pending',attempts=MAX(attempts-1,0),run_after=?,input_json=?,result_json=?,
        last_error=NULL,locked_at=NULL,updated_at=? WHERE id=? AND status='running' AND locked_at=?`).bind(
        runAfter, JSON.stringify(outcome.input || {}), JSON.stringify(outcome.result || {}), now(), job.id, lock,
      ).run();
    } else {
      const status = outcome.unsupported ? "unsupported" : "completed";
      const completion = await db.prepare("UPDATE background_jobs SET status=?,result_json=?,last_error=?,locked_at=NULL,updated_at=? WHERE id=? AND status='running' AND locked_at=?").bind(
        status, JSON.stringify(outcome.result || {}), outcome.message || null, now(), job.id, lock,
      ).run();
      if (outcome.unsupported && Number(completion.meta.changes || 0) > 0) await recordOperationLog({ storyId: job.storyId, turnNumber: job.turnNumber, operation: job.jobType,
        category: "native_image_unavailable", attempt: job.attempts, status: "unsupported", message: outcome.message || "Native image rendering is unavailable." });
    }
  } catch (error) {
    const failure = backgroundFailure(error);
    const retrying = failure.recoverable && job.attempts < job.maxAttempts;
    const runAfter = new Date(Date.now() + Math.max(failure.retryAfterMs, Math.min(60_000, 4_000 * 2 ** Math.max(0, job.attempts - 1)))).toISOString();
    const retryInput = { ...input };
    if (failure.restartRequired) delete retryInput.interactionId;
    const failureTransition = await db.prepare("UPDATE background_jobs SET status=?,run_after=?,input_json=?,last_error=?,locked_at=NULL,updated_at=? WHERE id=? AND status='running' AND locked_at=?").bind(
      retrying ? "retrying" : "failed", runAfter, JSON.stringify(retryInput), failure.message, now(), job.id, lock,
    ).run();
    if (Number(failureTransition.meta.changes || 0) > 0) await recordOperationLog({ storyId: job.storyId, turnNumber: job.turnNumber, operation: job.jobType, category: failure.category,
      attempt: job.attempts, status: retrying ? "retrying" : "failed", message: failure.message,
      context: { recoverable: failure.recoverable, maxAttempts: job.maxAttempts, transportTimeoutMs: 10 * 60 * 1000 } });
  }
  const more = Boolean(await db.prepare(`SELECT id FROM background_jobs WHERE status IN ('pending','retrying') AND attempts<max_attempts AND run_after<=?
    AND (?='' OR story_id=?) AND (?='' OR id=?) LIMIT 1`).bind(now(), storyId, storyId, requestedJobId, requestedJobId).first<Row>());
  return Response.json({ processed: true, jobId: job.id, more });
}

async function ensureBaselineJobs(db: D1Database, storyId: string) {
  await failExhaustedJobs(db, storyId);
  await reconcileActiveArtJobs(db, storyId);
  const [storyRow, contextRow, entityGuideRow, coverRow, activeCoverJob] = await Promise.all([
    db.prepare("SELECT title,foundation_json,latest_accepted_turn_number FROM stories WHERE id=?").bind(storyId).first<Row>(),
    db.prepare("SELECT id FROM context_snapshots WHERE story_id=? LIMIT 1").bind(storyId).first<Row>(),
    db.prepare("SELECT id FROM entity_appearance_guides WHERE story_id=? LIMIT 1").bind(storyId).first<Row>(),
    db.prepare(`SELECT * FROM art_assets WHERE story_id=? AND type='cover'
      ORDER BY CASE WHEN status='Ready' THEN 0 WHEN status IN ('Placeholder','Queued','Preparing') THEN 1 ELSE 2 END,created_at DESC LIMIT 1`).bind(storyId).first<Row>(),
    db.prepare(`SELECT id FROM background_jobs WHERE story_id=? AND job_type='art_cover'
      AND (status='running' OR (status IN ('pending','retrying') AND attempts<max_attempts)) LIMIT 1`).bind(storyId).first<Row>(),
  ]);
  if (!storyRow) return;
  const turnNumber = Math.max(1, Number(storyRow.latest_accepted_turn_number || 1));
  const statements: D1PreparedStatement[] = [];
  let repairAssetId = "";
  if (!contextRow) statements.push(enqueueJobStatement(db, {
    id: `context_reconcile:${storyId}:${turnNumber}:baseline`, storyId, turnNumber, jobType: "context_reconcile", input: { reason: "baseline context for an existing story" },
  }));
  if (!entityGuideRow) {
    const stamp = now();
    const foundation = json<StoryFoundation>(String(storyRow.foundation_json || ""), {} as StoryFoundation);
    const seedGuides = seedEntityAppearanceGuides(foundation, Math.min(1, turnNumber));
    for (const guide of seedGuides) statements.push(entityAppearanceGuideUpsert(db, storyId, guide, stamp));
    for (const observation of observationsFromGuides(storyId, seedGuides, Math.min(1, turnNumber), 0, "", stamp)) statements.push(entityAppearanceObservationUpsert(db, observation));
    statements.push(enqueueJobStatement(db, {
      id: `context_reconcile:${storyId}:${turnNumber}:entity-baseline-v1`, storyId, turnNumber, jobType: "context_reconcile",
      input: { reason: "durable entity appearance baseline for an existing story" },
    }));
  }
  const coverStatus = String(coverRow?.status || "");
  const repairableCover = !coverRow || ["Placeholder", "Queued", "Preparing"].includes(coverStatus);
  if (repairableCover && !activeCoverJob) {
    const assetId = String(coverRow?.id || `cover-baseline:${storyId}`);
    repairAssetId = assetId;
    const stamp = now();
    if (!coverRow) statements.push(db.prepare(`INSERT OR IGNORE INTO art_assets (id,story_id,turn_number,type,category,title,caption,prompt_summary,status,created_at,updated_at)
        VALUES (?,?,1,'cover','Cover',?,?,?,'Placeholder',?,?)`).bind(
        assetId, storyId, `${String(storyRow.title)} cover`, `Cover for ${String(storyRow.title)}`, "Typographic placeholder while illustrated art is prepared.", stamp, stamp,
      ));
    else statements.push(db.prepare("UPDATE art_assets SET status='Queued',updated_at=? WHERE id=?").bind(stamp, assetId));
    statements.push(enqueueReusableJobStatement(db, { id: `art_cover:${storyId}:1`, storyId, turnNumber: 1, jobType: "art_cover", input: { assetId } }));
  }
  if (statements.length) await db.batch(statements);
  if (repairAssetId) {
    const claimed = await db.prepare("SELECT input_json FROM background_jobs WHERE id=?").bind(`art_cover:${storyId}:1`).first<Row>();
    const claimedAssetId = String(json<Record<string, unknown>>(String(claimed?.input_json || ""), {}).assetId || "");
    if (claimedAssetId && claimedAssetId !== repairAssetId) {
      if (coverRow) await db.prepare("UPDATE art_assets SET status='Failed',caption='Superseded by a newer cover request',updated_at=? WHERE id=? AND status<>'Ready'")
        .bind(now(), repairAssetId).run();
      else await db.prepare("DELETE FROM art_assets WHERE id=? AND status='Placeholder'").bind(repairAssetId).run();
    }
  }
}

async function failExhaustedJobs(db: D1Database, storyId = "") {
  const rows = await db.prepare(`SELECT * FROM background_jobs WHERE status IN ('pending','retrying') AND attempts>=max_attempts
    AND (?='' OR story_id=?)`).bind(storyId, storyId).all<Row>();
  for (const row of rows.results) {
    const stamp = now();
    const error = "This job exhausted its automatic retry limit. Review the diagnostics and retry it explicitly.";
    const transition = await db.prepare("UPDATE background_jobs SET status='failed',last_error=?,locked_at=NULL,updated_at=? WHERE id=? AND status IN ('pending','retrying') AND attempts>=max_attempts")
      .bind(error, stamp, String(row.id)).run();
    if (Number(transition.meta.changes || 0) < 1) continue;
    const input = json<Record<string, unknown>>(String(row.input_json || ""), {});
    if (input.assetId) await db.prepare("UPDATE art_assets SET status='Failed',updated_at=? WHERE id=? AND status IN ('Queued','Preparing')")
      .bind(stamp, String(input.assetId)).run();
    await recordOperationLog({ storyId: String(row.story_id), turnNumber: Number(row.turn_number || 0), operation: String(row.job_type),
      category: "retry_limit", attempt: Number(row.attempts || 1), status: "failed", message: error });
  }
}

async function reconcileActiveArtJobs(db: D1Database, storyId: string, onlyType: JobType | "" = "", onlyTurn = 0) {
  const rows = await db.prepare(`SELECT * FROM background_jobs WHERE story_id=? AND job_type IN ('art_cover','art_scene')
    AND (status='running' OR (status IN ('pending','retrying') AND attempts<max_attempts))
    AND (?='' OR job_type=?) AND (?=0 OR turn_number=?) ORDER BY updated_at DESC`)
    .bind(storyId, onlyType, onlyType, onlyTurn, onlyTurn).all<Row>();
  const targets = new Map<string, Row[]>();
  for (const row of rows.results) {
    const key = `${String(row.job_type)}:${Number(row.turn_number || 0)}`;
    targets.set(key, [...(targets.get(key) || []), row]);
  }
  for (const group of targets.values()) {
    if (group.length < 2) continue;
    const first = group[0];
    const canonicalId = `${String(first.job_type)}:${storyId}:${Number(first.turn_number || 0)}`;
    const keeper = group.find((row) => String(row.status) === "running") || group.find((row) => String(row.id) === canonicalId) || first;
    for (const row of group) {
      if (String(row.id) === String(keeper.id)) continue;
      const stamp = now();
      const superseded = "Superseded by the active artwork request for the same target.";
      const transition = await db.prepare(`UPDATE background_jobs SET status='failed',last_error=?,locked_at=NULL,updated_at=? WHERE id=?
        AND (status='running' OR status IN ('pending','retrying'))`).bind(superseded, stamp, String(row.id)).run();
      if (Number(transition.meta.changes || 0) < 1) continue;
      const input = json<Record<string, unknown>>(String(row.input_json || ""), {});
      if (input.assetId) await db.prepare("UPDATE art_assets SET status='Failed',updated_at=? WHERE id=? AND status<>'Ready'")
        .bind(stamp, String(input.assetId)).run();
      await recordOperationLog({ storyId, turnNumber: Number(row.turn_number || 0), operation: String(row.job_type),
        category: "duplicate_art_job", attempt: Number(row.attempts || 1), status: "failed", message: superseded });
    }
  }
}

type BackgroundJobOutcome = { result: unknown; unsupported?: boolean; message?: string; deferred?: boolean; runAfterMs?: number; input?: Record<string, unknown> };

async function processBackgroundJob(job: BackgroundJob, input: Record<string, unknown>, lock: string): Promise<BackgroundJobOutcome> {
  if (job.jobType === "context_reconcile") return { result: await runContextJob(job, input, lock) };
  if (job.jobType === "checkpoint_reconcile") return { result: await runCheckpointJob(job, lock) };
  if (job.jobType === "art_cover" || job.jobType === "art_scene") return runArtJob(job, input, lock);
  throw new Error("Unknown background job type.");
}

async function runContextJob(job: BackgroundJob, input: Record<string, unknown>, lock: string) {
  const db = getD1();
  const story = await loadStory(job.storyId, true);
  if (!story) throw new Error("Story not found for context reconciliation.");
  const latestAccepted = story.latestAcceptedTurnNumber;
  const latestRow = await db.prepare("SELECT id,through_turn_number FROM context_snapshots WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(story.id).first<Row>();
  const latestSnapshotThrough = Number(latestRow?.through_turn_number || 0);
  const latestSnapshotId = String(latestRow?.id || "");
  if (latestSnapshotThrough >= latestAccepted && input.force !== true) {
    return { throughTurnNumber: latestAccepted, alreadyReconciled: true };
  }
  const through = nextReconciliationThrough(latestAccepted, latestSnapshotThrough);
  const boundaryTurnId = story.turns?.find((turn) => turn.turnNumber === through)?.id || "";
  if (!boundaryTurnId) throw new ApiRouteFailure("The continuity window no longer has an accepted boundary section.", "story_revision_changed", true);
  const previousRow = await db.prepare("SELECT snapshot_json,through_turn_number FROM context_snapshots WHERE story_id=? AND through_turn_number<? ORDER BY through_turn_number DESC LIMIT 1")
    .bind(story.id, through).first<Row>();
  const previousThrough = Number(previousRow?.through_turn_number || 0);
  const previousContext = json<ContextSnapshot | undefined>(String(previousRow?.snapshot_json || ""), undefined);
  const recentTurns = (story.turns || []).filter((turn) => turn.turnNumber > previousThrough && turn.turnNumber <= through)
    .map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, stateDelta: turn.stateDelta }));
  let existingGuides = previousContext?.entityAppearanceGuides?.length
    ? previousContext.entityAppearanceGuides
    : story.entityAppearanceGuides?.filter((guide) => guide.lastUpdatedTurn <= previousThrough).length
      ? story.entityAppearanceGuides.filter((guide) => guide.lastUpdatedTurn <= previousThrough)
    : seedEntityAppearanceGuides(story.foundation, Math.min(1, through));
  if (input.rebuildFromTurn && previousContext?.entityAppearanceGuides?.length) {
    const previousGuides = new Map(previousContext.entityAppearanceGuides.map((guide) => [`${guide.kind}:${guide.entityId}`, guide]));
    existingGuides = existingGuides.map((guide) => {
      const previous = previousGuides.get(`${guide.kind}:${guide.entityId}`);
      return previous ? { ...guide, current: previous.current, lastUpdatedTurn: previous.lastUpdatedTurn } : guide;
    });
  }
  const priorObservations = (story.entityAppearanceTimeline || []).filter((item) => item.turnNumber <= previousThrough).slice(-120);
  const snapshot = await createContextReconciliation({
    storyId: story.id, throughTurnNumber: through, foundation: story.foundation, state: storyStateThrough(story, through), cast: storyCastThrough(story, through),
    recentTurns, previousContext, previousArtProfile: previousContext?.storyArtProfile || initialArtProfile(story.foundation), previousEntityGuides: existingGuides,
    recentEntityObservations: priorObservations, previousThroughTurnNumber: previousThrough,
  });
  const lease = await db.prepare("SELECT id FROM background_jobs WHERE id=? AND status='running' AND locked_at=?").bind(job.id, lock).first<Row>();
  if (!lease) return { throughTurnNumber: through, cancelled: true };
  const snapshotGuides = mergeEntityAppearanceGuides(existingGuides, snapshot.entityAppearanceGuides, through);
  const latestGuideRows = await db.prepare("SELECT * FROM entity_appearance_guides WHERE story_id=? ORDER BY kind,name").bind(story.id).all<Row>();
  const latestGuides = latestGuideRows.results.map(entityAppearanceGuideFromRow).filter((guide) => guide.lastUpdatedTurn <= through);
  let mergeBase = latestGuides.length ? latestGuides : snapshotGuides;
  if (input.rebuildFromTurn) {
    const resetCurrents = new Map(existingGuides.map((guide) => [`${guide.kind}:${guide.entityId}`, guide.current]));
    mergeBase = mergeBase.map((guide) => ({ ...guide, current: resetCurrents.get(`${guide.kind}:${guide.entityId}`) || guide.current }));
  }
  const durableGuides = mergeEntityAppearanceGuides(mergeBase, snapshotGuides, through);
  const stamp = now();
  const snapshotId = crypto.randomUUID();
  const observations = observationsFromGuides(story.id, snapshotGuides, through, previousThrough, snapshotId, stamp);
  const managedSnapshot: ContextSnapshot = {
    ...snapshot,
    throughTurnNumber: through,
    storyArtProfile: snapshot.storyArtProfile || previousContext?.storyArtProfile || initialArtProfile(story.foundation),
    characterVisualProfiles: snapshot.characterVisualProfiles || [],
    locationVisualProfiles: snapshot.locationVisualProfiles || [],
    entityAppearanceGuides: snapshotGuides.map((guide) => ({ ...guide, timelineObservations: undefined })),
    entityAppearanceObservations: observations.map(({ turnNumber, summary, changes, evidence }) => ({ turnNumber, summary, changes, evidence })),
  };
  const mutationGuardId = `context:${job.id}:${through}:${crypto.randomUUID()}`;
  const statements = [
    backgroundBoundaryMutationGuardStatement(db, {
      id: mutationGuardId, storyId: story.id, throughTurnNumber: through, boundaryTurnId,
      jobId: job.id, lock, chain: "context", expectedHeadThrough: latestSnapshotThrough, expectedHeadId: latestSnapshotId, stamp,
    }),
    db.prepare("INSERT OR REPLACE INTO context_snapshots (id,story_id,through_turn_number,snapshot_json,created_at) VALUES (?,?,?,?,?)").bind(
      snapshotId, story.id, through, JSON.stringify(managedSnapshot), stamp),
    db.prepare(`INSERT INTO story_art_profiles (story_id,profile_json,last_updated_turn,updated_at) VALUES (?,?,?,?)
      ON CONFLICT(story_id) DO UPDATE SET profile_json=excluded.profile_json,last_updated_turn=excluded.last_updated_turn,updated_at=excluded.updated_at
      WHERE excluded.last_updated_turn>=story_art_profiles.last_updated_turn`).bind(
      story.id, JSON.stringify(managedSnapshot.storyArtProfile), through, stamp),
  ];
  if (through < latestAccepted) statements.push(enqueueJobStatement(db, {
    id: `context_reconcile:${story.id}:${through + 1}-${Math.min(latestAccepted, through + 12)}:catchup`, storyId: story.id,
    turnNumber: Math.min(latestAccepted, through + 12), jobType: "context_reconcile", input: { reason: "bounded continuity catch-up" },
  }));
  for (const profile of [...managedSnapshot.characterVisualProfiles, ...managedSnapshot.locationVisualProfiles]) statements.push(visualProfileUpsert(db, story.id, profile, through));
  for (const guide of durableGuides) statements.push(entityAppearanceGuideUpsert(db, story.id, guide, stamp));
  for (const observation of observations) statements.push(entityAppearanceObservationUpsert(db, observation));
  statements.push(mutationGuardReleaseStatement(db, mutationGuardId));
  try {
    await db.batch(statements);
  } catch (error) {
    if (isMutationGuardFailure(error)) throw new ApiRouteFailure(
      "The reconciled continuity window changed before it could be saved; the job will restart from the accepted timeline.",
      "story_revision_changed", true,
    );
    throw error;
  }
  return {
    throughTurnNumber: through,
    characters: managedSnapshot.characterState?.length || 0,
    visualProfiles: managedSnapshot.characterVisualProfiles.length + managedSnapshot.locationVisualProfiles.length,
    entityGuides: snapshotGuides.length,
    entityObservations: observations.length,
  };
}

async function runCheckpointJob(job: BackgroundJob, lock: string) {
  const db = getD1();
  const story = await loadStory(job.storyId, true);
  if (!story) throw new Error("Story not found for checkpoint reconciliation.");
  const latestAccepted = story.latestAcceptedTurnNumber;
  const newestRow = await db.prepare("SELECT id,through_turn_number FROM checkpoints WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(story.id).first<Row>();
  const after = Number(newestRow?.through_turn_number || 0);
  const checkpointHeadId = String(newestRow?.id || "");
  if (after >= latestAccepted) return { throughTurnNumber: latestAccepted, alreadyReconciled: true };
  const through = nextReconciliationThrough(latestAccepted, after);
  const boundaryTurnId = story.turns?.find((turn) => turn.turnNumber === through)?.id || "";
  if (!boundaryTurnId) throw new ApiRouteFailure("The checkpoint window no longer has an accepted boundary section.", "story_revision_changed", true);
  const previousRow = await db.prepare("SELECT checkpoint_json,through_turn_number FROM checkpoints WHERE story_id=? AND through_turn_number<? ORDER BY through_turn_number DESC LIMIT 1").bind(story.id, through).first<Row>();
  const turns = (story.turns || []).filter((turn) => turn.turnNumber > after && turn.turnNumber <= through).map((turn) => ({ turnNumber: turn.turnNumber, prose: turn.prose, delta: turn.stateDelta }));
  const [contextRow, entityObservationRows] = await Promise.all([
    db.prepare("SELECT snapshot_json FROM context_snapshots WHERE story_id=? AND through_turn_number<=? ORDER BY through_turn_number DESC LIMIT 1")
      .bind(story.id, through).first<Row>(),
    db.prepare("SELECT * FROM entity_appearance_observations WHERE story_id=? AND turn_number>? AND turn_number<=? ORDER BY turn_number,kind,name")
      .bind(story.id, after, through).all<Row>(),
  ]);
  const entityObservations = entityObservationRows.results.map(entityAppearanceObservationFromRow);
  const checkpointContext = json<ContextSnapshot | undefined>(String(contextRow?.snapshot_json || ""), undefined);
  const checkpoint = await createCheckpoint({ storyId: story.id, previous: json(String(previousRow?.checkpoint_json || ""), {}), turns,
    state: storyStateThrough(story, through), cast: storyCastThrough(story, through), throughTurnNumber: through,
    entityAppearanceGuides: checkpointContext?.entityAppearanceGuides
      || (story.entityAppearanceGuides || []).filter((guide) => guide.lastUpdatedTurn <= through),
    entityAppearanceObservations: entityObservations });
  const lease = await db.prepare("SELECT id FROM background_jobs WHERE id=? AND status='running' AND locked_at=?").bind(job.id, lock).first<Row>();
  if (!lease) return { throughTurnNumber: through, cancelled: true };
  const stamp = now();
  const mutationGuardId = `checkpoint:${job.id}:${through}:${crypto.randomUUID()}`;
  const statements = [
    backgroundBoundaryMutationGuardStatement(db, {
      id: mutationGuardId, storyId: story.id, throughTurnNumber: through, boundaryTurnId,
      jobId: job.id, lock, chain: "checkpoint", expectedHeadThrough: after, expectedHeadId: checkpointHeadId, stamp,
    }),
    db.prepare("INSERT OR REPLACE INTO checkpoints (id,story_id,through_turn_number,checkpoint_json,created_at) VALUES (?,?,?,?,?)").bind(
      crypto.randomUUID(), story.id, through, JSON.stringify(checkpoint), stamp),
    db.prepare("UPDATE stories SET latest_checkpoint_turn_number=MAX(latest_checkpoint_turn_number,?),updated_at=? WHERE id=?").bind(through, stamp, story.id),
  ];
  if (through < latestAccepted) statements.push(enqueueJobStatement(db, {
    id: `checkpoint_reconcile:${story.id}:${through + 1}-${Math.min(latestAccepted, through + 12)}:catchup`, storyId: story.id,
    turnNumber: Math.min(latestAccepted, through + 12), jobType: "checkpoint_reconcile", input: { reason: "bounded checkpoint catch-up" },
  }));
  statements.push(mutationGuardReleaseStatement(db, mutationGuardId));
  try {
    await db.batch(statements);
  } catch (error) {
    if (isMutationGuardFailure(error)) throw new ApiRouteFailure(
      "The checkpoint window changed before it could be saved; the job will restart from the accepted timeline.",
      "story_revision_changed", true,
    );
    throw error;
  }
  return { throughTurnNumber: through };
}

async function runArtJob(job: BackgroundJob, input: Record<string, unknown>, lock: string) {
  const story = await loadStory(job.storyId, true);
  if (!story) throw new Error("Story not found for art preparation.");
  const type = job.jobType === "art_cover" ? "cover" : "scene";
  const turn = type === "scene" ? story.turns?.find((item) => item.turnNumber === job.turnNumber) : undefined;
  if (type === "scene" && !turn) throw new GoogleImageFailure("The section selected for this illustration no longer exists.", "art_turn_missing", false);
  const db = getD1();
  const activeLease = await db.prepare("SELECT id FROM background_jobs WHERE id=? AND status='running' AND locked_at=?").bind(job.id, lock).first<Row>();
  if (!activeLease) return { result: { cancelled: true } };
  if (type === "scene" && String(input.turnId || "") !== turn!.id) {
    input.turnId = turn!.id;
    input.refreshBrief = true;
    input.briefReady = false;
    delete input.objectKey;
    delete input.objectKeyLock;
  }
  const assetId = String(input.assetId || "") || `art-asset:${job.id}`;
  input.assetId = assetId;
  const existing = await db.prepare("SELECT * FROM art_assets WHERE id=?").bind(assetId).first<Row>();
  const reusableBrief = Boolean(input.refreshBrief !== true && input.briefVersion === 2 && existing && (input.briefReady === true
    || (!["Placeholder", "Queued"].includes(String(existing.status || "")) && String(existing.prompt_summary || "").trim())));
  const artStory = type === "scene" ? await storyForArtTurn(db, story, turn!.turnNumber) : story;
  const brief = reusableBrief ? {
    shouldIllustrate: true,
    category: String(existing?.category || (type === "cover" ? "Cover" : "Scenes")) as ArtAsset["category"],
    title: String(existing?.title || (type === "cover" ? `${story.title} cover` : `Section ${job.turnNumber} illustration`)),
    caption: String(existing?.caption || ""),
    promptSummary: String(existing?.prompt_summary || ""),
  } : {
    shouldIllustrate: true,
    category: (type === "cover" ? "Cover" : "Scenes") as ArtAsset["category"],
    title: type === "cover" ? `${story.title} cover` : `Section ${job.turnNumber} illustration`,
    caption: type === "cover" ? `Cover for ${story.title}` : `Illustration for Section ${job.turnNumber}`,
    promptSummary: type === "cover"
      ? coverPromptSummary(story.foundation, initialArtProfile(story.foundation), seedEntityAppearanceGuides(story.foundation, 1))
      : scenePromptSummary(artStory, turn!),
  };
  input.briefVersion = 2;
  input.briefReady = true;
  const stamp = now();
  if (!brief.shouldIllustrate && type === "scene") {
    await db.prepare(`UPDATE art_assets SET title=?,caption=?,prompt_summary=?,status='Failed',updated_at=? WHERE id=?
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(
      brief.title, brief.caption || "This section was not selected as a strong illustration moment.", brief.promptSummary, stamp, assetId, job.id, lock,
    ).run();
    return { result: { selected: false, assetId } };
  }
  if (existing) await db.prepare(`UPDATE art_assets SET turn_id=?,category=?,title=?,caption=?,prompt_summary=?,status='Preparing',updated_at=? WHERE id=?
    AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(
    turn?.id || null, brief.category, brief.title, brief.caption, brief.promptSummary, stamp, assetId, job.id, lock,
  ).run();
  else await db.prepare(`INSERT INTO art_assets (id,story_id,turn_id,turn_number,type,category,title,caption,prompt_summary,status,created_at,updated_at)
    SELECT ?,?,?,?,?,?,?,?,?,'Preparing',?,? WHERE EXISTS
      (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(
    assetId, story.id, turn?.id || null, job.turnNumber || null, type, brief.category, brief.title, brief.caption, brief.promptSummary, stamp, stamp, job.id, lock,
  ).run();

  const bucket = getArtBucket();
  if (!bucket) {
    const unavailable = "Private art storage is not configured.";
    await db.prepare(`UPDATE art_assets SET status='Unsupported',updated_at=? WHERE id=?
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(now(), assetId, job.id, lock).run();
    return { unsupported: true, result: { assetId, brief }, message: unavailable };
  }

  const model = selectedGoogleImageModel(input.model);
  input.model = model;
  const renderVersion = type === "scene" ? turn!.id : "cover";
  const resumableKey = String(input.objectKey || "");
  const safePrefix = `stories/${story.id}/${assetId}/`;
  const stored = resumableKey.startsWith(safePrefix) ? await bucket.get(resumableKey) : null;
  if (stored) {
    const storedModel = stored.customMetadata?.model || model;
    if (storedModel === model) {
      await stored.body.cancel().catch(() => {});
      const storedMime = stored.httpMetadata?.contentType || String(existing?.mime_type || "image/jpeg");
      const recovered = await db.prepare(`UPDATE art_assets SET status='Ready',image_reference=?,mime_type=?,updated_at=? WHERE id=?
        AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(
        `r2:${resumableKey}`, storedMime, now(), assetId, job.id, lock,
      ).run();
      if (Number(recovered.meta.changes || 0) > 0) await recordOperationLog({ storyId: story.id, turnNumber: job.turnNumber, operation: job.jobType, category: "art_storage_resume",
        attempt: job.attempts, status: "recovered", message: "Recovered a completed art file after an interrupted status update." });
      return { result: { assetId, model: storedModel, mimeType: storedMime, resumed: true } };
    }
    await stored.body.cancel().catch(() => {});
  }
  const objectKey = artAttemptObjectKey({ storyId: story.id, assetId, renderVersion, model, lease: lock });
  input.objectKey = objectKey;
  input.objectKeyLock = lock;
  const persistedAttempt = await db.prepare(`UPDATE background_jobs SET input_json=?,updated_at=?
    WHERE id=? AND status='running' AND locked_at=?`).bind(JSON.stringify(input), now(), job.id, lock).run();
  if (Number(persistedAttempt.meta.changes || 0) < 1) return { result: { assetId, cancelled: true } };
  if (!process.env.GEMINI_API_KEY) {
    const unavailable = "Google image generation is not configured.";
    await db.prepare(`UPDATE art_assets SET status='Unsupported',updated_at=? WHERE id=?
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(now(), assetId, job.id, lock).run();
    return { unsupported: true, result: { assetId, brief }, message: unavailable };
  }
  const prompt = [
    `Create one finished ${type === "cover" ? "portrait book-cover illustration" : "cinematic story illustration"} for a private literary edition.`,
    brief.promptSummary,
    `Story title for context only: ${story.title}. Do not render the title or any other text in the image.`,
    "Preserve every supplied character, costume, prop, location, palette, and motif continuity detail. Avoid spoilers, watermarks, borders, mockups, and stock-art composition.",
  ].filter(Boolean).join("\n\n");
  try {
    const image = await generateGoogleImage({ prompt, model, aspectRatio: type === "cover" ? "2:3" : "16:9" });
    await bucket.put(objectKey, image.bytes, {
      httpMetadata: { contentType: image.mimeType },
      customMetadata: { storyId: story.id, assetId, model: image.model },
    });
    const published = await db.prepare(`UPDATE art_assets SET status='Ready',image_reference=?,mime_type=?,updated_at=? WHERE id=?
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(
      `r2:${objectKey}`, image.mimeType, now(), assetId, job.id, lock,
    ).run();
    if (Number(published.meta.changes || 0) < 1) return { result: { assetId, cancelled: true } };
    await recordOperationLog({ storyId: story.id, turnNumber: job.turnNumber, operation: job.jobType,
      category: "google_image_generate_content",
      attempt: job.attempts, status: "completed", message: `Generated ${type} art with ${image.model}.`, context: { model: image.model, bytes: image.bytes.byteLength } });
    return { result: { assetId, model: image.model, mimeType: image.mimeType } };
  } catch (error) {
    const failure = backgroundFailure(error);
    const retrying = failure.recoverable && job.attempts < job.maxAttempts;
    await db.prepare(`UPDATE art_assets SET status=?,updated_at=? WHERE id=?
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)`).bind(retrying ? "Preparing" : "Failed", now(), assetId, job.id, lock).run();
    throw error;
  }
}

function backgroundFailure(error: unknown) {
  if (error instanceof GoogleImageFailure) return error;
  if (error instanceof ApiRouteFailure) return error;
  return { message: message(error), category: "background_job", recoverable: true, retryAfterMs: 0, restartRequired: false };
}

function storyStateThrough(story: Story, throughTurnNumber: number): StoryState {
  if (throughTurnNumber >= story.latestAcceptedTurnNumber) return story.storyState!;
  const target = story.turns?.find((turn) => turn.turnNumber === throughTurnNumber);
  const delta = target?.stateDelta as { nextStoryState?: StoryState } | undefined;
  return delta?.nextStoryState || story.storyState!;
}

function storyCastThrough(story: Story, throughTurnNumber: number): CastMember[] {
  if (throughTurnNumber >= story.latestAcceptedTurnNumber) return story.cast || [];
  const target = story.turns?.find((turn) => turn.turnNumber === throughTurnNumber);
  const targetDelta = target?.stateDelta as { nextCast?: CastMember[] } | undefined;
  if (Array.isArray(targetDelta?.nextCast)) return targetDelta.nextCast;
  const next = story.turns?.find((turn) => turn.turnNumber === throughTurnNumber + 1);
  const nextDelta = next?.stateDelta as { priorCast?: CastMember[] } | undefined;
  return Array.isArray(nextDelta?.priorCast) ? nextDelta.priorCast : story.cast || [];
}

async function storyForArtTurn(db: D1Database, story: Story, turnNumber: number): Promise<Story> {
  const row = await db.prepare("SELECT snapshot_json FROM context_snapshots WHERE story_id=? AND through_turn_number<=? ORDER BY through_turn_number DESC LIMIT 1")
    .bind(story.id, turnNumber).first<Row>();
  const context = json<ContextSnapshot | undefined>(String(row?.snapshot_json || ""), undefined);
  return {
    ...story,
    contextSnapshot: context,
    artProfile: context?.storyArtProfile || initialArtProfile(story.foundation),
    entityAppearanceGuides: context?.entityAppearanceGuides || (story.entityAppearanceGuides || []).filter((guide) => guide.lastUpdatedTurn <= turnNumber),
    entityAppearanceTimeline: (story.entityAppearanceTimeline || []).filter((item) => item.turnNumber <= turnNumber),
  };
}

function writerMutationGuardStatement(db: D1Database, input: {
  id: string; storyId: string; expectedTurnNumber: number; expectedTurnId: string;
  generationKey: string; generationLease: string; stamp: string;
}) {
  return db.prepare(`INSERT INTO mutation_guards (id,story_id,asserted,created_at)
    SELECT ?,?,CASE WHEN
      EXISTS (SELECT 1 FROM stories WHERE id=? AND latest_accepted_turn_number=?)
      AND COALESCE((SELECT MAX(turn_number) FROM turns WHERE story_id=?),0)=?
      AND COALESCE((SELECT id FROM turns WHERE story_id=? ORDER BY turn_number DESC LIMIT 1),'')=?
      AND EXISTS (SELECT 1 FROM generation_jobs WHERE idempotency_key=? AND status='generating' AND error=?)
    THEN 1 ELSE 0 END,?`).bind(
    input.id, input.storyId, input.storyId, input.expectedTurnNumber,
    input.storyId, input.expectedTurnNumber, input.storyId, input.expectedTurnId,
    input.generationKey, input.generationLease, input.stamp,
  );
}

function regenerationMutationGuardStatement(db: D1Database, input: {
  id: string; storyId: string; expectedTurnNumber: number; expectedTurnId: string;
  generationKey: string; generationLease: string; stamp: string;
}) {
  return db.prepare(`INSERT INTO mutation_guards (id,story_id,asserted,created_at)
    SELECT ?,?,CASE WHEN
      EXISTS (SELECT 1 FROM stories WHERE id=? AND latest_accepted_turn_number=?)
      AND EXISTS (SELECT 1 FROM turns WHERE story_id=? AND turn_number=? AND id=?)
      AND EXISTS (SELECT 1 FROM generation_jobs WHERE idempotency_key=? AND status='generating' AND error=?)
    THEN 1 ELSE 0 END,?`).bind(
    input.id, input.storyId, input.storyId, input.expectedTurnNumber,
    input.storyId, input.expectedTurnNumber, input.expectedTurnId,
    input.generationKey, input.generationLease, input.stamp,
  );
}

function backgroundBoundaryMutationGuardStatement(db: D1Database, input: {
  id: string; storyId: string; throughTurnNumber: number; boundaryTurnId: string;
  jobId: string; lock: string; chain: "context" | "checkpoint";
  expectedHeadThrough: number; expectedHeadId: string; stamp: string;
}) {
  const chainTable = input.chain === "context" ? "context_snapshots" : "checkpoints";
  return db.prepare(`INSERT INTO mutation_guards (id,story_id,asserted,created_at)
    SELECT ?,?,CASE WHEN
      EXISTS (SELECT 1 FROM turns WHERE story_id=? AND turn_number=? AND id=?)
      AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)
      AND COALESCE((SELECT through_turn_number FROM ${chainTable} WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1),0)=?
      AND COALESCE((SELECT id FROM ${chainTable} WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1),'')=?
    THEN 1 ELSE 0 END,?`).bind(
    input.id, input.storyId, input.storyId, input.throughTurnNumber, input.boundaryTurnId,
    input.jobId, input.lock, input.storyId, input.expectedHeadThrough, input.storyId, input.expectedHeadId, input.stamp,
  );
}

function mutationGuardReleaseStatement(db: D1Database, id: string) {
  return db.prepare("DELETE FROM mutation_guards WHERE id=?").bind(id);
}

function isMutationGuardFailure(error: unknown) {
  return /mutation_guard_asserted_check|check constraint failed/i.test(message(error));
}

async function loadStory(storyId: string, includeDetails: boolean): Promise<Story | null> {
  const db = getD1();
  const row = await db.prepare("SELECT * FROM stories WHERE id=?").bind(storyId).first<Row>();
  if (!row) return null;
  const story = storyFromRow(row);
  if (!includeDetails) return story;
  const [turnRows, castRows, stateRow, contextRow, artProfileRow, visualRows, entityGuideRows, entityObservationRows, artRows, jobRows, writingJobRow] = await Promise.all([
    db.prepare("SELECT * FROM turns WHERE story_id=? ORDER BY turn_number ASC").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM cast_members WHERE story_id=? ORDER BY name ASC").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM story_states WHERE story_id=?").bind(storyId).first<Row>(),
    db.prepare("SELECT * FROM context_snapshots WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1").bind(storyId).first<Row>(),
    db.prepare("SELECT * FROM story_art_profiles WHERE story_id=?").bind(storyId).first<Row>(),
    db.prepare("SELECT * FROM visual_profiles WHERE story_id=? ORDER BY kind,name").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM entity_appearance_guides WHERE story_id=? ORDER BY kind,name").bind(storyId).all<Row>(),
    db.prepare(`SELECT * FROM (SELECT * FROM entity_appearance_observations WHERE story_id=? ORDER BY turn_number DESC,created_at DESC LIMIT 240)
      ORDER BY turn_number ASC,kind,name`).bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM art_assets WHERE story_id=? ORDER BY CASE category WHEN 'Cover' THEN 0 WHEN 'Scenes' THEN 1 WHEN 'Characters' THEN 2 ELSE 3 END,turn_number,created_at DESC").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM background_jobs WHERE story_id=? ORDER BY updated_at DESC LIMIT 30").bind(storyId).all<Row>(),
    db.prepare("SELECT * FROM generation_jobs WHERE story_id=? ORDER BY turn_number DESC LIMIT 1").bind(storyId).first<Row>(),
  ]);
  story.turns = turnRows.results.map(turnFromRow);
  story.cast = castRows.results.map((cast: Row) => json<CastMember>(String(cast.canonical_json || ""), {} as CastMember));
  story.storyState = json<StoryState>(String(stateRow?.state_json || ""), {} as StoryState);
  story.contextSnapshot = contextRow ? json<ContextSnapshot | undefined>(String(contextRow.snapshot_json || ""), undefined) : undefined;
  story.artProfile = artProfileRow ? json<StoryArtProfile | undefined>(String(artProfileRow.profile_json || ""), undefined) : undefined;
  story.visualProfiles = visualRows.results.map(visualFromRow);
  story.entityAppearanceGuides = entityGuideRows.results.map(entityAppearanceGuideFromRow);
  story.entityAppearanceTimeline = entityObservationRows.results.map(entityAppearanceObservationFromRow);
  story.art = artRows.results.map(artFromRow);
  story.jobs = jobRows.results.map(jobFromRow);
  story.writingJob = writingJobRow ? writingJobFromRow(writingJobRow) : undefined;
  story.logs = await loadLogs(30, storyId);
  return story;
}

async function loadLogs(limit = 50, storyId = ""): Promise<OperationLog[]> {
  const rows = await getD1().prepare(`SELECT * FROM operation_logs WHERE (?='' OR story_id=?) ORDER BY created_at DESC LIMIT ?`)
    .bind(storyId, storyId, Math.max(1, Math.min(100, limit))).all<Row>();
  return rows.results.map(logFromRow);
}

async function serveArtAsset(assetId: string) {
  const row = await getD1().prepare("SELECT * FROM art_assets WHERE id=?").bind(assetId).first<Row>();
  if (!row || String(row.status) !== "Ready" || !row.image_reference) return Response.json({ error: "Art is not ready." }, { status: 404 });
  const reference = String(row.image_reference);
  const mimeType = String(row.mime_type || "image/jpeg");
  if (reference.startsWith("r2:")) {
    const object = await getArtBucket()?.get(reference.slice(3));
        if (!object) {
          const db = getD1();
          await db.prepare("UPDATE art_assets SET status=?,updated_at=? WHERE id=?").bind(String(row.type) === "cover" ? "Placeholder" : "Failed", now(), assetId).run();
          if (String(row.type) === "cover") await ensureBaselineJobs(db, String(row.story_id));
      return Response.json({ error: "Art file not found. A replacement has been queued." }, { status: 404 });
    }
    return new Response(object.body as BodyInit, { headers: { "content-type": mimeType, "cache-control": "private, max-age=3600" } });
  }
  if (!/^https:\/\//i.test(reference)) return Response.json({ error: "Art reference is invalid." }, { status: 404 });
  const source = await fetch(reference, { signal: AbortSignal.timeout(10 * 60 * 1000) });
  if (!source.ok) return Response.json({ error: "Art source is unavailable." }, { status: 502 });
  return new Response(source.body, { headers: { "content-type": source.headers.get("content-type") || mimeType, "cache-control": "private, max-age=3600" } });
}

function initialArtProfile(foundation: StoryFoundation): StoryArtProfile {
  const cast = foundation.initialCast || [];
  return {
    artStyle: "Editorial storybook illustration with expressive silhouettes, tactile texture, and restrained detail",
    coverStyle: "A single iconic composition with strong negative space and hand-lettered-title-friendly framing",
    palette: ["weathered paper", "deep umber", "muted vermilion", "one setting-derived accent"],
    mood: [...(foundation.tone || []), ...(foundation.genres || [])].slice(0, 4).join(", ") || "intimate and atmospheric",
    protagonistAppearance: cast.find((member) => member.id === foundation.mainViewpointCharacterId)?.physicalDescription || cast[0]?.physicalDescription || "To be reconciled from the opening section",
    majorCastAppearance: cast.slice(0, 5).map((member) => `${member.name}: ${member.physicalDescription}`),
    keyLocationAppearance: foundation.setting ? [foundation.setting] : [],
    creatureDesignLanguage: "Follow established setting logic; avoid generic fantasy shorthand unless the prose establishes it",
    recurringMotifs: foundation.narrativePromises?.slice(0, 4) || [],
    avoid: ["text baked into the image", "unestablished costume changes", "visual spoilers", "generic stock-art composition"],
    lastUpdatedTurn: 1,
  };
}

function coverPromptSummary(foundation: StoryFoundation, profile: StoryArtProfile, entityGuides: EntityAppearanceGuide[] = []) {
  const durableEntities = entityGuides.filter((guide) => guide.firstSeenTurn <= 1).slice(0, 10)
    .map((guide) => entityGuidePromptLine(guide, [], 1, false));
  return [
    `Design language: ${profile.coverStyle}. ${profile.artStyle}.`,
    `Story premise: ${foundation.shortDescription || foundation.openingSituation}.`,
    `Setting: ${foundation.setting}. Mood: ${profile.mood}. Palette: ${(profile.palette || []).join(", ")}.`,
    `Primary figure: ${profile.protagonistAppearance}.`,
    profile.majorCastAppearance?.length ? `Other established figures: ${profile.majorCastAppearance.slice(0, 4).join("; ")}.` : "",
    durableEntities.length ? `Durable entity appearance/style guides: ${durableEntities.join("; ")}.` : "",
    profile.recurringMotifs?.length ? `Recurring visual motifs: ${profile.recurringMotifs.slice(0, 5).join(", ")}.` : "",
    `Avoid: ${(profile.avoid || []).join(", ")}.`,
  ].filter(Boolean).join("\n");
}

function scenePromptSummary(story: Story, turn: Turn) {
  const profile = story.artProfile || initialArtProfile(story.foundation);
  const visibleProfiles = (story.visualProfiles || []).filter((item) => item.lastUpdatedTurn <= turn.turnNumber).slice(0, 8)
    .map((item) => `${item.name}: ${item.visualDescription || [item.clothing, item.architecture, item.atmosphere].filter(Boolean).join(", ")}`);
  const durableEntities = (story.entityAppearanceGuides || []).filter((guide) => guide.firstSeenTurn <= turn.turnNumber).slice(0, 12)
    .map((guide) => entityGuidePromptLine(guide, story.entityAppearanceTimeline || [], turn.turnNumber, true));
  return [
    `Choose the clearest visually decisive moment from Section ${turn.turnNumber} and illustrate that single moment.`,
    `Story art direction: ${profile.artStyle}. Mood: ${profile.mood}. Palette: ${(profile.palette || []).join(", ")}.`,
    durableEntities.length ? `Durable entity appearance/style guides (baseline traits are authoritative; current details apply at this timeline point): ${durableEntities.join("; ")}.` : "",
    visibleProfiles.length ? `Established visual continuity: ${visibleProfiles.join("; ")}.` : `Protagonist continuity: ${profile.protagonistAppearance}.`,
    `Section text:\n${turn.prose.slice(0, 2_800)}`,
    `Avoid: ${(profile.avoid || []).join(", ")}.`,
  ].filter(Boolean).join("\n\n");
}

function entityGuidePromptLine(guide: EntityAppearanceGuide, timeline: EntityAppearanceObservation[], targetTurn: number, includeCurrent: boolean) {
  const baseline = [guide.baseline.summary, ...(guide.baseline.signatureTraits || []), ...(guide.baseline.styleNotes || [])].filter(Boolean).join(", ");
  const current = includeCurrent && guide.lastUpdatedTurn <= targetTurn
    ? [guide.current.appearance, guide.current.wardrobeOrSurface, guide.current.condition, ...(guide.current.temporaryChanges || [])].filter(Boolean).join(", ")
    : "";
  const observations = timeline.filter((item) => item.kind === guide.kind && item.entityId === guide.entityId && item.turnNumber <= targetTurn)
    .slice(-6).map((item) => `Section ${item.turnNumber}: ${item.summary}`).join("; ");
  return `${guide.kind} ${guide.name} [${guide.entityId}] — baseline: ${baseline || "not yet established"}${current ? `; current at this point: ${current}` : ""}${observations ? `; timeline through this section: ${observations}` : ""}; avoid: ${(guide.baseline.avoid || []).join(", ") || "unestablished changes"}`;
}

function visualProfileUpsert(db: D1Database, storyId: string, profile: VisualProfile, turn: number) {
  const id = `${storyId}:${profile.kind}:${profile.entityId}`;
  return db.prepare(`INSERT INTO visual_profiles (id,story_id,kind,entity_id,name,profile_json,last_updated_turn,updated_at)
    VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(story_id,kind,entity_id) DO UPDATE SET name=excluded.name,profile_json=excluded.profile_json,
    last_updated_turn=excluded.last_updated_turn,updated_at=excluded.updated_at
    WHERE excluded.last_updated_turn>=visual_profiles.last_updated_turn`).bind(
    id, storyId, profile.kind, profile.entityId, profile.name, JSON.stringify({ ...profile, id, storyId, lastUpdatedTurn: turn }), turn, now(),
  );
}

function visualFromRow(row: Row): VisualProfile {
  return { ...json<VisualProfile>(String(row.profile_json || ""), {} as VisualProfile), id: String(row.id), storyId: String(row.story_id),
    kind: String(row.kind) as VisualProfile["kind"], entityId: String(row.entity_id), name: String(row.name), lastUpdatedTurn: Number(row.last_updated_turn || 0) };
}

function entityAppearanceGuideUpsert(db: D1Database, storyId: string, guide: EntityAppearanceGuide, stamp = now()) {
  const id = `${storyId}:${guide.kind}:${guide.entityId}`;
  return db.prepare(`INSERT INTO entity_appearance_guides
    (id,story_id,kind,entity_id,name,aliases_json,baseline_json,current_json,first_seen_turn,last_updated_turn,created_at,updated_at)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(story_id,kind,entity_id) DO UPDATE SET name=excluded.name,aliases_json=excluded.aliases_json,
      baseline_json=excluded.baseline_json,current_json=excluded.current_json,first_seen_turn=MIN(entity_appearance_guides.first_seen_turn,excluded.first_seen_turn),
      last_updated_turn=excluded.last_updated_turn,updated_at=excluded.updated_at
    WHERE excluded.last_updated_turn>=entity_appearance_guides.last_updated_turn`).bind(
    id, storyId, guide.kind, guide.entityId, guide.name, JSON.stringify(guide.aliases || []), JSON.stringify(guide.baseline),
    JSON.stringify(guide.current), guide.firstSeenTurn, guide.lastUpdatedTurn, stamp, stamp,
  );
}

function entityAppearanceObservationUpsert(db: D1Database, observation: EntityAppearanceObservation) {
  return db.prepare(`INSERT INTO entity_appearance_observations
    (id,story_id,guide_id,kind,entity_id,name,turn_number,observation_json,source_snapshot_id,created_at)
    VALUES (?,?,?,?,?,?,?,?,?,?)
    ON CONFLICT(story_id,kind,entity_id,turn_number) DO UPDATE SET name=excluded.name,observation_json=excluded.observation_json,
      source_snapshot_id=excluded.source_snapshot_id,created_at=excluded.created_at`).bind(
    observation.id, observation.storyId, observation.guideId, observation.kind, observation.entityId, observation.name,
    observation.turnNumber, JSON.stringify({ summary: observation.summary, changes: observation.changes, evidence: observation.evidence }),
    observation.sourceSnapshotId || null, observation.createdAt,
  );
}

function entityAppearanceGuideFromRow(row: Row): EntityAppearanceGuide {
  return {
    id: String(row.id), storyId: String(row.story_id), kind: String(row.kind) as EntityAppearanceGuide["kind"],
    entityId: String(row.entity_id), name: String(row.name), aliases: json<string[]>(String(row.aliases_json || ""), []),
    baseline: json(String(row.baseline_json || ""), { summary: "Not yet visually established", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] }),
    current: json(String(row.current_json || ""), { appearance: "Not yet visually established", wardrobeOrSurface: "", condition: "", location: "", temporaryChanges: [] }),
    firstSeenTurn: Number(row.first_seen_turn || 0), lastUpdatedTurn: Number(row.last_updated_turn || 0),
  };
}

function entityAppearanceObservationFromRow(row: Row): EntityAppearanceObservation {
  const observation = json<{ summary?: string; changes?: string[]; evidence?: string[] }>(String(row.observation_json || ""), {});
  return {
    id: String(row.id), storyId: String(row.story_id), guideId: String(row.guide_id),
    kind: String(row.kind) as EntityAppearanceObservation["kind"], entityId: String(row.entity_id), name: String(row.name),
    turnNumber: Number(row.turn_number || 0), summary: String(observation.summary || ""), changes: observation.changes || [], evidence: observation.evidence || [],
    sourceSnapshotId: row.source_snapshot_id ? String(row.source_snapshot_id) : undefined, createdAt: String(row.created_at),
  };
}

function artFromRow(row: Row): ArtAsset {
  return { id: String(row.id), storyId: String(row.story_id), turnId: row.turn_id ? String(row.turn_id) : undefined,
    turnNumber: row.turn_number == null ? undefined : Number(row.turn_number), type: String(row.type) as ArtAsset["type"],
    category: String(row.category) as ArtAsset["category"], title: String(row.title), caption: String(row.caption || ""),
    promptSummary: String(row.prompt_summary || ""), status: String(row.status) as ArtAsset["status"],
    imageReference: row.image_reference ? String(row.image_reference) : undefined, mimeType: row.mime_type ? String(row.mime_type) : undefined,
    createdAt: String(row.created_at), updatedAt: String(row.updated_at) };
}

function jobFromRow(row: Row): BackgroundJob {
  return { id: String(row.id), storyId: String(row.story_id), turnNumber: row.turn_number == null ? undefined : Number(row.turn_number),
    jobType: String(row.job_type) as BackgroundJob["jobType"], status: String(row.status) as BackgroundJob["status"],
    attempts: Number(row.attempts || 0), maxAttempts: Number(row.max_attempts || 3), runAfter: String(row.run_after),
    lastError: row.last_error ? String(row.last_error) : undefined, createdAt: String(row.created_at), updatedAt: String(row.updated_at) };
}

function writingJobFromRow(row: Row): WritingJob {
  const rawError = String(row.error || "");
  const detail = rawError.startsWith("{")
    ? json<{ message?: string; category?: string; recoverable?: boolean; retryAfterMs?: number }>(rawError, {})
    : {};
  return {
    turnNumber: Number(row.turn_number || 0), status: String(row.status) as WritingJob["status"],
    error: detail.message || (rawError && !rawError.startsWith("lease:") ? rawError : undefined),
    category: detail.category, recoverable: detail.recoverable, retryAfterMs: detail.retryAfterMs, updatedAt: String(row.updated_at),
  };
}

function logFromRow(row: Row): OperationLog {
  return { id: String(row.id), storyId: row.story_id ? String(row.story_id) : undefined,
    turnNumber: row.turn_number == null ? undefined : Number(row.turn_number), operation: String(row.operation), category: String(row.category),
    attempt: Number(row.attempt || 1), status: String(row.status) as OperationLog["status"], message: String(row.message),
    context: json<Record<string, unknown>>(String(row.context_json || ""), {}), createdAt: String(row.created_at) };
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
async function claimGenerationGuard(db: D1Database, key: string, storyId: string, turnNumber: number, lease: string) {
  const existing = await db.prepare("SELECT status,error,updated_at FROM generation_jobs WHERE idempotency_key=?").bind(key).first<Row>();
  const status = String(existing?.status || "");
  const updatedAt = String(existing?.updated_at || "");
  const stale = status === "generating" && (!Number.isFinite(Date.parse(updatedAt)) || Date.parse(updatedAt) < Date.now() - WRITER_LEASE_MS);
  const stamp = now();
  if (!existing) {
    await db.prepare("INSERT OR IGNORE INTO generation_jobs (idempotency_key,story_id,turn_number,status,error,updated_at) VALUES (?,?,?,'generating',?,?)")
      .bind(key, storyId, turnNumber, lease, stamp).run();
  } else if (status === "failed" || stale) {
    await db.prepare(`UPDATE generation_jobs SET status='generating',error=?,updated_at=?
      WHERE idempotency_key=? AND status=? AND COALESCE(error,'')=? AND updated_at=?`).bind(
      lease, stamp, key, status, String(existing.error || ""), updatedAt,
    ).run();
  } else {
    return false;
  }
  const claimed = await db.prepare("SELECT status,error FROM generation_jobs WHERE idempotency_key=?").bind(key).first<Row>();
  return String(claimed?.status || "") === "generating" && String(claimed?.error || "") === lease;
}
async function refreshGenerationLease(db: D1Database, key: string, lease: string) {
  const refreshed = await db.prepare("UPDATE generation_jobs SET updated_at=? WHERE idempotency_key=? AND status='generating' AND error=?")
    .bind(now(), key, lease).run();
  if (Number(refreshed.meta.changes || 0) < 1) throw new ApiRouteFailure(
    "A resumed writing request replaced this late draft, so it was safely discarded.", "writer_concurrency", true,
  );
}
function writingFailure(error: unknown) {
  if (error instanceof AiFailure || error instanceof ApiRouteFailure) return {
    message: error.message, category: error.category, recoverable: error.recoverable, retryAfterMs: error.retryAfterMs,
  };
  const errorMessage = message(error);
  if (/did not pass continuity review|empty section|replacement draft is incomplete/i.test(errorMessage)) {
    return { message: errorMessage, category: "validation", recoverable: false, retryAfterMs: 0 };
  }
  if (/newer section arrived|resumed writing request replaced/i.test(errorMessage)) {
    return { message: errorMessage, category: "writer_concurrency", recoverable: true, retryAfterMs: 0 };
  }
  return { message: errorMessage, category: "server", recoverable: false, retryAfterMs: 0 };
}
async function routeError(error: unknown, context: { storyId?: string; turnNumber?: number; operation?: string } = {}) {
  const errorMessage = message(error);
  const details = error instanceof ApiRouteFailure || error instanceof AiFailure
    ? { category: error.category, recoverable: error.recoverable, retryAfterMs: error.retryAfterMs }
    : { category: "server", recoverable: false, retryAfterMs: 0 };
  console.error("[kotoba-api]", errorMessage);
  await recordOperationLog({ storyId: context.storyId, turnNumber: context.turnNumber, operation: context.operation || "api_route",
    category: details.category, status: "failed", message: errorMessage, context: { recoverable: details.recoverable, retryAfterMs: details.retryAfterMs } });
  return Response.json({ error: errorMessage, ...details }, { status: 500 });
}

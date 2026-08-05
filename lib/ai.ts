import type {
  AuthorProfile,
  CastMember,
  StoryFoundation,
  StoryState,
  TurnResult,
  ContextSnapshot,
  EntityAppearanceGuide,
  EntityAppearanceObservation,
  StoryArtProfile,
  VisualProfile,
} from "./types";
import type { StoryArtStyleAnchor } from "./story-art-style-anchor";
import { recordOperationLog } from "./operation-log";

const authorShape = `{
  "displayName": string,
  "shortDescription": string,
  "selectedGenres": string[],
  "voice": string,
  "tone": string[],
  "pacing": string,
  "preferredPointOfView": string,
  "preferredTense": string,
  "proseDensity": string,
  "sensoryBias": string[],
  "recurringThemes": string[],
  "cadenceRules": string[],
  "writingRules": string[],
  "thingsToAvoid": string[]
}`;

const castShape = `{
  "id": stable-lowercase-slug,
  "name": string,
  "aliases": string[],
  "pronouns": string,
  "genderPresentation": string,
  "narrativeRole": string,
  "viewpointPriority": string,
  "physicalDescription": string,
  "personality": string,
  "goals": string[],
  "fears": string[],
  "knownSecrets": string[],
  "importantRelationships": string[],
  "currentStatus": string,
  "currentLocation": string,
  "importantPossessions": string[],
  "abilitiesOrPowers": string[],
  "lastUpdatedTurn": number,
  "readerKnownSummary": string
}`;

const stateShape = `{
  "currentTime": string,
  "currentLocation": string,
  "currentScene": string,
  "activeViewpointCharacterId": string,
  "castPresent": string[],
  "recentEvents": string[],
  "establishedWorldFacts": string[],
  "importantRelationshipFacts": string[],
  "openPlotThreads": string[],
  "resolvedPlotThreads": string[],
  "activePromises": string[],
  "importantItems": string[],
  "injuriesAndConditions": string[],
  "factsThatMustRemainTrue": string[],
  "milestonesCompleted": string[],
  "milestonesNotYetCompleted": string[],
  "currentNarrativePressure": string,
  "currentArcDirection": string,
  "lastUpdatedTurn": number
}`;

type AiCallContext = { operation: string; storyId?: string; turnNumber?: number };

export class AiFailure extends Error {
  constructor(message: string, public category: string, public recoverable: boolean, public retryAfterMs = 0) {
    super(message);
  }
}

class JsonParseFailure extends AiFailure {
  constructor(message = "The author returned an unreadable draft.") { super(message, "parser", true); }
}

const MAX_ATTEMPTS = 3;
const TRANSPORT_TIMEOUT_MS = 10 * 60 * 1000;
const BASE_BACKOFF_MS = [2_000, 8_000, 20_000];

async function callJson<T>(
  system: string,
  prompt: string,
  maxOutputTokens = 8192,
  context: AiCallContext = { operation: "runtime_generation" },
  validate?: (value: T) => boolean,
): Promise<T> {
  let lastFailure: AiFailure | null = null;
  const deadline = Date.now() + TRANSPORT_TIMEOUT_MS;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      const strictSystem = lastFailure?.category === "parser"
        ? `${system}\nA previous response was not valid JSON. Return one complete strict JSON object with no markdown fence, preamble, or trailing commentary.`
        : system;
      const remainingMs = deadline - Date.now();
      if (remainingMs <= 0) throw new AiFailure("The writing request timed out after ten minutes.", "timeout", true);
      const text = await requestText(strictSystem, prompt, maxOutputTokens, remainingMs);
      const parsed = parseJson<T>(text);
      if (validate && !validate(parsed)) throw new JsonParseFailure("The author returned valid JSON with an incomplete response shape.");
      if (attempt > 1 && lastFailure) {
        await recordOperationLog({ ...context, category: lastFailure.category, attempt, status: "recovered", message: `Recovered on attempt ${attempt} after ${lastFailure.category}.` });
      }
      return parsed;
    } catch (error) {
      const failure = normalizeFailure(error);
      lastFailure = failure;
      const waitMs = Math.max(failure.retryAfterMs, BASE_BACKOFF_MS[attempt - 1] || 20_000);
      const canRetry = failure.recoverable && attempt < MAX_ATTEMPTS && deadline - Date.now() > waitMs;
      await recordOperationLog({
        ...context, category: failure.category, attempt, status: canRetry ? "retrying" : "failed",
        message: canRetry ? `${failure.message} A bounded retry is scheduled.` : `${failure.message} Retry limit reached.`,
        context: { maxAttempts: MAX_ATTEMPTS, totalTransportWindowMs: TRANSPORT_TIMEOUT_MS },
      });
      if (!canRetry) throw new AiFailure(`${failure.message} Existing story data is unchanged.`, failure.category, failure.recoverable, failure.retryAfterMs);
      await delay(waitMs);
    }
  }
  throw new AiFailure("The author could not complete the request. Existing story data is unchanged.", "retry_limit", true);
}

async function requestText(system: string, prompt: string, maxOutputTokens: number, timeoutMs: number): Promise<string> {
  const provider = (process.env.LLM_PROVIDER || (process.env.GEMINI_API_KEY ? "gemini" : "openai")).toLowerCase();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), Math.max(1, timeoutMs));

  try {
    if (provider === "gemini" && process.env.GEMINI_API_KEY) {
      const base = (process.env.GEMINI_API_URL || "https://generativelanguage.googleapis.com/v1beta").replace(/\/$/, "");
      const model = process.env.WRITER_MODEL || process.env.DEFAULT_MODEL || "gemini-2.5-flash";
      const response = await fetch(`${base}/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(process.env.GEMINI_API_KEY)}`, {
        method: "POST", signal: controller.signal,
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          systemInstruction: { parts: [{ text: system }] },
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig: { responseMimeType: "application/json", temperature: 0.86, maxOutputTokens },
        }),
      });
      if (!response.ok) throw httpFailure(response);
      const payload = await parseProviderResponse<{ candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }> }>(response);
      return payload.candidates?.[0]?.content?.parts?.map((part) => part.text || "").join("") || "";
    }

    if (process.env.OPENAI_API_KEY) {
      const base = (process.env.OPENAI_API_URL || "https://api.openai.com/v1").replace(/\/$/, "");
      const model = process.env.WRITER_MODEL || process.env.DEFAULT_MODEL || "gpt-4.1-mini";
      const response = await fetch(`${base}/chat/completions`, {
        method: "POST", signal: controller.signal,
        headers: { "content-type": "application/json", authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
        body: JSON.stringify({
          model, messages: [{ role: "system", content: system }, { role: "user", content: prompt }],
          response_format: { type: "json_object" }, temperature: 0.86, max_tokens: maxOutputTokens,
        }),
      });
      if (!response.ok) throw httpFailure(response);
      const payload = await parseProviderResponse<{ choices?: Array<{ message?: { content?: string } }> }>(response);
      return payload.choices?.[0]?.message?.content || "";
    }

    throw new AiFailure("Runtime writing is not configured.", "configuration", false);
  } catch (error) {
    if (error instanceof AiFailure) throw error;
    if (controller.signal.aborted) throw new AiFailure("The writing request timed out after ten minutes.", "timeout", true);
    throw new AiFailure(error instanceof Error ? error.message : "The writing transport was interrupted.", "transport", true);
  } finally {
    clearTimeout(timeout);
  }
}

async function parseProviderResponse<T>(response: Response): Promise<T> {
  try {
    return await response.json() as T;
  } catch {
    throw new AiFailure("The author service returned an unreadable response.", "parser", true);
  }
}

function httpFailure(response: Response) {
  const retryable = [408, 409, 425, 429, 500, 502, 503, 504].includes(response.status);
  const retryAfter = Number(response.headers.get("retry-after") || 0);
  return new AiFailure(`The author service returned HTTP ${response.status}.`, `http_${response.status}`, retryable, Number.isFinite(retryAfter) ? Math.min(retryAfter * 1000, 60_000) : 0);
}

function normalizeFailure(error: unknown) {
  if (error instanceof AiFailure) return error;
  return new AiFailure(error instanceof Error ? error.message : "The writing request was interrupted.", "transport", true);
}

function delay(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

function parseJson<T>(value: string): T {
  const clean = value.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  try {
    return JSON.parse(clean) as T;
  } catch {
    const start = clean.indexOf("{");
    const end = clean.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try { return JSON.parse(clean.slice(start, end + 1)) as T; }
      catch { /* Normalize every malformed response as a recoverable parser failure. */ }
    }
    throw new JsonParseFailure();
  }
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}

export async function createAuthorProfile(input: { genres: string[]; name?: string; description: string; revision?: string }) {
  const result = await callJson<AuthorProfile>(
    "You create nuanced fictional author identities for a private living-fiction library. Return only the requested JSON. Never imitate a real living author.",
    `Create a complete reusable fictional author profile.
Genres: ${input.genres.join(", ")}
Optional name: ${input.name || "Invent a memorable pen name"}
Desired storyteller: ${input.description}
Revision request: ${input.revision || "None"}

Use this exact shape: ${authorShape}
Keep rules practical and literary. Avoid AI jargon, prompt language, or generic filler.`,
    4096, { operation: "author_profile" },
  );
  return normalizeAuthor(result, input.genres, input.name);
}

function normalizeAuthor(value: AuthorProfile, genres: string[], preferredName?: string): AuthorProfile {
  return {
    displayName: preferredName?.trim() || value.displayName || "The Unnamed Author",
    shortDescription: value.shortDescription || "A distinctive fictional storyteller.",
    selectedGenres: list(value.selectedGenres).length ? list(value.selectedGenres) : genres,
    voice: value.voice || "Clear, attentive, and character-led.",
    tone: list(value.tone),
    pacing: value.pacing || "Measured, with purposeful acceleration.",
    preferredPointOfView: value.preferredPointOfView || "Third person limited",
    preferredTense: value.preferredTense || "Past tense",
    proseDensity: value.proseDensity || "Balanced",
    sensoryBias: list(value.sensoryBias),
    recurringThemes: list(value.recurringThemes),
    cadenceRules: list(value.cadenceRules),
    writingRules: list(value.writingRules),
    thingsToAvoid: list(value.thingsToAvoid),
    id: value.id || "",
  };
}

type StoryCreationResult = {
  foundation: StoryFoundation;
  initialState: StoryState;
  firstTurn: TurnResult;
};

export async function createStoryFoundation(input: { author: AuthorProfile; idea: string; title?: string; storyId?: string }) {
  const result = await callJson<StoryCreationResult>(
    "You are a meticulous fiction engine. Build one private story foundation and write exactly one opening section. Return JSON only. Preserve a clear separation between prose and continuity data.",
    `Pinned fictional author profile (never modify it):
${JSON.stringify(input.author)}

Reader's story idea:
${input.idea}

Optional title: ${input.title || "Invent one"}

Return exactly:
{
  "foundation": {
    "title": string,
    "shortDescription": one or two sentences,
    "genres": string[], "tone": string[], "pointOfView": string, "tense": string,
    "openingSituation": string, "centralConflict": string,
    "narrativePromises": string[], "importantConstraints": string[],
    "additionalInstructions": string, "broadDirection": string, "setting": string,
    "initialWorldFacts": string[], "initialRelationshipFacts": string[],
    "initialOpenPlotThreads": string[], "factsThatMustRemainTrue": string[],
    "initialNarrationVoiceRecommendation": string,
    "mainViewpointCharacterId": string,
    "initialCast": [${castShape}]
  },
  "initialState": ${stateShape},
  "firstTurn": {
    "prose": string,
    "stateDelta": object,
    "nextStoryState": ${stateShape},
    "castUpdates": [${castShape}],
    "relationshipUpdates": string[], "worldFactUpdates": string[],
    "threadUpdates": string[], "milestoneUpdates": string[],
    "viewpointCharacterId": string, "narrationVoiceHint": string,
    "turnIntent": object
  }
}

Section 1 must be a substantial 900–1,300 word coherent dramatic unit (never more than 1,600), begin in motion, contain no visible section heading, and not resolve the premise. Use stable lowercase IDs for cast. Put hidden secrets only in knownSecrets; readerKnownSummary must reveal only what the prose reveals.`,
    16384, { operation: "story_foundation", storyId: input.storyId, turnNumber: 1 },
  );
  result.foundation.title = input.title?.trim() || result.foundation.title || "Untitled Story";
  result.foundation.initialCast = normalizeCast(result.foundation.initialCast, 1);
  result.initialState = normalizeState(result.initialState, 0, result.foundation);
  result.firstTurn = normalizeTurn(result.firstTurn, 1, result.foundation, result.initialState);
  return result;
}

export async function continueStory(input: {
  storyId: string;
  author: AuthorProfile;
  foundation: StoryFoundation;
  checkpoint: unknown;
  state: StoryState;
  cast: CastMember[];
  recentTurns: Array<{ turnNumber: number; prose: string; stateDelta: unknown }>;
  nextTurnNumber: number;
  note?: string;
  managedContext?: unknown;
}) {
  const result = await callJson<TurnResult>(
    "You continue a private living novel one section at a time. Return JSON only. Continuity is authoritative. Never mention AI, prompts, state, or application behavior in prose.",
    `Write exactly Section ${input.nextTurnNumber}; do not write later sections.

PINNED AUTHOR: ${JSON.stringify(input.author)}
FOUNDATION: ${JSON.stringify(input.foundation)}
LATEST CHECKPOINT: ${JSON.stringify(input.checkpoint || {})}
CURRENT AUTHORITATIVE STATE: ${JSON.stringify(input.state)}
LATEST MANAGED CHARACTER/FACT CONTEXT: ${JSON.stringify(input.managedContext || {})}
CANONICAL CAST: ${JSON.stringify(input.cast)}
RECENT SECTIONS AND DELTAS: ${JSON.stringify(input.recentTurns)}
ONE-TIME NOTE TO THE AUTHOR: ${input.note?.trim() || "None"}

First make a hidden TurnIntent for this one section. Then write the prose and durable updates. Return:
{
  "prose": string,
  "stateDelta": object,
  "nextStoryState": ${stateShape},
  "castUpdates": [${castShape}],
  "relationshipUpdates": string[], "worldFactUpdates": string[],
  "threadUpdates": string[], "milestoneUpdates": string[],
  "viewpointCharacterId": string, "narrationVoiceHint": string,
  "turnIntent": {
    "storyId": string, "intendedTurnNumber": ${input.nextTurnNumber},
    "viewpointCharacterId": string, "startingSituation": string,
    "immediateGoal": string, "meaningfulChange": string,
    "threadsToAdvance": string[], "factsToPreserve": string[],
    "eventsToAvoidRepeating": string[], "factsThatMustNotYetChange": string[],
    "desiredEndingPressure": string
  }
}

The stateDelta object must include "checkpointRecommended": true and a short "checkpointReason" only when this section contains a major time jump, major location change, sustained viewpoint change, cast restructuring, arc ending, major reveal, or major status/power change. Otherwise set checkpointRecommended to false.

Prose rules: 900–1,300 words preferred, 700 minimum unless a dramatically necessary ending, 1,600 maximum. Begin in motion, not recap. One coherent dramatic unit. Preserve names, pronouns, chronology, possessions, injuries, abilities, relationships, POV, tense, and world rules. Advance something meaningful without resolving the premise. Do not repeat the last opening, discovery, events, or emotional conclusion. No visible heading and no reader address unless the form requires it. The one-time note influences only this section and must never appear as an instruction in prose.`,
    16384, { operation: "continue_story", storyId: input.storyId, turnNumber: input.nextTurnNumber },
  );
  return normalizeTurn(result, input.nextTurnNumber, input.foundation, input.state);
}

export async function repairTurn(input: {
  storyId?: string;
  draft: TurnResult;
  issues: string[];
  author: AuthorProfile;
  foundation: StoryFoundation;
  state: StoryState;
  cast: CastMember[];
  nextTurnNumber: number;
}) {
  const result = await callJson<TurnResult>(
    "Repair one fiction section while preserving its intended events. Return JSON only. Do not explain the repair.",
    `Repair Section ${input.nextTurnNumber} for these issues: ${input.issues.join("; ")}.
Pinned author: ${JSON.stringify(input.author)}
Foundation: ${JSON.stringify(input.foundation)}
Pre-section state: ${JSON.stringify(input.state)}
Cast: ${JSON.stringify(input.cast)}
Candidate: ${JSON.stringify(input.draft)}

Return the same JSON shape. Keep prose 900–1,300 words, 700–1,600 hard range, no heading, no recap, and ensure state/cast updates describe only the repaired prose.`,
    16384, { operation: "repair_turn", storyId: input.storyId, turnNumber: input.nextTurnNumber },
  );
  return normalizeTurn(result, input.nextTurnNumber, input.foundation, input.state);
}

export async function createCheckpoint(input: {
  storyId: string;
  previous: unknown;
  turns: unknown[];
  state: StoryState;
  cast: CastMember[];
  throughTurnNumber: number;
  entityAppearanceGuides?: EntityAppearanceGuide[];
  entityAppearanceObservations?: EntityAppearanceObservation[];
}) {
  return callJson<Record<string, unknown>>(
    "Reconcile a compact canonical fiction checkpoint. Return JSON only. Never invent facts not supported by the supplied material.",
    `Reconcile continuity through Section ${input.throughTurnNumber}.
Previous checkpoint: ${JSON.stringify(input.previous || {})}
Later accepted sections and deltas: ${JSON.stringify(input.turns)}
Current state: ${JSON.stringify(input.state)}
Current cast: ${JSON.stringify(input.cast)}
Durable entity appearance/style guides: ${JSON.stringify(input.entityAppearanceGuides || [])}
Appearance observations linked to this timeline window: ${JSON.stringify(input.entityAppearanceObservations || [])}

Return {"storyId":string,"throughTurnNumber":number,"compactStorySummary":string,"canonicalCast":array,"canonicalRelationships":array,"canonicalWorldFacts":array,"currentTimeline":string,"currentLocation":string,"activeThreads":array,"resolvedThreads":array,"importantItems":array,"factsThatMustRemainTrue":array,"milestones":object,"narrativeDirection":string,"entityAppearanceGuideSummary":array}. Deduplicate facts, reconcile contradictions, and preserve items, injuries, powers, promises, constraints, stable character IDs, stable entity IDs, baseline visual traits, and section-linked appearance changes.`,
    8192, { operation: "checkpoint_reconcile", storyId: input.storyId, turnNumber: input.throughTurnNumber },
  );
}

type NarrativeContextReconciliation = Pick<ContextSnapshot,
  "throughTurnNumber" | "compactStorySummary" | "characterState" | "keyFacts" | "openQuestions"
>;

export type VisualContextReconciliation = {
  visualContinuityNotes: string[];
  storyArtProfile: StoryArtProfile;
  characterVisualProfiles: VisualProfile[];
  locationVisualProfiles: VisualProfile[];
  entityAppearanceGuides: EntityAppearanceGuide[];
};

function completeVisualContext(value: VisualContextReconciliation) {
  if (!value || typeof value !== "object") return false;
  const profile = value.storyArtProfile;
  if (!profile || typeof profile !== "object") return false;
  if (![value.visualContinuityNotes, value.characterVisualProfiles, value.locationVisualProfiles, value.entityAppearanceGuides,
    profile.palette, profile.majorCastAppearance, profile.keyLocationAppearance, profile.recurringMotifs, profile.avoid]
    .every(Array.isArray)) return false;
  if (![profile.artStyle, profile.coverStyle, profile.mood, profile.protagonistAppearance, profile.creatureDesignLanguage]
    .every((item) => typeof item === "string")) return false;
  if (!profile.artStyle.trim() || !profile.coverStyle.trim() || value.entityAppearanceGuides.length < 1) return false;
  return value.entityAppearanceGuides.every((guide) => Boolean(
    guide && typeof guide === "object" && typeof guide.entityId === "string" && guide.entityId.trim()
    && typeof guide.name === "string" && guide.name.trim() && typeof guide.baseline === "object" && typeof guide.current === "object"
    && Array.isArray(guide.timelineObservations),
  ));
}

export async function createContextReconciliation(input: {
  storyId: string;
  throughTurnNumber: number;
  foundation: StoryFoundation;
  state: StoryState;
  cast: CastMember[];
  recentTurns: unknown[];
  previousContext?: unknown;
}) {
  return callJson<NarrativeContextReconciliation>(
    "You reconcile compact private author-state continuity for an ongoing novel. Return JSON only. Do not invent unsupported facts or expose this hidden working context in story prose.",
    `Reconcile durable context through Section ${input.throughTurnNumber}.
Foundation: ${JSON.stringify(input.foundation)}
Current state: ${JSON.stringify(input.state)}
Current cast: ${JSON.stringify(input.cast)}
Recent accepted sections and deltas: ${JSON.stringify(input.recentTurns)}
Previous managed context: ${JSON.stringify(input.previousContext || {})}

Return exactly {
  "throughTurnNumber": ${input.throughTurnNumber},
  "compactStorySummary": string,
  "characterState": [{"characterId":string,"name":string,"currentMotives":string[],"immediateGoals":string[],"emotionalState":string,"appearanceNow":string,"keyFacts":string[],"relationships":string[],"currentLocation":string}],
  "keyFacts": string[], "openQuestions": string[]
}. Preserve motives, goals, relationships, chronology, promises, constraints, secrets, possessions, injuries, powers, and other author-only facts. This pass does not create or update art direction, visual profiles, or appearance guides.`,
    8192, { operation: "context_reconcile", storyId: input.storyId, turnNumber: input.throughTurnNumber },
  );
}

export async function createVisualContextReconciliation(input: {
  storyId: string;
  throughTurnNumber: number;
  foundation: Pick<StoryFoundation, "title" | "shortDescription" | "genres" | "tone" | "setting" | "openingSituation">;
  acceptedTurns: Array<{ turnNumber: number; prose: string }>;
  previousVisualContext?: Partial<VisualContextReconciliation>;
  recentEntityObservations?: EntityAppearanceObservation[];
  previousThroughTurnNumber?: number;
}) {
  const safeFoundation = {
    title: input.foundation.title,
    shortDescription: input.foundation.shortDescription,
    genres: input.foundation.genres,
    tone: input.foundation.tone,
    setting: input.foundation.setting,
    openingSituation: input.foundation.openingSituation,
  };
  return callJson<VisualContextReconciliation>(
    "You reconcile illustration continuity from published story prose only. Return JSON only. You have no access to hidden author state. Never infer a secret, latent ability, concealed possession, unseen location, future costume, unrevealed identity, or transformation. An entity fact is eligible only when the supplied accepted prose visibly establishes it.",
    `Reconcile spoiler-safe visual context through Section ${input.throughTurnNumber}.
Opening-level book projection (style guidance only; never use it as evidence for an entity fact): ${JSON.stringify(safeFoundation)}
Accepted prose evidence: ${JSON.stringify(input.acceptedTurns)}
Previous prose-only visual context: ${JSON.stringify(input.previousVisualContext || {})}
Previous prose-only appearance observations: ${JSON.stringify(input.recentEntityObservations || [])}

Return exactly {
  "visualContinuityNotes": string[],
  "storyArtProfile": {"artStyle":string,"coverStyle":string,"palette":string[],"mood":string,"protagonistAppearance":string,"majorCastAppearance":string[],"keyLocationAppearance":string[],"creatureDesignLanguage":string,"recurringMotifs":string[],"avoid":string[],"lastUpdatedTurn":${input.throughTurnNumber}},
  "characterVisualProfiles": [{"id":string,"kind":"character","entityId":string,"name":string,"agePresentation":string,"genderPresentation":string,"bodyType":string,"hair":string,"face":string,"clothing":string,"notableProps":string[],"distinctiveMarkings":string[],"armorOrGear":string[],"currentVisualChanges":string[],"lastUpdatedTurn":${input.throughTurnNumber}}],
  "locationVisualProfiles": [{"id":string,"kind":"location","entityId":string,"name":string,"visualDescription":string,"architecture":string,"lighting":string,"atmosphere":string,"dominantColors":string[],"importantLandmarks":string[],"lastUpdatedTurn":${input.throughTurnNumber}}],
  "entityAppearanceGuides": [{
    "id":string,"kind":"character"|"location"|"item"|"creature"|"group"|"other","entityId":stable-lowercase-slug,"name":string,"aliases":string[],
    "baseline":{"summary":string,"signatureTraits":string[],"styleNotes":string[],"palette":string[],"motifs":string[],"avoid":string[]},
    "current":{"appearance":string,"wardrobeOrSurface":string,"condition":string,"location":string,"temporaryChanges":string[]},
    "firstSeenTurn":number,"lastUpdatedTurn":${input.throughTurnNumber},
    "timelineObservations":[{"turnNumber":number,"summary":string,"changes":string[],"evidence":string[]}]
  }]
}. Include recurring named visual entities supported by the accepted prose: characters, locations, important items, creatures, and groups. Reuse stable entity IDs. Treat each baseline as additive and preserve earlier prose-supported traits unless later prose explicitly changes them. Use current only for the latest visibly established wardrobe, surface, condition, location, and temporary changes. timelineObservations must contain only newly supported observations from Sections ${(input.previousThroughTurnNumber || 0) + 1}-${input.throughTurnNumber}; every evidence entry must identify its exact Section number and a short phrase actually present in that section. If prose does not support a field, use an empty string or empty array. Never fill a gap by inference.`,
    8192, { operation: "visual_context_reconcile", storyId: input.storyId, turnNumber: input.throughTurnNumber }, completeVisualContext,
  );
}

export async function createStoryArtStyleAnchor(input: {
  storyId: string;
  foundation: Pick<StoryFoundation, "title" | "shortDescription" | "genres" | "tone" | "setting" | "openingSituation">;
}) {
  const safeProjection = {
    title: input.foundation.title,
    shortDescription: input.foundation.shortDescription,
    genres: input.foundation.genres,
    tone: input.foundation.tone,
    setting: input.foundation.setting,
    openingSituation: input.foundation.openingSituation,
  };
  return callJson<StoryArtStyleAnchor>(
    "You define one permanent visual identity for a private novel from a spoiler-safe opening projection. Return JSON only. Never name or imitate a living artist, and never infer later plot events, identities, powers, injuries, costumes, or locations.",
    `Create a concrete, distinctive book-wide art style anchor from this opening-only projection:
${JSON.stringify(safeProjection)}

Return exactly {"summary":string,"medium":string,"visualLanguage":string,"palette":string[],"lighting":string,"compositionRules":string[],"textureNotes":string[],"recurringMotifs":string[],"negativeConstraints":string[]}.
Anchor craft, materials, palette, lighting, composition, and non-plot motifs in the supplied setting and tone. The result must remain appropriate for the cover and every historical section without revealing or assuming anything outside this projection.`,
    4096, { operation: "art_style_anchor", storyId: input.storyId, turnNumber: 1 },
  );
}

export async function createArtBrief(input: {
  storyId: string;
  turnNumber?: number;
  type: "cover" | "scene";
  storyTitle: string;
  layeredGroundingPrompt: string;
  candidateEntities: Array<{ entityId: string; kind: string; name: string }>;
}) {
  return callJson<{
    shouldIllustrate: boolean;
    category: "Cover" | "Scenes" | "Characters" | "Locations";
    title: string;
    caption: string;
    chosenMoment: string;
    compositionPlan: string;
    referencedEntityIds: string[];
    promptSummary: string;
  }>(
    "You are a hidden art director for a private living-fiction edition. Select one visually concrete, emotionally important, compositionally legible image. The supplied style and continuity layers are authoritative. Return JSON only.",
    `Prepare a ${input.type} art brief for ${input.storyTitle}.

AUTHORITATIVE LAYERED GROUNDING:
${input.layeredGroundingPrompt}

Eligible scoped entities: ${JSON.stringify(input.candidateEntities)}

Return {"shouldIllustrate":boolean,"category":"Cover"|"Scenes"|"Characters"|"Locations","title":string,"caption":string,"chosenMoment":string,"compositionPlan":string,"referencedEntityIds":string[],"promptSummary":string}.
For a cover, shouldIllustrate must be true. For a scene, choose false only when no concrete single moment is supportable. referencedEntityIds may contain only the exact kind-qualified ID strings from Eligible scoped entities, and only for entities actually visible or architecturally defining the chosen image. The prompt summary is a concise shot plan, not a replacement for the authoritative grounding. Preserve supplied faces, bodies, clothing, props, locations, palette, materials, motifs, lighting, and edition style. Never add facts, people, locations, costumes, injuries, text, or spoilers absent from the grounding. Prefer omission or obscurity when evidence is incomplete.`,
    4096, { operation: `art_${input.type}_brief`, storyId: input.storyId, turnNumber: input.turnNumber },
  );
}

export function validationIssues(result: TurnResult, recentProse = "") {
  const issues: string[] = [];
  const count = result.prose.trim().split(/\s+/).filter(Boolean).length;
  if (count < 700) issues.push(`too short at ${count} words`);
  if (count > 1600) issues.push(`too long at ${count} words`);
  if (/^\s*(section|chapter)\s+\w+/i.test(result.prose)) issues.push("contains an unnecessary visible heading");
  if (/\b(as an ai|language model|the prompt|continuity record|generation process)\b/i.test(result.prose)) issues.push("exposes generation machinery");
  const opening = result.prose.toLowerCase().split(/\s+/).slice(0, 16).join(" ");
  if (opening && recentProse.toLowerCase().includes(opening)) issues.push("repeats the previous section opening");
  if (!result.nextStoryState || !result.stateDelta) issues.push("missing durable state updates");
  return issues;
}

function normalizeCast(value: CastMember[] | undefined, turn: number): CastMember[] {
  if (!Array.isArray(value)) return [];
  return value.filter((member) => member?.name).map((member) => ({
    id: member.id || member.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
    name: member.name,
    aliases: list(member.aliases), pronouns: member.pronouns || "unspecified",
    genderPresentation: member.genderPresentation || "unspecified",
    narrativeRole: member.narrativeRole || "Supporting character",
    viewpointPriority: member.viewpointPriority || "Secondary",
    physicalDescription: member.physicalDescription || "Not yet established",
    personality: member.personality || "Still emerging",
    goals: list(member.goals), fears: list(member.fears), knownSecrets: list(member.knownSecrets),
    importantRelationships: list(member.importantRelationships),
    currentStatus: member.currentStatus || "Present",
    currentLocation: member.currentLocation || "Unknown",
    importantPossessions: list(member.importantPossessions), abilitiesOrPowers: list(member.abilitiesOrPowers),
    lastUpdatedTurn: turn,
    readerKnownSummary: member.readerKnownSummary || member.physicalDescription || "Not yet fully known.",
  }));
}

function normalizeState(value: StoryState | undefined, turn: number, foundation: StoryFoundation): StoryState {
  const v = value || {} as StoryState;
  return {
    currentTime: v.currentTime || "Opening moments",
    currentLocation: v.currentLocation || foundation.setting || "The opening setting",
    currentScene: v.currentScene || foundation.openingSituation || "The story begins",
    activeViewpointCharacterId: v.activeViewpointCharacterId || foundation.mainViewpointCharacterId || "protagonist",
    castPresent: list(v.castPresent), recentEvents: list(v.recentEvents),
    establishedWorldFacts: list(v.establishedWorldFacts).length ? list(v.establishedWorldFacts) : list(foundation.initialWorldFacts),
    importantRelationshipFacts: list(v.importantRelationshipFacts).length ? list(v.importantRelationshipFacts) : list(foundation.initialRelationshipFacts),
    openPlotThreads: list(v.openPlotThreads).length ? list(v.openPlotThreads) : list(foundation.initialOpenPlotThreads),
    resolvedPlotThreads: list(v.resolvedPlotThreads), activePromises: list(v.activePromises).length ? list(v.activePromises) : list(foundation.narrativePromises),
    importantItems: list(v.importantItems), injuriesAndConditions: list(v.injuriesAndConditions),
    factsThatMustRemainTrue: list(v.factsThatMustRemainTrue).length ? list(v.factsThatMustRemainTrue) : list(foundation.factsThatMustRemainTrue),
    milestonesCompleted: list(v.milestonesCompleted), milestonesNotYetCompleted: list(v.milestonesNotYetCompleted),
    currentNarrativePressure: v.currentNarrativePressure || foundation.centralConflict || "Pressure is gathering",
    currentArcDirection: v.currentArcDirection || foundation.broadDirection || "Toward the central conflict",
    lastUpdatedTurn: turn,
  };
}

function normalizeTurn(value: TurnResult, turn: number, foundation: StoryFoundation, previousState: StoryState): TurnResult {
  const prose = String(value?.prose || "").trim();
  if (!prose) throw new Error("The author returned an empty section. Please try again.");
  return {
    prose,
    stateDelta: value.stateDelta && typeof value.stateDelta === "object" ? value.stateDelta : {},
    nextStoryState: normalizeState(value.nextStoryState || previousState, turn, foundation),
    castUpdates: normalizeCast(value.castUpdates, turn),
    relationshipUpdates: list(value.relationshipUpdates), worldFactUpdates: list(value.worldFactUpdates),
    threadUpdates: list(value.threadUpdates), milestoneUpdates: list(value.milestoneUpdates),
    viewpointCharacterId: value.viewpointCharacterId || previousState.activeViewpointCharacterId || foundation.mainViewpointCharacterId,
    narrationVoiceHint: value.narrationVoiceHint || foundation.initialNarrationVoiceRecommendation || "neutral",
    turnIntent: value.turnIntent && typeof value.turnIntent === "object" ? value.turnIntent : {},
  };
}

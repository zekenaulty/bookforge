import type {
  AuthorProfile,
  CastMember,
  StoryFoundation,
  StoryState,
  TurnResult,
} from "./types";

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

async function callJson<T>(system: string, prompt: string, maxOutputTokens = 8192): Promise<T> {
  const provider = (process.env.LLM_PROVIDER || (process.env.GEMINI_API_KEY ? "gemini" : "openai")).toLowerCase();

  if (provider === "gemini" && process.env.GEMINI_API_KEY) {
    const base = (process.env.GEMINI_API_URL || "https://generativelanguage.googleapis.com/v1beta").replace(/\/$/, "");
    const model = process.env.WRITER_MODEL || process.env.DEFAULT_MODEL || "gemini-2.5-flash";
    const response = await fetch(`${base}/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(process.env.GEMINI_API_KEY)}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: system }] },
        contents: [{ role: "user", parts: [{ text: prompt }] }],
        generationConfig: {
          responseMimeType: "application/json",
          temperature: 0.86,
          maxOutputTokens,
        },
      }),
    });
    if (!response.ok) throw new Error(`The author could not write right now (${response.status}).`);
    const payload = await response.json() as { candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }> };
    const text = payload.candidates?.[0]?.content?.parts?.map((part) => part.text || "").join("") || "";
    return parseJson<T>(text);
  }

  if (process.env.OPENAI_API_KEY) {
    const base = (process.env.OPENAI_API_URL || "https://api.openai.com/v1").replace(/\/$/, "");
    const model = process.env.WRITER_MODEL || process.env.DEFAULT_MODEL || "gpt-4.1-mini";
    const response = await fetch(`${base}/chat/completions`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model,
        messages: [{ role: "system", content: system }, { role: "user", content: prompt }],
        response_format: { type: "json_object" },
        temperature: 0.86,
        max_tokens: maxOutputTokens,
      }),
    });
    if (!response.ok) throw new Error(`The author could not write right now (${response.status}).`);
    const payload = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
    return parseJson<T>(payload.choices?.[0]?.message?.content || "");
  }

  throw new Error("Runtime writing is not configured. Add an OpenAI or Gemini API key in Settings for the hosted app.");
}

function parseJson<T>(value: string): T {
  const clean = value.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  try {
    return JSON.parse(clean) as T;
  } catch {
    const start = clean.indexOf("{");
    const end = clean.lastIndexOf("}");
    if (start >= 0 && end > start) return JSON.parse(clean.slice(start, end + 1)) as T;
    throw new Error("The author returned an unreadable draft. Please try again.");
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
    4096,
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

export async function createStoryFoundation(input: { author: AuthorProfile; idea: string; title?: string }) {
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
    16384,
  );
  result.foundation.title = input.title?.trim() || result.foundation.title || "Untitled Story";
  result.foundation.initialCast = normalizeCast(result.foundation.initialCast, 1);
  result.initialState = normalizeState(result.initialState, 0, result.foundation);
  result.firstTurn = normalizeTurn(result.firstTurn, 1, result.foundation, result.initialState);
  return result;
}

export async function continueStory(input: {
  author: AuthorProfile;
  foundation: StoryFoundation;
  checkpoint: unknown;
  state: StoryState;
  cast: CastMember[];
  recentTurns: Array<{ turnNumber: number; prose: string; stateDelta: unknown }>;
  nextTurnNumber: number;
  note?: string;
}) {
  const result = await callJson<TurnResult>(
    "You continue a private living novel one section at a time. Return JSON only. Continuity is authoritative. Never mention AI, prompts, state, or application behavior in prose.",
    `Write exactly Section ${input.nextTurnNumber}; do not write later sections.

PINNED AUTHOR: ${JSON.stringify(input.author)}
FOUNDATION: ${JSON.stringify(input.foundation)}
LATEST CHECKPOINT: ${JSON.stringify(input.checkpoint || {})}
CURRENT AUTHORITATIVE STATE: ${JSON.stringify(input.state)}
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
    16384,
  );
  return normalizeTurn(result, input.nextTurnNumber, input.foundation, input.state);
}

export async function repairTurn(input: {
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
    16384,
  );
  return normalizeTurn(result, input.nextTurnNumber, input.foundation, input.state);
}

export async function createCheckpoint(input: { previous: unknown; turns: unknown[]; state: StoryState; cast: CastMember[]; throughTurnNumber: number }) {
  return callJson<Record<string, unknown>>(
    "Reconcile a compact canonical fiction checkpoint. Return JSON only. Never invent facts not supported by the supplied material.",
    `Reconcile continuity through Section ${input.throughTurnNumber}.
Previous checkpoint: ${JSON.stringify(input.previous || {})}
Later accepted sections and deltas: ${JSON.stringify(input.turns)}
Current state: ${JSON.stringify(input.state)}
Current cast: ${JSON.stringify(input.cast)}

Return {"storyId":string,"throughTurnNumber":number,"compactStorySummary":string,"canonicalCast":array,"canonicalRelationships":array,"canonicalWorldFacts":array,"currentTimeline":string,"currentLocation":string,"activeThreads":array,"resolvedThreads":array,"importantItems":array,"factsThatMustRemainTrue":array,"milestones":object,"narrativeDirection":string}. Deduplicate facts, reconcile contradictions, and preserve items, injuries, powers, promises, constraints, and stable character IDs.`,
    8192,
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

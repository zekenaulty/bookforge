import type {
  CastMember,
  EntityAppearanceBaseline,
  EntityAppearanceCurrent,
  EntityAppearanceGuide,
  EntityAppearanceObservation,
  EntityAppearanceTimelineDraft,
  EntityKind,
  StoryFoundation,
} from "./types";

const ENTITY_KINDS = new Set<EntityKind>(["character", "location", "item", "creature", "group", "other"]);

export function nextReconciliationThrough(latestAcceptedTurn: number, previousThroughTurn: number, windowSize = 12): number {
  const latest = Math.max(0, Math.floor(latestAcceptedTurn));
  const previous = Math.max(0, Math.min(latest, Math.floor(previousThroughTurn)));
  return Math.min(latest, previous + Math.max(1, Math.floor(windowSize)));
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map(String).map((item) => item.trim()).filter(Boolean);
}

function unique(values: string[]): string[] {
  return [...new Set(values.map((item) => item.trim()).filter(Boolean))];
}

function text(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function turnNumber(value: unknown, fallback: number, maximum: number): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? Math.max(0, Math.min(maximum, parsed)) : fallback;
}

export function entitySlug(value: unknown, fallback = "entity"): string {
  return text(value, fallback).normalize("NFKC").toLowerCase().replace(/[^\p{L}\p{N}]+/gu, "-").replace(/(^-|-$)/g, "") || fallback;
}

function normalizeKind(value: unknown): EntityKind {
  const kind = text(value, "other") as EntityKind;
  return ENTITY_KINDS.has(kind) ? kind : "other";
}

function normalizeBaseline(value: unknown, fallback = "Not yet visually established"): EntityAppearanceBaseline {
  const candidate = value && typeof value === "object" ? value as Partial<EntityAppearanceBaseline> : {};
  return {
    summary: text(candidate.summary, fallback),
    signatureTraits: strings(candidate.signatureTraits),
    styleNotes: strings(candidate.styleNotes),
    palette: strings(candidate.palette),
    motifs: strings(candidate.motifs),
    avoid: strings(candidate.avoid),
  };
}

function normalizeCurrent(value: unknown, fallback = ""): EntityAppearanceCurrent {
  const candidate = value && typeof value === "object" ? value as Partial<EntityAppearanceCurrent> : {};
  return {
    appearance: text(candidate.appearance, fallback),
    wardrobeOrSurface: text(candidate.wardrobeOrSurface),
    condition: text(candidate.condition),
    location: text(candidate.location),
    temporaryChanges: strings(candidate.temporaryChanges),
  };
}

function mergeBaseline(previous: EntityAppearanceBaseline, candidate: EntityAppearanceBaseline): EntityAppearanceBaseline {
  const placeholder = /^not yet (?:visually )?established$/i.test(previous.summary);
  return {
    summary: placeholder ? candidate.summary : previous.summary,
    signatureTraits: unique([...previous.signatureTraits, ...candidate.signatureTraits]),
    styleNotes: unique([...previous.styleNotes, ...candidate.styleNotes]),
    palette: unique([...previous.palette, ...candidate.palette]),
    motifs: unique([...previous.motifs, ...candidate.motifs]),
    avoid: unique([...previous.avoid, ...candidate.avoid]),
  };
}

function mergeCurrent(previous: EntityAppearanceCurrent, candidate: EntityAppearanceCurrent, rawCandidate: unknown): EntityAppearanceCurrent {
  const patch = rawCandidate && typeof rawCandidate === "object" ? rawCandidate as Partial<EntityAppearanceCurrent> : {};
  const has = (field: keyof EntityAppearanceCurrent) => Object.prototype.hasOwnProperty.call(patch, field);
  return {
    appearance: has("appearance") ? text(candidate.appearance, previous.appearance) : previous.appearance,
    wardrobeOrSurface: has("wardrobeOrSurface") ? candidate.wardrobeOrSurface : previous.wardrobeOrSurface,
    condition: has("condition") ? candidate.condition : previous.condition,
    location: has("location") ? candidate.location : previous.location,
    temporaryChanges: has("temporaryChanges") ? candidate.temporaryChanges : previous.temporaryChanges,
  };
}

export function normalizeEntityAppearanceGuide(value: unknown, throughTurnNumber: number): EntityAppearanceGuide | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<EntityAppearanceGuide>;
  const name = text(candidate.name);
  if (!name) return null;
  const kind = normalizeKind(candidate.kind);
  const entityId = entitySlug(candidate.entityId || name);
  const firstSeenTurn = turnNumber(candidate.firstSeenTurn, throughTurnNumber, throughTurnNumber);
  return {
    id: text(candidate.id, `${kind}:${entityId}`),
    kind,
    entityId,
    name,
    aliases: unique(strings(candidate.aliases)),
    baseline: normalizeBaseline(candidate.baseline),
    current: normalizeCurrent(candidate.current),
    firstSeenTurn,
    lastUpdatedTurn: throughTurnNumber,
    timelineObservations: normalizeEntityTimeline(candidate.timelineObservations, throughTurnNumber),
  };
}

export function normalizeEntityTimeline(value: unknown, throughTurnNumber: number, afterTurnNumber = -1): EntityAppearanceTimelineDraft[] {
  if (!Array.isArray(value)) return [];
  const byTurn = new Map<number, EntityAppearanceTimelineDraft>();
  for (const item of value) {
    if (!item || typeof item !== "object") continue;
    const candidate = item as Partial<EntityAppearanceTimelineDraft>;
    const turn = Number(candidate.turnNumber);
    const summary = text(candidate.summary);
    if (!Number.isSafeInteger(turn) || turn < 0 || turn > throughTurnNumber || turn <= afterTurnNumber || !summary) continue;
    const existing = byTurn.get(turn);
    byTurn.set(turn, {
      turnNumber: turn,
      summary: existing ? `${existing.summary}; ${summary}` : summary,
      changes: unique([...(existing?.changes || []), ...strings(candidate.changes)]),
      evidence: unique([...(existing?.evidence || []), ...strings(candidate.evidence)]),
    });
  }
  return [...byTurn.values()].sort((a, b) => a.turnNumber - b.turnNumber);
}

export function mergeEntityAppearanceGuides(existing: EntityAppearanceGuide[], candidates: unknown, throughTurnNumber: number): EntityAppearanceGuide[] {
  const merged = new Map<string, EntityAppearanceGuide>();
  for (const guide of existing) {
    const normalized = normalizeEntityAppearanceGuide(guide, Math.max(guide.lastUpdatedTurn || 0, throughTurnNumber));
    if (!normalized) continue;
    normalized.storyId = guide.storyId;
    normalized.id = guide.id || normalized.id;
    normalized.firstSeenTurn = guide.firstSeenTurn;
    normalized.lastUpdatedTurn = guide.lastUpdatedTurn;
    normalized.timelineObservations = guide.timelineObservations || [];
    merged.set(`${normalized.kind}:${normalized.entityId}`, normalized);
  }
  if (!Array.isArray(candidates)) return [...merged.values()];
  for (const value of candidates) {
    const candidate = normalizeEntityAppearanceGuide(value, throughTurnNumber);
    if (!candidate) continue;
    const key = `${candidate.kind}:${candidate.entityId}`;
    const previous = merged.get(key);
    if (!previous) {
      merged.set(key, candidate);
      continue;
    }
    if (throughTurnNumber < previous.lastUpdatedTurn) continue;
    merged.set(key, {
      ...previous,
      name: candidate.name || previous.name,
      aliases: unique([...previous.aliases, ...candidate.aliases]),
      baseline: mergeBaseline(previous.baseline, candidate.baseline),
      current: mergeCurrent(previous.current, candidate.current, (value as Partial<EntityAppearanceGuide>).current),
      firstSeenTurn: Math.min(previous.firstSeenTurn, candidate.firstSeenTurn),
      lastUpdatedTurn: Math.max(previous.lastUpdatedTurn, throughTurnNumber),
      timelineObservations: candidate.timelineObservations || [],
    });
  }
  return [...merged.values()].sort((a, b) => a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name));
}

export function observationsFromGuides(
  storyId: string,
  guides: EntityAppearanceGuide[],
  throughTurnNumber: number,
  afterTurnNumber: number,
  sourceSnapshotId: string,
  createdAt: string,
): EntityAppearanceObservation[] {
  const observations: EntityAppearanceObservation[] = [];
  for (const guide of guides) {
    for (const observation of normalizeEntityTimeline(guide.timelineObservations, throughTurnNumber, afterTurnNumber)) {
      const guideId = `${storyId}:${guide.kind}:${guide.entityId}`;
      observations.push({
        ...observation,
        id: `${guideId}:${observation.turnNumber}`,
        storyId,
        guideId,
        kind: guide.kind,
        entityId: guide.entityId,
        name: guide.name,
        sourceSnapshotId,
        createdAt,
      });
    }
  }
  return observations;
}

export function seedEntityAppearanceGuides(foundation: StoryFoundation, throughTurnNumber = 1): EntityAppearanceGuide[] {
  const characterGuides = (foundation.initialCast || []).map((member: CastMember): EntityAppearanceGuide => ({
    id: `character:${entitySlug(member.id || member.name)}`,
    kind: "character",
    entityId: entitySlug(member.id || member.name),
    name: member.name,
    aliases: unique(member.aliases || []),
    baseline: {
      summary: text(member.physicalDescription, "Not yet visually established"),
      signatureTraits: unique([member.genderPresentation, ...(member.importantPossessions || []), ...(member.abilitiesOrPowers || [])].filter(Boolean)),
      styleNotes: [], palette: [], motifs: [],
      avoid: ["unestablished facial, body, costume, or equipment changes"],
    },
    current: {
      appearance: text(member.physicalDescription, "Not yet visually established"),
      wardrobeOrSurface: "",
      condition: text(member.currentStatus),
      location: text(member.currentLocation),
      temporaryChanges: [],
    },
    firstSeenTurn: throughTurnNumber,
    lastUpdatedTurn: throughTurnNumber,
    timelineObservations: [{
      turnNumber: throughTurnNumber,
      summary: text(member.physicalDescription, `${member.name}'s initial appearance is not yet visually established.`),
      changes: [], evidence: ["Opening foundation and accepted first section"],
    }],
  }));
  if (!text(foundation.setting)) return characterGuides;
  return [...characterGuides, {
    id: "location:opening-setting",
    kind: "location",
    entityId: "opening-setting",
    name: "Opening setting",
    aliases: [],
    baseline: {
      summary: foundation.setting,
      signatureTraits: [], styleNotes: [], palette: [], motifs: [],
      avoid: ["unestablished architecture, geography, or atmosphere changes"],
    },
    current: { appearance: foundation.setting, wardrobeOrSurface: "", condition: "", location: foundation.setting, temporaryChanges: [] },
    firstSeenTurn: throughTurnNumber,
    lastUpdatedTurn: throughTurnNumber,
    timelineObservations: [{ turnNumber: throughTurnNumber, summary: foundation.setting, changes: [], evidence: ["Opening foundation and accepted first section"] }],
  }];
}

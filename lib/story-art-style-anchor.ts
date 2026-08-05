export type StoryArtStyleAnchor = {
  summary: string;
  medium: string;
  visualLanguage: string;
  palette: string[];
  lighting: string;
  compositionRules: string[];
  textureNotes: string[];
  recurringMotifs: string[];
  negativeConstraints: string[];
};

export type StoryArtStyleAnchorProvenance = {
  source: string;
  sourceId?: string;
  model?: string;
  reason?: string;
};

export type StoryArtStyleAnchorRecord = {
  storyId: string;
  anchor: StoryArtStyleAnchor;
  revision: number;
  provenance: StoryArtStyleAnchorProvenance;
  updatedThroughTurn: number;
  createdAt: string;
  updatedAt: string;
};

type Row = Record<string, unknown>;

function text(value: unknown, maximum = 600): string {
  if (typeof value !== "string") return "";
  const normalized = value.normalize("NFKC")
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return normalized.slice(0, maximum);
}

function strings(value: unknown, maximum = 16, itemMaximum = 240): string[] {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.map((item) => text(item, itemMaximum)).filter(Boolean))].slice(0, maximum);
}

function nonNegativeInteger(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= 0 ? parsed : fallback;
}

function positiveInteger(value: unknown, fallback = 1): number {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= 1 ? parsed : fallback;
}

function object(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function parseObject(value: unknown): Record<string, unknown> {
  if (typeof value !== "string") return object(value);
  try {
    return object(JSON.parse(value));
  } catch {
    return {};
  }
}

export function normalizeStoryArtStyleAnchor(value: unknown): StoryArtStyleAnchor {
  const candidate = object(value);
  return {
    summary: text(candidate.summary, 400),
    medium: text(candidate.medium, 300),
    visualLanguage: text(candidate.visualLanguage, 600),
    palette: strings(candidate.palette, 12, 80),
    lighting: text(candidate.lighting, 400),
    compositionRules: strings(candidate.compositionRules, 12, 240),
    textureNotes: strings(candidate.textureNotes, 12, 240),
    recurringMotifs: strings(candidate.recurringMotifs, 12, 160),
    negativeConstraints: strings(candidate.negativeConstraints, 20, 180),
  };
}

export function normalizeStoryArtStyleAnchorProvenance(value: unknown): StoryArtStyleAnchorProvenance {
  const candidate = object(value);
  const normalized: StoryArtStyleAnchorProvenance = { source: text(candidate.source, 80) || "unknown" };
  const sourceId = text(candidate.sourceId, 160);
  const model = text(candidate.model, 120);
  const reason = text(candidate.reason, 400);
  if (sourceId) normalized.sourceId = sourceId;
  if (model) normalized.model = model;
  if (reason) normalized.reason = reason;
  return normalized;
}

export function storyArtStyleAnchorFromRow(row: Row): StoryArtStyleAnchorRecord {
  return {
    storyId: text(row.story_id, 160),
    anchor: normalizeStoryArtStyleAnchor(parseObject(row.anchor_json)),
    revision: positiveInteger(row.revision),
    provenance: normalizeStoryArtStyleAnchorProvenance(parseObject(row.provenance_json)),
    updatedThroughTurn: nonNegativeInteger(row.updated_through_turn),
    createdAt: text(row.created_at, 80),
    updatedAt: text(row.updated_at, 80),
  };
}

export type StoryArtStyleAnchorWrite = Pick<
  StoryArtStyleAnchorRecord,
  "storyId" | "anchor" | "revision" | "provenance" | "updatedThroughTurn"
> & { createdAt?: string; updatedAt?: string };

export const STORY_ART_STYLE_ANCHOR_UPSERT_SQL = `INSERT INTO story_art_style_anchors
  (story_id,anchor_json,revision,provenance_json,updated_through_turn,created_at,updated_at)
  VALUES (?,?,?,?,?,?,?)
  ON CONFLICT(story_id) DO UPDATE SET
    anchor_json=excluded.anchor_json,
    revision=excluded.revision,
    provenance_json=excluded.provenance_json,
    updated_through_turn=excluded.updated_through_turn,
    updated_at=excluded.updated_at
  WHERE excluded.updated_through_turn>=story_art_style_anchors.updated_through_turn
    AND (excluded.revision>story_art_style_anchors.revision
      OR (excluded.revision=story_art_style_anchors.revision
        AND excluded.anchor_json=story_art_style_anchors.anchor_json))`;

export function storyArtStyleAnchorUpsertStatement(db: D1Database, input: StoryArtStyleAnchorWrite): D1PreparedStatement {
  const storyId = text(input.storyId, 160);
  if (!storyId) throw new Error("A story id is required for an art style anchor.");
  const revision = positiveInteger(input.revision, 0);
  if (!revision) throw new Error("An art style anchor revision must be a positive integer.");
  const updatedThroughTurn = nonNegativeInteger(input.updatedThroughTurn, -1);
  if (updatedThroughTurn < 0) throw new Error("An art style anchor section boundary must be a non-negative integer.");
  const createdAt = text(input.createdAt, 80) || new Date().toISOString();
  const updatedAt = text(input.updatedAt, 80) || createdAt;
  const anchorJson = JSON.stringify(normalizeStoryArtStyleAnchor(input.anchor));
  const provenanceJson = JSON.stringify(normalizeStoryArtStyleAnchorProvenance(input.provenance));
  return db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).bind(
    storyId,
    anchorJson,
    revision,
    provenanceJson,
    updatedThroughTurn,
    createdAt,
    updatedAt,
  );
}

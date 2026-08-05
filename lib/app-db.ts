import { env } from "cloudflare:workers";

let initialization: Promise<void> | null = null;

export function getD1(): D1Database {
  if (!env.DB) throw new Error("Private library storage is unavailable.");
  return env.DB as D1Database;
}

export function getArtBucket(): R2Bucket | null {
  return env.ART ? env.ART as R2Bucket : null;
}

export function getImageTransformer(): ImagesBinding | null {
  return env.IMAGES ? env.IMAGES as ImagesBinding : null;
}

const schemaStatements = [
  `CREATE TABLE IF NOT EXISTS authors (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    short_description TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    short_description TEXT NOT NULL,
    selected_author_id TEXT NOT NULL,
    author_snapshot_json TEXT NOT NULL,
    original_idea TEXT NOT NULL,
    foundation_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    latest_accepted_turn_number INTEGER NOT NULL DEFAULT 0,
    latest_checkpoint_turn_number INTEGER NOT NULL DEFAULT 0,
    default_narration_voice TEXT,
    main_viewpoint_character_id TEXT,
    reading_turn_number INTEGER NOT NULL DEFAULT 1,
    playback_rate INTEGER NOT NULL DEFAULT 100,
    auto_read_next INTEGER NOT NULL DEFAULT 0,
    auto_write_next INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS turns (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    prose TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    direction_used TEXT,
    state_delta_json TEXT NOT NULL,
    narration_json TEXT NOT NULL,
    generation_status TEXT NOT NULL DEFAULT 'Accepted',
    validation_status TEXT NOT NULL DEFAULT 'Passed',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, turn_number)
  )`,
  `CREATE TABLE IF NOT EXISTS narrations (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    turn_id TEXT NOT NULL,
    voice_id TEXT NOT NULL,
    voice_presentation TEXT NOT NULL,
    playback_rate INTEGER NOT NULL DEFAULT 100,
    status TEXT NOT NULL DEFAULT 'Ready',
    audio_reference TEXT NOT NULL,
    duration INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS cast_members (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    name TEXT NOT NULL,
    visible_json TEXT NOT NULL,
    canonical_json TEXT NOT NULL,
    last_updated_turn INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE TABLE IF NOT EXISTS story_states (
    story_id TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    last_updated_turn INTEGER NOT NULL DEFAULT 0
  )`,
  `CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    through_turn_number INTEGER NOT NULL,
    checkpoint_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, through_turn_number)
  )`,
  `CREATE TABLE IF NOT EXISTS generation_jobs (
    idempotency_key TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS operation_logs (
    id TEXT PRIMARY KEY,
    story_id TEXT,
    turn_number INTEGER,
    operation TEXT NOT NULL,
    category TEXT NOT NULL,
    attempt INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS mutation_guards (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    asserted INTEGER NOT NULL CHECK(asserted = 1),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS background_jobs (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    turn_number INTEGER,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    run_after TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    input_json TEXT NOT NULL DEFAULT '{}',
    result_json TEXT NOT NULL DEFAULT '{}',
    last_error TEXT,
    locked_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS context_snapshots (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    through_turn_number INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, through_turn_number)
  )`,
  `CREATE TABLE IF NOT EXISTS story_art_profiles (
    story_id TEXT PRIMARY KEY,
    profile_json TEXT NOT NULL,
    last_updated_turn INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE TABLE IF NOT EXISTS visual_profiles (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    last_updated_turn INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, kind, entity_id)
  )`,
  `CREATE TABLE IF NOT EXISTS entity_appearance_guides (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    name TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    baseline_json TEXT NOT NULL,
    current_json TEXT NOT NULL,
    first_seen_turn INTEGER NOT NULL DEFAULT 0,
    last_updated_turn INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, kind, entity_id)
  )`,
  `CREATE TABLE IF NOT EXISTS entity_appearance_observations (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    guide_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    name TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    observation_json TEXT NOT NULL,
    source_snapshot_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(story_id, kind, entity_id, turn_number)
  )`,
  `CREATE TABLE IF NOT EXISTS art_assets (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    turn_id TEXT,
    turn_number INTEGER,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    caption TEXT NOT NULL,
    prompt_summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Placeholder',
    image_reference TEXT,
    mime_type TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  )`,
  `CREATE INDEX IF NOT EXISTS stories_status_updated_idx ON stories(status, updated_at DESC)`,
  `CREATE INDEX IF NOT EXISTS turns_story_number_idx ON turns(story_id, turn_number)`,
  `CREATE INDEX IF NOT EXISTS narrations_story_turn_idx ON narrations(story_id, turn_id)`,
  `CREATE INDEX IF NOT EXISTS cast_story_idx ON cast_members(story_id)`,
  `CREATE INDEX IF NOT EXISTS checkpoints_story_turn_idx ON checkpoints(story_id, through_turn_number DESC)`,
  `CREATE INDEX IF NOT EXISTS operation_logs_story_created_idx ON operation_logs(story_id, created_at DESC)`,
  `CREATE INDEX IF NOT EXISTS background_jobs_status_run_idx ON background_jobs(status, run_after)`,
  `CREATE INDEX IF NOT EXISTS background_jobs_story_idx ON background_jobs(story_id, created_at DESC)`,
  `CREATE INDEX IF NOT EXISTS context_snapshots_story_turn_idx ON context_snapshots(story_id, through_turn_number DESC)`,
  `CREATE INDEX IF NOT EXISTS visual_profiles_story_idx ON visual_profiles(story_id, kind)`,
  `CREATE INDEX IF NOT EXISTS entity_appearance_guides_story_idx ON entity_appearance_guides(story_id, kind, name)`,
  `CREATE INDEX IF NOT EXISTS entity_appearance_observations_story_turn_idx ON entity_appearance_observations(story_id, turn_number, kind)`,
  `CREATE INDEX IF NOT EXISTS art_assets_story_turn_idx ON art_assets(story_id, turn_number, created_at)`,
];

export async function ensureDatabase() {
  if (!initialization) {
    initialization = (async () => {
      const db = getD1();
      await db.batch(schemaStatements.map((statement) => db.prepare(statement)));
    })().catch((error) => {
      initialization = null;
      throw error;
    });
  }
  await initialization;
}

export function json<T>(value: string | null | undefined, fallback: T): T {
  if (!value) return fallback;
  try {
    return JSON.parse(value) as T;
  } catch {
    return fallback;
  }
}

export function words(value: string) {
  return value.trim().split(/\s+/).filter(Boolean).length;
}

export function now() {
  return new Date().toISOString();
}

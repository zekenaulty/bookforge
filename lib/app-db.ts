import { env } from "cloudflare:workers";

let initialization: Promise<void> | null = null;

export function getD1(): D1Database {
  if (!env.DB) throw new Error("Private library storage is unavailable.");
  return env.DB as D1Database;
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
  `CREATE INDEX IF NOT EXISTS stories_status_updated_idx ON stories(status, updated_at DESC)`,
  `CREATE INDEX IF NOT EXISTS turns_story_number_idx ON turns(story_id, turn_number)`,
  `CREATE INDEX IF NOT EXISTS narrations_story_turn_idx ON narrations(story_id, turn_id)`,
  `CREATE INDEX IF NOT EXISTS cast_story_idx ON cast_members(story_id)`,
  `CREATE INDEX IF NOT EXISTS checkpoints_story_turn_idx ON checkpoints(story_id, through_turn_number DESC)`,
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

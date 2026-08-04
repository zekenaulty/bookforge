import { sql } from "drizzle-orm";
import { integer, sqliteTable, text, uniqueIndex } from "drizzle-orm/sqlite-core";

export const authors = sqliteTable("authors", {
  id: text("id").primaryKey(),
  displayName: text("display_name").notNull(),
  shortDescription: text("short_description").notNull(),
  profileJson: text("profile_json").notNull(),
  archived: integer("archived", { mode: "boolean" }).notNull().default(false),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const stories = sqliteTable("stories", {
  id: text("id").primaryKey(),
  title: text("title").notNull(),
  shortDescription: text("short_description").notNull(),
  selectedAuthorId: text("selected_author_id").notNull(),
  authorSnapshotJson: text("author_snapshot_json").notNull(),
  originalIdea: text("original_idea").notNull(),
  foundationJson: text("foundation_json").notNull(),
  status: text("status").notNull().default("Active"),
  latestAcceptedTurnNumber: integer("latest_accepted_turn_number").notNull().default(0),
  latestCheckpointTurnNumber: integer("latest_checkpoint_turn_number").notNull().default(0),
  defaultNarrationVoice: text("default_narration_voice"),
  mainViewpointCharacterId: text("main_viewpoint_character_id"),
  readingTurnNumber: integer("reading_turn_number").notNull().default(1),
  playbackRate: integer("playback_rate").notNull().default(100),
  autoReadNext: integer("auto_read_next", { mode: "boolean" }).notNull().default(false),
  autoWriteNext: integer("auto_write_next", { mode: "boolean" }).notNull().default(false),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const turns = sqliteTable(
  "turns",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    turnNumber: integer("turn_number").notNull(),
    prose: text("prose").notNull(),
    wordCount: integer("word_count").notNull(),
    directionUsed: text("direction_used"),
    stateDeltaJson: text("state_delta_json").notNull(),
    narrationJson: text("narration_json").notNull(),
    generationStatus: text("generation_status").notNull().default("Accepted"),
    validationStatus: text("validation_status").notNull().default("Passed"),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [uniqueIndex("turns_story_turn_unique").on(table.storyId, table.turnNumber)],
);

export const narrations = sqliteTable("narrations", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  turnId: text("turn_id").notNull(),
  voiceId: text("voice_id").notNull(),
  voicePresentation: text("voice_presentation").notNull(),
  playbackRate: integer("playback_rate").notNull().default(100),
  status: text("status").notNull().default("Ready"),
  audioReference: text("audio_reference").notNull(),
  duration: integer("duration"),
  createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

export const castMembers = sqliteTable("cast_members", {
  id: text("id").primaryKey(),
  storyId: text("story_id").notNull(),
  name: text("name").notNull(),
  visibleJson: text("visible_json").notNull(),
  canonicalJson: text("canonical_json").notNull(),
  lastUpdatedTurn: integer("last_updated_turn").notNull().default(0),
});

export const storyStates = sqliteTable("story_states", {
  storyId: text("story_id").primaryKey(),
  stateJson: text("state_json").notNull(),
  lastUpdatedTurn: integer("last_updated_turn").notNull().default(0),
});

export const checkpoints = sqliteTable(
  "checkpoints",
  {
    id: text("id").primaryKey(),
    storyId: text("story_id").notNull(),
    throughTurnNumber: integer("through_turn_number").notNull(),
    checkpointJson: text("checkpoint_json").notNull(),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [uniqueIndex("checkpoint_story_turn_unique").on(table.storyId, table.throughTurnNumber)],
);

export const generationJobs = sqliteTable("generation_jobs", {
  idempotencyKey: text("idempotency_key").primaryKey(),
  storyId: text("story_id").notNull(),
  turnNumber: integer("turn_number").notNull(),
  status: text("status").notNull(),
  error: text("error"),
  updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
});

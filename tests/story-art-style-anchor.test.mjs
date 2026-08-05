import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";
import {
  STORY_ART_STYLE_ANCHOR_UPSERT_SQL,
  normalizeStoryArtStyleAnchor,
  storyArtStyleAnchorFromRow,
  storyArtStyleAnchorUpsertStatement,
} from "../lib/story-art-style-anchor.ts";

const anchor = {
  summary: " Ink-wash maritime fantasy ",
  medium: "gouache and ink",
  visualLanguage: "graphic silhouettes with fine nautical detail",
  palette: ["indigo", " amber ", "indigo", ""],
  lighting: "storm-filtered lantern light",
  compositionRules: ["deep foreground framing", "deep foreground framing", "clear focal silhouette"],
  textureNotes: ["visible dry-brush grain"],
  recurringMotifs: ["compass roses"],
  negativeConstraints: ["no photorealism"],
};

function sqlValues({ storyId = "story-1", candidate = anchor, revision = 1, source = "foundation", through = 1, stamp = "2026-08-04T00:00:00.000Z" } = {}) {
  return [
    storyId,
    JSON.stringify(normalizeStoryArtStyleAnchor(candidate)),
    revision,
    JSON.stringify({ source }),
    through,
    stamp,
    stamp,
  ];
}

test("normalizes a deterministic story-wide style payload and safely reads stored rows", () => {
  const normalized = normalizeStoryArtStyleAnchor(anchor);
  assert.equal(normalized.summary, "Ink-wash maritime fantasy");
  assert.deepEqual(normalized.palette, ["indigo", "amber"]);
  assert.deepEqual(normalized.compositionRules, ["deep foreground framing", "clear focal silhouette"]);

  const bounded = normalizeStoryArtStyleAnchor({
    summary: `\u0000 ${"s".repeat(600)}`,
    palette: Array.from({ length: 30 }, (_, index) => `${index}-${"p".repeat(100)}`),
    negativeConstraints: Array.from({ length: 30 }, (_, index) => `avoid-${index}`),
  });
  assert.equal(bounded.summary.length, 400);
  assert.equal(bounded.palette.length, 12);
  assert.ok(bounded.palette.every((item) => item.length <= 80));
  assert.equal(bounded.negativeConstraints.length, 20);
  assert.doesNotMatch(bounded.summary, /\u0000/);

  const record = storyArtStyleAnchorFromRow({
    story_id: "story-1",
    anchor_json: JSON.stringify(normalized),
    revision: 2,
    provenance_json: JSON.stringify({ source: "author_agent", model: "model-1" }),
    updated_through_turn: 12,
    created_at: "created",
    updated_at: "updated",
  });
  assert.equal(record.storyId, "story-1");
  assert.equal(record.revision, 2);
  assert.equal(record.provenance.model, "model-1");
  assert.equal(record.updatedThroughTurn, 12);

  const malformed = storyArtStyleAnchorFromRow({ story_id: "story-2", anchor_json: "{", provenance_json: "bad" });
  assert.equal(malformed.anchor.summary, "");
  assert.equal(malformed.provenance.source, "unknown");
  assert.equal(malformed.revision, 1);
});

test("upsert helper validates boundaries and returns a batchable D1 statement", () => {
  let preparedSql = "";
  let bindings = [];
  const statement = { bind: (...values) => { bindings = values; return statement; } };
  const db = { prepare: (sql) => { preparedSql = sql; return statement; } };
  const result = storyArtStyleAnchorUpsertStatement(db, {
    storyId: " story-1 ", anchor, revision: 1, provenance: { source: "foundation" }, updatedThroughTurn: 1,
    createdAt: "created", updatedAt: "updated",
  });
  assert.equal(result, statement);
  assert.equal(preparedSql, STORY_ART_STYLE_ANCHOR_UPSERT_SQL);
  assert.equal(bindings[0], "story-1");
  assert.equal(JSON.parse(bindings[1]).summary, "Ink-wash maritime fantasy");
  assert.throws(() => storyArtStyleAnchorUpsertStatement(db, {
    storyId: "", anchor, revision: 1, provenance: { source: "test" }, updatedThroughTurn: 0,
  }), /story id/i);
  assert.throws(() => storyArtStyleAnchorUpsertStatement(db, {
    storyId: "story", anchor, revision: 0, provenance: { source: "test" }, updatedThroughTurn: 0,
  }), /revision/i);
  assert.throws(() => storyArtStyleAnchorUpsertStatement(db, {
    storyId: "story", anchor, revision: 1, provenance: { source: "test" }, updatedThroughTurn: -1,
  }), /section boundary/i);
});

test("migration enforces one anchor per story and rejects stale or same-revision drift", async () => {
  const db = new DatabaseSync(":memory:");
  const migration = await readFile(new URL("../drizzle/0004_vengeful_scrambler.sql", import.meta.url), "utf8");
  db.exec(migration);

  db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).run(...sqlValues());
  db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).run(...sqlValues({ candidate: { ...anchor, medium: "oil" }, through: 12 }));
  let row = db.prepare("SELECT * FROM story_art_style_anchors WHERE story_id=?").get("story-1");
  assert.equal(JSON.parse(row.anchor_json).medium, "gouache and ink", "same revision cannot silently change the anchor");
  assert.equal(row.updated_through_turn, 1);

  db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).run(...sqlValues({ through: 12, source: "context_reconcile" }));
  row = db.prepare("SELECT * FROM story_art_style_anchors WHERE story_id=?").get("story-1");
  assert.equal(row.updated_through_turn, 12, "the unchanged anchor can be revalidated through a later section");
  assert.equal(JSON.parse(row.provenance_json).source, "context_reconcile");

  db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).run(...sqlValues({ candidate: { ...anchor, medium: "oil" }, revision: 2, through: 6 }));
  row = db.prepare("SELECT * FROM story_art_style_anchors WHERE story_id=?").get("story-1");
  assert.equal(row.revision, 1, "a later revision cannot move the validated section boundary backward");

  db.prepare(STORY_ART_STYLE_ANCHOR_UPSERT_SQL).run(...sqlValues({ candidate: { ...anchor, medium: "oil" }, revision: 2, through: 12 }));
  row = db.prepare("SELECT * FROM story_art_style_anchors WHERE story_id=?").get("story-1");
  assert.equal(row.revision, 2);
  assert.equal(JSON.parse(row.anchor_json).medium, "oil");
  assert.throws(() => db.prepare("UPDATE story_art_style_anchors SET revision=0 WHERE story_id='story-1'").run(), /CHECK constraint failed/i);
  assert.throws(() => db.prepare("UPDATE story_art_style_anchors SET updated_through_turn=-1 WHERE story_id='story-1'").run(), /CHECK constraint failed/i);
  db.close();
});

test("schema, runtime bootstrap, and generated migration stay aligned", async () => {
  const root = new URL("../", import.meta.url);
  const [schema, runtimeDb, migration] = await Promise.all([
    readFile(new URL("db/schema.ts", root), "utf8"),
    readFile(new URL("lib/app-db.ts", root), "utf8"),
    readFile(new URL("drizzle/0004_vengeful_scrambler.sql", root), "utf8"),
  ]);
  for (const source of [schema, runtimeDb, migration]) {
    assert.match(source, /story_art_style_anchors/);
    assert.match(source, /updated_through_turn/);
    assert.match(source, /provenance_json/);
  }
  assert.match(schema, /story_art_style_anchor_revision_check/);
  assert.match(runtimeDb, /CHECK\(revision >= 1\)/);
  assert.match(migration, /story_art_style_anchor_turn_check/);
});

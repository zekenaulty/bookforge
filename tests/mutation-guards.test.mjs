import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { DatabaseSync } from "node:sqlite";
import test from "node:test";

const writerGuardSql = `INSERT INTO mutation_guards (id,story_id,asserted,created_at)
  SELECT ?,?,CASE WHEN
    EXISTS (SELECT 1 FROM stories WHERE id=? AND latest_accepted_turn_number=?)
    AND COALESCE((SELECT MAX(turn_number) FROM turns WHERE story_id=?),0)=?
    AND COALESCE((SELECT id FROM turns WHERE story_id=? ORDER BY turn_number DESC LIMIT 1),'')=?
    AND EXISTS (SELECT 1 FROM generation_jobs WHERE idempotency_key=? AND status='generating' AND error=?)
  THEN 1 ELSE 0 END,?`;

const boundaryGuardSql = `INSERT INTO mutation_guards (id,story_id,asserted,created_at)
  SELECT ?,?,CASE WHEN
    EXISTS (SELECT 1 FROM turns WHERE story_id=? AND turn_number=? AND id=?)
    AND EXISTS (SELECT 1 FROM background_jobs WHERE id=? AND status='running' AND locked_at=?)
    AND COALESCE((SELECT through_turn_number FROM context_snapshots WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1),0)=?
    AND COALESCE((SELECT id FROM context_snapshots WHERE story_id=? ORDER BY through_turn_number DESC LIMIT 1),'')=?
  THEN 1 ELSE 0 END,?`;

async function database() {
  const db = new DatabaseSync(":memory:");
  db.exec(`
    CREATE TABLE stories (id TEXT PRIMARY KEY, latest_accepted_turn_number INTEGER NOT NULL);
    CREATE TABLE turns (id TEXT PRIMARY KEY, story_id TEXT NOT NULL, turn_number INTEGER NOT NULL);
    CREATE TABLE generation_jobs (idempotency_key TEXT PRIMARY KEY, status TEXT NOT NULL, error TEXT);
    CREATE TABLE background_jobs (id TEXT PRIMARY KEY, status TEXT NOT NULL, locked_at TEXT);
    CREATE TABLE context_snapshots (id TEXT PRIMARY KEY, story_id TEXT NOT NULL, through_turn_number INTEGER NOT NULL, UNIQUE(story_id,through_turn_number));
  `);
  db.exec(await readFile(new URL("../drizzle/0003_fat_legion.sql", import.meta.url), "utf8"));
  return db;
}

function transaction(db, mutate) {
  db.exec("BEGIN IMMEDIATE");
  try {
    mutate();
    db.exec("COMMIT");
  } catch (error) {
    db.exec("ROLLBACK");
    throw error;
  }
}

test("writer mutation guard rolls back every statement when its predecessor CAS is stale", async () => {
  const db = await database();
  db.prepare("INSERT INTO stories VALUES (?,?)").run("story", 1);
  db.prepare("INSERT INTO turns VALUES (?,?,?)").run("turn-1", "story", 1);
  db.prepare("INSERT INTO generation_jobs VALUES (?,?,?)").run("story:2", "generating", "lease-2");

  transaction(db, () => {
    db.prepare(writerGuardSql).run("guard-ok", "story", "story", 1, "story", 1, "story", "turn-1", "story:2", "lease-2", "now");
    db.prepare("INSERT INTO turns VALUES (?,?,?)").run("turn-2", "story", 2);
    db.prepare("UPDATE stories SET latest_accepted_turn_number=2 WHERE id='story'").run();
    db.prepare("DELETE FROM mutation_guards WHERE id='guard-ok'").run();
  });
  assert.equal(db.prepare("SELECT latest_accepted_turn_number AS n FROM stories WHERE id='story'").get().n, 2);

  assert.throws(() => transaction(db, () => {
    db.prepare(writerGuardSql).run("guard-stale", "story", "story", 1, "story", 1, "story", "turn-1", "story:2", "lease-2", "now");
    db.prepare("INSERT INTO turns VALUES (?,?,?)").run("must-not-persist", "story", 99);
  }), /CHECK constraint failed/i);
  assert.equal(db.prepare("SELECT COUNT(*) AS n FROM turns WHERE id='must-not-persist'").get().n, 0);
  assert.equal(db.prepare("SELECT COUNT(*) AS n FROM mutation_guards").get().n, 0);
  db.close();
});

test("background guard permits append-only growth but rejects replaced boundaries and late peer commits", async () => {
  const db = await database();
  db.prepare("INSERT INTO stories VALUES (?,?)").run("story", 13);
  db.prepare("INSERT INTO turns VALUES (?,?,?)").run("turn-12", "story", 12);
  db.prepare("INSERT INTO turns VALUES (?,?,?)").run("turn-13", "story", 13);
  db.prepare("INSERT INTO background_jobs VALUES (?,?,?)").run("context-job", "running", "lock");

  transaction(db, () => {
    db.prepare(boundaryGuardSql).run("guard-window", "story", "story", 12, "turn-12", "context-job", "lock", "story", 0, "story", "", "now");
    db.prepare("INSERT INTO context_snapshots VALUES (?,?,?)").run("snapshot-12", "story", 12);
    db.prepare("DELETE FROM mutation_guards WHERE id='guard-window'").run();
  });
  assert.equal(db.prepare("SELECT COUNT(*) AS n FROM context_snapshots").get().n, 1);

  assert.throws(() => transaction(db, () => {
    db.prepare(boundaryGuardSql).run("guard-late-peer", "story", "story", 12, "turn-12", "context-job", "lock", "story", 0, "story", "", "now");
    db.prepare("INSERT OR REPLACE INTO context_snapshots VALUES (?,?,?)").run("late-snapshot-12", "story", 12);
  }), /CHECK constraint failed/i);
  assert.equal(db.prepare("SELECT id FROM context_snapshots WHERE through_turn_number=12").get().id, "snapshot-12");

  db.prepare("UPDATE turns SET id='turn-12-replaced' WHERE id='turn-12'").run();
  assert.throws(() => transaction(db, () => {
    db.prepare(boundaryGuardSql).run("guard-stale-window", "story", "story", 12, "turn-12", "context-job", "lock", "story", 12, "story", "snapshot-12", "now");
    db.prepare("INSERT INTO context_snapshots VALUES (?,?,?)").run("stale-snapshot", "story", 12);
  }), /CHECK constraint failed/i);
  assert.equal(db.prepare("SELECT COUNT(*) AS n FROM context_snapshots WHERE id='stale-snapshot'").get().n, 0);
  db.close();
});

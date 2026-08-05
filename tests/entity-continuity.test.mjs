import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  entitySlug,
  exactProseSurfaceMatch,
  mergeEntityAppearanceGuides,
  nextReconciliationThrough,
  normalizeEntityTimeline,
  observationsFromGuides,
  seedEntityAppearanceGuides,
} from "../lib/entity-continuity.ts";

const foundation = {
  setting: "A rain-dark harbor built around black basalt stairs.",
  initialCast: [{
    id: "mara-vale", name: "Mara Vale", aliases: ["Mara"], genderPresentation: "woman",
    physicalDescription: "Tall, silver-streaked black hair, amber coat, brass compass.",
    importantPossessions: ["secret brass key"], abilitiesOrPowers: ["latent tide-sight"], currentStatus: "secretly cursed", currentLocation: "hidden cell",
  }],
};

test("prose identity matching is token-bounded and returns the published surface", () => {
  assert.equal(exactProseSurfaceMatch("The party crashed into annual rites.", "Art"), undefined);
  assert.equal(exactProseSurfaceMatch("ANN waited beneath the arch.", "Ann"), "ANN");
  assert.equal(exactProseSurfaceMatch("仮面の葵は振り返った。", "葵"), "葵");
});

test("seeds character and location style baselines with Section 1 timeline links", () => {
  const guides = seedEntityAppearanceGuides(foundation, 1);
  assert.deepEqual(guides.map((guide) => guide.kind), ["character", "location"]);
  assert.match(guides[0].baseline.summary, /silver-streaked black hair/);
  assert.deepEqual(guides[0].baseline.signatureTraits, ["woman"]);
  assert.doesNotMatch(JSON.stringify(guides[0]), /secret brass key|latent tide-sight|secretly cursed|hidden cell/);
  assert.equal(guides[0].timelineObservations[0].turnNumber, 1);
  assert.equal(guides[1].entityId, "opening-setting");
});

test("rolling reconciliation enriches a baseline without erasing prior traits", () => {
  const existing = seedEntityAppearanceGuides(foundation, 1);
  const merged = mergeEntityAppearanceGuides(existing, [{
    kind: "character", entityId: "mara-vale", name: "Mara Vale", aliases: ["Captain Vale"], firstSeenTurn: 1,
    baseline: {
      summary: "A completely different summary must not replace the baseline.",
      signatureTraits: ["scar over left eyebrow"], styleNotes: ["weathered maritime tailoring"], palette: ["amber", "charcoal"], motifs: ["compass rose"], avoid: ["modern clothing"],
    },
    current: { appearance: "Rain-soaked, with a fresh eyebrow cut.", wardrobeOrSurface: "amber coat", condition: "minor cut", location: "breakwater", temporaryChanges: ["wet hair"] },
    timelineObservations: [{ turnNumber: 12, summary: "Mara reaches the breakwater in the storm.", changes: ["fresh eyebrow cut"], evidence: ["Section 12"] }],
  }], 12);
  const mara = merged.find((guide) => guide.entityId === "mara-vale");
  assert.match(mara.baseline.summary, /silver-streaked black hair/);
  assert.ok(mara.baseline.signatureTraits.includes("woman"));
  assert.ok(!mara.baseline.signatureTraits.includes("secret brass key"));
  assert.ok(mara.baseline.signatureTraits.includes("scar over left eyebrow"));
  assert.ok(mara.aliases.includes("Captain Vale"));
  assert.equal(mara.current.condition, "minor cut");
  assert.equal(mara.lastUpdatedTurn, 12);
});

test("older reconciliation cannot roll current appearance backward and explicit empty transient state clears", () => {
  const current = mergeEntityAppearanceGuides([], [{
    kind: "character", entityId: "mara", name: "Mara", aliases: [], firstSeenTurn: 1,
    baseline: { summary: "Black hair", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] },
    current: { appearance: "Black hair", wardrobeOrSurface: "coat", condition: "wet", location: "pier", temporaryChanges: ["rain-soaked"] },
  }], 13);
  const stale = mergeEntityAppearanceGuides(current, [{
    kind: "character", entityId: "mara", name: "Mara", aliases: [], firstSeenTurn: 1,
    baseline: { summary: "Black hair", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] },
    current: { appearance: "Black hair", wardrobeOrSurface: "old coat", condition: "injured", location: "harbor", temporaryChanges: ["bleeding"] },
  }], 12);
  assert.equal(stale[0].current.condition, "wet");
  const omitted = mergeEntityAppearanceGuides(stale, [{
    kind: "character", entityId: "mara", name: "Mara", aliases: [], firstSeenTurn: 1,
    baseline: { summary: "Black hair", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] },
  }], 14);
  assert.equal(omitted[0].current.condition, "wet");
  assert.equal(omitted[0].current.location, "pier");
  const dry = mergeEntityAppearanceGuides(stale, [{
    kind: "character", entityId: "mara", name: "Mara", aliases: [], firstSeenTurn: 1,
    baseline: { summary: "Black hair", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] },
    current: { appearance: "Black hair", wardrobeOrSurface: "coat", condition: "", location: "inside", temporaryChanges: [] },
  }], 15);
  assert.equal(dry[0].current.condition, "");
  assert.deepEqual(dry[0].current.temporaryChanges, []);
});

test("non-Latin entity ids remain distinct", () => {
  assert.equal(entitySlug("怪獣 一"), "怪獣-一");
  assert.equal(entitySlug("怪獣 二"), "怪獣-二");
  assert.notEqual(entitySlug("怪獣 一"), entitySlug("怪獣 二"));
});

test("long reconciliation gaps advance in bounded sequential windows without skipping sections", () => {
  const windows = [];
  let previous = 0;
  while (previous < 40) {
    previous = nextReconciliationThrough(40, previous);
    windows.push(previous);
  }
  assert.deepEqual(windows, [12, 24, 36, 40]);
});

test("timeline observations remain ordered, bounded to accepted turns, and deterministically keyed", () => {
  const guides = mergeEntityAppearanceGuides([], [{
    kind: "item", entityId: "glass-key", name: "Glass Key", aliases: [], firstSeenTurn: 4,
    baseline: { summary: "A translucent key", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] },
    current: { appearance: "Cracked", wardrobeOrSurface: "", condition: "cracked", location: "Mara's pocket", temporaryChanges: [] },
    timelineObservations: [
      { turnNumber: 13, summary: "Future hallucination", changes: [], evidence: [] },
      { turnNumber: 12, summary: "The key cracks", changes: ["hairline crack"], evidence: ["Section 12"] },
      { turnNumber: 12, summary: "but remains usable", changes: ["still usable"], evidence: ["closing beat"] },
      { turnNumber: 3, summary: "Too old for this window", changes: [], evidence: [] },
    ],
  }], 12);
  assert.deepEqual(normalizeEntityTimeline(guides[0].timelineObservations, 12, 3).map((item) => item.turnNumber), [12]);
  const observations = observationsFromGuides("story-1", guides, 12, 3, "snapshot-12", "2026-08-04T00:00:00.000Z");
  assert.equal(observations.length, 1);
  assert.equal(observations[0].id, "story-1:item:glass-key:12");
  assert.match(observations[0].summary, /The key cracks; but remains usable/);
});

test("persists guides and observations and atomically rejects stale continuity commits", async () => {
  const root = new URL("../", import.meta.url);
  const [schema, runtimeDb, route, ai, entityMigration, guardMigration] = await Promise.all([
    readFile(new URL("db/schema.ts", root), "utf8"),
    readFile(new URL("lib/app-db.ts", root), "utf8"),
    readFile(new URL("app/api/app/route.ts", root), "utf8"),
    readFile(new URL("lib/ai.ts", root), "utf8"),
    readFile(new URL("drizzle/0002_motionless_celestials.sql", root), "utf8"),
    readFile(new URL("drizzle/0003_fat_legion.sql", root), "utf8"),
  ]);
  for (const source of [schema, runtimeDb, entityMigration]) {
    assert.match(source, /entity_appearance_guides/);
    assert.match(source, /entity_appearance_observations/);
  }
  assert.match(schema, /mutationGuards/);
  assert.match(runtimeDb, /CREATE TABLE IF NOT EXISTS mutation_guards/);
  assert.match(guardMigration, /mutation_guard_asserted_check/);
  assert.match(route, /nextReconciliationThrough\(latestAccepted, latestSnapshotThrough\)/);
  assert.match(route, /nextReconciliationThrough\(latestAccepted, after\)/);
  assert.match(route, /CONTEXT_RECONCILE_INTERVAL = 12/);
  assert.match(route, /const checkpointTarget = story\.latestCheckpointTurnNumber \+ 12/);
  assert.match(route, /latest_checkpoint_turn_number=MAX\(latest_checkpoint_turn_number,\?\)/);
  assert.match(route, /DELETE FROM entity_appearance_observations WHERE story_id=\? AND turn_number>=\?/);
  assert.match(route, /DELETE FROM entity_appearance_guides WHERE story_id=\?/);
  assert.match(route, /DELETE FROM visual_profiles WHERE story_id=\?/);
  assert.match(route, /story\.turns\.slice\(0, -1\)\.slice\(-12\)/);
  assert.match(route, /if \(input\.rebuildFromTurn && previousVisualContext\?\.entityAppearanceGuides\?\.length\)/);
  assert.match(route, /writerMutationGuardStatement\(db/);
  assert.match(route, /regenerationMutationGuardStatement\(db/);
  assert.match(route, /backgroundBoundaryMutationGuardStatement\(db/);
  assert.match(route, /INSERT INTO mutation_guards/);
  assert.match(route, /EXISTS \(SELECT 1 FROM turns WHERE story_id=\? AND turn_number=\? AND id=\?\)/);
  assert.match(route, /expectedHeadThrough: latestSnapshotThrough, expectedHeadId: latestSnapshotId/);
  assert.match(route, /expectedHeadThrough: after, expectedHeadId: checkpointHeadId/);
  assert.match(route, /filter\(\(guide\) => guide\.lastUpdatedTurn <= through\)/);
  assert.doesNotMatch(route, /Story advanced; reconcile from the new accepted tail/);
  assert.match(route, /regen:\$\{turnId\}/);
  assert.match(route, /writer_predecessor_changed/);
  assert.match(route, /WRITER_LEASE_MS = 12 \* 60_000/);
  assert.match(route, /status='generating' AND error=\?/);
  assert.match(route, /refreshGenerationLease\(db, key, generationLease\)/);
  assert.match(route, /category: "writer_lease", recoverable: true, retryAfterMs: 2_000/);
  assert.match(route, /JSON\.stringify\(failure\)/);
  assert.match(route, /error: errorMessage, \.\.\.details/);
  assert.match(ai, /const deadline = Date\.now\(\) \+ TRANSPORT_TIMEOUT_MS/);
  assert.match(ai, /timelineObservations must contain only newly supported observations/);
  assert.match(ai, /"item"\|"creature"\|"group"/);
});

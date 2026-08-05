import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

const [route, ai, googleImage] = await Promise.all([
  readFile(new URL("app/api/app/route.ts", root), "utf8"),
  readFile(new URL("lib/ai.ts", root), "utf8"),
  readFile(new URL("lib/google-image.ts", root), "utf8"),
]);

function between(source, start, end) {
  const startIndex = source.indexOf(start);
  assert.notEqual(startIndex, -1, `missing start marker: ${start}`);
  const endIndex = source.indexOf(end, startIndex + start.length);
  assert.notEqual(endIndex, -1, `missing end marker: ${end}`);
  return source.slice(startIndex, endIndex);
}

const artRunner = between(route, "async function runArtJob", "function clearArtPromptPlan");
const artBriefFunction = between(ai, "export async function createArtBrief", "export function validationIssues");
const contextRunner = between(route, "async function runContextJob", "async function runCheckpointJob");
const narrativeContextFunction = between(ai, "export async function createContextReconciliation", "export async function createVisualContextReconciliation");
const visualContextFunction = between(ai, "export async function createVisualContextReconciliation", "export async function createStoryArtStyleAnchor");

test("v3 art jobs persist a prepared plan, defer, then enter the guarded render phase", () => {
  const prepareStart = artRunner.indexOf("if (!reusablePlan)");
  const planPersist = artRunner.indexOf("UPDATE background_jobs SET input_json=?", prepareStart);
  const deferred = artRunner.indexOf("return { deferred: true, runAfterMs: 0, input", planPersist);
  const renderHashCheck = artRunner.indexOf("await sha256Hex(finalPrompt) !== promptHash", deferred);
  const providerCall = artRunner.indexOf("await generateGoogleImage", renderHashCheck);

  assert.ok(prepareStart >= 0);
  assert.ok(planPersist > prepareStart);
  assert.ok(deferred > planPersist);
  assert.ok(renderHashCheck > deferred);
  assert.ok(providerCall > renderHashCheck);
  assert.match(artRunner, /promptPlanVersion:\s*3/);
  assert.match(artRunner, /promptPhase:\s*"render"/);
  assert.match(artRunner, /targetTurnId[\s\S]*scopeThroughTurn:\s*targetTurnNumber[\s\S]*styleAnchorRevision/);
  assert.match(route, /Math\.max\(0, outcome\.runAfterMs \?\? 0\)/);
});

test("the full prompt stays in hidden job input while public art rows receive only a bounded safe summary", () => {
  const preparedInput = between(artRunner, "Object.assign(input, {", "delete input.refreshBrief");
  assert.match(preparedInput, /safePromptSummary:\s*safeSummary/);
  assert.match(preparedInput, /\bfinalPrompt\b/);
  assert.match(preparedInput, /\bpromptHash\b/);

  const persistedPlan = between(artRunner, "const persistedPlan", "return { deferred: true");
  assert.match(persistedPlan, /UPDATE background_jobs SET input_json=\?/);
  assert.match(persistedPlan, /JSON\.stringify\(input\)/);
  assert.match(persistedPlan, /ensureArtAssetForLease[\s\S]*promptSummary:\s*safeSummary/);
  assert.doesNotMatch(persistedPlan, /promptSummary:\s*finalPrompt/);

  const safeSummary = between(route, "function safeArtSummary", "async function sha256Hex");
  assert.match(safeSummary, /\.slice\(0,\s*900\)/);

  const artMapper = between(route, "function artFromRow", "function jobFromRow");
  const jobMapper = between(route, "function jobFromRow", "function writingJobFromRow");
  assert.match(artMapper, /promptSummary:\s*String\(row\.prompt_summary/);
  assert.doesNotMatch(`${artMapper}\n${jobMapper}`, /input_json|finalPrompt|promptHash/);
});

test("pending legacy v2 briefs are safely upgraded through the scoped v3 planner", () => {
  const migrationMarker = artRunner.indexOf("migratedFromBriefVersion");
  const briefCall = artRunner.indexOf("await createArtBrief", migrationMarker);
  const layeredPrompt = artRunner.indexOf("const finalPrompt = finalPromptLayers.prompt", briefCall);

  assert.ok(migrationMarker >= 0);
  assert.ok(briefCall > migrationMarker);
  assert.ok(layeredPrompt > briefCall);
  assert.doesNotMatch(artRunner, /legacyBrief|const finalPrompt = legacy/);
  assert.match(artRunner, /migratedFromBriefVersion/);
});

test("every provider submission is counted and atomically guarded by lease, exact turn, and style revision", () => {
  const callback = between(artRunner, "beforeProviderSubmit: async", "    });\n    await bucket.put");
  assert.match(callback, /input\.providerSubmissionCount\s*=\s*nextSubmissionCount/);
  assert.match(callback, /UPDATE background_jobs SET input_json=\?,updated_at=\? WHERE id=\? AND status='running' AND locked_at=\?/);
  assert.match(callback, /EXISTS \(SELECT 1 FROM turns WHERE story_id=\? AND turn_number=\? AND id=\?\)/);
  assert.match(callback, /EXISTS \(SELECT 1 FROM story_art_style_anchors WHERE story_id=\? AND revision=\?\)/);
  assert.match(callback, /"art_submission_guard", false/);

  const googleLoop = between(googleImage, "async function googleJson", "function googleBase");
  const callbackIndex = googleLoop.indexOf("await budget.beforeSubmit(nextSubmissionCount)");
  const countIndex = googleLoop.indexOf("budget.used = nextSubmissionCount", callbackIndex);
  const fetchIndex = googleLoop.indexOf("await fetch(", countIndex);
  assert.ok(callbackIndex >= 0);
  assert.ok(countIndex > callbackIndex);
  assert.ok(fetchIndex > countIndex);
  assert.match(googleLoop, /budget\.used >= budget\.maximum/);
});

test("the hidden art director receives only layered grounding and a minimal entity shortlist", () => {
  const invocation = between(artRunner, "const prepared = await createArtBrief({", "      });");
  assert.match(invocation, /storyId:\s*story\.id/);
  assert.match(invocation, /storyTitle:\s*story\.title/);
  assert.match(invocation, /layeredGroundingPrompt:\s*basePrompt\.prompt/);
  assert.match(invocation, /candidateEntities:[\s\S]*entityId:[\s\S]*kind:[\s\S]*name:/);
  assert.match(invocation, /entityId: `\$\{item\.kind\}:\$\{item\.entityId\}`/);
  assert.doesNotMatch(invocation, /\b(?:story|foundation|authorSnapshot|storyState|cast|knownSecrets)\s*[:,]/);

  const signature = artBriefFunction.slice(0, artBriefFunction.indexOf("}) {"));
  assert.match(signature, /layeredGroundingPrompt:\s*string/);
  assert.match(signature, /candidateEntities:\s*Array<\{ entityId: string; kind: string; name: string \}>/);
  assert.doesNotMatch(signature, /foundation|authorSnapshot|storyState|cast|knownSecrets/);
});

test("empty planner selections stay empty and user-requested scenes fall back instead of disappearing", () => {
  assert.match(artRunner, /const selected = plannerSucceeded \? new Set\(selectedEntityRefs\) : undefined/);
  assert.match(artRunner, /direction\.shouldIllustrate === false && type === "scene" && input\.requestedByUser !== true/);
  assert.match(artRunner, /selected\.has\(`\$\{item\.kind\}:\$\{item\.entityId\}`\)/);
});

test("R2 recovery and publish are bound to the exact prompt, turn, style revision, and lease", () => {
  assert.match(artRunner, /expectedRenderPrefix/);
  assert.match(artRunner, /stored\.customMetadata\?\.promptHash === String\(input\.promptHash/);
  assert.match(artRunner, /stored\.customMetadata\?\.styleAnchorRevision === String\(styleAnchorRevision\)/);
  assert.match(artRunner, /stored\.customMetadata\?\.targetTurnId === targetTurnId/);
  assert.match(artRunner, /targetTurnId \},/);
  assert.match(artRunner, /return artGuardFailureOutcome/);

  const guardOutcome = between(route, "async function artGuardFailureOutcome", "function backgroundFailure");
  assert.match(guardOutcome, /status='running' AND locked_at=\?/);
  assert.match(guardOutcome, /SELECT id FROM turns WHERE story_id=\? AND turn_number=\?/);
  assert.match(guardOutcome, /SELECT revision FROM story_art_style_anchors/);
  assert.match(guardOutcome, /runAfterMs: 0/);
});

test("Section 1 regeneration invalidates and requeues cover work", () => {
  const regeneration = between(route, "async function handleAcceptRegeneration", "type JobType");
  assert.match(regeneration, /job_type IN \('art_scene','art_cover'\)/);
  assert.match(regeneration, /type<>'cover' OR \?=1/);
  assert.match(regeneration, /enqueueReusableJobStatement[\s\S]*art_cover:\$\{storyId\}:1/);
});

test("historical art reconstruction fails closed instead of borrowing tail state or cast", () => {
  const state = between(route, "function artStoryStateThrough", "function artStoryCastThrough");
  const cast = between(route, "function artStoryCastThrough", "async function storyForArtTurn");
  const scoped = between(route, "async function storyForArtTurn", "function writerMutationGuardStatement");
  assert.match(state, /return delta\?\.nextStoryState/);
  assert.doesNotMatch(state, /story\.storyState!/);
  assert.match(cast, /return Array\.isArray\(nextDelta\?\.priorCast\) \? nextDelta\.priorCast : \[\]/);
  assert.doesNotMatch(cast, /: story\.cast/);
  assert.match(scoped, /storyState: artStoryStateThrough/);
  assert.match(scoped, /cast: artStoryCastThrough/);
  assert.match(scoped, /context\?\.visualContextVersion === 2/);
  assert.match(scoped, /entityAppearanceTimeline: proseSafeContext \?/);
});

test("visual reconciliation is a separate prose-only pass and hidden continuity cannot author art records", () => {
  assert.doesNotMatch(narrativeContextFunction, /storyArtProfile|characterVisualProfiles|locationVisualProfiles|entityAppearanceGuides/);
  assert.match(visualContextFunction, /acceptedTurns: Array<\{ turnNumber: number; prose: string \}>/);
  assert.match(visualContextFunction, /Opening-level book projection \(style guidance only; never use it as evidence for an entity fact\)/);
  assert.match(visualContextFunction, /every evidence entry must identify its exact Section number/);
  assert.match(visualContextFunction, /completeVisualContext/);
  assert.doesNotMatch(visualContextFunction, /\bstate:\s*StoryState|\bcast:\s*CastMember|knownSecrets|stateDelta/);

  const visualInvocation = between(contextRunner, "createVisualContextReconciliation({", "    }),");
  assert.match(visualInvocation, /foundation: visualFoundationProjection\(story\.foundation\)/);
  assert.match(visualInvocation, /acceptedTurns: acceptedVisualTurns/);
  assert.match(visualInvocation, /previousVisualContext/);
  assert.doesNotMatch(visualInvocation, /\bstate:|\bcast:|stateDelta|knownSecrets/);
  assert.match(contextRunner, /visualContextVersion: 2/);
  assert.match(contextRunner, /storyArtProfile: visualSnapshot\.storyArtProfile/);
  assert.match(contextRunner, /entityAppearanceGuides: snapshotGuides/);
});

test("legacy visual context is rebuilt from accepted prose and old visual stores are discarded atomically", () => {
  const baseline = between(route, "async function ensureBaselineJobs", "async function failExhaustedJobs");
  assert.match(baseline, /visualContextVersion \|\| 0\) < 2/);
  assert.match(baseline, /visual-safe-v2/);
  assert.match(baseline, /enqueueReusableJobStatement/);
  assert.match(baseline, /force: true, rebuildVisual: true/);
  assert.match(contextRunner, /proseOnlyVisualRebuildTurns\(story, through\)/);
  assert.match(contextRunner, /previousVisualIsSafe \? previousThrough : 0/);
  assert.match(route, /proseVerifiedLegacyObservations/);
  assert.match(route, /const safeChanges = verified\(observation\.changes \|\| \[\]\)/);
  assert.match(route, /const safeEvidence = verified\(observation\.evidence \|\| \[\]\)/);
  assert.match(route, /const safeName = names\.map\(\(name\) => exactProseSurfaceMatch\(turn\.prose, name\)\)/);
  assert.match(route, /const entityId = `legacy-\$\{entitySlug\(safeName\)\}`/);
  assert.match(route, /name: safeName/);
  assert.match(contextRunner, /const resetVisualStores = !previousVisualIsSafe/);
  const mutationBatch = contextRunner.slice(contextRunner.indexOf("backgroundBoundaryMutationGuardStatement"));
  const guard = mutationBatch.indexOf("backgroundBoundaryMutationGuardStatement");
  const deleteProfiles = mutationBatch.indexOf('DELETE FROM visual_profiles');
  const saveSnapshot = mutationBatch.indexOf('INSERT OR REPLACE INTO context_snapshots');
  assert.ok(deleteProfiles > guard);
  assert.ok(saveSnapshot > deleteProfiles);
  assert.match(mutationBatch, /DELETE FROM entity_appearance_observations/);
  assert.match(mutationBatch, /DELETE FROM entity_appearance_guides/);
});

test("book style refinement receives only the opening-safe foundation projection", () => {
  const foundationFunction = between(ai, "export async function createStoryFoundation", "export async function continueStory");
  const styleFunction = between(ai, "export async function createStoryArtStyleAnchor", "export async function createArtBrief");
  assert.doesNotMatch(foundationFunction, /artStyleAnchor/);
  assert.match(styleFunction, /const safeProjection/);
  assert.doesNotMatch(styleFunction, /initialCast|centralConflict|knownSecrets|narrativePromises|importantConstraints/);
});

import assert from "node:assert/strict";
import test from "node:test";
import { composeLayeredArtPrompt, deriveStoryVisualStyleAnchor, selectScopedArtEntities } from "../lib/art-prompt.ts";

function foundation(overrides = {}) {
  return {
    title: "The Brass Tide",
    shortDescription: "Mara enters the Black Breakwater to recover a drowned compass.",
    genres: ["maritime fantasy"],
    tone: ["melancholy", "tense"],
    pointOfView: "third person limited",
    tense: "past",
    openingSituation: "Mara reaches the harbor before a storm.",
    centralConflict: "The tide remembers every debt.",
    narrativePromises: ["compass roses", "echoing bells"],
    importantConstraints: [],
    additionalInstructions: "",
    broadDirection: "",
    setting: "A rain-dark harbor of black basalt stairs and copper lamps.",
    initialWorldFacts: [],
    initialRelationshipFacts: [],
    initialOpenPlotThreads: [],
    factsThatMustRemainTrue: [],
    initialNarrationVoiceRecommendation: "",
    mainViewpointCharacterId: "mara-vale",
    initialCast: [{ id: "mara-vale", name: "Mara Vale", aliases: ["Mara"], physicalDescription: "Silver-streaked black hair and an amber coat." }],
    ...overrides,
  };
}

function guide(overrides = {}) {
  return {
    id: "story:character:mara-vale",
    kind: "character",
    entityId: "mara-vale",
    name: "Mara Vale",
    aliases: ["Captain Vale", "Mara"],
    baseline: {
      summary: "Tall, silver-streaked black hair, weathered amber coat.",
      signatureTraits: ["brass compass", "scar over left eyebrow"],
      styleNotes: ["weathered maritime tailoring"],
      palette: ["amber", "charcoal"],
      motifs: ["compass rose"],
      avoid: ["modern clothing"],
    },
    current: {
      appearance: "Rain-soaked",
      wardrobeOrSurface: "amber coat",
      condition: "uninjured",
      location: "Black Breakwater",
      temporaryChanges: ["wet hair"],
    },
    firstSeenTurn: 1,
    lastUpdatedTurn: 4,
    ...overrides,
  };
}

function baseInput(overrides = {}) {
  return {
    storyId: "story-brass-tide",
    storyTitle: "The Brass Tide",
    assetType: "scene",
    targetTurnNumber: 4,
    foundation: foundation(),
    artProfile: {
      artStyle: "Layered ink wash over rough cotton paper, sharp amber rim light",
      coverStyle: "Monumental silhouettes with a low horizon",
      palette: ["basalt", "amber", "storm blue"],
      mood: "salt-dark and watchful",
      protagonistAppearance: "Mara in an amber coat",
      majorCastAppearance: [],
      keyLocationAppearance: [],
      creatureDesignLanguage: "Marine forms built from tide-worn geometry",
      recurringMotifs: ["compass roses"],
      avoid: ["glossy 3D rendering"],
      lastUpdatedTurn: 4,
    },
    turn: { turnNumber: 4, prose: "Captain Vale crossed the Black Breakwater. Copper lamps streaked the rain." },
    sceneSetting: "The Black Breakwater in hard rain",
    entityAppearanceGuides: [
      guide(),
      guide({
        id: "story:location:black-breakwater", kind: "location", entityId: "black-breakwater", name: "Black Breakwater", aliases: ["the breakwater"],
        baseline: { summary: "Black basalt stairs descend between copper storm lamps.", signatureTraits: ["uneven sea wall"], styleNotes: ["severe maritime geometry"], palette: ["black basalt", "oxidized copper"], motifs: ["tide marks"], avoid: ["white marble"] },
        current: { appearance: "Rain-polished basalt", wardrobeOrSurface: "", condition: "storm-lashed", location: "outer harbor", temporaryChanges: ["high tide"] },
      }),
      guide({ id: "story:character:orin", entityId: "orin", name: "Orin", aliases: [], baseline: { summary: "A red-haired mechanic", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] } }),
    ],
    entityAppearanceTimeline: [{
      id: "story:character:mara-vale:4", storyId: "story-brass-tide", guideId: "story:character:mara-vale", kind: "character", entityId: "mara-vale", name: "Mara Vale", turnNumber: 4,
      summary: "Mara's coat and hair are soaked by rain.", changes: ["wet hair"], evidence: ["Section 4"], createdAt: "2026-08-04T00:00:00Z",
    }],
    visualProfiles: [{ id: "vp-mara", kind: "character", entityId: "mara-vale", name: "Mara Vale", hair: "silver-streaked black", clothing: "weathered amber coat", distinctiveMarkings: ["left-eyebrow scar"], lastUpdatedTurn: 4 }],
    ...overrides,
  };
}

test("derives a stable, distinct book style anchor from story-scoped direction", () => {
  const first = deriveStoryVisualStyleAnchor(baseInput());
  const repeated = deriveStoryVisualStyleAnchor(baseInput());
  const other = deriveStoryVisualStyleAnchor(baseInput({ storyId: "story-other", storyTitle: "Another Sea" }));
  assert.deepEqual(first, repeated);
  assert.notEqual(first.anchorId, other.anchorId);
  assert.match(first.artStyle, /Layered ink wash/);
  assert.deepEqual(first.palette, ["basalt", "amber", "storm blue"]);
  assert.ok(first.renderingRules.some((rule) => /consistent across this book/i.test(rule)));
});

test("fallback anchors vary materially and deterministically with each story foundation", () => {
  const harborInput = baseInput({ artProfile: undefined });
  const desertInput = baseInput({
    storyId: "story-glass-desert", storyTitle: "The Glass Desert", artProfile: undefined,
    foundation: foundation({
      title: "The Glass Desert", genres: ["solar myth"], tone: ["austere", "radiant"],
      setting: "A wind-carved desert of singing glass dunes beneath two pale suns.",
      narrativePromises: ["prismatic shadows", "buried observatories"],
    }),
  });
  const harbor = deriveStoryVisualStyleAnchor(harborInput);
  const desert = deriveStoryVisualStyleAnchor(desertInput);
  assert.deepEqual(harbor, deriveStoryVisualStyleAnchor(harborInput));
  assert.notEqual(harbor.artStyle, desert.artStyle);
  assert.notDeepEqual(harbor.palette, desert.palette);
  assert.match(harbor.artStyle, /rain-dark harbor/);
  assert.match(desert.artStyle, /singing glass dunes/);
});

test("selects only known characters and locations actually scoped to the requested scene", () => {
  const entities = selectScopedArtEntities(baseInput());
  assert.deepEqual(new Set(entities.map((entity) => entity.entityId)), new Set(["mara-vale", "black-breakwater"]));
  const mara = entities.find((entity) => entity.entityId === "mara-vale");
  const breakwater = entities.find((entity) => entity.entityId === "black-breakwater");
  assert.match(mara.visualProfile.hair, /silver-streaked/);
  assert.equal(mara.observations.length, 1);
  assert.ok(breakwater.matchedBy.some((reason) => reason.includes("black-breakwater") || reason.includes("location-description")));
});

test("honors aliases and explicit cast references without substring false positives", () => {
  const byAlias = selectScopedArtEntities(baseInput({ turn: { turnNumber: 4, prose: "Mara waited beneath the lamps." }, sceneSetting: "" }));
  assert.equal(byAlias[0].entityId, "mara-vale");
  const notAnnual = selectScopedArtEntities(baseInput({
    turn: { turnNumber: 4, prose: "The annual storm arrived." }, sceneSetting: "", requestedEntityRefs: [],
    entityAppearanceGuides: [guide({ entityId: "ann", name: "Ann", aliases: [] })],
  }));
  assert.equal(notAnnual.length, 0);
});

test("uses exact turn-scoped cast for a newly introduced character not yet in the rolling snapshot", () => {
  const result = composeLayeredArtPrompt(baseInput({
    targetTurnNumber: 13,
    turn: { turnNumber: 13, prose: "Ilyan stepped from the spray and raised the tuning fork." },
    sceneSetting: "Outer harbor stairs",
    entityAppearanceGuides: baseInput().entityAppearanceGuides,
    entityAppearanceTimeline: [],
    visualProfiles: [],
    cast: [{
      id: "ilyan", name: "Ilyan", aliases: ["the Listener"], physicalDescription: "Compact, copper-brown curls, sea-glass spectacles, slate fisher's coat.",
      currentLocation: "PRIVATE HIDDEN BUNKER", currentStatus: "PRIVATE SECRETLY POSSESSED", importantPossessions: ["silver tuning fork"], abilitiesOrPowers: ["hears submerged bells"], lastUpdatedTurn: 13,
      pronouns: "he/him", genderPresentation: "man", narrativeRole: "PRIVATE ROLE", viewpointPriority: "PRIVATE PRIORITY", personality: "PRIVATE PERSONALITY", goals: [], fears: [], knownSecrets: ["PRIVATE SECRET"], importantRelationships: [],
    }],
  }));
  const ilyan = result.scopedEntities.find((entity) => entity.entityId === "ilyan");
  assert.ok(ilyan);
  assert.match(ilyan.guide.id, /^turn-scoped-cast:/);
  assert.match(result.prompt, /sea-glass spectacles/);
  assert.doesNotMatch(result.prompt, /PRIVATE HIDDEN BUNKER|PRIVATE SECRETLY POSSESSED|silver tuning fork|hears submerged bells|PRIVATE ROLE|PRIVATE PRIORITY|PRIVATE PERSONALITY|PRIVATE SECRET/);
});

test("rejects future-mutated guides, visual and art profiles, observations, state, and turns", () => {
  const result = composeLayeredArtPrompt(baseInput({
    targetTurnNumber: 4,
    turn: { turnNumber: 5, prose: "FUTURE TURN SECRET" },
    storyState: { lastUpdatedTurn: 5, currentLocation: "FUTURE PALACE", currentScene: "FUTURE CORONATION", castPresent: ["future-queen"] },
    artProfile: { ...baseInput().artProfile, artStyle: "FUTURE STYLE", lastUpdatedTurn: 5 },
    entityAppearanceGuides: [
      guide({ lastUpdatedTurn: 5, current: { appearance: "FUTURE CROWN", wardrobeOrSurface: "", condition: "", location: "", temporaryChanges: [] } }),
      guide({ id: "future", entityId: "future-queen", name: "Future Queen", firstSeenTurn: 5, lastUpdatedTurn: 5 }),
    ],
    entityAppearanceTimeline: [{ ...baseInput().entityAppearanceTimeline[0], id: "future-observation", turnNumber: 5, summary: "FUTURE WOUND" }],
    visualProfiles: [{ ...baseInput().visualProfiles[0], hair: "FUTURE BLUE HAIR", lastUpdatedTurn: 5 }],
    cast: [{ id: "future-queen", name: "Future Queen", aliases: [], physicalDescription: "FUTURE CAST DESCRIPTION", currentLocation: "FUTURE PALACE", currentStatus: "crowned", importantPossessions: [], abilitiesOrPowers: [], lastUpdatedTurn: 5 }],
  }));
  assert.doesNotMatch(result.prompt, /FUTURE/);
  assert.equal(result.scopedEntities.length, 0);
  assert.match(result.styleAnchor.artStyle, /this story's world/);
  assert.match(result.prompt, /Continuity cutoff: Section 4/);
});

test("uses the timeless persisted story anchor only for its owning story", () => {
  const styleAnchor = {
    storyId: "story-brass-tide", revision: 3, updatedThroughTurn: 99, createdAt: "2026-08-04T00:00:00Z", updatedAt: "2026-08-04T00:00:00Z", provenance: { source: "hidden-author-turn" },
    anchor: {
      summary: "Graphic maritime melancholy", medium: "Opaque gouache", visualLanguage: "Angular silhouettes", palette: ["lamp amber", "basalt"], lighting: "Copper pools in blue rain",
      compositionRules: ["low horizon"], textureNotes: ["dry-brush salt bloom"], recurringMotifs: ["broken compass circles"], negativeConstraints: ["photorealism"],
    },
  };
  const accepted = composeLayeredArtPrompt(baseInput({ styleAnchor }));
  assert.match(accepted.prompt, /Opaque gouache/);
  assert.match(accepted.prompt, /Copper pools in blue rain/);
  assert.match(accepted.prompt, /dry-brush salt bloom/);
  assert.match(accepted.prompt, /photorealism/);
  assert.match(accepted.styleAnchor.anchorId, /-r3$/);

  const wrongStory = composeLayeredArtPrompt(baseInput({ styleAnchor: { ...styleAnchor, storyId: "another-story" } }));
  assert.doesNotMatch(wrongStory.prompt, /Opaque gouache/);
  assert.match(wrongStory.prompt, /Layered ink wash/);
});

test("builds ordered, auditable layers with setting and appearance detail", () => {
  const result = composeLayeredArtPrompt(baseInput({ assetRequest: "Frame Mara against the lamps." }));
  assert.deepEqual(result.layers.map((item) => item.id), ["asset", "style", "composition", "setting", "entities", "evidence", "constraints"]);
  assert.match(result.prompt, /LOCKED BOOK STYLE ANCHOR/);
  assert.match(result.prompt, /Black basalt stairs descend between copper storm lamps/);
  assert.match(result.prompt, /silver-streaked black hair/);
  assert.match(result.prompt, /left-eyebrow scar/);
  assert.match(result.prompt, /timeline evidence through this section: Section 4/);
  assert.match(result.prompt, /modern clothing/);
});

test("uses a cover-specific contract and safely scopes opening entities", () => {
  const result = composeLayeredArtPrompt(baseInput({ assetType: "cover", targetTurnNumber: 1, turn: undefined, artProfile: { ...baseInput().artProfile, lastUpdatedTurn: 1 }, entityAppearanceGuides: baseInput().entityAppearanceGuides.map((item) => ({ ...item, lastUpdatedTurn: 1 })) }));
  assert.match(result.prompt, /portrait 2:3 literary book-cover illustration/);
  assert.match(result.prompt, /title-safe negative space/);
  assert.ok(result.scopedEntities.some((entity) => entity.entityId === "mara-vale"));
  assert.ok(result.scopedEntities.some((entity) => entity.entityId === "black-breakwater"));
});

test("bounds source evidence and entity count deterministically", () => {
  const many = Array.from({ length: 20 }, (_, index) => guide({ id: `g-${index}`, entityId: `person-${index}`, name: `Person ${index}`, aliases: [] }));
  const input = baseInput({
    maxEntities: 3,
    maxSourceCharacters: 500,
    requestedEntityRefs: many.map((item) => item.entityId),
    turn: { turnNumber: 4, prose: `OPENING Person 0 ${"storm ".repeat(2_000)} LATE DECISIVE MOMENT` },
    entityAppearanceGuides: many,
  });
  const first = composeLayeredArtPrompt(input);
  const second = composeLayeredArtPrompt(input);
  assert.equal(first.prompt, second.prompt);
  assert.equal(first.scopedEntities.length, 3);
  const evidence = first.layers.find((item) => item.id === "evidence").lines.join(" ");
  assert.ok(evidence.length < 900);
  assert.doesNotMatch(evidence, /storm (?:storm ){100}/);
  assert.match(evidence, /OPENING/);
  assert.match(evidence, /LATE DECISIVE MOMENT/);
});

test("finds an entity mentioned only in the closing excerpt of a long section", () => {
  const late = guide({ id: "late", entityId: "late-arrival", name: "Late Arrival", aliases: [] });
  const entities = selectScopedArtEntities(baseInput({
    requestedEntityRefs: [], storyState: undefined, sceneSetting: "", sceneIntent: "", assetRequest: "",
    turn: { turnNumber: 4, prose: `Opening rain. ${"waves ".repeat(2_500)} Late Arrival stepped beneath the final lamp.` },
    entityAppearanceGuides: [late], entityAppearanceTimeline: [], visualProfiles: [],
  }));
  assert.ok(entities.some((entity) => entity.entityId === "late-arrival"));
});

test("kind-qualified references disambiguate colliding character and location ids", () => {
  const collision = [
    guide({ id: "character-meridian", entityId: "meridian", name: "Meridian", aliases: [] }),
    guide({ id: "location-meridian", kind: "location", entityId: "meridian", name: "Meridian Hall", aliases: [],
      baseline: { summary: "An octagonal hall of green stone.", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] } }),
  ];
  const entities = selectScopedArtEntities(baseInput({
    requestedEntityRefs: ["location:meridian"], storyState: undefined, sceneSetting: "", sceneIntent: "", assetRequest: "",
    turn: { turnNumber: 4, prose: "Rain crossed an unnamed threshold." }, entityAppearanceGuides: collision,
  }));
  assert.deepEqual(entities.map((entity) => `${entity.kind}:${entity.entityId}`), ["location:meridian"]);
});

test("reserves room for a defining location in a crowded scene", () => {
  const crowded = [
    guide({ id: "a", entityId: "a", name: "A", aliases: [] }),
    guide({ id: "b", entityId: "b", name: "B", aliases: [] }),
    guide({ id: "c", entityId: "c", name: "C", aliases: [] }),
    guide({ id: "dock", kind: "location", entityId: "dock", name: "Dock", aliases: [],
      baseline: { summary: "A narrow iron dock.", signatureTraits: [], styleNotes: [], palette: [], motifs: [], avoid: [] } }),
  ];
  const entities = selectScopedArtEntities(baseInput({ maxEntities: 2, requestedEntityRefs: ["character:a", "character:b", "character:c", "location:dock"],
    storyState: undefined, sceneSetting: "", turn: { turnNumber: 4, prose: "A gathering in rain." }, entityAppearanceGuides: crowded }));
  assert.equal(entities.length, 2);
  assert.ok(entities.some((entity) => entity.kind === "location" && entity.entityId === "dock"));
});

test("creates a turn-scoped setting guide when snapshots lag behind accepted state", () => {
  const result = composeLayeredArtPrompt(baseInput({
    storyState: { lastUpdatedTurn: 4, currentLocation: "Obsidian Atrium", currentScene: "PRIVATE UNREVEALED CLONE CHAMBER", castPresent: [] },
    sceneSetting: "", entityAppearanceGuides: [], entityAppearanceTimeline: [], visualProfiles: [], cast: [],
    turn: { turnNumber: 4, prose: "Water fell from the atrium arches into the mirror pool." },
  }));
  assert.match(result.prompt, /Obsidian Atrium/);
  assert.match(result.prompt, /atrium arches/);
  assert.doesNotMatch(result.prompt, /PRIVATE UNREVEALED CLONE CHAMBER/);
  assert.ok(result.scopedEntities.some((entity) => entity.kind === "location" && /^turn-location-/.test(entity.entityId)));
});

test("rejects canonical state locations that have no accepted-prose evidence", () => {
  const result = composeLayeredArtPrompt(baseInput({
    storyState: { lastUpdatedTurn: 4, currentLocation: "SECRET MOON BASE", currentScene: "UNREVEALED CLONE CHAMBER", castPresent: [] },
    sceneSetting: "", entityAppearanceGuides: [], entityAppearanceTimeline: [], visualProfiles: [], cast: [],
    turn: { turnNumber: 4, prose: "Mara waited in the rain beside a familiar wall." },
  }));
  assert.doesNotMatch(result.prompt, /SECRET MOON BASE|UNREVEALED CLONE CHAMBER/);
});

test("retrieves nearest accepted prose for a scoped entity between context snapshots", () => {
  const result = composeLayeredArtPrompt(baseInput({
    targetTurnNumber: 4,
    acceptedTurns: [
      { turnNumber: 2, prose: "Mara tied a lapis scarf over her amber coat before entering the rain." },
      { turnNumber: 3, prose: "The storm erased the last dry footprints." },
      { turnNumber: 4, prose: "Mara raised the lamp and listened." },
    ],
    turn: { turnNumber: 4, prose: "Mara raised the lamp and listened." },
    sceneSetting: "", entityAppearanceTimeline: [], visualProfiles: [],
  }));
  assert.match(result.prompt, /accepted prior prose near this entity: Section 2/);
  assert.match(result.prompt, /lapis scarf/);
});

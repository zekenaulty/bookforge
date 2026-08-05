import type { StoryArtStyleAnchorRecord } from "./story-art-style-anchor";

export type AuthorProfile = {
  id: string;
  displayName: string;
  shortDescription: string;
  selectedGenres: string[];
  voice: string;
  tone: string[];
  pacing: string;
  preferredPointOfView: string;
  preferredTense: string;
  proseDensity: string;
  sensoryBias: string[];
  recurringThemes: string[];
  cadenceRules: string[];
  writingRules: string[];
  thingsToAvoid: string[];
  archived?: boolean;
  createdAt?: string;
  updatedAt?: string;
};

export type CastMember = {
  id: string;
  storyId?: string;
  name: string;
  aliases: string[];
  pronouns: string;
  genderPresentation: string;
  narrativeRole: string;
  viewpointPriority: string;
  physicalDescription: string;
  personality: string;
  goals: string[];
  fears: string[];
  knownSecrets: string[];
  importantRelationships: string[];
  currentStatus: string;
  currentLocation: string;
  importantPossessions: string[];
  abilitiesOrPowers: string[];
  lastUpdatedTurn: number;
  readerKnownSummary?: string;
};

export type StoryFoundation = {
  title: string;
  shortDescription: string;
  genres: string[];
  tone: string[];
  pointOfView: string;
  tense: string;
  openingSituation: string;
  centralConflict: string;
  narrativePromises: string[];
  importantConstraints: string[];
  additionalInstructions: string;
  broadDirection: string;
  setting: string;
  initialWorldFacts: string[];
  initialRelationshipFacts: string[];
  initialOpenPlotThreads: string[];
  factsThatMustRemainTrue: string[];
  initialNarrationVoiceRecommendation: string;
  mainViewpointCharacterId: string;
  initialCast: CastMember[];
};

export type StoryState = {
  currentTime: string;
  currentLocation: string;
  currentScene: string;
  activeViewpointCharacterId: string;
  castPresent: string[];
  recentEvents: string[];
  establishedWorldFacts: string[];
  importantRelationshipFacts: string[];
  openPlotThreads: string[];
  resolvedPlotThreads: string[];
  activePromises: string[];
  importantItems: string[];
  injuriesAndConditions: string[];
  factsThatMustRemainTrue: string[];
  milestonesCompleted: string[];
  milestonesNotYetCompleted: string[];
  currentNarrativePressure: string;
  currentArcDirection: string;
  lastUpdatedTurn: number;
};

export type TurnResult = {
  prose: string;
  stateDelta: Record<string, unknown>;
  nextStoryState: StoryState;
  castUpdates: CastMember[];
  relationshipUpdates: string[];
  worldFactUpdates: string[];
  threadUpdates: string[];
  milestoneUpdates: string[];
  viewpointCharacterId: string;
  narrationVoiceHint: string;
  turnIntent: Record<string, unknown>;
};

export type Turn = {
  id: string;
  storyId: string;
  turnNumber: number;
  prose: string;
  wordCount: number;
  createdAt: string;
  directionUsed: string;
  stateDelta: Record<string, unknown>;
  narration: Record<string, unknown>;
  generationStatus: string;
  validationStatus: string;
};

export type Story = {
  id: string;
  title: string;
  shortDescription: string;
  selectedAuthorId: string;
  authorSnapshot: AuthorProfile;
  originalIdea: string;
  foundation: StoryFoundation;
  status: "Active" | "Finished" | "Archived";
  latestAcceptedTurnNumber: number;
  latestCheckpointTurnNumber: number;
  defaultNarrationVoice?: string;
  mainViewpointCharacterId?: string;
  readingTurnNumber: number;
  playbackRate: number;
  autoReadNext: boolean;
  autoWriteNext: boolean;
  createdAt: string;
  updatedAt: string;
  turns?: Turn[];
  cast?: CastMember[];
  storyState?: StoryState;
  contextSnapshot?: ContextSnapshot;
  artProfile?: StoryArtProfile;
  artStyleAnchor?: StoryArtStyleAnchorRecord;
  visualProfiles?: VisualProfile[];
  entityAppearanceGuides?: EntityAppearanceGuide[];
  entityAppearanceTimeline?: EntityAppearanceObservation[];
  writingJob?: WritingJob;
  art?: ArtAsset[];
  jobs?: BackgroundJob[];
  logs?: OperationLog[];
};

export type StoryArtProfile = {
  artStyle: string;
  coverStyle: string;
  palette: string[];
  mood: string;
  protagonistAppearance: string;
  majorCastAppearance: string[];
  keyLocationAppearance: string[];
  creatureDesignLanguage: string;
  recurringMotifs: string[];
  avoid: string[];
  lastUpdatedTurn: number;
};

export type VisualProfile = {
  id: string;
  storyId?: string;
  kind: "character" | "location";
  entityId: string;
  name: string;
  agePresentation?: string;
  genderPresentation?: string;
  bodyType?: string;
  hair?: string;
  face?: string;
  clothing?: string;
  notableProps?: string[];
  distinctiveMarkings?: string[];
  armorOrGear?: string[];
  currentVisualChanges?: string[];
  visualDescription?: string;
  architecture?: string;
  lighting?: string;
  atmosphere?: string;
  dominantColors?: string[];
  importantLandmarks?: string[];
  lastUpdatedTurn: number;
};

export type EntityKind = "character" | "location" | "item" | "creature" | "group" | "other";

export type EntityAppearanceBaseline = {
  summary: string;
  signatureTraits: string[];
  styleNotes: string[];
  palette: string[];
  motifs: string[];
  avoid: string[];
};

export type EntityAppearanceCurrent = {
  appearance: string;
  wardrobeOrSurface: string;
  condition: string;
  location: string;
  temporaryChanges: string[];
};

export type EntityAppearanceTimelineDraft = {
  turnNumber: number;
  summary: string;
  changes: string[];
  evidence: string[];
};

export type EntityAppearanceGuide = {
  id: string;
  storyId?: string;
  kind: EntityKind;
  entityId: string;
  name: string;
  aliases: string[];
  baseline: EntityAppearanceBaseline;
  current: EntityAppearanceCurrent;
  firstSeenTurn: number;
  lastUpdatedTurn: number;
  timelineObservations?: EntityAppearanceTimelineDraft[];
};

export type EntityAppearanceObservation = EntityAppearanceTimelineDraft & {
  id: string;
  storyId: string;
  guideId: string;
  kind: EntityKind;
  entityId: string;
  name: string;
  sourceSnapshotId?: string;
  createdAt: string;
};

export type WritingJob = {
  turnNumber: number;
  status: "generating" | "completed" | "failed";
  error?: string;
  category?: string;
  recoverable?: boolean;
  retryAfterMs?: number;
  updatedAt: string;
};

export type ContextSnapshot = {
  throughTurnNumber: number;
  visualContextVersion?: number;
  compactStorySummary: string;
  characterState: Array<{
    characterId: string;
    name: string;
    currentMotives: string[];
    immediateGoals: string[];
    emotionalState: string;
    appearanceNow: string;
    keyFacts: string[];
    relationships: string[];
    currentLocation: string;
  }>;
  keyFacts: string[];
  openQuestions: string[];
  visualContinuityNotes: string[];
  storyArtProfile: StoryArtProfile;
  characterVisualProfiles: VisualProfile[];
  locationVisualProfiles: VisualProfile[];
  entityAppearanceGuides?: EntityAppearanceGuide[];
  entityAppearanceObservations?: EntityAppearanceTimelineDraft[];
};

export type ArtAsset = {
  id: string;
  storyId: string;
  turnId?: string;
  turnNumber?: number;
  type: "cover" | "scene" | "character" | "location";
  category: "Cover" | "Scenes" | "Characters" | "Locations";
  title: string;
  caption: string;
  promptSummary: string;
  status: "Placeholder" | "Queued" | "Preparing" | "Ready" | "Failed" | "Unsupported";
  imageReference?: string;
  mimeType?: string;
  createdAt: string;
  updatedAt: string;
};

export type BackgroundJob = {
  id: string;
  storyId: string;
  turnNumber?: number;
  jobType: "context_reconcile" | "checkpoint_reconcile" | "art_cover" | "art_scene";
  status: "pending" | "running" | "retrying" | "completed" | "failed" | "unsupported";
  attempts: number;
  maxAttempts: number;
  runAfter: string;
  lastError?: string;
  createdAt: string;
  updatedAt: string;
};

export type OperationLog = {
  id: string;
  storyId?: string;
  turnNumber?: number;
  operation: string;
  category: string;
  attempt: number;
  status: "retrying" | "recovered" | "failed" | "completed" | "unsupported";
  message: string;
  context: Record<string, unknown>;
  createdAt: string;
};

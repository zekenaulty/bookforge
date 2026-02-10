You’ve already laid more of the foundation for my earlier “pillars” than I realized. The snapshot shows you’re converging on a very specific (and very good) pattern:

1. durable canon lives in registries
2. scenes operate on a slice/posture/view
3. the only way canon changes is via explicit patch blocks
4. lint enforces canon mostly on “authoritative surfaces,” and gives prose room to breathe  

With that lens, here’s my revised “big strokes” set—focused on what’s *actually missing* (or only half-present) relative to what you already built.

1. Canon lexicon / alias rules: you already started it, but it’s currently “inventory-shaped”
   This one is real in your system already: you’ve explicitly called out canonical naming + aliases, and your registries even have optional `aliases` fields.  
   Also: you already have the enforcement boundary (“only authoritative surfaces get canonical enforcement; narrative can alias freely”), which is the hard part. 

What’s missing (big-stroke) is generalizing this from “items/devices” into a single cross-entity identity layer that covers the other drift magnets:

* locations (so “Character Creation Void” doesn’t slowly fork into variants)
* factions/orgs
* skills/titles/classes/effects (anything the continuity system owns)
* threads/quests (you have thread IDs + labels, but no alias discipline yet)
* recurring UI labels/panels (“System Notification” vs “Warning” vs whatever)

The tiny-lift version isn’t “build a huge dictionary.” It’s: **make “aliases + canonical display_name + authoritative surface rules” a shared contract for every registry-like thing** the loop already injects (character_registry, thread_registry, future location registry, etc.). Your linter already knows how to behave if you feed it the right canon surface. 

2. Character knowledge & secrets: you’ve implicitly reserved the slot, but there’s no durable structure yet
   This is the biggest “continuity ROI” hole I see after appearance. You already have a constitution-level invariant against amnesia, but that’s a policy statement, not a state structure. 
   And you’ve already introduced the concept that some updates are “knowledge-like intangible updates.” 

What’s missing is a **durable, queryable representation of who knows what** that the writer/lint/repair can all reference deterministically. Without it, you’ll keep seeing the classic failure mode: characters act on thread facts “because the model knows them,” not because the character earned them.

Big-stroke design that matches your existing architecture:

* a durable “fact/knowledge” registry with stable IDs
* per-character “known_fact_ids” (and optionally “sealed_fact_ids”)
* discovery events only happen via explicit patch blocks (same as inventory)
* lint checks “speaker references FACT_X before discovery scene” as error; ambiguous cases as warning

This plugs directly into your timeline/ontology gating too: some knowledge can be learned in flashbacks/dreams without mutating physical canon, which your scope gating already anticipates. 

3. Relationship state: you’ve got the “don’t drift” rule, but no anchor
   Same story: your constitution says “don’t change established names/relationships,”  but there’s no durable graph that defines what “relationship” currently is.

If you want tiny lift / huge payoff, keep it brutally small:

* per character-pair: 1–2 axes (trust / hostility), plus a short “stance label”
* updates only when scene card includes a relationship beat (or repair explicitly adds it)
* lint only flags hard contradictions (reverence → contempt with no catalyst), otherwise stays quiet

This buys dialogue consistency over long runs without needing “psychology simulation.”

4. Location bible + world frame: you have “location strings,” not “location identity”
   Right now locations appear as plain strings in scene context and in canonical “last_seen” records. 
   That’s enough to function, but it’s also how you get slow drift: spelling variants, renamed rooms, vibe mutations, and continuity bugs that look like “nothing changed” but actually changed the stage.

The big-stroke upgrade (in your existing pattern) is:

* `location_registry` with stable IDs + display_name + aliases (same alias contract you already built for items/devices)
* optional durable “profile” fields (layout-ish notes, vibe, recurring props, constraints)
* a “world_frame_current” (time-of-day, lighting, ambient system tone, weather if relevant)

Even if you keep profiles extremely short, this becomes a continuity anchor *and* a future art insert hook (covers, chapter plates, etc.) without having to re-infer the setting every time.

5. Event ledger beyond milestones: you’re close, but it’s not fully “ID-backed”
   You already enforce “milestone uniqueness” and you’re already treating some things as canonical “must_stay_true.” 
   You also have the rule “if an event appears in prose, it must appear in key_events,” which is exactly the right instinct. 

What’s missing is a durable, ID-based ledger for irreversible beats that aren’t cleanly milestones (discoveries, betrayals, vows, permanent injuries, “first time seen,” etc.). Without IDs, you’ll keep getting “near-duplicate” repeats that slide past lint because the phrasing differs.

If you want the smallest possible lift:

* define a durable `event_registry` where each entry is `{event_id, canonical_one_liner, irreversible_flag, occurred_at}`
* scenes can add new events only through patch blocks
* lint uses registry IDs for repetition checks rather than fuzzy prose comparisons

6. Voiceprints: you have author personas, but not character dialogue identity
   Your snapshot contains rich author persona reference material, but that’s “narrator voice,” not “character voice.” 

If you don’t add a voice anchor per character, multi-character scenes will gradually converge into one blended “house voice,” especially when pacing gets tight.

Tiny-lift version:

* per character: a 5–10 token “voiceprint” (cadence, favorite structures, taboo phrases, metaphor palette)
* writer gets it; lint only warns on obvious cross-contamination (e.g., Character A using Character B’s signature tics)

7. “Authoritative surfaces policy”: you already have it—next step is making it reusable everywhere
   You’ve already nailed the conceptual boundary and even codified it in operational semantics: authoritative blocks get canonical enforcement; narrative does not. 
   Your linter prompt also explicitly instructs classification and says “default to EPHEMERAL (warning) when unsure,” which is the exact move that prevents “lint becomes a religion.” 

So what’s “missing” here isn’t the idea—it’s consolidation: **stop re-describing the policy in each prompt and make it a single injected policy object / contract that every phase uses** (write, lint, repair, state_repair). Your system is already behaving as if that object exists (“authoritative_surfaces/state/registries”); the win is making it truly first-class so new subsystems (appearance, knowledge, relationships, locations) plug in without inventing their own enforcement logic. 

If you only pick two after appearance (still true, but now better grounded in your architecture): do Knowledge/Secrets + Generalized Lexicon.
Reason: your system already has the registry + alias scaffolding for objects (items/devices) and already has the enforcement boundary; extending those patterns to (a) facts/knowledge and (b) all named entities will kill a ton of drift and false lint failures without adding “simulation systems.”

If you want, I can rewrite the above into a single “Continuity Pillars” proposal that uses one consistent template per pillar: “durable canon file, scene slice fields, patch block name, lint rule scope, authoritative-surface behavior.” That will match how your item_registry / plot_devices work today.

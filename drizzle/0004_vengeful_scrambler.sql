CREATE TABLE `story_art_style_anchors` (
	`story_id` text PRIMARY KEY NOT NULL,
	`anchor_json` text NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`provenance_json` text DEFAULT '{}' NOT NULL,
	`updated_through_turn` integer DEFAULT 0 NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT "story_art_style_anchor_revision_check" CHECK("story_art_style_anchors"."revision" >= 1),
	CONSTRAINT "story_art_style_anchor_turn_check" CHECK("story_art_style_anchors"."updated_through_turn" >= 0)
);

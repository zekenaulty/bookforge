CREATE TABLE `entity_appearance_guides` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`kind` text NOT NULL,
	`entity_id` text NOT NULL,
	`name` text NOT NULL,
	`aliases_json` text DEFAULT '[]' NOT NULL,
	`baseline_json` text NOT NULL,
	`current_json` text NOT NULL,
	`first_seen_turn` integer DEFAULT 0 NOT NULL,
	`last_updated_turn` integer DEFAULT 0 NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `entity_appearance_story_kind_entity_unique` ON `entity_appearance_guides` (`story_id`,`kind`,`entity_id`);--> statement-breakpoint
CREATE TABLE `entity_appearance_observations` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`guide_id` text NOT NULL,
	`kind` text NOT NULL,
	`entity_id` text NOT NULL,
	`name` text NOT NULL,
	`turn_number` integer NOT NULL,
	`observation_json` text NOT NULL,
	`source_snapshot_id` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `entity_observation_story_kind_entity_turn_unique` ON `entity_appearance_observations` (`story_id`,`kind`,`entity_id`,`turn_number`);
CREATE TABLE `art_assets` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`turn_id` text,
	`turn_number` integer,
	`type` text NOT NULL,
	`category` text NOT NULL,
	`title` text NOT NULL,
	`caption` text NOT NULL,
	`prompt_summary` text DEFAULT '' NOT NULL,
	`status` text DEFAULT 'Placeholder' NOT NULL,
	`image_reference` text,
	`mime_type` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `background_jobs` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`turn_number` integer,
	`job_type` text NOT NULL,
	`status` text DEFAULT 'pending' NOT NULL,
	`attempts` integer DEFAULT 0 NOT NULL,
	`max_attempts` integer DEFAULT 3 NOT NULL,
	`run_after` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`input_json` text DEFAULT '{}' NOT NULL,
	`result_json` text DEFAULT '{}' NOT NULL,
	`last_error` text,
	`locked_at` text,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `context_snapshots` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`through_turn_number` integer NOT NULL,
	`snapshot_json` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `context_story_turn_unique` ON `context_snapshots` (`story_id`,`through_turn_number`);--> statement-breakpoint
CREATE TABLE `operation_logs` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text,
	`turn_number` integer,
	`operation` text NOT NULL,
	`category` text NOT NULL,
	`attempt` integer DEFAULT 1 NOT NULL,
	`status` text NOT NULL,
	`message` text NOT NULL,
	`context_json` text DEFAULT '{}' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `story_art_profiles` (
	`story_id` text PRIMARY KEY NOT NULL,
	`profile_json` text NOT NULL,
	`last_updated_turn` integer DEFAULT 0 NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `visual_profiles` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`kind` text NOT NULL,
	`entity_id` text NOT NULL,
	`name` text NOT NULL,
	`profile_json` text NOT NULL,
	`last_updated_turn` integer DEFAULT 0 NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `visual_story_kind_entity_unique` ON `visual_profiles` (`story_id`,`kind`,`entity_id`);
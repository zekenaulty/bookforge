CREATE TABLE `authors` (
	`id` text PRIMARY KEY NOT NULL,
	`display_name` text NOT NULL,
	`short_description` text NOT NULL,
	`profile_json` text NOT NULL,
	`archived` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `cast_members` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`name` text NOT NULL,
	`visible_json` text NOT NULL,
	`canonical_json` text NOT NULL,
	`last_updated_turn` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `checkpoints` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`through_turn_number` integer NOT NULL,
	`checkpoint_json` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `checkpoint_story_turn_unique` ON `checkpoints` (`story_id`,`through_turn_number`);--> statement-breakpoint
CREATE TABLE `generation_jobs` (
	`idempotency_key` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`turn_number` integer NOT NULL,
	`status` text NOT NULL,
	`error` text,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `narrations` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`turn_id` text NOT NULL,
	`voice_id` text NOT NULL,
	`voice_presentation` text NOT NULL,
	`playback_rate` integer DEFAULT 100 NOT NULL,
	`status` text DEFAULT 'Ready' NOT NULL,
	`audio_reference` text NOT NULL,
	`duration` integer,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `stories` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`short_description` text NOT NULL,
	`selected_author_id` text NOT NULL,
	`author_snapshot_json` text NOT NULL,
	`original_idea` text NOT NULL,
	`foundation_json` text NOT NULL,
	`status` text DEFAULT 'Active' NOT NULL,
	`latest_accepted_turn_number` integer DEFAULT 0 NOT NULL,
	`latest_checkpoint_turn_number` integer DEFAULT 0 NOT NULL,
	`default_narration_voice` text,
	`main_viewpoint_character_id` text,
	`reading_turn_number` integer DEFAULT 1 NOT NULL,
	`playback_rate` integer DEFAULT 100 NOT NULL,
	`auto_read_next` integer DEFAULT false NOT NULL,
	`auto_write_next` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE TABLE `story_states` (
	`story_id` text PRIMARY KEY NOT NULL,
	`state_json` text NOT NULL,
	`last_updated_turn` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE TABLE `turns` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`turn_number` integer NOT NULL,
	`prose` text NOT NULL,
	`word_count` integer NOT NULL,
	`direction_used` text,
	`state_delta_json` text NOT NULL,
	`narration_json` text NOT NULL,
	`generation_status` text DEFAULT 'Accepted' NOT NULL,
	`validation_status` text DEFAULT 'Passed' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `turns_story_turn_unique` ON `turns` (`story_id`,`turn_number`);
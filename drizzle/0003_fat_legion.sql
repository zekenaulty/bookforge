CREATE TABLE `mutation_guards` (
	`id` text PRIMARY KEY NOT NULL,
	`story_id` text NOT NULL,
	`asserted` integer NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	CONSTRAINT "mutation_guard_asserted_check" CHECK("mutation_guards"."asserted" = 1)
);

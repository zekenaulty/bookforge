import { ensureDatabase, getD1, now } from "./app-db";

export type OperationLogInput = {
  storyId?: string;
  turnNumber?: number;
  operation: string;
  category: string;
  attempt?: number;
  status: "retrying" | "recovered" | "failed" | "completed" | "unsupported";
  message: string;
  context?: Record<string, unknown>;
};

export async function recordOperationLog(entry: OperationLogInput) {
  try {
    await ensureDatabase();
    await getD1().prepare(`INSERT INTO operation_logs
      (id,story_id,turn_number,operation,category,attempt,status,message,context_json,created_at)
      VALUES (?,?,?,?,?,?,?,?,?,?)`).bind(
      crypto.randomUUID(), entry.storyId || null, entry.turnNumber ?? null, entry.operation,
      entry.category, entry.attempt || 1, entry.status, entry.message.slice(0, 1200),
      JSON.stringify(entry.context || {}), now(),
    ).run();
  } catch (error) {
    console.error("Operation logging failed", error instanceof Error ? error.message : error);
  }
}

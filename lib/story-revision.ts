export function regenerationTargetsCurrentTurn(
  turnIntent: unknown,
  latestTurn: { id: string; turnNumber: number },
): boolean {
  if (!turnIntent || typeof turnIntent !== "object") return false;
  const intent = turnIntent as { regenerationOfTurnId?: unknown; intendedTurnNumber?: unknown };
  return String(intent.regenerationOfTurnId || "") === latestTurn.id
    && Number(intent.intendedTurnNumber) === latestTurn.turnNumber;
}

export function storyTailMatches(
  expected: { turnNumber: number; turnId: string },
  actual: { turnNumber: unknown; turnId: unknown },
): boolean {
  return Number(actual.turnNumber) === expected.turnNumber && String(actual.turnId || "") === expected.turnId;
}

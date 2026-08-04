export type ReaderNavigationIntent = "first" | "previous" | "next" | "last";

export type ReaderNavigationDecision =
  | { kind: "move"; turnNumber: number }
  | { kind: "write"; turnNumber: number }
  | { kind: "stay"; turnNumber: number };

type TurnNumberLike = { turnNumber: number };

export function readerTurnNumbers(turns: TurnNumberLike[] | undefined) {
  return [...new Set((turns || []).map((turn) => turn.turnNumber).filter((turn) => Number.isInteger(turn) && turn > 0))]
    .sort((left, right) => left - right);
}

export function normalizeReaderTurn(turns: TurnNumberLike[] | undefined, requested: number) {
  const numbers = readerTurnNumbers(turns);
  if (!numbers.length) return 1;
  if (numbers.includes(requested)) return requested;
  const earlier = numbers.filter((turn) => turn <= requested).at(-1);
  return earlier ?? numbers[0];
}

export function resolveReaderNavigation(
  turns: TurnNumberLike[] | undefined,
  currentTurn: number,
  intent: ReaderNavigationIntent,
  canWrite: boolean,
): ReaderNavigationDecision {
  const numbers = readerTurnNumbers(turns);
  const normalized = normalizeReaderTurn(turns, currentTurn);
  if (!numbers.length) return { kind: "stay", turnNumber: normalized };
  const index = Math.max(0, numbers.indexOf(normalized));
  const last = numbers.at(-1)!;

  if (intent === "first") return normalized === numbers[0]
    ? { kind: "stay", turnNumber: normalized }
    : { kind: "move", turnNumber: numbers[0] };
  if (intent === "previous") return index > 0
    ? { kind: "move", turnNumber: numbers[index - 1] }
    : { kind: "stay", turnNumber: normalized };
  if (intent === "next" && index < numbers.length - 1) return { kind: "move", turnNumber: numbers[index + 1] };
  if (intent === "last" && normalized !== last) return { kind: "move", turnNumber: last };
  return canWrite ? { kind: "write", turnNumber: last } : { kind: "stay", turnNumber: last };
}

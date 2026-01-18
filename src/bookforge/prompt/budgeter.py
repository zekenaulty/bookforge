from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def estimate_tokens(text: str) -> int:
    chars = len(text)
    if chars <= 0:
        return 0
    return max(1, (chars + 3) // 4)


@dataclass(frozen=True)
class BudgetSection:
    name: str
    chars: int
    tokens: int
    budget_tokens: Optional[int]
    over_budget: bool


@dataclass(frozen=True)
class BudgetReport:
    step: str
    sections: List[BudgetSection]
    total_chars: int
    total_tokens: int
    total_budget: Optional[int]
    over_budget: bool


def _normalize_budget(value: Any) -> Optional[int]:
    if isinstance(value, int) and value > 0:
        return value
    return None


def evaluate_budget(step: str, segments: Dict[str, str], budgets: Dict[str, Any]) -> BudgetReport:
    step_budget = budgets.get(step, {}) if isinstance(budgets, dict) else {}
    sections: List[BudgetSection] = []
    total_chars = 0
    total_tokens = 0
    over_budget = False

    for name, value in segments.items():
        text = value or ""
        chars = len(text)
        tokens = estimate_tokens(text)
        budget_tokens = _normalize_budget(step_budget.get(name))
        section_over = budget_tokens is not None and tokens > budget_tokens
        sections.append(
            BudgetSection(
                name=name,
                chars=chars,
                tokens=tokens,
                budget_tokens=budget_tokens,
                over_budget=section_over,
            )
        )
        total_chars += chars
        total_tokens += tokens
        if section_over:
            over_budget = True

    total_budget = _normalize_budget(step_budget.get("total"))
    if total_budget is not None and total_tokens > total_budget:
        over_budget = True

    return BudgetReport(
        step=step,
        sections=sections,
        total_chars=total_chars,
        total_tokens=total_tokens,
        total_budget=total_budget,
        over_budget=over_budget,
    )

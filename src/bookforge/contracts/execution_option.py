from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_BRANCH_POLICIES = {"main_only", "derived_only", "any"}


def _clean_required(value: Any, field_name: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


@dataclass(frozen=True, slots=True)
class ExecutionOption:
    action: str
    summary: str
    branch_policy: str
    mutates_canonical_state: bool
    requires_expected_node: bool
    allowed: bool
    selector_requirements: List[str] = field(default_factory=list)
    workflow_family: Optional[str] = None
    refusal_reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    schema_version: str = "execution_option_v1"

    def __post_init__(self) -> None:
        action = _clean_required(self.action, "action")
        summary = _clean_required(self.summary, "summary")
        branch_policy = _clean_required(self.branch_policy, "branch_policy")
        if branch_policy not in _BRANCH_POLICIES:
            raise ValueError(f"Unknown branch_policy: {branch_policy}")
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "branch_policy", branch_policy)
        object.__setattr__(self, "workflow_family", _clean_optional(self.workflow_family))
        object.__setattr__(self, "refusal_reason", _clean_optional(self.refusal_reason))
        object.__setattr__(
            self,
            "selector_requirements",
            [str(item).strip() for item in self.selector_requirements if str(item).strip()],
        )
        object.__setattr__(self, "details", dict(self.details) if isinstance(self.details, dict) else {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action": self.action,
            "summary": self.summary,
            "branch_policy": self.branch_policy,
            "workflow_family": self.workflow_family,
            "mutates_canonical_state": self.mutates_canonical_state,
            "requires_expected_node": self.requires_expected_node,
            "allowed": self.allowed,
            "selector_requirements": list(self.selector_requirements),
            "refusal_reason": self.refusal_reason,
            "details": dict(self.details),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExecutionOption":
        if not isinstance(payload, dict):
            raise ValueError("ExecutionOption payload must be a dictionary.")
        return cls(
            action=payload.get("action"),
            summary=payload.get("summary"),
            branch_policy=payload.get("branch_policy"),
            workflow_family=payload.get("workflow_family"),
            mutates_canonical_state=bool(payload.get("mutates_canonical_state")),
            requires_expected_node=bool(payload.get("requires_expected_node")),
            allowed=bool(payload.get("allowed")),
            selector_requirements=list(payload.get("selector_requirements") or []),
            refusal_reason=payload.get("refusal_reason"),
            details=payload.get("details") or {},
            schema_version=str(payload.get("schema_version") or "execution_option_v1"),
        )

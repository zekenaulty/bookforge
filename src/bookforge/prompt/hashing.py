from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class PromptHashes:
    stable_prefix: str
    dynamic_payload: str
    assembled_prompt: str


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_prompt_parts(stable_prefix: str, dynamic_payload: str, assembled_prompt: str) -> PromptHashes:
    return PromptHashes(
        stable_prefix=hash_text(stable_prefix),
        dynamic_payload=hash_text(dynamic_payload),
        assembled_prompt=hash_text(assembled_prompt),
    )

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


DEFAULT_SYSTEM_TEMPLATE = """You are the BookForge skill specialist for {{display_name}}.
Skill id: {{skill_id}}
Kind: {{kind}}
Category: {{category}}
Graph node: {{graph_node}}
Phase id: {{phase_id}}
Logical phase: {{logical_phase}}

Primary contract:
{{prompt_contract}}

Treat passed params as the authoritative working context.
Use source refs only for alignment and traceability.
Return {{output_hint}}."""


DEFAULT_USER_TEMPLATE = """Request:
{{request}}

Working parameters:
{{params_json}}

Required params:
{{required_params_text}}

Optional params:
{{optional_params_text}}

Source references:
{{source_refs_text}}

Help references:
{{help_refs_text}}

Routes:
{{routes_text}}"""


TOKEN_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    display_name: str
    llm_description: str
    kind: str
    category: str
    graph_node: str
    phase_id: str
    logical_phase: str
    prompt_contract: str
    output_hint: str
    required_params: tuple[str, ...] = ()
    optional_params: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    help_refs: tuple[str, ...] = ()
    routes: tuple[str, ...] = ()
    example_params: Dict[str, Any] = field(default_factory=dict)
    default_model: str = "gemini-2.5-flash"
    default_temperature: float = 0.2
    response_mime_type: str = "text/plain"
    response_json_schema: Optional[Dict[str, Any]] = None
    system_template: str = DEFAULT_SYSTEM_TEMPLATE
    user_template: str = DEFAULT_USER_TEMPLATE

    def metadata_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "display_name": self.display_name,
            "llm_description": self.llm_description,
            "kind": self.kind,
            "category": self.category,
            "graph_node": self.graph_node,
            "phase_id": self.phase_id,
            "logical_phase": self.logical_phase,
            "prompt_contract": self.prompt_contract,
            "output_hint": self.output_hint,
            "required_params": list(self.required_params),
            "optional_params": list(self.optional_params),
            "source_refs": list(self.source_refs),
            "help_refs": list(self.help_refs),
            "routes": list(self.routes),
            "example_params": self.example_params,
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "response_mime_type": self.response_mime_type,
            "response_json_schema": self.response_json_schema,
        }


def build_skill_definition(metadata: Mapping[str, Any]) -> SkillDefinition:
    return SkillDefinition(
        skill_id=str(metadata["skill_id"]),
        display_name=str(metadata["display_name"]),
        llm_description=str(metadata["llm_description"]),
        kind=str(metadata["kind"]),
        category=str(metadata["category"]),
        graph_node=str(metadata["graph_node"]),
        phase_id=str(metadata["phase_id"]),
        logical_phase=str(metadata["logical_phase"]),
        prompt_contract=str(metadata["prompt_contract"]),
        output_hint=str(metadata["output_hint"]),
        required_params=tuple(str(value) for value in metadata.get("required_params", [])),
        optional_params=tuple(str(value) for value in metadata.get("optional_params", [])),
        source_refs=tuple(str(value) for value in metadata.get("source_refs", [])),
        help_refs=tuple(str(value) for value in metadata.get("help_refs", [])),
        routes=tuple(str(value) for value in metadata.get("routes", [])),
        example_params=dict(metadata.get("example_params", {})),
        default_model=str(metadata.get("default_model", "gemini-2.5-flash")),
        default_temperature=float(metadata.get("default_temperature", 0.2)),
        response_mime_type=str(metadata.get("response_mime_type", "text/plain")),
        response_json_schema=dict(metadata["response_json_schema"]) if isinstance(metadata.get("response_json_schema"), dict) else None,
        system_template=str(metadata.get("system_template", DEFAULT_SYSTEM_TEMPLATE)),
        user_template=str(metadata.get("user_template", DEFAULT_USER_TEMPLATE)),
    )


def _resolve_token(data: Mapping[str, Any], token: str) -> Any:
    current: Any = data
    for part in token.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
            continue
        return ""
    return current


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def render_template(template: str, params: Mapping[str, Any]) -> str:
    return TOKEN_PATTERN.sub(lambda match: _stringify(_resolve_token(params, match.group(1))), template)


def _load_params_file(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Parameter file must contain a JSON object.")
    return payload


def _parse_override(raw: str) -> tuple[str, Any]:
    if "=" not in raw:
        raise ValueError(f"Override must look like key=value: {raw}")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Override key cannot be empty: {raw}")
    value = value.strip()
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    return key, parsed


def _merge_params(file_params: Dict[str, Any], overrides: Sequence[str]) -> Dict[str, Any]:
    payload = dict(file_params)
    for raw in overrides:
        key, value = _parse_override(raw)
        payload[key] = value
    return payload


def _validate_required_params(skill: SkillDefinition, params: Mapping[str, Any]) -> None:
    missing = [name for name in skill.required_params if name not in params]
    if missing:
        raise ValueError(f"Missing required params for {skill.skill_id}: {', '.join(missing)}")


def build_prompt_bundle(skill: SkillDefinition, params: Mapping[str, Any]) -> Dict[str, Any]:
    _validate_required_params(skill, params)

    working = dict(params)
    if "request" not in working:
        working["request"] = f"Execute {skill.display_name}."

    context = {
        **skill.metadata_dict(),
        **working,
        "params_json": json.dumps(working, ensure_ascii=False, indent=2),
        "required_params_text": "\n".join(f"- {value}" for value in skill.required_params) or "- none",
        "optional_params_text": "\n".join(f"- {value}" for value in skill.optional_params) or "- none",
        "source_refs_text": "\n".join(f"- {value}" for value in skill.source_refs) or "- none",
        "help_refs_text": "\n".join(f"- {value}" for value in skill.help_refs) or "- none",
        "routes_text": "\n".join(f"- {value}" for value in skill.routes) or "- none",
    }

    system_prompt = render_template(skill.system_template, context).strip()
    user_prompt = render_template(skill.user_template, context).strip()

    return {
        "skill": skill.metadata_dict(),
        "params": working,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def execute_skill(
    skill: SkillDefinition,
    params: Mapping[str, Any],
    *,
    dry_run: bool = False,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: int = 8192,
) -> Dict[str, Any]:
    bundle = build_prompt_bundle(skill, params)
    if dry_run:
        return bundle

    resolved_api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not resolved_api_key:
        raise RuntimeError("Set GEMINI_API_KEY or GOOGLE_API_KEY before executing a Gemini skill.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Install the skills runtime dependency with `pip install .[skills]` or `pip install google-genai`."
        ) from exc

    config_kwargs: Dict[str, Any] = {
        "system_instruction": bundle["system_prompt"],
        "temperature": skill.default_temperature if temperature is None else temperature,
        "max_output_tokens": max_output_tokens,
    }
    if skill.response_mime_type:
        config_kwargs["response_mime_type"] = skill.response_mime_type
    if skill.response_json_schema:
        config_kwargs["response_json_schema"] = skill.response_json_schema

    client = genai.Client(api_key=resolved_api_key)
    response = client.models.generate_content(
        model=model or skill.default_model,
        contents=bundle["user_prompt"],
        config=types.GenerateContentConfig(**config_kwargs),
    )

    return {
        **bundle,
        "provider": "gemini",
        "model": model or skill.default_model,
        "response_text": getattr(response, "text", "") or "",
    }


def skill_main(skill: SkillDefinition) -> int:
    parser = argparse.ArgumentParser(prog=skill.skill_id)
    parser.add_argument("--params-file", help="Path to a JSON params file.")
    parser.add_argument("--set", action="append", default=[], help="Inline override in key=value form. JSON values are allowed.")
    parser.add_argument("--model", help="Override Gemini model id.")
    parser.add_argument("--temperature", type=float, help="Override generation temperature.")
    parser.add_argument("--max-output-tokens", type=int, default=8192, help="Override max output tokens.")
    parser.add_argument("--dry-run", action="store_true", help="Render prompts without calling Gemini.")
    parser.add_argument("--dump-definition", action="store_true", help="Print the skill metadata as JSON.")
    parser.add_argument("--dump-example", action="store_true", help="Print example params as JSON.")
    args = parser.parse_args()

    if args.dump_definition:
        print(json.dumps(skill.metadata_dict(), ensure_ascii=True, indent=2))
        return 0

    if args.dump_example:
        print(json.dumps(skill.example_params, ensure_ascii=True, indent=2))
        return 0

    params = _merge_params(_load_params_file(args.params_file), args.set)
    result = execute_skill(
        skill,
        params,
        dry_run=args.dry_run,
        model=args.model,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
    )
    if args.dry_run:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(result["response_text"])
    return 0

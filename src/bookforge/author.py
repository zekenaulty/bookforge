from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import os
import re

from bookforge.config.env import load_config
from bookforge.llm.factory import get_llm_client, resolve_model
from bookforge.llm.types import Message, LLMResponse
from bookforge.llm.logging import log_llm_error, log_llm_response, should_log_llm
from bookforge.llm.errors import LLMRequestError
from bookforge.prompt.renderer import render_template_file
from bookforge.util.paths import repo_root

AUTHOR_TEMPLATE = repo_root(Path(__file__).resolve()) / 'resources' / 'prompt_templates' / 'author_generate.md'

@dataclass(frozen=True)
class AuthorArtifacts:
    author_json: Dict[str, Any]
    author_style_md: str
    system_fragment_md: str

def slugify(name: str) -> str:
    value = (name or '').strip().lower()
    value = re.sub(r'[^a-z0-9\s-]+', '', value)
    value = re.sub(r'\s+', '-', value)
    value = re.sub(r'-{2,}', '-', value)
    value = value.strip('-')
    return value or 'author'

def _clean_json_payload(payload: str) -> str:
    cleaned = payload.strip()
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u201c", '"').replace("\u201d", '"')
    cleaned = cleaned.replace("\u2018", "'").replace("\u2019", "'")
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
    return cleaned


def _extract_json(text: str) -> Dict[str, Any]:
    match = re.search(r"```json\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        payload = match.group(1)
    else:
        match = re.search(r"(\{[\s\S]*\})", text)
        if not match:
            raise ValueError('No JSON object found in response.')
        payload = match.group(1)
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        cleaned = _clean_json_payload(payload)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                data = ast.literal_eval(cleaned)
            except (ValueError, SyntaxError) as exc:
                raise ValueError('Invalid JSON in response.') from exc
    if not isinstance(data, dict):
        raise ValueError('Author response JSON must be an object.')
    return data

def _load_index(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    return data if isinstance(data, dict) else {}

def _next_version(index: Dict[str, Any]) -> str:
    versions = index.get('versions', []) if isinstance(index.get('versions', []), list) else []
    highest = 0
    for entry in versions:
        if not isinstance(entry, dict):
            continue
        version = str(entry.get('version', ''))
        match = re.match(r'v(\d+)$', version)
        if match:
            highest = max(highest, int(match.group(1)))
    return f'v{highest + 1}'

def _build_prompt(influences: Optional[str], prompt_text: Optional[str], name: Optional[str], notes: Optional[str]) -> str:
    if not AUTHOR_TEMPLATE.exists():
        raise FileNotFoundError(f'Author template not found: {AUTHOR_TEMPLATE}')
    values = {
        'influences': influences or '',
        'prompt_text': prompt_text or '',
        'persona_name': name or '',
        'notes': notes or '',
    }
    return render_template_file(AUTHOR_TEMPLATE, values)



def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    raw = raw.strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _author_max_tokens() -> int:
    return _int_env("BOOKFORGE_AUTHOR_MAX_TOKENS", 6096)


def _response_truncated(response: LLMResponse) -> bool:
    raw = response.raw
    if not isinstance(raw, dict):
        return False
    candidates = raw.get("candidates", [])
    if not candidates:
        return False
    finish = candidates[0].get("finishReason")
    return str(finish).upper() == "MAX_TOKENS"


def generate_author(
    workspace: Path,
    influences: Optional[str],
    prompt_file: Optional[Path],
    name: Optional[str],
    notes: Optional[str],
) -> Path:
    if not influences and not prompt_file:
        raise ValueError('Provide --influences or --prompt-file.')

    prompt_text = None
    if prompt_file:
        prompt_text = prompt_file.read_text(encoding='utf-8')

    config = load_config()
    client = get_llm_client(config, phase="planner")
    model = resolve_model('planner', config)

    prompt = _build_prompt(influences, prompt_text, name, notes)
    messages: List[Message] = [
        {'role': 'system', 'content': 'You create original author personas for BookForge.'},
        {'role': 'user', 'content': prompt},
    ]

    max_tokens = _author_max_tokens()
    key_slot = getattr(client, "key_slot", None)
    try:
        response = client.chat(messages, model=model, temperature=0.7, max_tokens=max_tokens)
    except LLMRequestError as exc:
        if should_log_llm():
            extra = {"key_slot": key_slot} if key_slot else None
            log_llm_error(workspace, "author_generate_error", exc, messages=messages, extra=extra)
        raise

    log_path: Optional[Path] = None
    log_extra = {"key_slot": key_slot} if key_slot else None
    if should_log_llm():
        log_path = log_llm_response(workspace, "author_generate", response, messages=messages, extra=log_extra)
    try:
        data = _extract_json(response.text)
    except ValueError as exc:
        if not log_path:
            log_path = log_llm_response(workspace, "author_generate", response, messages=messages, extra=log_extra)
        extra_msg = ""
        if _response_truncated(response):
            extra_msg = f" Model output hit MAX_TOKENS ({max_tokens}); increase BOOKFORGE_AUTHOR_MAX_TOKENS or reduce output size."
        raise ValueError(f"{exc}{extra_msg} (raw response logged to {log_path})") from exc

    author = data.get('author') if isinstance(data.get('author'), dict) else {}
    author_style_md = str(data.get('author_style_md') or '')
    system_fragment_md = str(data.get('system_fragment_md') or '')

    if not author:
        raise ValueError('Author JSON missing author object.')
    if not author.get('persona_name'):
        if name:
            author['persona_name'] = name
        else:
            raise ValueError('Author persona_name missing.')

    banned_phrases = data.get('banned_phrases')
    if isinstance(banned_phrases, list) and banned_phrases:
        author['banned_phrases'] = [str(item) for item in banned_phrases]

    slug = slugify(author['persona_name'])
    author_root = workspace / 'authors' / slug
    index_path = author_root / 'index.json'
    index = _load_index(index_path)
    version = _next_version(index)
    version_dir = author_root / version
    version_dir.mkdir(parents=True, exist_ok=True)

    (version_dir / 'author.json').write_text(json.dumps(author, ensure_ascii=True, indent=2), encoding='utf-8')
    (version_dir / 'author_style.md').write_text(author_style_md, encoding='utf-8')
    (version_dir / 'system_fragment.md').write_text(system_fragment_md, encoding='utf-8')

    versions = index.get('versions', []) if isinstance(index.get('versions', []), list) else []
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    versions.append({
        'version': version,
        'created_at': created_at,
        'notes': notes or '',
        'files': {
            'author_json': f'{version}/author.json',
            'author_style_md': f'{version}/author_style.md',
            'system_fragment_md': f'{version}/system_fragment.md',
        },
    })

    index = {
        'author_slug': slug,
        'display_name': author.get('persona_name', ''),
        'default_version': version,
        'versions': versions,
    }
    author_root.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, ensure_ascii=True, indent=2), encoding='utf-8')

    return version_dir

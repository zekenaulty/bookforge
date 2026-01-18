#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
iterate-book-v2.py — A Unified Weaver with a Living World Bible

Nyx's Deeper Magic (Refined):
This version corrects a logical gap in the workflow. The system now
explicitly transforms the high-level chapter 'blueprint' (the initial plan)
into a detailed, multi-level 'scroll' (the final spec with sections and
sub-sections) before attempting to write prose.

Key Enhancements from Previous Version:
- **Blueprint-to-Scroll Transformation:** A new function, `refine_chapter_plan_for_writing`,
  is introduced. It takes the Architect's high-level plan for a chapter
  and instructs the Planner model to break it down into the granular
  section/sub-section structure required for prose generation.
- **Corrected Workflow:** The main loop now follows this sequence:
  1. Plan high-level chapter blueprint.
  2. **Refine blueprint into a detailed, writable structure.**
  3. Write prose based on the refined structure.
  4. Reflect and update the world grimoires.
  This ensures the writing loop never encounters a missing 'subsections' key.
"""

import argparse
import json
import os
import random
import re
import sys
import time
import textwrap
import hashlib
from datetime import datetime, timezone
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Assuming llm_client.py exists and contains the client classes
from llm_client import GeminiClient, OpenAIClient, OllamaClient

# --- Configuration & Constants ---

def load_config(path: str = "config.json") -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Configuration file not found at: {path}")
    return json.loads(p.read_text(encoding="utf-8"))

_CONFIG = None
def get_config():
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = load_config()
    return _CONFIG

def get_param(key, default=None):
    return get_config().get(key, default)

# --- LLM Client Management ---

def make_client(model_key: str) -> Any:
    """Creates an LLM client based on a specific model key from config.json."""
    cfg = get_config()
    provider = (cfg.get("PROVIDER") or "openai").lower()
    model_name = cfg.get(model_key)
    if not model_name:
        raise ValueError(f"Model key '{model_key}' not found in config.json")

    api_key = cfg.get("API_KEY") or os.getenv("API_KEY")
    api_url = cfg.get("API_URL")

    if provider == "openai":
        if not api_key:
            raise RuntimeError("OpenAI API key not found.")
        return OpenAIClient(model_name, api_url or "https://api.openai.com/v1/chat/completions", api_key)
    if provider == "gemini":
        if not api_key:
            raise RuntimeError("Gemini API key not found.")
        return GeminiClient(model_name, api_url or "https://generativelanguage.googleapis.com/v1beta", api_key)
    if provider == "ollama":
        return OllamaClient(model_name, api_url or "http://localhost:11434/api/chat")

    raise RuntimeError(f"Unknown provider: {provider}")

def llm_call(client: Any, system_messages: List[str], user_msg: str, is_json: bool = False) -> str:
    """Helper for a single LLM call, handling JSON extraction if needed."""
    client.reset_history()
    for sm in system_messages:
        client.add_message("system", sm)
    client.add_message("user", user_msg)
    raw = client.call()

    if is_json:
        # A more robust JSON extractor
        match = re.search(r'```json\s*([\s\S]*?)\s*```|({[\s\S]*}|\[[\s\S]*\])', raw)
        if match:
            json_str = match.group(1) or match.group(2)
            try:
                json.loads(json_str)
                return json_str.strip()
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}\nRaw output was:\n{raw}", file=sys.stderr)
                raise
        raise ValueError("LLM did not return a discernible JSON object or array.")
    return raw.strip()

# --- Utility Functions ---

def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def save_json(path: Path, data: Any):
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))

def load_json_if_exists(path: Path) -> Optional[Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

def simple_attentional_gate(text: str, salient_terms: Set[str], min_hits: int = 1) -> bool:
    if not text or not salient_terms:
        return True
    tokens = set(re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower()))
    normalized_terms = {term.lower() for term in salient_terms}
    hits = len(tokens & normalized_terms)
    return hits >= min_hits


def collect_salient_terms(out_dir: Path) -> Set[str]:
    terms: Set[str] = set()
    roster_path = out_dir / "_context" / "characters.roster.json"
    roster = load_json_if_exists(roster_path) or []
    if isinstance(roster, list):
        for entry in roster:
            if not isinstance(entry, dict):
                continue
            name = (entry.get("name") or "").strip()
            if name:
                terms.add(name)
                terms.update(part for part in name.split() if part)
    goals_path = out_dir / "_context" / "book_goals.md"
    if goals_path.exists():
        goals_text = load_text(goals_path)
        for word in re.findall(r"[A-Za-z][A-Za-z\-']+", goals_text.lower()):
            if len(word) > 3:
                terms.add(word)
    return terms


def phase_is_locked(out_dir: Path, phase: str) -> bool:
    lock_path = out_dir / "_context" / "phase_lock.json"
    data = load_json_if_exists(lock_path) or {}
    if not isinstance(data, dict):
        return False
    return bool(data.get(phase) is True)


def set_phase_lock(out_dir: Path, phase: str, locked: bool = True) -> None:
    lock_path = out_dir / "_context" / "phase_lock.json"
    data = load_json_if_exists(lock_path) or {}
    if not isinstance(data, dict):
        data = {}
    data[phase] = bool(locked)
    save_json(lock_path, data)



def build_indexed_slug(chapter_idx: int, raw_slug: Optional[str], fallback_title: Optional[str]) -> str:
    base = sanitize_slug(raw_slug or fallback_title or f"chapter-{chapter_idx}")
    indexed = f"{chapter_idx:02d}-{base}" if base else f"{chapter_idx:02d}-chapter-{chapter_idx}"
    return sanitize_slug(indexed)

def sanitize_slug(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^\w\- ]+", "", name)
    return re.sub(r"\s+", "-", name).strip("-") or "untitled"


# --- Resume & Checkpoint Management ---

def current_timestamp() -> str:
    """Return an ISO8601 UTC timestamp suitable for checkpoint bookkeeping."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CheckpointManager:
    """Persists coarse-grained progress markers so phases can resume safely."""
    def __init__(self, book_root: Path):
        self.book_root = book_root
        self.path = self.book_root / '_context' / 'iterate_state.json'
        self.state: Dict[str, Any] = {'version': 2, 'phases': {}}
        if self.path.exists():
            try:
                loaded = json.loads(self.path.read_text(encoding='utf-8'))
                if isinstance(loaded, dict):
                    self.state.update({k: v for k, v in loaded.items() if k not in {'phases'}})
                    phases = loaded.get('phases')
                    if isinstance(phases, dict):
                        self.state['phases'] = phases
            except Exception:
                # Corrupted checkpoint files should not break execution; start fresh instead.
                self.state = {'version': 2, 'phases': {}}
        if 'phases' not in self.state or not isinstance(self.state['phases'], dict):
            self.state['phases'] = {}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding='utf-8')

    def _ensure_phase(self, phase: str) -> Dict[str, Any]:
        phases = self.state.setdefault('phases', {})
        if phase not in phases or not isinstance(phases[phase], dict):
            phases[phase] = {'status': 'pending', 'progress': {}}
        return phases[phase]

    def mark_phase_start(self, phase: str, **progress) -> None:
        entry = self._ensure_phase(phase)
        entry['status'] = 'in_progress'
        entry['updated_at'] = current_timestamp()
        entry.setdefault('progress', {}).update(progress)
        self.save()

    def update_phase(self, phase: str, **progress) -> None:
        entry = self._ensure_phase(phase)
        entry.setdefault('progress', {}).update(progress)
        entry['updated_at'] = current_timestamp()
        self.save()

    def mark_phase_complete(self, phase: str, **progress) -> None:
        entry = self._ensure_phase(phase)
        entry['status'] = 'complete'
        entry['updated_at'] = current_timestamp()
        entry.setdefault('progress', {}).update(progress)
        self.save()

    def is_complete(self, phase: str) -> bool:
        return self.state.get('phases', {}).get(phase, {}).get('status') == 'complete'

    def get(self, phase: str) -> Dict[str, Any]:
        entry = self.state.get('phases', {}).get(phase)
        return dict(entry) if isinstance(entry, dict) else {}


def migrate_legacy_story_layout(output_root: Path) -> None:
    """Move legacy blueprint-first story.json files into the new checkpoint layout."""
    story_path = output_root / 'story.json'
    blueprint_path = output_root / '_context' / 'blueprints.json'
    story = load_json_if_exists(story_path)
    if not story or blueprint_path.exists():
        return
    chapters = story.get('chapters', [])
    if chapters and all(isinstance(chapter, dict) and 'chapter' in chapter for chapter in chapters):
        save_json(blueprint_path, story)
        final_stub = {
            'book_title': story.get('book_title', 'Untitled'),
            'meta': story.get('meta', {}),
            'chapters': []
        }
        save_json(story_path, final_stub)


def load_blueprint_spec(output_root: Path, default_title: str, default_meta: Dict[str, Any]) -> Tuple[Path, Dict[str, Any]]:
    blueprint_path = output_root / '_context' / 'blueprints.json'
    data = load_json_if_exists(blueprint_path)
    if data is None:
        data = {'book_title': default_title or 'Untitled', 'meta': default_meta or {}, 'chapters': []}
    else:
        data.setdefault('book_title', default_title or data.get('book_title', 'Untitled'))
        data.setdefault('meta', default_meta or data.get('meta', {}))
        data.setdefault('chapters', data.get('chapters', []))
    return blueprint_path, data


def load_final_story_spec(story_path: Path, default_title: str, default_meta: Dict[str, Any]) -> Dict[str, Any]:
    data = load_json_if_exists(story_path)
    if data is None:
        data = {'book_title': default_title or 'Untitled', 'meta': default_meta or {}, 'chapters': []}
    else:
        data.setdefault('book_title', data.get('book_title', default_title or 'Untitled'))
        data.setdefault('meta', data.get('meta', default_meta or {}))
        data.setdefault('chapters', data.get('chapters', []))
    cleaned_chapters: List[Dict[str, Any]] = []
    for chapter in data.get('chapters', []):
        if isinstance(chapter, dict) and 'chapter' in chapter:
            # Legacy blueprint node; keep blueprints in blueprints.json instead of story.json.
            continue
        cleaned_chapters.append(chapter)
    data['chapters'] = cleaned_chapters
    return data

class SchemaValidationError(Exception):
    """Raised when LLM output fails structural validation."""


def ensure_slug_field(node: Dict[str, Any], fallback: str) -> str:
    slug = sanitize_slug(node.get("slug") or node.get("title") or fallback)
    node["slug"] = slug
    return slug


def validate_blueprint_structure(blueprint: Dict[str, Any], chapter_index: int) -> Dict[str, Any]:
    if not isinstance(blueprint, dict):
        raise SchemaValidationError("Blueprint must be a JSON object.")
    chapter_obj = blueprint.get("chapter")
    if not isinstance(chapter_obj, dict):
        raise SchemaValidationError("Blueprint missing 'chapter' object.")

    title = chapter_obj.get("title")
    summary = chapter_obj.get("summary")
    structure = chapter_obj.get("structure")

    if not isinstance(title, str) or not title.strip():
        raise SchemaValidationError("Chapter title is required for blueprint planning.")
    if not isinstance(summary, str) or not summary.strip():
        raise SchemaValidationError("Chapter summary is required for blueprint planning.")
    if not isinstance(structure, list) or not structure:
        raise SchemaValidationError("Chapter blueprint must contain a non-empty 'structure' array.")

    clean_structure: List[Dict[str, str]] = []
    required_keys = ["summary", "goal", "obstacle", "turn", "fallout"]
    for idx, entry in enumerate(structure, start=1):
        if not isinstance(entry, dict):
            raise SchemaValidationError(f"Structure entry #{idx} must be an object with required keys.")
        section_title = entry.get("section")
        if not isinstance(section_title, str) or not section_title.strip():
            raise SchemaValidationError(f"Structure entry #{idx} missing 'section' title.")
        clean_entry = {"section": section_title.strip()}
        for key in required_keys:
            value = entry.get(key) or entry.get(key.capitalize())
            if not isinstance(value, str) or not value.strip():
                raise SchemaValidationError(f"Structure entry '{section_title}' missing '{key}'.")
            clean_entry[key] = value.strip()
        # Maintain backward compatibility with older 'content' field if it exists
        content = entry.get("content")
        if isinstance(content, str) and content.strip():
            clean_entry["summary"] = clean_entry["summary"] or content.strip()
        clean_structure.append(clean_entry)

    chapter_obj["title"] = title.strip()
    chapter_obj["summary"] = summary.strip()
    chapter_obj["structure"] = clean_structure
    blueprint["chapter"] = chapter_obj
    return blueprint


def validate_refined_chapter_structure(chapter: Dict[str, Any], chapter_index: int) -> Dict[str, Any]:
    if not isinstance(chapter, dict):
        raise SchemaValidationError("Refined chapter must be a JSON object.")

    title = chapter.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SchemaValidationError("Refined chapter requires a non-empty 'title'.")
    chapter["title"] = title.strip()

    metadata = chapter.get("metadata")
    if metadata is None:
        metadata = {}
        chapter["metadata"] = metadata
    if not isinstance(metadata, dict):
        raise SchemaValidationError("Refined chapter 'metadata' must be an object.")

    synopsis = metadata.get("synopsis") or chapter.get("description")
    if not isinstance(synopsis, str) or not synopsis.strip():
        raise SchemaValidationError("Refined chapter must include 'metadata.synopsis'.")
    metadata["synopsis"] = synopsis.strip()

    description = chapter.get("description")
    if not isinstance(description, str):
        chapter["description"] = synopsis.strip()
    else:
        chapter["description"] = description.strip()

    sections = chapter.get("subsections")
    if not isinstance(sections, list) or not sections:
        raise SchemaValidationError("Refined chapter must include at least one section in 'subsections'.")

    clean_sections: List[Dict[str, Any]] = []
    required_meta_keys = ["scene_goal", "obstacle", "turn", "fallout", "carry_forward"]
    for sec_idx, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            raise SchemaValidationError(f"Section #{sec_idx} must be an object.")
        sec_title = section.get("title")
        sec_desc = section.get("description", "")
        sub_sections = section.get("subsections")

        if not isinstance(sec_title, str) or not sec_title.strip():
            raise SchemaValidationError(f"Section #{sec_idx} missing 'title'.")
        if not isinstance(sec_desc, str):
            sec_desc = ""
        if not isinstance(sub_sections, list) or not sub_sections:
            raise SchemaValidationError(f"Section '{sec_title}' must contain at least one nested subsection.")

        section_meta = section.get("metadata")
        if not isinstance(section_meta, dict):
            raise SchemaValidationError(f"Section '{sec_title}' must include metadata with scene dynamics.")
        for key in required_meta_keys:
            value = section_meta.get(key)
            if not isinstance(value, str) or not value.strip():
                raise SchemaValidationError(f"Section '{sec_title}' missing metadata field '{key}'.")
            section_meta[key] = value.strip()
        section["metadata"] = section_meta

        ensure_slug_field(section, f"chapter-{chapter_index}-section-{sec_idx}")
        section["title"] = sec_title.strip()
        section["description"] = sec_desc.strip()

        clean_subsections: List[Dict[str, Any]] = []
        for sub_idx, sub in enumerate(sub_sections, start=1):
            if not isinstance(sub, dict):
                raise SchemaValidationError(f"Subsection #{sec_idx}.{sub_idx} must be an object.")
            sub_title = sub.get("title")
            sub_desc = sub.get("description")
            sub_meta = sub.get("metadata")
            if not isinstance(sub_title, str) or not sub_title.strip():
                raise SchemaValidationError(f"Subsection #{sec_idx}.{sub_idx} missing 'title'.")
            if not isinstance(sub_desc, str) or not sub_desc.strip():
                raise SchemaValidationError(f"Subsection '{sub_title}' requires a descriptive 'description'.")
            if not isinstance(sub_meta, dict):
                raise SchemaValidationError(f"Subsection '{sub_title}' must include metadata with scene dynamics.")
            for key in required_meta_keys:
                value = sub_meta.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise SchemaValidationError(f"Subsection '{sub_title}' missing metadata field '{key}'.")
                sub_meta[key] = value.strip()
            sub["metadata"] = sub_meta
            ensure_slug_field(sub, f"chapter-{chapter_index}-section-{sec_idx}-sub-{sub_idx}")
            sub["title"] = sub_title.strip()
            sub["description"] = sub_desc.strip()
            clean_subsections.append(sub)

        section["subsections"] = clean_subsections
        clean_sections.append(section)

    chapter["subsections"] = clean_sections
    ensure_slug_field(chapter, f"chapter-{chapter_index}")
    return chapter




# --- World Context Utilities ---


def load_json_list(path: Path) -> List[Any]:
    data = load_json_if_exists(path)
    return data if isinstance(data, list) else []


def render_roster_excerpt(path: Path, max_entries: int = 20) -> str:
    roster = load_json_list(path)
    if not roster:
        return "[]"
    if len(roster) <= max_entries:
        return json.dumps(roster, ensure_ascii=False, indent=2)
    excerpt = roster[:max_entries]
    truncated_note = {
        "note": f"... {len(roster) - max_entries} additional entries omitted for brevity ..."
    }
    return json.dumps(excerpt + [truncated_note], ensure_ascii=False, indent=2)


def render_recent_knowledge(path: Path, limit: int = 10) -> str:
    knowledge = load_json_list(path)
    if not knowledge:
        return "[]"
    recent = knowledge[-limit:]
    return json.dumps(recent, ensure_ascii=False, indent=2)


def append_json_entries(path: Path, new_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not new_entries:
        return load_json_list(path)
    combined = load_json_list(path) + new_entries
    save_json(path, combined)
    return combined


def find_character_id(name: str, roster: List[Dict[str, Any]]) -> str:
    normalized = (name or "").strip().lower()
    for entry in roster:
        entry_name = entry.get("name", "").strip().lower()
        if entry_name == normalized:
            entry_id = entry.get("id") or sanitize_slug(entry.get("name") or normalized or "character")
            entry["id"] = entry_id
            return entry_id
    return sanitize_slug(name or "character")


def match_section_slug(section_title: Optional[str], chapter_meta: Dict[str, Any]) -> Optional[str]:
    if not section_title:
        return None
    normalized = section_title.strip().lower()
    for section in chapter_meta.get("sections", []):
        if section.get("title", "").strip().lower() == normalized:
            return section.get("slug")
        for sub in section.get("subsections", []):
            if sub.get("title", "").strip().lower() == normalized:
                return sub.get("slug")
    return None


def build_character_knowledge_entry(character_id: str, summary: str, chapter_slug: Optional[str], section_slug: Optional[str], source: str, sequence: int) -> Dict[str, Any]:
    return {
        "id": f"{character_id}-{source}-{sequence}",
        "character": character_id,
        "summary": summary.strip(),
        "chapter": chapter_slug,
        "section": section_slug,
        "timestamp": current_timestamp(),
        "source": source,
    }


def append_timeline_entries(path: Path, entries: List[Dict[str, Any]]) -> None:
    if not entries:
        return
    timeline = load_json_list(path)
    timeline.extend(entries)
    save_json(path, timeline)

def _sanitize_metrics_value(value: Optional[str]) -> str:
    return (value or "").replace(",", ";").replace("\n", " ").replace("\r", " ").strip()

class MetricsLogger:
    def __init__(self, out_dir: Path):
        self.path = out_dir / "_context" / "metrics.csv"
        if not self.path.exists():
            write_text(self.path, "timestamp,phase,chapter_slug,section_slug,sub_slug,event,details\n")

    def log(
        self,
        phase: str,
        chapter_slug: Optional[str],
        section_slug: Optional[str],
        sub_slug: Optional[str],
        event: str,
        details: str = "",
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized_event = _sanitize_metrics_value(event)
        normalized_details = _sanitize_metrics_value(details)
        line = ",".join([
            current_timestamp(),
            phase,
            (chapter_slug or ""),
            (section_slug or ""),
            (sub_slug or ""),
            normalized_event,
            normalized_details,
        ]) + "\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)

# --- Context & State Management ---
class ContextManager:
    """Manages the creation and retrieval of contextual documents and summaries."""
    def __init__(self, book_root: Path, client: Any):
        self.book_root = book_root
        self.ctx_dir = self.book_root / "_context"
        self.ctx_dir.mkdir(parents=True, exist_ok=True)
        self.client = client

    def get_or_build_author_summary(self, raw_persona: str) -> str:
        stamp_path = self.ctx_dir / "author.summary.hash"
        summary_path = self.ctx_dir / "author.summary.txt"
        current_hash = hashlib.sha1(raw_persona.encode('utf-8')).hexdigest()
        if summary_path.exists() and stamp_path.exists() and stamp_path.read_text(encoding="utf-8") == current_hash:
            return summary_path.read_text(encoding="utf-8")
        print("      - Generating new author style summary...")
        user_msg = f"Compress the following author persona into a concise, actionable style guide. Max 1024 tokens.\n\n{raw_persona}"
        summary = llm_call(self.client, [], user_msg)
        write_text(summary_path, summary)
        write_text(stamp_path, current_hash)
        return summary

    def update_chapter_memory(self, chapter_slug: str, sub_section_title: str, markdown_content: str, system_messages: list):
        memory_path = self.ctx_dir / f"{chapter_slug}.memory.json"
        print(f"      - Summarizing and saving memory for: '{sub_section_title}'...")
        user_msg = f"Summarize the key plot points, character actions, and thematic developments of the following scene in 2-3 bullet points for a 'previously on' context memory.\n\n--- SCENE ---\n{markdown_content}"
        summary = llm_call(self.client, system_messages, user_msg)
        memory = load_json_if_exists(memory_path) or []
        memory.append({"title": sub_section_title, "summary": summary})
        save_json(memory_path, memory)

    def get_recent_memories(self, chapter_slug: str, n: int = 3) -> str:
        memory_path = self.ctx_dir / f"{chapter_slug}.memory.json"
        memory = load_json_if_exists(memory_path) or []
        if not memory:
            return ""
        recent_items = memory[-max(1, n):]
        lines = []
        for item in recent_items:
            summary = (item.get('summary') or '').strip()
            if len(summary) > 280:
                summary = summary[:277] + '...'
            lines.append(f"- In '{item.get('title', 'Scene')}', {summary}")
        return "--- RECENTLY IN THIS CHAPTER ---\n" + "\n".join(lines)

    def get_full_chapter_summary(self, chapter_slug: str, system_messages: list) -> str:
        memory_path = self.ctx_dir / f"{chapter_slug}.memory.json"
        memory = load_json_if_exists(memory_path) or []
        if not memory: return "This is the first chapter."

        full_text = "\n".join([f"- **{item['title']}**: {item['summary']}" for item in memory])
        print("      - Generating full summary of previous chapter for transition planning...")
        user_msg = f"Synthesize the following scene summaries into a concise, 1-2 paragraph summary of the entire chapter's narrative arc, key events, and character developments.\n\n{full_text}"
        return llm_call(self.client, system_messages, user_msg)

# --- Core Weaver Functions ---

def build_master_system_messages(raw_author: str, style_summary: str, book_goals_text: str, plan_text: str, out_dir: Path) -> List[str]:
    """Builds the core system messages, now including the living world grimoires."""
    messages = [
        f"--- AUTHOR PERSONA ---\n{raw_author}",
        f"--- AUTHOR STYLE SUMMARY ---\n{style_summary}",
        f"--- BOOK GOALS ---\n{book_goals_text}",
        f"--- OVERALL STORY PLAN ---\n{plan_text}",
    ]

    roster_path = out_dir / "_context" / "characters.roster.json"
    knowledge_path = out_dir / "_context" / "characters.knowledge.json"
    if roster_path.exists():
        messages.append(f"--- WORLD BIBLE: CHARACTERS (ROSTER) ---\n{render_roster_excerpt(roster_path)}")
    if knowledge_path.exists():
        messages.append(f"--- WORLD KNOWLEDGE: CHARACTER FACTS ---\n{render_recent_knowledge(knowledge_path)}")

    for grimoire in ["locations", "systems"]:
        path = out_dir / "_context" / f"{grimoire}.json"
        if path.exists():
            messages.append(f"--- WORLD BIBLE: {grimoire.upper()} ---\n{render_roster_excerpt(path, max_entries=15)}")

    cache_dir = out_dir / "_context" / "plan_cache"
    if cache_dir.exists():
        cache_files = sorted(cache_dir.glob("pass_*.md"))
        if cache_files:
            for cache_file in cache_files[-2:]:
                messages.append(f"--- ITERATIVE PLANNING CACHE ({cache_file.stem.upper()}) ---\n{load_text(cache_file)}")
    return messages


def plan_initial_vision(client: Any, raw_author: str, seed_prompt: str, out_dir: Path):
    """Generates high-level goals and plan. (Runs once)."""
    print("[weaver] Checking for high-level book goals and story plan...")
    goals_path = out_dir / "_context/book_goals.md"
    plan_path = out_dir / "_context/story.plan.md"
    if not (goals_path.exists() and plan_path.exists()):
        print("[weaver] Generating high-level book goals...")
        user_goals = f"Define the soul of a new novel based on this seed. Answer in detail: 1. Goals for book? 2. Goals for characters? 3. Surface plot? 4. Deeper meaning?\n\nSeed: {seed_prompt}"
        book_goals_text = llm_call(client, [f"You are a master storyteller. Persona:\n{raw_author}"], user_goals)
        write_text(goals_path, book_goals_text)
        
        print("[weaver] Generating overall story plan...")
        user_plan = f"Create a comprehensive STORY PLAN for a novel. Include: Conceptual Vision, Plot Summary (3 acts), and Character List. Base this on the following goals and seed.\n\n--- GOALS ---\n{book_goals_text}\n\n--- SEED ---\n{seed_prompt}"
        plan_text = llm_call(client, [f"You are a master world-builder. Persona:\n{raw_author}"], user_plan)
        write_text(plan_path, plan_text)
    return load_text(goals_path), load_text(plan_path)



def migrate_legacy_world_bibles(out_dir: Path) -> None:
    """Upgrades older world bible files (e.g., characters.json) to the newer split format."""
    legacy_characters = out_dir / "_context" / "characters.json"
    roster_path = out_dir / "_context" / "characters.roster.json"
    knowledge_path = out_dir / "_context" / "characters.knowledge.json"
    if legacy_characters.exists() and not roster_path.exists():
        raw = load_json_if_exists(legacy_characters) or []
        roster: List[Dict[str, Any]] = []
        knowledge: List[Dict[str, Any]] = []
        for idx, entry in enumerate(raw, start=1):
            knowledge_notes = entry.pop("knowledge", []) if isinstance(entry, dict) else []
            name = entry.get("name") if isinstance(entry, dict) else f"Character {idx}"
            character_id = sanitize_slug(entry.get("id") or name or f"character-{idx}") if isinstance(entry, dict) else f"character-{idx}"
            if isinstance(entry, dict):
                entry["id"] = character_id
                roster.append(entry)
            for note_idx, note in enumerate(knowledge_notes, start=1):
                if isinstance(note, str) and note.strip():
                    knowledge.append(build_character_knowledge_entry(
                        character_id,
                        note,
                        chapter_slug=None,
                        section_slug=None,
                        source="seed",
                        sequence=len(knowledge) + 1,
                    ))
        if roster:
            save_json(roster_path, roster)
        elif not roster_path.exists():
            save_json(roster_path, [])
        if knowledge:
            save_json(knowledge_path, knowledge)
        elif not knowledge_path.exists():
            save_json(knowledge_path, [])
        try:
            legacy_characters.unlink()
        except OSError:
            pass

def plan_world_grimoires(client: Any, system_messages: List[str], out_dir: Path):
    """Generates the initial state of the world bible JSON files."""
    migrate_legacy_world_bibles(out_dir)

    config = {
        "characters": textwrap.dedent("""            Based on the story plan, generate the initial world bible for 'characters'.
            Return a STRICT JSON object with:
              - roster: list of characters with fields id (slug), name, description, status, and any notable traits.
              - knowledge: list of objects with fields character (name) and summary (1-2 sentences of key knowledge).
            """),
        "locations": textwrap.dedent("""            Based on the story plan, generate the initial world bible for 'locations'.
            Return a STRICT JSON array. For each entry include name, description, and current status.
            """),
        "systems": textwrap.dedent("""            Based on the story plan, generate the initial world bible for 'systems'.
            Return a STRICT JSON array describing each system's name, rules/function, and current state.
            """),
    }

    for grimoire_name, prompt_details in config.items():
        if grimoire_name == "characters":
            roster_path = out_dir / "_context" / "characters.roster.json"
            knowledge_path = out_dir / "_context" / "characters.knowledge.json"
            if roster_path.exists() and knowledge_path.exists():
                continue
            print(f"[weaver] Seeding new grimoire: {grimoire_name}...")
            prompt = "Return ONLY STRICT JSON.\n" + prompt_details.strip()
            json_obj = json.loads(llm_call(client, system_messages, prompt, is_json=True))
            roster_raw = json_obj.get("roster", []) if isinstance(json_obj, dict) else []
            knowledge_raw = json_obj.get("knowledge", []) if isinstance(json_obj, dict) else []

            roster: List[Dict[str, Any]] = []
            for idx, entry in enumerate(roster_raw, start=1):
                if not isinstance(entry, dict):
                    continue
                character_id = sanitize_slug(entry.get("id") or entry.get("name") or f"character-{idx}")
                entry["id"] = character_id
                roster.append(entry)
            save_json(roster_path, roster)

            knowledge_entries: List[Dict[str, Any]] = []
            for note in knowledge_raw:
                if not isinstance(note, dict):
                    continue
                summary = note.get("summary") or note.get("detail")
                character_name = note.get("character") or note.get("name")
                if not summary or not character_name:
                    continue
                char_id = find_character_id(character_name, roster)
                knowledge_entries.append(
                    build_character_knowledge_entry(
                        character_id=char_id,
                        summary=summary,
                        chapter_slug=None,
                        section_slug=None,
                        source="seed",
                        sequence=len(knowledge_entries) + 1,
                    )
                )
            save_json(knowledge_path, knowledge_entries)
            continue

        path = out_dir / "_context" / f"{grimoire_name}.json"
        if path.exists():
            continue
        print(f"[weaver] Seeding new grimoire: {grimoire_name}.json...")
        prompt = "Return ONLY STRICT JSON.\n" + prompt_details.strip()
        json_str = llm_call(client, system_messages, prompt, is_json=True)
        save_json(path, json.loads(json_str))

    timeline_path = out_dir / "_context" / "timeline.json"
    if not timeline_path.exists():
        save_json(timeline_path, [])




def perform_iterative_planning_passes(
    planner_client: Any,
    raw_persona: str,
    style_summary: str,
    book_goals_text: str,
    plan_text: str,
    out_dir: Path,
    checkpoint: CheckpointManager,
    passes: int = 2,
) -> None:
    cache_dir = out_dir / "_context" / "plan_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(cache_dir.glob("pass_*.md"))
    target_passes = max(0, passes)

    if existing and len(existing) >= target_passes:
        checkpoint.update_phase("planning_passes", passes=len(existing))
        return

    checkpoint.mark_phase_start("planning_passes", target=target_passes)

    for pass_index in range(len(existing) + 1, target_passes + 1):
        pass_path = cache_dir / f"pass_{pass_index}.md"
        system_messages = build_master_system_messages(
            raw_author=raw_persona,
            style_summary=style_summary,
            book_goals_text=book_goals_text,
            plan_text=plan_text,
            out_dir=out_dir,
        )
        prompt = textwrap.dedent(
            f"""            You are performing iterative planning refinement for a novel. This is pass {pass_index} of {target_passes}.


            Create a concise planning brief (<= 600 tokens) with sections:
              1. Story Arc Adjustments
              2. Character Priorities
              3. Location/Setting Notes
              4. Systems/Rules Considerations
            Focus on actionable changes for upcoming chapters; avoid rehashing earlier notes unless they change.
            """
        )
        response = llm_call(planner_client, system_messages, prompt)
        salient = collect_salient_terms(out_dir)
        if not simple_attentional_gate(response, salient, min_hits=1):
            retry_prompt = prompt + "\n\nEnsure the brief explicitly references currently salient characters/themes."
            response = llm_call(planner_client, system_messages, retry_prompt)
        write_text(pass_path, response)
        checkpoint.update_phase("planning_passes", last_pass=pass_index)

    checkpoint.mark_phase_complete("planning_passes", passes=target_passes)

def update_character_grimoire_after_chapter(
    client: Any,
    master_systems: List[str],
    chapter_content: str,
    out_dir: Path,
    chapter_meta: Dict[str, Any],
) -> None:
    roster_path = out_dir / "_context" / "characters.roster.json"
    knowledge_path = out_dir / "_context" / "characters.knowledge.json"
    timeline_path = out_dir / "_context" / "timeline.json"

    if not roster_path.exists():
        return

    roster = load_json_list(roster_path)
    knowledge = load_json_list(knowledge_path)
    existing_summaries = { (entry.get("summary") or "").strip().lower() for entry in knowledge if isinstance(entry, dict) }
    roster_excerpt = render_roster_excerpt(roster_path)
    knowledge_excerpt = render_recent_knowledge(knowledge_path, limit=8)

    prompt = textwrap.dedent(
        f"""\
        You are the keeper of the character roster. Update the roster and capture new knowledge based on the latest chapter content.

        Provide:
          - roster: the refreshed roster list with any status/trait adjustments or new characters added.
          - knowledge_updates: ONLY new knowledge objects with keys: character (name), summary (1-2 sentences), related_section (exact title from the provided outline or null).

        --- CHAPTER CONTENT ---
        {chapter_content}

        --- CURRENT ROSTER (TRUNCATED) ---
        {roster_excerpt}

        --- RECENT KNOWLEDGE (MOST RECENT FIRST) ---
        {knowledge_excerpt}

        --- SECTION OUTLINE ---
        {json.dumps(chapter_meta.get('sections', []), ensure_ascii=False, indent=2)}

        Return ONLY STRICT JSON object {{ \"roster\": [...], \"knowledge_updates\": [...] }}.
        """
    )
    response = llm_call(client, master_systems, prompt, is_json=True)
    data = json.loads(response)

    new_roster = data.get("roster") if isinstance(data, dict) else None
    if isinstance(new_roster, list) and new_roster:
        for entry in new_roster:
            if isinstance(entry, dict):
                entry.setdefault("id", sanitize_slug(entry.get("id") or entry.get("name") or "character"))
        save_json(roster_path, new_roster)
        roster = new_roster

    updates = data.get("knowledge_updates") if isinstance(data, dict) else []
    new_entries: List[Dict[str, Any]] = []
    timeline_entries: List[Dict[str, Any]] = []
    knowledge_count = len(knowledge)
    chapter_slug = chapter_meta.get("slug") or "chapter"

    if isinstance(updates, list):
        for note in updates:
            if not isinstance(note, dict):
                continue
            summary = note.get("summary") or note.get("detail")
            character_name = note.get("character") or note.get("name")
            if not summary or not character_name:
                continue
            normalized_summary = summary.strip().lower()
            if normalized_summary in existing_summaries:
                continue
            existing_summaries.add(normalized_summary)
            char_id = find_character_id(character_name, roster)
            section_title = note.get("related_section")
            section_slug = match_section_slug(section_title, chapter_meta)
            if section_title and not section_slug:
                continue
            knowledge_count += 1
            entry = build_character_knowledge_entry(
                character_id=char_id,
                summary=summary,
                chapter_slug=chapter_slug,
                section_slug=section_slug,
                source=chapter_slug,
                sequence=knowledge_count,
            )
            new_entries.append(entry)
            timeline_entries.append({
                "timestamp": entry["timestamp"],
                "chapter": chapter_slug,
                "section": section_slug,
                "type": "character",
                "subject": char_id,
                "summary": summary.strip(),
            })

    append_json_entries(knowledge_path, new_entries)
    append_timeline_entries(timeline_path, timeline_entries)


def update_world_grimoires_after_chapter(
    client: Any,
    master_systems: List[str],
    chapter_content: str,
    out_dir: Path,
    chapter_meta: Dict[str, Any],
) -> None:
    """Reads a chapter's content and updates the world bible JSON files with retries."""
    print("    - Reflecting on chapter to update world grimoires...")

    update_character_grimoire_after_chapter(client, master_systems, chapter_content, out_dir, chapter_meta)

    for grimoire_name in ["locations", "systems"]:
        path = out_dir / "_context" / f"{grimoire_name}.json"
        if not path.exists():
            continue

        current_data = load_json_if_exists(path) or []
        base_prompt = textwrap.dedent(
            """            Return ONLY STRICT JSON.
            You are the keeper of the world bible. The last chapter contained these events:
            --- CHAPTER CONTENT ---
            {chapter_content}

            Here is the current '{grimoire}' grimoire (may be truncated):
            --- CURRENT {grimoire_upper} ---
            {current_data}

            Update the grimoire based on the chapter's events. Add new entries or modify existing ones (e.g., update a location's status or expand system rules). Return the COMPLETE grimoire as STRICT JSON array.
            """
        ).strip()

        feedback = ""
        max_attempts = 4
        updated_data = None

        for attempt in range(max_attempts):
            prompt = base_prompt.format(
                chapter_content=chapter_content,
                grimoire=grimoire_name,
                grimoire_upper=grimoire_name.upper(),
                current_data=json.dumps(current_data[:20], ensure_ascii=False, indent=2),
            )
            if feedback:
                prompt += f"\n\n--- CORRECTION NOTICE ---\nPrevious attempt error: {feedback}. Return ONLY STRICT JSON array."

            try:
                updated_json_str = llm_call(client, master_systems, prompt, is_json=True)
                updated_data = json.loads(updated_json_str)
                break
            except (ValueError, json.JSONDecodeError) as err:
                feedback = str(err)
                print(f"        ! Grimoire update attempt {attempt+1}/{max_attempts} failed for '{grimoire_name}': {err}")
                if attempt < max_attempts - 1:
                    if attempt == 0:
                        delay = 0.6 + random.random() * 0.6
                    else:
                        delay = min(30.0, (2 ** attempt) + random.random())
                    print(f"        - Retrying grimoire update after {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise

        if updated_data is not None:
            save_json(path, updated_data)
            print(f"      - Grimoire '{grimoire_name}.json' has been updated.")
def plan_inter_section_transition(client: Any, system_messages: list, last_section_summary: str, next_section_title: str, next_section_desc: str) -> str:
    # ... (implementation unchanged) ...
    if not last_section_summary:
        return f"This is the first section. Establish the setting and character's state, addressing the goal: '{next_section_desc}'."
    print(f"      - Planning transition to section: '{next_section_title}'...")
    prompt = f"Last scene summary:\n{last_section_summary}\n\nNext scene is '{next_section_title}', with goal: '{next_section_desc}'.\n\nBriefly describe the narrative transition (pacing, location, mindset)."
    return llm_call(client, system_messages, prompt)

def generate_prose_for_subsection(writer_client: Any, system_messages: list, context: dict, transition_plan: str) -> str:
    # ... (implementation unchanged) ...
    print(f"      - Writing prose for: '{context['sub_title']}'...")
    prompt = (
        f"Write the following scene. Adhere to the persona and style guides.\n\n--- CONTEXT ---\n"
        f"Book: {context['book_title']}\nChapter: {context['ch_title']}\n"
        f"Section Arc: {context['sec_title']} - {context['sec_desc']}\n"
        f"This Scene: {context['sub_title']} - {context['sub_desc']}\n\n"
        f"--- SECTION DYNAMICS ---\nSection Goal: {context['section_scene_goal']}\nImmediate Obstacle: {context['section_obstacle']}\nSection Turn: {context['section_turn']}\nSection Fallout: {context['section_fallout']}\nSection Carry Forward: {context['section_carry_forward']}\n\n"
        f"--- SCENE BEAT ---\nScene Goal: {context['scene_goal']}\nImmediate Obstacle: {context['obstacle']}\nTurning Point: {context['turn']}\nFallout / Next Beat: {context['fallout']}\nCarry Forward into Next Scene: {context['carry_forward']}\n\n"
        f"--- NARRATIVE BRIDGE PLAN ---\n{transition_plan}\n\n"
        f"{context['recent_memories']}\n--- END CONTEXT ---\n\n"
        "Write only the prose for this scene. Ensure you dramatize the goal, obstacle, turn, and fallout without summarizing them. Carry the momentum into the stated carry-forward. Begin."
    )
    return llm_call(writer_client, system_messages, prompt)

# --- Main Weaver Workflow ---

# --- Phase Orchestration Helpers ---

def ensure_vision_phase(planner_client: Any, raw_persona: str, seed_prompt: str, output_root: Path, checkpoint: CheckpointManager) -> Tuple[str, str]:
    phase_name = "vision"
    goals_path = output_root / "_context" / "book_goals.md"
    plan_path = output_root / "_context" / "story.plan.md"
    locked = phase_is_locked(output_root, phase_name)
    if goals_path.exists() and plan_path.exists():
        checkpoint.mark_phase_complete(phase_name, outputs=["book_goals.md", "story.plan.md"])
        if not locked:
            set_phase_lock(output_root, phase_name, True)
        return load_text(goals_path), load_text(plan_path)
    if locked:
        raise RuntimeError("Vision phase is locked; remove the phase lock before regenerating goals or plan.")
    checkpoint.mark_phase_start(phase_name)
    book_goals_text, plan_text = plan_initial_vision(planner_client, raw_persona, seed_prompt, output_root)
    checkpoint.mark_phase_complete(phase_name, outputs=["book_goals.md", "story.plan.md"])
    set_phase_lock(output_root, phase_name, True)
    return book_goals_text, plan_text


def ensure_world_grimoires_phase(planner_client: Any, system_messages: List[str], output_root: Path, checkpoint: CheckpointManager) -> None:
    phase_name = "world"
    grimoire_files = [
        output_root / "_context" / "characters.roster.json",
        output_root / "_context" / "characters.knowledge.json",
        output_root / "_context" / "locations.json",
        output_root / "_context" / "systems.json",
        output_root / "_context" / "timeline.json",
    ]
    if all(path.exists() for path in grimoire_files):
        checkpoint.mark_phase_complete(phase_name, grimoires=len(grimoire_files))
        return
    checkpoint.mark_phase_start(phase_name)
    plan_world_grimoires(planner_client, system_messages, output_root)
    checkpoint.mark_phase_complete(phase_name, grimoires=len(grimoire_files))




def plan_chapter_blueprint(
    client: Any,
    system_messages: List[str],
    book_spec: Dict[str, Any],
    last_chapter_summary: str,
    chapter_num: int,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Create the high-level narrative blueprint for a chapter with retry/backoff."""
    print(f"  - Planning high-level blueprint for Chapter {chapter_num}...")

    base_prompt = textwrap.dedent("""
        Return ONLY STRICT JSON.
        Architect the high-level blueprint for Chapter {chapter_num}. Your response must be a JSON object
        matching `{{ "chapter": {{ "title": string, "summary": string, "structure": [ {{ "section": string, "summary": string, "goal": string, "obstacle": string, "turn": string, "fallout": string }} ] }} }}`.

        Each structure entry must describe a distinct beat. Use:
          - summary: 2-3 sentences explaining what happens in the beat.
          - goal: what the POV or driving force wants in this beat.
          - obstacle: the immediate resistance or complication.
          - turn: the moment that changes the trajectory of the beat.
          - fallout: how this beat sets up the next.

        --- SUMMARY OF PREVIOUS CHAPTER ---
        {previous_summary}

        --- CURRENT BOOK BLUEPRINT (for context) ---
        {book_spec_json}

        Return ONLY STRICT JSON for the next chapter blueprint.
    """).strip()

    max_attempts = 4
    feedback = ""
    for attempt in range(max_attempts):
        prompt = base_prompt.format(
            chapter_num=chapter_num,
            previous_summary=last_chapter_summary or "This is the first chapter.",
            book_spec_json=json.dumps(book_spec, ensure_ascii=False, indent=2),
        )
        if feedback:
            prompt += "\n\n--- SCHEMA FEEDBACK ---\n" + feedback
        try:
            blueprint_str = llm_call(client, system_messages, prompt, is_json=True)
            blueprint_data = json.loads(blueprint_str)
            salient_terms = collect_salient_terms(out_dir) if out_dir else set()
            chapter_block = blueprint_data.get("chapter", {}) if isinstance(blueprint_data, dict) else {}
            gated_text = f"{chapter_block.get('title', '')} {chapter_block.get('summary', '')}"
            if not simple_attentional_gate(gated_text, salient_terms, min_hits=1):
                raise SchemaValidationError("Attentional gate: blueprint lacks salient-character/theme anchors.")
            return validate_blueprint_structure(blueprint_data, chapter_num)
        except SchemaValidationError as err:
            feedback = f"Schema validation failed: {err}. Return ONLY STRICT JSON for Chapter {chapter_num} using the exact schema."
            print(f"    ! Blueprint attempt {attempt+1}/{max_attempts} failed validation: {err}")
        except (json.JSONDecodeError, ValueError) as err:
            feedback = f"JSON parsing failed ({err}). Return ONLY STRICT JSON for the chapter blueprint."
            print(f"    ! Blueprint attempt {attempt+1}/{max_attempts} returned invalid JSON: {err}")
        except requests.exceptions.RequestException as err:
            feedback = f"Transport error ({err}). Repeat the same instructions and return ONLY STRICT JSON."
            print(f"    ! Blueprint attempt {attempt+1}/{max_attempts} hit API error: {err}")
        if attempt < max_attempts - 1:
            if attempt == 0:
                delay = 0.6 + random.random() * 0.6
            else:
                delay = min(30.0, (2 ** attempt) + random.random())
            print(f"    - Retrying after {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError(f"Unable to produce a valid blueprint for Chapter {chapter_num} after {max_attempts} attempts.")



def ensure_blueprint_phase(
    planner_client: Any,
    raw_persona: str,
    style_summary: str,
    book_goals_text: str,
    plan_text: str,
    output_root: Path,
    existing_final_spec: Dict[str, Any],
    target_chapters: int,
    checkpoint: CheckpointManager,
    ctx_mgr: Optional[ContextManager] = None,
) -> Dict[str, Any]:
    phase_name = "blueprint"
    default_title = existing_final_spec.get("book_title", "Untitled")
    default_meta = existing_final_spec.get("meta", {})

    blueprint_path, blueprint_spec = load_blueprint_spec(output_root, default_title, default_meta)
    blueprint_spec.setdefault("book_title", default_title)
    blueprint_spec.setdefault("meta", default_meta or {})
    blueprint_spec.setdefault("chapters", [])
    save_json(blueprint_path, blueprint_spec)

    if phase_is_locked(output_root, phase_name):
        checkpoint.mark_phase_complete(phase_name, total=len(blueprint_spec.get("chapters", [])))
        return blueprint_spec

    existing_blueprints = len(blueprint_spec.get("chapters", []))
    existing_final_chapters = existing_final_spec.get("chapters") or []
    existing_final_count = len(existing_final_chapters)
    target_total = target_chapters if target_chapters is not None else max(existing_blueprints, existing_final_count)
    needed = max(0, target_total - existing_blueprints)

    if needed == 0:
        checkpoint.mark_phase_complete(phase_name, total=existing_blueprints)
        set_phase_lock(output_root, phase_name, True)
        return blueprint_spec

    print("--- Architect Phase: Planning high-level chapter blueprints ---")
    checkpoint.mark_phase_start(phase_name, have=existing_blueprints, target=target_total)

    master_system_messages = build_master_system_messages(
        raw_author=raw_persona,
        style_summary=style_summary,
        book_goals_text=book_goals_text,
        plan_text=plan_text,
        out_dir=output_root,
    )

    for i in range(existing_blueprints + 1, target_total + 1):
        prev_summary = "This is the first chapter."
        if i > 1:
            prev_slug = None
            if len(existing_final_chapters) >= (i - 1):
                prev_chapter = existing_final_chapters[i - 2]
                prev_slug = sanitize_slug(prev_chapter.get("slug") or prev_chapter.get("title") or f"chapter-{i-1}")
            if prev_slug and ctx_mgr:
                fetched = ctx_mgr.get_full_chapter_summary(prev_slug, master_system_messages)
                if fetched:
                    prev_summary = fetched
            if prev_summary == "This is the first chapter." and len(existing_final_chapters) >= (i - 1):
                prev_chapter = existing_final_chapters[i - 2]
                prev_summary = (
                    prev_chapter.get("metadata", {}).get("synopsis")
                    or prev_chapter.get("description")
                    or prev_summary
                )

        validated_bp = plan_chapter_blueprint(
            planner_client,
            master_system_messages,
            existing_final_spec,
            prev_summary,
            i,
            output_root,
        )

        chapter_entry = validated_bp["chapter"]
        ensure_slug_field(chapter_entry, f"chapter-{i}")
        chapter_entry["slug"] = build_indexed_slug(i, chapter_entry.get("slug"), chapter_entry.get("title"))
        blueprint_spec.setdefault("chapters", []).append(validated_bp)
        save_json(blueprint_path, blueprint_spec)
        checkpoint.update_phase(phase_name, planned=len(blueprint_spec["chapters"]), last=i)
        print(f"  - Planned Chapter {i}: {chapter_entry.get('title')}")

    set_phase_lock(output_root, phase_name, True)
    checkpoint.mark_phase_complete(phase_name, total=len(blueprint_spec.get("chapters", [])))
    return blueprint_spec






def refine_chapter_plan_for_writing(
    client: Any,
    system_messages: List[str],
    chapter_blueprint: Dict[str, Any],
    chapter_num: int,
) -> Dict[str, Any]:
    """Transform the high-level blueprint into a detailed, writable chapter spec with retries."""
    print(f"  - Refining blueprint into detailed structure for Chapter {chapter_num}...")
    blueprint_inner = chapter_blueprint.get("chapter", {})

    base_prompt = textwrap.dedent("""
        Return ONLY STRICT JSON.
        You are a master outliner. Transform the following high-level chapter blueprint into a detailed, multi-level chapter specification suitable for a writer. The final output must be a single chapter object in STRICT JSON, adhering to the final book schema: `{{ "title": string, "slug": string, "description": string, "metadata": {{ "synopsis": string }}, "subsections": [ {{ "title": string, "slug": string, "description": string, "metadata": {{ "scene_goal": string, "obstacle": string, "turn": string, "fallout": string, "carry_forward": string }}, "subsections": [ {{ "title": string, "slug": string, "description": string, "metadata": {{ "scene_goal": string, "obstacle": string, "turn": string, "fallout": string, "carry_forward": string }} }} ] }} ] }}`.

        **Instructions:**
        1. Use the chapter blueprint's `title` and `summary` for the chapter's `title` and `metadata.synopsis`.
        2. Map each blueprint `structure` item to a first-level section. Use its `summary` for the section description and carry its `goal`, `obstacle`, `turn`, and `fallout` into the section `metadata`. Invent a `carry_forward` string that states what this section hands off to the next.
        3. For each section, break the `summary` into multiple scene-level subsections. Each subsection must have a vivid `description` (2-3 paragraphs) and a `metadata` object detailing `scene_goal`, `obstacle`, `turn`, `fallout`, and `carry_forward` specific to that beat. Ensure subsections escalate tension and avoid repeating previous subsections.
        4. Preserve continuity hooks by referencing consequences from previous sections when appropriate.

        --- CHAPTER BLUEPRINT TO REFINE ---
        {blueprint}

        Return ONLY STRICT JSON for the refined, final-schema chapter object.
    """).strip()

    max_attempts = 4
    feedback = ""
    for attempt in range(max_attempts):
        prompt = base_prompt.format(blueprint=json.dumps(blueprint_inner, ensure_ascii=False, indent=2))
        if feedback:
            prompt += "\n\n--- SCHEMA FEEDBACK ---\n" + feedback
        try:
            refined_str = llm_call(client, system_messages, prompt, is_json=True)
            refined_data = json.loads(refined_str)
            return validate_refined_chapter_structure(refined_data, chapter_num)
        except SchemaValidationError as err:
            feedback = f"Schema validation failed: {err}. Return ONLY STRICT JSON for chapter {chapter_num} matching the schema."
            print(f"    ! Refinement attempt {attempt+1}/{max_attempts} failed validation: {err}")
        except (json.JSONDecodeError, ValueError) as err:
            feedback = f"JSON parsing failed ({err}). Return ONLY STRICT JSON for the chapter object."
            print(f"    ! Refinement attempt {attempt+1}/{max_attempts} returned invalid JSON: {err}")
        except requests.exceptions.RequestException as err:
            feedback = f"Transport error ({err}). Repeat the same instructions and return ONLY STRICT JSON."
            print(f"    ! Refinement attempt {attempt+1}/{max_attempts} hit API error: {err}")
        if attempt < max_attempts - 1:
            if attempt == 0:
                delay = 0.6 + random.random() * 0.6
            else:
                delay = min(30.0, (2 ** attempt) + random.random())
            print(f"    - Retrying after {delay:.1f}s...")
            time.sleep(delay)
    raise RuntimeError(f"Unable to refine Chapter {chapter_num} blueprint after {max_attempts} attempts.")

def ensure_refine_phase(
    planner_client: Any,
    raw_persona: str,
    style_summary: str,
    book_goals_text: str,
    plan_text: str,
    output_root: Path,
    blueprint_spec: Dict[str, Any],
    story_json_path: Path,
    checkpoint: CheckpointManager,
) -> Dict[str, Any]:
    phase_name = "refine"
    if not phase_is_locked(output_root, "blueprint"):
        set_phase_lock(output_root, "blueprint", True)
    final_spec = load_final_story_spec(story_json_path, blueprint_spec.get("book_title", "Untitled"), blueprint_spec.get("meta", {}))
    final_spec.setdefault("book_title", blueprint_spec.get("book_title", final_spec.get("book_title", "Untitled")))
    final_spec.setdefault("meta", final_spec.get("meta", {}))

    if phase_is_locked(output_root, "refine"):
        checkpoint.mark_phase_complete(phase_name, total=len(final_spec.get("chapters", [])))
        save_json(story_json_path, final_spec)
        return final_spec

    validated_existing: List[Dict[str, Any]] = []
    for idx, existing_chapter in enumerate(final_spec.get("chapters", []), start=1):
        try:
            validated_existing.append(validate_refined_chapter_structure(existing_chapter, idx))
        except SchemaValidationError as err:
            slug = sanitize_slug(existing_chapter.get("slug") or existing_chapter.get("title") or f"chapter-{idx}")
            print(f"    - Existing chapter '{existing_chapter.get('title', slug)}' failed validation: {err}. It will be regenerated.")

    deduped_chapters: List[Dict[str, Any]] = []
    seen_slugs: Set[str] = set()
    for chapter in validated_existing:
        slug = sanitize_slug(chapter.get("slug") or chapter.get("title"))
        if slug in seen_slugs:
            print(f"    - Deduping duplicate chapter slug '{slug}' from prior run.")
            continue
        chapter["slug"] = slug
        seen_slugs.add(slug)
        deduped_chapters.append(chapter)

    final_spec["chapters"] = deduped_chapters
    save_json(story_json_path, final_spec)

    existing_slugs = set(seen_slugs)
    total_blueprints = len(blueprint_spec.get("chapters", []))
    if total_blueprints == 0:
        checkpoint.mark_phase_complete(phase_name, total=len(existing_slugs))
        set_phase_lock(output_root, "refine", True)
        save_json(story_json_path, final_spec)
        return final_spec
    if len(existing_slugs) >= total_blueprints:
        checkpoint.mark_phase_complete(phase_name, total=len(existing_slugs))
        set_phase_lock(output_root, "refine", True)
        save_json(story_json_path, final_spec)
        return final_spec

    print("--- Scribe Phase: Refining blueprints into writable specs ---")
    checkpoint.mark_phase_start(phase_name, have=len(existing_slugs), target=total_blueprints)
    for idx, chapter_blueprint in enumerate(blueprint_spec.get("chapters", []), start=1):
        expected_slug = build_indexed_slug(
            idx,
            chapter_blueprint.get("chapter", {}).get("slug"),
            chapter_blueprint.get("chapter", {}).get("title")
        )
        unique_slug = expected_slug
        suffix = 2
        while unique_slug in existing_slugs:
            unique_slug = sanitize_slug(f"{expected_slug}-{suffix}")
            suffix += 1
        expected_slug = unique_slug
        chapter_blueprint.setdefault("chapter", {})["slug"] = expected_slug

        master_system_messages = build_master_system_messages(raw_persona, style_summary, book_goals_text, plan_text, output_root)
        refined_chapter_spec = refine_chapter_plan_for_writing(planner_client, master_system_messages, chapter_blueprint, idx)
        refined_chapter_spec["slug"] = expected_slug
        final_spec.setdefault("chapters", []).append(refined_chapter_spec)
        existing_slugs.add(expected_slug)
        save_json(story_json_path, final_spec)
        checkpoint.update_phase(phase_name, refined=len(final_spec.get("chapters", [])), last=idx)
        print(f"  - Chapter {idx} refined.")

    checkpoint.mark_phase_complete(phase_name, total=len(final_spec.get("chapters", [])))
    set_phase_lock(output_root, "refine", True)
    save_json(story_json_path, final_spec)
    return final_spec


def perform_writing_phase(
    planner_client: Any,
    writer_client: Any,
    raw_persona: str,
    style_summary: str,
    book_goals_text: str,
    plan_text: str,
    final_spec: Dict[str, Any],
    output_root: Path,
    ctx_mgr: ContextManager,
    checkpoint: CheckpointManager,
) -> None:
    chapters = final_spec.get("chapters", [])
    if not chapters:
        print("[weaver] No refined chapters found; skipping prose generation.")
        checkpoint.mark_phase_complete("write", total=0)
        return

    total_leaf = sum(len(section.get("subsections", [])) for chapter in chapters for section in chapter.get("subsections", []))
    if total_leaf == 0:
        print("[weaver] Refined chapters lack leaf subsections; nothing to write.")
        checkpoint.mark_phase_complete("write", total=0)
        return

    existing_written = 0
    for ch_idx, chapter in enumerate(chapters, start=1):
        ch_slug = sanitize_slug(chapter.get("slug") or chapter.get("title") or f"chapter-{ch_idx}")
        chapter_dir = output_root / f"{ch_idx:02d}-{ch_slug}"
        for s_idx, section in enumerate(chapter.get("subsections", []), start=1):
            sec_slug = sanitize_slug(section.get("slug") or section.get("title") or f"section-{s_idx}")
            section_dir = chapter_dir / f"{s_idx:02d}-{sec_slug}"
            for sub_idx, sub_section in enumerate(section.get("subsections", []), start=1):
                sub_slug = sanitize_slug(sub_section.get("slug") or sub_section.get("title") or f"subsection-{sub_idx}")
                md_path = section_dir / f"{sub_idx:03d}-{sub_slug}.md"
                if md_path.exists():
                    existing_written += 1

    if existing_written >= total_leaf:
        print("[weaver] All prose already exists; skipping writing phase.")
        checkpoint.mark_phase_complete("write", total=total_leaf)
        return

    checkpoint.mark_phase_start("write", completed=existing_written, total=total_leaf)
    print("--- Weaver Phase: Writing prose ---")

    mlog = MetricsLogger(output_root)
    book_title = final_spec.get("book_title", "Untitled")
    written = existing_written

    for ch_idx, chapter in enumerate(chapters, start=1):
        ch_title = chapter.get("title", f"Chapter {ch_idx}")
        ch_slug = sanitize_slug(chapter.get("slug") or ch_title)
        chapter_dir = output_root / f"{ch_idx:02d}-{ch_slug}"
        chapter_dir.mkdir(parents=True, exist_ok=True)
        print(f"--- Weaving Chapter {ch_idx}: {ch_title} ---")

        master_system_messages = build_master_system_messages(raw_persona, style_summary, book_goals_text, plan_text, output_root)

        chapter_outline: List[Dict[str, Any]] = []
        for s_idx, section in enumerate(chapter.get("subsections", []), start=1):
            sec_title = section.get("title", f"Section {s_idx}")
            sec_slug = sanitize_slug(section.get("slug") or sec_title or f"section-{s_idx}")
            sec_meta = section.get("metadata", {}) if isinstance(section.get("metadata"), dict) else {}
            sub_outline: List[Dict[str, Any]] = []
            for sub_idx, sub_section in enumerate(section.get("subsections", []), start=1):
                sub_title = sub_section.get("title", f"Sub-section {sub_idx}")
                sub_slug = sanitize_slug(sub_section.get("slug") or sub_title or f"subsection-{sub_idx}")
                sub_meta = sub_section.get("metadata", {}) if isinstance(sub_section.get("metadata"), dict) else {}
                sub_outline.append({"title": sub_title, "slug": sub_slug, "metadata": sub_meta})
            chapter_outline.append({"title": sec_title, "slug": sec_slug, "metadata": sec_meta, "subsections": sub_outline})

        last_section_summary = ""
        chapter_new_prose: List[str] = []
        for s_idx, section in enumerate(chapter.get("subsections", []), start=1):
            section_outline = chapter_outline[s_idx - 1] if s_idx - 1 < len(chapter_outline) else {"title": section.get("title", f"Section {s_idx}"), "slug": sanitize_slug(section.get("slug") or section.get("title") or f"section-{s_idx}"), "metadata": {}, "subsections": []}
            sec_title = section_outline["title"]
            sec_slug = section_outline["slug"]
            section_meta = section_outline.get("metadata") if isinstance(section_outline.get("metadata"), dict) else {}
            sec_desc = section.get("description", "")
            section_dir = chapter_dir / f"{s_idx:02d}-{sec_slug}"
            section_dir.mkdir(parents=True, exist_ok=True)

            section_entries: List[Dict[str, Any]] = []
            for sub_idx, sub_section in enumerate(section.get("subsections", []), start=1):
                if sub_idx - 1 < len(section_outline["subsections"]):
                    sub_outline = section_outline["subsections"][sub_idx - 1]
                    sub_title = sub_outline["title"]
                    sub_slug = sub_outline["slug"]
                    sub_meta = sub_outline.get("metadata") if isinstance(sub_outline.get("metadata"), dict) else {}
                else:
                    sub_title = sub_section.get("title", f"Sub-section {sub_idx}")
                    sub_slug = sanitize_slug(sub_section.get("slug") or sub_section.get("title") or f"subsection-{sub_idx}")
                    sub_meta = sub_section.get("metadata") if isinstance(sub_section.get("metadata"), dict) else {}
                sub_desc = sub_section.get("description", "")
                md_path = section_dir / f"{sub_idx:03d}-{sub_slug}.md"
                exists = md_path.exists()
                content = load_text(md_path) if exists else ""
                section_entries.append({
                    "index": sub_idx,
                    "title": sub_title,
                    "slug": sub_slug,
                    "description": sub_desc,
                    "path": md_path,
                    "exists": exists,
                    "content": content,
                    "metadata": sub_meta,
                })

            missing_entries = [entry for entry in section_entries if not entry["exists"]]
            transition_plan = ""
            if missing_entries:
                transition_plan = plan_inter_section_transition(
                    planner_client,
                    master_system_messages,
                    last_section_summary,
                    sec_title,
                    sec_desc,
                )

            current_section_prose_parts: List[str] = []
            current_section_new_parts: List[str] = []
            for entry in section_entries:
                if entry["exists"]:
                    prose = entry["content"]
                    if prose:
                        current_section_prose_parts.append(prose)
                    print(f"      - Skipping existing sub-section: '{entry['title']}'")
                    mlog.log("write", ch_slug, sec_slug, entry["slug"], "skip_existing", entry["title"])
                    checkpoint.update_phase("write", completed=written, total=total_leaf, current_chapter=ch_slug)
                    continue

                sub_meta = entry.get("metadata", {}) if isinstance(entry.get("metadata"), dict) else {}
                writer_context = {
                    "book_title": book_title,
                    "ch_title": ch_title,
                    "sec_title": sec_title,
                    "sec_desc": sec_desc,
                    "section_scene_goal": section_meta.get("scene_goal", ""),
                    "section_obstacle": section_meta.get("obstacle", ""),
                    "section_turn": section_meta.get("turn", ""),
                    "section_fallout": section_meta.get("fallout", ""),
                    "section_carry_forward": section_meta.get("carry_forward", ""),
                    "sub_title": entry["title"],
                    "sub_desc": entry["description"],
                    "scene_goal": sub_meta.get("scene_goal", ""),
                    "obstacle": sub_meta.get("obstacle", ""),
                    "turn": sub_meta.get("turn", ""),
                    "fallout": sub_meta.get("fallout", ""),
                    "carry_forward": sub_meta.get("carry_forward", ""),
                    "recent_memories": ctx_mgr.get_recent_memories(ch_slug),
                }
                prose = generate_prose_for_subsection(writer_client, master_system_messages, writer_context, transition_plan)
                write_text(entry["path"], prose)
                ctx_mgr.update_chapter_memory(ch_slug, entry["title"], prose, master_system_messages)
                mlog.log("write", ch_slug, sec_slug, entry["slug"], "wrote_prose", f"{len(prose)} chars")
                written += 1
                current_section_prose_parts.append(prose)
                current_section_new_parts.append(prose)
                checkpoint.update_phase("write", completed=written, total=total_leaf, current_chapter=ch_slug)

            if current_section_prose_parts:
                last_section_summary = "\n\n".join(current_section_prose_parts)

            if current_section_new_parts:
                chapter_new_prose.append("\n\n".join(current_section_new_parts))

        if chapter_new_prose:
            chapter_payload = "\n\n---\n\n".join(chapter_new_prose)


            chapter_meta = {"slug": ch_slug, "title": ch_title, "sections": chapter_outline}
            update_world_grimoires_after_chapter(planner_client, master_system_messages, chapter_payload, output_root, chapter_meta)

    checkpoint.mark_phase_complete("write", total=total_leaf, completed=written)

def main():
    parser = argparse.ArgumentParser(description="Iterative Fiction Weaver v2")
    parser.add_argument("prompt", help="Seed idea/premise for the book")
    parser.add_argument("--output", default=get_param("OUTPUT_ROOT", "book-output"))
    parser.add_argument("--author", default=get_param("DEFAULT_AUTHOR_PERSONA"))
    parser.add_argument("--chapters", type=int, default=12, help="Total chapters to write.")
    args = parser.parse_args()

    print("Initializing the Weaver v2...")
    planner_client = make_client("PLANNER_MODEL")
    writer_client = make_client("WRITER_MODEL")

    output_root = Path(args.output).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    migrate_legacy_story_layout(output_root)

    checkpoint = CheckpointManager(output_root)

    story_json_path = output_root / "story.json"
    final_stub = load_final_story_spec(story_json_path, "Untitled", {})
    if not story_json_path.exists():
        save_json(story_json_path, final_stub)

    raw_persona = load_text(Path(args.author))
    ctx_mgr = ContextManager(output_root, planner_client)
    style_summary = ctx_mgr.get_or_build_author_summary(raw_persona)

    book_goals_text, plan_text = ensure_vision_phase(planner_client, raw_persona, args.prompt, output_root, checkpoint)

    initial_system_messages = [        f"--- AUTHOR PERSONA ---{raw_persona}",
        f"--- BOOK GOALS ---{book_goals_text}",
        f"--- OVERALL STORY PLAN ---{plan_text}",
    ]
    ensure_world_grimoires_phase(planner_client, initial_system_messages, output_root, checkpoint)

    planning_passes = get_param("ITERATIVE_PLANNING_PASSES", 2)
    try:
        planning_passes = int(planning_passes)
    except (TypeError, ValueError):
        planning_passes = 2
    if planning_passes > 0:
        perform_iterative_planning_passes(
            planner_client,
            raw_persona,
            style_summary,
            book_goals_text,
            plan_text,
            output_root,
            checkpoint,
            passes=planning_passes,
        )

    blueprint_spec = ensure_blueprint_phase(
        planner_client,
        raw_persona,
        style_summary,
        book_goals_text,
        plan_text,
        output_root,
        final_stub,
        args.chapters,
        checkpoint,
        ctx_mgr,
    )

    final_spec = ensure_refine_phase(
        planner_client,
        raw_persona,
        style_summary,
        book_goals_text,
        plan_text,
        output_root,
        blueprint_spec,
        story_json_path,
        checkpoint,
    )

    perform_writing_phase(
        planner_client,
        writer_client,
        raw_persona,
        style_summary,
        book_goals_text,
        plan_text,
        final_spec,
        output_root,
        ctx_mgr,
        checkpoint,
    )

    print("\n--- Book Generation Complete ---")


if __name__ == "__main__":
    main()


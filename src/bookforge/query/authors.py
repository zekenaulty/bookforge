from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import _common


@dataclass(frozen=True, slots=True)
class AuthorVersionRecord:
    version: str
    created_at: Optional[str]
    notes: str
    files: Dict[str, str]
    schema_version: str = "author_version_record_v1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "version": self.version,
            "created_at": self.created_at,
            "notes": self.notes,
            "files": dict(self.files),
        }


@dataclass(frozen=True, slots=True)
class AuthorProfileView:
    author_slug: str
    author_ref: str
    display_name: str
    default_version: str
    selected_version: str
    versions: List[AuthorVersionRecord]
    version_notes: str
    persona_name: str
    voice: Optional[str]
    themes: List[str]
    sensory_bias: Optional[str]
    pacing: Optional[str]
    style_rules: List[str]
    taboos: List[str]
    cadence_rules: List[str]
    banned_phrases: List[str]
    influences: List[Dict[str, Any]]
    style_summary: str
    style_markdown: str
    system_fragment: str
    profile_markdown: str
    short_description: str
    source_paths: Dict[str, Optional[str]]
    source: str
    artifact_status: str
    warnings: List[str]
    schema_version: str = "author_profile_view_v1"

    @property
    def version_count(self) -> int:
        return len(self.versions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "author_slug": self.author_slug,
            "author_ref": self.author_ref,
            "display_name": self.display_name,
            "default_version": self.default_version,
            "selected_version": self.selected_version,
            "versions": self.version_count,
            "version_records": [version.to_dict() for version in self.versions],
            "version_notes": self.version_notes,
            "persona_name": self.persona_name,
            "voice": self.voice,
            "themes": list(self.themes),
            "sensory_bias": self.sensory_bias,
            "pacing": self.pacing,
            "style_rules": list(self.style_rules),
            "taboos": list(self.taboos),
            "cadence_rules": list(self.cadence_rules),
            "banned_phrases": list(self.banned_phrases),
            "influences": [dict(item) for item in self.influences],
            "style_summary": self.style_summary,
            "style_markdown": self.style_markdown,
            "system_fragment": self.system_fragment,
            "profile_markdown": self.profile_markdown,
            "short_description": self.short_description,
            "source_paths": dict(self.source_paths),
            "source": self.source,
            "artifact_status": self.artifact_status,
            "warnings": list(self.warnings),
        }


def list_author_profiles(workspace) -> List[AuthorProfileView]:
    authors_root = Path(workspace) / "authors"
    if not authors_root.exists():
        return []
    profiles: List[AuthorProfileView] = []
    for index_path in sorted(authors_root.glob("*/index.json"), key=lambda path: path.parent.name.lower()):
        try:
            profiles.append(get_author_profile(workspace, index_path.parent.name))
        except Exception:
            continue
    return profiles


def get_author_profile(workspace, author_ref: str, *, version: Optional[str] = None) -> AuthorProfileView:
    authors_root = Path(workspace) / "authors"
    author_slug, ref_version = _parse_author_ref(author_ref)
    author_root = authors_root / author_slug
    if not author_root.exists():
        raise FileNotFoundError(f"Author not found: {author_slug}")

    index_path = author_root / "index.json"
    index = _common.read_json(index_path) or {}
    default_version = _text(index.get("default_version")) or "v1"
    selected_version = version or ref_version or default_version
    versions = _version_records(index.get("versions"))
    selected_record = _find_version(versions, selected_version)
    if selected_record is None:
        raise FileNotFoundError(f"Author version not found: {author_slug}/{selected_version}")

    selected_version = selected_record.version
    display_name = _text(index.get("display_name")) or author_slug
    files = selected_record.files
    author_json_path = author_root / _file_path(files, "author_json", selected_version, "author.json")
    style_path = author_root / _file_path(files, "author_style_md", selected_version, "author_style.md")
    system_path = author_root / _file_path(files, "system_fragment_md", selected_version, "system_fragment.md")

    warnings: List[str] = []
    author_data = _safe_json(author_json_path, warnings, "author_json")
    style_markdown = _safe_text(style_path, warnings, "author_style_md")
    system_fragment = _safe_text(system_path, warnings, "system_fragment_md")

    trait_profile = author_data.get("trait_profile") if isinstance(author_data.get("trait_profile"), dict) else {}
    persona_name = _text(author_data.get("persona_name")) or display_name
    voice = _text(trait_profile.get("voice"))
    themes = _text_list(trait_profile.get("themes"))
    sensory_bias = _text(trait_profile.get("sensory_bias"))
    pacing = _text(trait_profile.get("pacing"))
    style_rules = _text_list(author_data.get("style_rules"))
    taboos = _text_list(author_data.get("taboos"))
    cadence_rules = _text_list(author_data.get("cadence_rules"))
    banned_phrases = _text_list(author_data.get("banned_phrases"))
    influences = [dict(item) for item in author_data.get("influences", []) if isinstance(item, dict)]
    style_summary = _first_paragraph(style_markdown)
    short_description = style_summary or voice or selected_record.notes
    profile_markdown = _profile_markdown(
        display_name=display_name,
        author_ref=f"{author_slug}/{selected_version}",
        version_notes=selected_record.notes,
        style_summary=style_summary,
        voice=voice,
        themes=themes,
        sensory_bias=sensory_bias,
        pacing=pacing,
        style_rules=style_rules,
        taboos=taboos,
        cadence_rules=cadence_rules,
        system_fragment=system_fragment,
    )

    return AuthorProfileView(
        author_slug=author_slug,
        author_ref=f"{author_slug}/{selected_version}",
        display_name=display_name,
        default_version=default_version,
        selected_version=selected_version,
        versions=versions,
        version_notes=selected_record.notes,
        persona_name=persona_name,
        voice=voice,
        themes=themes,
        sensory_bias=sensory_bias,
        pacing=pacing,
        style_rules=style_rules,
        taboos=taboos,
        cadence_rules=cadence_rules,
        banned_phrases=banned_phrases,
        influences=influences,
        style_summary=style_summary,
        style_markdown=style_markdown,
        system_fragment=system_fragment,
        profile_markdown=profile_markdown,
        short_description=short_description,
        source_paths={
            "index_json": _relative(index_path, authors_root),
            "author_json": _relative(author_json_path, authors_root),
            "author_style_md": _relative(style_path, authors_root),
            "system_fragment_md": _relative(system_path, authors_root),
        },
        source="bookforge-query",
        artifact_status="authoritative",
        warnings=warnings,
    )


def _parse_author_ref(author_ref: str) -> tuple[str, Optional[str]]:
    parts = [part.strip() for part in str(author_ref or "").strip().split("/", 1)]
    slug = parts[0] if parts and parts[0] else ""
    if not slug:
        raise ValueError("author_ref must include an author slug")
    version = parts[1] if len(parts) > 1 and parts[1] else None
    return slug, version


def _version_records(value: Any) -> List[AuthorVersionRecord]:
    records: List[AuthorVersionRecord] = []
    if not isinstance(value, list):
        return records
    for item in value:
        if not isinstance(item, dict):
            continue
        version = _text(item.get("version"))
        if not version:
            continue
        files = item.get("files") if isinstance(item.get("files"), dict) else {}
        records.append(
            AuthorVersionRecord(
                version=version,
                created_at=_text(item.get("created_at")),
                notes=_text(item.get("notes")) or "",
                files={str(key): str(val) for key, val in files.items()},
            )
        )
    return records


def _find_version(records: List[AuthorVersionRecord], selected_version: str) -> Optional[AuthorVersionRecord]:
    for record in records:
        if record.version == selected_version:
            return record
    return records[0] if records else None


def _file_path(files: Dict[str, str], key: str, version: str, fallback: str) -> str:
    return str(files.get(key) or f"{version}/{fallback}")


def _safe_json(path: Path, warnings: List[str], label: str) -> Dict[str, Any]:
    try:
        payload = _common.read_json(path)
    except Exception as exc:
        warnings.append(f"Unable to read {label}: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_text(path: Path, warnings: List[str], label: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception as exc:
        warnings.append(f"Unable to read {label}: {exc}")
        return ""


def _profile_markdown(
    *,
    display_name: str,
    author_ref: str,
    version_notes: str,
    style_summary: str,
    voice: Optional[str],
    themes: List[str],
    sensory_bias: Optional[str],
    pacing: Optional[str],
    style_rules: List[str],
    taboos: List[str],
    cadence_rules: List[str],
    system_fragment: str,
) -> str:
    lines: List[str] = [f"# {display_name}", "", f"Author ref: `{author_ref}`", ""]
    if style_summary:
        lines.extend(["## Soul And Style", style_summary, ""])
    if voice:
        lines.extend(["## Voice", voice, ""])
    if version_notes:
        lines.extend(["## Version Notes", version_notes, ""])
    if themes:
        lines.extend(["## Thematic Gravity", *[f"- {theme}" for theme in themes], ""])
    physical = [item for item in (sensory_bias, pacing) if item]
    if physical:
        lines.extend(["## Texture And Motion", *[f"- {item}" for item in physical], ""])
    if style_rules:
        lines.extend(["## Style Rules", *[f"- {item}" for item in style_rules], ""])
    if cadence_rules:
        lines.extend(["## Cadence", *[f"- {item}" for item in cadence_rules], ""])
    if taboos:
        lines.extend(["## Taboos", *[f"- {item}" for item in taboos], ""])
    if system_fragment:
        lines.extend(["## System Fragment", system_fragment.strip(), ""])
    return "\n".join(lines).strip()


def _text(value: Any) -> Optional[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _text_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _first_paragraph(text: str) -> str:
    chunks = [chunk.strip() for chunk in text.replace("\r\n", "\n").split("\n\n")]
    return next((chunk for chunk in chunks if chunk), "")


def _relative(path: Path, root: Path) -> Optional[str]:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)

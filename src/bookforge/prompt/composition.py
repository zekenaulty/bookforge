from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set
import codecs
import hashlib
import json
import re

from jsonschema import Draft202012Validator

from bookforge.util.paths import repo_root


PLACEHOLDER_TOKEN_PATTERN = re.compile(r"\{\{[^}]+\}\}")
PROMPT_COMPOSITION_SCHEMA_VERSION = "1.0"


@dataclass
class PromptCompositionError(Exception):
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class CompositionRunResult:
    output_dir: Path
    compiled_templates: Dict[str, str] = field(default_factory=dict)
    checksums: Dict[str, str] = field(default_factory=dict)
    placeholder_audits: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    traces: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


def _composition_root() -> Path:
    return repo_root(Path(__file__).resolve()) / "resources" / "prompt_composition"


def _load_json(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise PromptCompositionError(f"Missing {label}: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptCompositionError(f"Invalid JSON in {label}: {path}") from exc


def _load_manifest_schema(composition_root: Path) -> Dict[str, Any]:
    return _load_json(composition_root / "manifest.schema.json", "manifest schema")


def _load_allowlist(composition_root: Path) -> Set[str]:
    data = _load_json(composition_root / "prompt_tokens_allowlist.json", "placeholder allowlist")
    schema_version = str(data.get("schema_version", "")).strip()
    if schema_version != PROMPT_COMPOSITION_SCHEMA_VERSION:
        raise PromptCompositionError(
            "prompt_tokens_allowlist.json must declare schema_version='1.0'"
        )
    tokens = data.get("allowed_tokens")
    if not isinstance(tokens, list) or not all(isinstance(item, str) for item in tokens):
        raise PromptCompositionError(
            "prompt_tokens_allowlist.json must contain allowed_tokens as an array of strings"
        )
    return set(tokens)


def _load_expected_checksums(composition_root: Path) -> Dict[str, str]:
    checksums_path = composition_root / "source_of_truth_checksums.json"
    if not checksums_path.exists():
        return {}
    payload = _load_json(checksums_path, "source-of-truth checksums")
    values = payload.get("checksums")
    if not isinstance(values, dict):
        raise PromptCompositionError("source_of_truth_checksums.json must contain a checksums object")
    normalized: Dict[str, str] = {}
    for key, value in values.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise PromptCompositionError(
                "source_of_truth_checksums.json checksums must map string template names to hashes"
            )
        normalized[key] = value.upper().strip()
    return normalized


def _line_count(text: str) -> int:
    if text == "":
        return 0
    if text.endswith("\n"):
        return text.count("\n")
    return text.count("\n") + 1


def _read_fragment_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(codecs.BOM_UTF8):
        raise PromptCompositionError(f"UTF-8 BOM not allowed in composition fragment: {path}")
    if b"\r" in raw:
        raise PromptCompositionError(f"CRLF/CR newline detected in composition fragment: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PromptCompositionError(f"Fragment is not valid UTF-8: {path}") from exc
    if text == "":
        raise PromptCompositionError(f"Composition fragment cannot be empty: {path}")
    return text


def _write_text_utf8_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def _validate_manifest_schema(manifest_path: Path, manifest: Dict[str, Any], schema: Dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda error: list(error.path))
    if not errors:
        return
    first = errors[0]
    dotted_path = ".".join([str(part) for part in first.path])
    path_label = dotted_path or "<root>"
    raise PromptCompositionError(
        f"Manifest schema validation failed for {manifest_path} at {path_label}: {first.message}"
    )


def _validate_manifest_contract(manifest_path: Path, manifest: Dict[str, Any]) -> None:
    template = str(manifest.get("template", "")).strip()
    entries = manifest.get("entries", [])
    if not template:
        raise PromptCompositionError(f"Manifest template is required: {manifest_path}")
    if not isinstance(entries, list) or not entries:
        raise PromptCompositionError(f"Manifest entries must be a non-empty array: {manifest_path}")

    seen_entry_ids: Set[str] = set()
    seen_semantic_ids: Set[str] = set()

    for entry in entries:
        entry_id = str(entry.get("entry_id", "")).strip()
        semantic_id = str(entry.get("semantic_id", "")).strip()
        owner_phase = str(entry.get("owner_phase", "")).strip()
        applies_to = entry.get("applies_to")
        source_span = entry.get("source_prompt_span")
        repeat_policy = entry.get("repeat_policy")
        dedupe_eligible = entry.get("dedupe_eligible")

        if not entry_id:
            raise PromptCompositionError(f"Manifest entry_id cannot be empty: {manifest_path}")
        if entry_id in seen_entry_ids:
            raise PromptCompositionError(f"Duplicate entry_id {entry_id!r} in manifest {manifest_path}")
        seen_entry_ids.add(entry_id)

        if not semantic_id:
            raise PromptCompositionError(f"Manifest semantic_id cannot be empty: {manifest_path}")
        if semantic_id in seen_semantic_ids:
            raise PromptCompositionError(
                f"Duplicate semantic_id {semantic_id!r} in manifest {manifest_path}"
            )
        seen_semantic_ids.add(semantic_id)

        if not owner_phase:
            raise PromptCompositionError(
                f"Manifest entry {entry_id} is missing owner_phase in {manifest_path}"
            )

        if not isinstance(applies_to, list) or template not in applies_to:
            raise PromptCompositionError(
                f"Manifest entry {entry_id} in {manifest_path} must include template {template!r} in applies_to"
            )

        if not isinstance(source_span, dict):
            raise PromptCompositionError(
                f"Manifest entry {entry_id} in {manifest_path} is missing source_prompt_span"
            )
        line_start = int(source_span.get("line_start", 0))
        line_end = int(source_span.get("line_end", 0))
        if line_start < 1 or line_end < line_start:
            raise PromptCompositionError(
                f"Invalid source_prompt_span for entry {entry_id} in {manifest_path}: {source_span}"
            )

        if not isinstance(dedupe_eligible, bool):
            raise PromptCompositionError(
                f"dedupe_eligible must be boolean for entry {entry_id} in {manifest_path}"
            )

        if not isinstance(repeat_policy, dict):
            raise PromptCompositionError(
                f"repeat_policy must be an object for entry {entry_id} in {manifest_path}"
            )

        repeat_count = int(repeat_policy.get("repeat_count", 0))
        if repeat_count < 1:
            raise PromptCompositionError(
                f"repeat_policy.repeat_count must be >= 1 for entry {entry_id} in {manifest_path}"
            )
        if repeat_count > 1:
            justification = str(repeat_policy.get("justification", "")).strip()
            if not justification:
                raise PromptCompositionError(
                    f"repeat_policy.justification is required when repeat_count > 1 for entry {entry_id} in {manifest_path}"
                )


def _manifest_paths(manifests_dir: Path) -> List[Path]:
    if not manifests_dir.exists():
        raise PromptCompositionError(f"Composition manifest folder not found: {manifests_dir}")
    paths = sorted(manifests_dir.glob("*.composition.manifest.json"))
    if not paths:
        raise PromptCompositionError(f"No manifests found in: {manifests_dir}")
    return paths


def _compose_manifest(
    *,
    repo: Path,
    manifest_path: Path,
    manifest: Mapping[str, Any],
    allowlist: Set[str],
) -> Dict[str, Any]:
    template = str(manifest["template"])
    entries = list(manifest["entries"])

    compiled_parts: List[str] = []
    debug_parts: List[str] = []
    trace_segments: List[Dict[str, Any]] = []
    current_line = 1

    for entry in entries:
        entry_id = str(entry["entry_id"])
        semantic_id = str(entry["semantic_id"])
        source_path = repo / str(entry["source_path"])
        guard_level = str(entry["guard_level"])
        risk_class = str(entry["risk_class"])
        fragment_span = entry["source_prompt_span"]
        repeat_count = int(entry["repeat_policy"]["repeat_count"])

        if not source_path.exists():
            raise PromptCompositionError(
                f"Manifest {manifest_path} references missing source_path: {source_path}"
            )

        text = _read_fragment_text(source_path)
        source_line_count = _line_count(text)
        if int(fragment_span["line_end"]) > source_line_count:
            raise PromptCompositionError(
                f"Manifest {manifest_path} entry {entry_id} line_end exceeds source lines "
                f"({fragment_span['line_end']} > {source_line_count})"
            )

        for repeat_index in range(repeat_count):
            line_count = _line_count(text)
            compiled_line_start = current_line
            compiled_line_end = current_line + line_count - 1
            trace_segments.append(
                {
                    "compiled_line_start": compiled_line_start,
                    "compiled_line_end": compiled_line_end,
                    "fragment_path": str(entry["source_path"]),
                    "fragment_span": {
                        "line_start": int(fragment_span["line_start"]),
                        "line_end": int(fragment_span["line_end"]),
                    },
                    "manifest_entry_id": entry_id,
                    "semantic_id": semantic_id,
                    "guard_level": guard_level,
                    "risk_class": risk_class,
                    "repeat_index": repeat_index + 1,
                    "repeat_count": repeat_count,
                }
            )

            debug_parts.append(
                f"<!-- begin entry={entry_id} semantic={semantic_id} source={entry['source_path']} repeat={repeat_index + 1}/{repeat_count} -->\n"
            )
            debug_parts.append(text)
            debug_parts.append(f"<!-- end entry={entry_id} semantic={semantic_id} -->\n")
            compiled_parts.append(text)
            current_line = compiled_line_end + 1

    compiled_text = "".join(compiled_parts)
    debug_text = "".join(debug_parts)

    if "\r" in compiled_text:
        raise PromptCompositionError(
            f"Composed output contains CR/CRLF newlines for template {template}"
        )

    tokens = sorted(set(PLACEHOLDER_TOKEN_PATTERN.findall(compiled_text)))
    unknown_tokens = sorted([token for token in tokens if token not in allowlist])
    allowed_tokens = sorted([token for token in tokens if token in allowlist])
    if unknown_tokens:
        raise PromptCompositionError(
            f"Unknown placeholder tokens in {template}: {', '.join(unknown_tokens)}"
        )

    digest = hashlib.sha256(compiled_text.encode("utf-8")).hexdigest().upper()

    return {
        "template": template,
        "compiled_text": compiled_text,
        "debug_text": debug_text,
        "trace_segments": trace_segments,
        "placeholder_audit": {
            "template": template,
            "allowed_tokens": allowed_tokens,
            "unknown_tokens": unknown_tokens,
            "status": "pass",
        },
        "sha256": digest,
    }


def compose_prompt_templates(
    output_dir: Optional[Path] = None,
    *,
    write_reports: bool = True,
    enforce_checksums: bool = False,
) -> CompositionRunResult:
    repo = repo_root(Path(__file__).resolve())
    composition_root = _composition_root()
    manifests_dir = composition_root / "manifests"
    report_root = composition_root / "reports"

    target_dir = output_dir or (repo / "resources" / "prompt_templates")

    manifest_schema = _load_manifest_schema(composition_root)
    allowlist = _load_allowlist(composition_root)
    expected_checksums = _load_expected_checksums(composition_root)

    result = CompositionRunResult(output_dir=target_dir)

    for manifest_path in _manifest_paths(manifests_dir):
        manifest = _load_json(manifest_path, "composition manifest")
        _validate_manifest_schema(manifest_path, manifest, manifest_schema)
        _validate_manifest_contract(manifest_path, manifest)

        composed = _compose_manifest(
            repo=repo,
            manifest_path=manifest_path,
            manifest=manifest,
            allowlist=allowlist,
        )
        template = str(composed["template"])
        result.compiled_templates[template] = str(composed["compiled_text"])
        result.checksums[template] = str(composed["sha256"])
        result.traces[template] = list(composed["trace_segments"])
        result.placeholder_audits[template] = dict(composed["placeholder_audit"])

        _write_text_utf8_lf(target_dir / template, str(composed["compiled_text"]))

        if write_reports:
            _write_text_utf8_lf(
                report_root / "compiled_trace" / f"{template}.trace.json",
                json.dumps(
                    {
                        "template": template,
                        "segments": composed["trace_segments"],
                    },
                    ensure_ascii=True,
                    indent=2,
                )
                + "\n",
            )
            _write_text_utf8_lf(
                report_root / "placeholder_audit" / f"{template}.json",
                json.dumps(composed["placeholder_audit"], ensure_ascii=True, indent=2) + "\n",
            )
            _write_text_utf8_lf(
                report_root / "compiled_debug" / template,
                str(composed["debug_text"]),
            )

    if enforce_checksums and expected_checksums:
        missing = sorted([name for name in result.checksums.keys() if name not in expected_checksums])
        extra = sorted([name for name in expected_checksums.keys() if name not in result.checksums])
        mismatches = sorted(
            [
                name
                for name, digest in result.checksums.items()
                if expected_checksums.get(name, "").upper().strip() != digest
            ]
        )
        if missing or extra or mismatches:
            details: List[str] = []
            if missing:
                details.append(f"missing expected checksum entries: {', '.join(missing)}")
            if extra:
                details.append(f"unexpected expected-checksum entries: {', '.join(extra)}")
            if mismatches:
                details.append(f"checksum mismatch templates: {', '.join(mismatches)}")
            raise PromptCompositionError(
                "Source-of-truth checksum validation failed: " + "; ".join(details)
            )

    return result


def validate_prompt_composition_determinism(output_dir: Optional[Path] = None) -> Dict[str, str]:
    first = compose_prompt_templates(output_dir=output_dir, write_reports=False)
    second = compose_prompt_templates(output_dir=output_dir, write_reports=False)

    if first.checksums != second.checksums:
        raise PromptCompositionError("Prompt composition determinism check failed: checksum sets differ")

    for template, first_text in first.compiled_templates.items():
        second_text = second.compiled_templates.get(template, "")
        if first_text != second_text:
            raise PromptCompositionError(
                f"Prompt composition determinism check failed: content differs for {template}"
            )

    return dict(first.checksums)

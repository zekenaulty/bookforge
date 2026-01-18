import os
import time
import subprocess
from pathlib import Path

# Try to use pathspec for accurate .gitignore semantics; fallback to Git plumbing
try:
    from pathspec import PathSpec  # type: ignore
except Exception:  # pragma: no cover - optional dep
    PathSpec = None  # type: ignore

# ------------------------------------------------------------------------------
# 1) .gitignore loading and matching helpers
# ------------------------------------------------------------------------------

def load_gitignore_spec(root: Path):
    """Load a PathSpec for .gitignore if available.

    Falls back to None if pathspec is not installed or file is missing.
    """
    gitignore_path = root / ".gitignore"
    if PathSpec and gitignore_path.exists():
        with gitignore_path.open("r", encoding="utf-8", errors="ignore") as f:
            return PathSpec.from_lines("gitwildmatch", f)
    return None


def get_git_included_files(root: Path):
    """Return a set of repo-relative POSIX paths that are NOT ignored by Git.

    Uses `git ls-files -co --exclude-standard` to include tracked and
    untracked-but-not-ignored files. Returns an empty set if Git is not
    available or the directory is not a Git repository.
    """
    try:
        completed = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        files = set()
        for line in completed.stdout.splitlines():
            p = line.strip()
            if p:
                # Ensure POSIX style
                files.add(p.replace("\\", "/"))
        return files
    except Exception:
        return set()


def build_allowed_dirs_from_files(files):
    """From a set of POSIX file paths, compute all ancestor directories."""
    allowed = {""}
    for f in files:
        parts = f.split("/")
        cur = []
        for part in parts[:-1]:  # exclude filename
            cur.append(part)
            allowed.add("/".join(cur))
    return allowed

# ------------------------------------------------------------------------------
# 2) Additional excluded extensions (non-text formats)
# ------------------------------------------------------------------------------

EXCLUDED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp",
    ".tiff", ".zip", ".tar", ".gz", ".rar",
    ".7z", ".pdf", ".exe", ".dll", ".bin",
    ".iso"
}

def is_text_file(file_path: Path) -> bool:
    """
    Check if a file should be considered text based on extension.
    """
    return file_path.suffix.lower() not in EXCLUDED_EXTENSIONS

def should_ignore(rel_posix_path: str, is_dir: bool, spec, self_rel_posix: str, include_set):
    """Return True if the path should be ignored.

    Precedence:
    - Always ignore `arc.py` itself.
    - If a PathSpec is available, use it (.gitignore semantics).
    - Else, if a Git include set is provided, ignore anything not in the set
      (for files) and any directory not in allowed dirs.
    """
    # Always ignore arc.py itself
    if rel_posix_path == self_rel_posix:
        return True

    if spec is not None:
        test = rel_posix_path
        if is_dir and not test.endswith("/"):
            test += "/"
        return bool(spec.match_file(test))

    # Fallback: Git include set strategy
    if include_set is not None:
        if is_dir:
            # Directory is ignored if no included files live under it
            return rel_posix_path not in include_set
        else:
            return rel_posix_path not in include_set

    return False

# ------------------------------------------------------------------------------
# 3) Build directory structure as a tree string, honoring .gitignore
# ------------------------------------------------------------------------------

def get_directory_structure(directory: str) -> str:
    """
    Recursively get the directory structure as a tree-like string,
    skipping any folders/files that match the .gitignore-style patterns.
    """
    structure = []
    root_path = Path(directory).resolve()

    # Prefer Git for ignore resolution; fallback to local .gitignore parsing
    include_files = get_git_included_files(root_path)
    allowed_dirs = build_allowed_dirs_from_files(include_files) if include_files else None
    spec = None
    if not include_files:
        spec = load_gitignore_spec(root_path)

    # arc.py self relative path
    try:
        self_rel = Path(__file__).resolve().relative_to(root_path).as_posix()
    except Exception:
        self_rel = "arc.py"

    for current_root, dirs, files in os.walk(root_path):
        rel_dir = Path(current_root).resolve().relative_to(root_path).as_posix()
        if rel_dir == ".":
            rel_dir = ""

        # Prune directories according to ignore rules
        pruned_dirs = []
        kept_dirs = []
        for d in list(dirs):
            rel = (Path(rel_dir) / d).as_posix() if rel_dir else d
            if should_ignore(rel, True, spec, self_rel, allowed_dirs):
                pruned_dirs.append(d)
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        # If this directory itself should be ignored, skip adding entry
        if rel_dir and should_ignore(rel_dir, True, spec, self_rel, allowed_dirs):
            continue

        # Build tree indentation
        level = Path(current_root).resolve().relative_to(root_path).as_posix().count("/")
        indent = "  " * level
        basename = os.path.basename(current_root) if rel_dir else os.path.basename(root_path)
        structure.append(f"{indent}- {basename}/")

        sub_indent = "  " * (level + 1)
        for file in files:
            rel_file = (Path(rel_dir) / file).as_posix() if rel_dir else file
            if should_ignore(rel_file, False, spec, self_rel, include_files):
                continue
            structure.append(f"{sub_indent}- {file}")

    return "\n".join(structure)

# ------------------------------------------------------------------------------
# 4) Main function to create the Markdown snapshot
# ------------------------------------------------------------------------------

def create_markdown_snapshot(directory: str):
    """
    Create a Markdown file containing:
      - The .gitignore-style list of default exclusions
      - The directory structure (excluding matches)
      - The contents of included text files
    """
    # Prepare file name with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    dir_path = Path(directory).resolve()
    markdown_filename = f"{dir_path.name}.{timestamp}.md"
    markdown_filepath = dir_path.parent / markdown_filename

    with open(markdown_filepath, "w", encoding="utf-8") as md_file:
        # ----------------------------------------------------------------------
        # Write directory structure
        # ----------------------------------------------------------------------
        md_file.write("# Directory Snapshot\n\n")
        md_file.write("```plaintext\n")
        md_file.write(get_directory_structure(str(dir_path)))
        md_file.write("\n```\n\n")

        # ----------------------------------------------------------------------
        # Traverse files and add their content if not excluded
        # ----------------------------------------------------------------------
        # Prepare ignore machinery for content phase as well
        include_files = get_git_included_files(dir_path)
        allowed_dirs = build_allowed_dirs_from_files(include_files) if include_files else None
        spec = None
        if not include_files:
            spec = load_gitignore_spec(dir_path)

        try:
            self_rel = Path(__file__).resolve().relative_to(dir_path).as_posix()
        except Exception:
            self_rel = "arc.py"

        for root, dirs, files in os.walk(dir_path):
            rel_root = Path(root).resolve().relative_to(dir_path).as_posix()

            # Prune directories aggressively based on ignore rules
            dirs[:] = [
                d
                for d in dirs
                if not should_ignore((Path(rel_root) / d).as_posix() if rel_root else d, True, spec, self_rel, allowed_dirs)
            ]

            # Skip the folder itself if ignored
            if rel_root and should_ignore(rel_root, True, spec, self_rel, allowed_dirs):
                continue

            for file in files:
                file_path = Path(root) / file
                rel_path_str = file_path.resolve().relative_to(dir_path).as_posix()

                if should_ignore(rel_path_str, False, spec, self_rel, include_files):
                    continue

                if not is_text_file(file_path):
                    continue

                # Include text file content in the Markdown
                md_file.write(f"## {rel_path_str}\n\n")
                md_file.write(f"**Path:** `{file_path}`\n\n")
                md_file.write("```plaintext\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        md_file.write(f.read())
                except Exception as e:
                    md_file.write(f"Error reading file: {e}")
                md_file.write("\n```\n\n")

    print(f"Markdown snapshot created: {markdown_filepath}")

# ------------------------------------------------------------------------------
# Usage example
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    target_directory = "."  # or specify your directory
    create_markdown_snapshot(target_directory)

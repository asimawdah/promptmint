from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path

from .models import ProjectFile, ScanResult

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
}

DEFAULT_EXCLUDED_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".DS_Store",
    "promptmint-output.md",
}

DEPENDENCY_FILES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "composer.json",
    "composer.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "pubspec.yaml",
    "pubspec.lock",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".php": "php",
    ".dart": "dart",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
}

TEXT_SUFFIXES = set(LANGUAGE_BY_SUFFIX) | {
    ".txt",
    ".ini",
    ".cfg",
    ".conf",
    ".gitignore",
    ".dockerignore",
}


def scan_project(
    root: str | Path,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_file_bytes: int = 50_000,
) -> ScanResult:
    root_path = Path(root).resolve()
    exclude_patterns = exclude or []
    gitignore_patterns = _read_gitignore_patterns(root_path)
    include_patterns = include or []

    files: list[ProjectFile] = []
    dependency_files: list[ProjectFile] = []
    tree_paths: list[str] = []

    for path in sorted(root_path.rglob("*")):
        rel = path.relative_to(root_path).as_posix()
        if _is_excluded(path, rel, root_path, exclude_patterns, gitignore_patterns):
            continue
        if path.is_dir():
            tree_paths.append(rel + "/")
            continue
        if include_patterns and not _matches_any(rel, include_patterns):
            continue
        if not _is_text_file(path):
            continue
        if path.stat().st_size > max_file_bytes:
            continue

        project_file = ProjectFile(
            relative_path=rel,
            language=_language_for(path),
            content=path.read_text(encoding="utf-8", errors="replace"),
        )
        files.append(project_file)
        if path.name in DEPENDENCY_FILES:
            dependency_files.append(project_file)
        tree_paths.append(rel)

    return ScanResult(
        root=str(root_path),
        tree=_render_tree(tree_paths),
        files=files,
        dependency_files=dependency_files,
        git_diff=_git_diff(root_path),
    )


def _read_gitignore_patterns(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []

    patterns: list[str] = []
    for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
        pattern = line.strip()
        if not pattern or pattern.startswith("#") or pattern.startswith("!"):
            continue
        patterns.append(pattern.lstrip("/"))
    return patterns


def _is_excluded(
    path: Path,
    rel: str,
    root: Path,
    extra_patterns: list[str],
    gitignore_patterns: list[str] | None = None,
) -> bool:
    parts = set(path.relative_to(root).parts)
    if parts & DEFAULT_EXCLUDED_DIRS:
        return True
    if path.name in DEFAULT_EXCLUDED_FILES:
        return True
    patterns = extra_patterns + (gitignore_patterns or [])
    return _matches_any(rel, patterns)


def _matches_any(rel: str, patterns: list[str]) -> bool:
    path = Path(rel)
    for pattern in patterns:
        pattern = pattern.strip()
        if not pattern:
            continue
        normalized = pattern.rstrip("/")
        if fnmatch.fnmatch(rel, pattern) or path.match(pattern):
            return True
        if normalized and (rel == normalized or rel.startswith(normalized + "/")):
            return True
        if "**/" in pattern and fnmatch.fnmatch(rel, pattern.replace("**/", "")):
            return True
    return False


def _is_text_file(path: Path) -> bool:
    if path.name in DEPENDENCY_FILES or path.name in {"README", "LICENSE", "Makefile"}:
        return True
    if path.suffix in TEXT_SUFFIXES:
        return True
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return False
    return b"\0" not in chunk and path.suffix == ""


def _language_for(path: Path) -> str:
    if path.name == "Dockerfile":
        return "dockerfile"
    return LANGUAGE_BY_SUFFIX.get(path.suffix, "text")


def _render_tree(paths: list[str]) -> str:
    return "\n".join(paths)


def _git_diff(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "--no-ext-diff"],
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()

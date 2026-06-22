from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectFile:
    relative_path: str
    language: str
    content: str


@dataclass(frozen=True)
class ScanResult:
    root: str
    tree: str
    files: list[ProjectFile] = field(default_factory=list)
    dependency_files: list[ProjectFile] = field(default_factory=list)
    git_diff: str = ""

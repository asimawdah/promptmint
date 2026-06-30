from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromptMetadata:
    mode: str
    goal_present: bool
    file_count: int
    dependency_file_count: int
    includes_git_diff: bool
    includes_error_log: bool
    required_variables: tuple[str, ...] = field(default_factory=tuple)
    provided_variables: tuple[str, ...] = field(default_factory=tuple)

    def to_markdown_lines(self) -> list[str]:
        lines = [
            "## Prompt Metadata",
            "",
            f"- Mode: `{self.mode}`",
            f"- Goal provided: `{str(self.goal_present).lower()}`",
            f"- Files included: `{self.file_count}`",
            f"- Dependency files included: `{self.dependency_file_count}`",
            f"- Includes git diff: `{str(self.includes_git_diff).lower()}`",
            f"- Includes error log: `{str(self.includes_error_log).lower()}`",
        ]
        if self.required_variables:
            lines.append(f"- Required variables: `{', '.join(self.required_variables)}`")
        if self.provided_variables:
            lines.append(f"- Provided variables: `{', '.join(self.provided_variables)}`")
        lines.append("")
        return lines


def parse_variable_assignment(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise ValueError("variables must use NAME=VALUE format")
    name, assigned_value = value.split("=", 1)
    name = name.strip()
    if not name:
        raise ValueError("variable name cannot be empty")
    if not _is_safe_variable_name(name):
        raise ValueError("variable names may contain only letters, numbers, underscores, and dashes")
    return name, assigned_value.strip()


def parse_variable_assignments(values: list[str] | None) -> dict[str, str]:
    variables: dict[str, str] = {}
    for value in values or []:
        name, assigned_value = parse_variable_assignment(value)
        if name in variables:
            raise ValueError(f"duplicate prompt variable: {name}")
        variables[name] = assigned_value
    return variables


def normalize_required_variables(values: list[str] | None) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for name in _iter_required_variable_names(values):
        if not name:
            raise ValueError("required variable name cannot be empty")
        if not _is_safe_variable_name(name):
            raise ValueError("required variable names may contain only letters, numbers, underscores, and dashes")
        if name not in seen:
            normalized.append(name)
            seen.add(name)
    return tuple(normalized)


def missing_required_variables(required: tuple[str, ...], provided: dict[str, str]) -> list[str]:
    return [name for name in required if not provided.get(name)]


def _iter_required_variable_names(values: list[str] | None) -> list[str]:
    names: list[str] = []
    for value in values or []:
        parts = value.split(",")
        for part in parts:
            names.append(part.strip())
    return names


def _is_safe_variable_name(name: str) -> bool:
    return all(char.isalnum() or char in {"_", "-"} for char in name)

from __future__ import annotations

from dataclasses import dataclass, field


PROMPT_METADATA_SCHEMA_VERSION = 1


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
    schema_version: int = PROMPT_METADATA_SCHEMA_VERSION

    @property
    def validation_status(self) -> str:
        missing = set(self.required_variables) - set(self.provided_variables)
        return "incomplete" if missing else "complete"

    def to_markdown_lines(self) -> list[str]:
        lines = [
            "## Prompt Metadata",
            "",
            f"- Schema version: `{self.schema_version}`",
            f"- Mode: `{self.mode}`",
            f"- Goal provided: `{str(self.goal_present).lower()}`",
            f"- Files included: `{self.file_count}`",
            f"- Dependency files included: `{self.dependency_file_count}`",
            f"- Includes git diff: `{str(self.includes_git_diff).lower()}`",
            f"- Includes error log: `{str(self.includes_error_log).lower()}`",
            f"- Variable validation: `{self.validation_status}`",
            f"- Required variable count: `{len(self.required_variables)}`",
            f"- Provided variable count: `{len(self.provided_variables)}`",
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
    name = canonical_prompt_variable_name(name)
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
        canonical_name = canonical_prompt_variable_name(name, required=True)
        if canonical_name not in seen:
            normalized.append(canonical_name)
            seen.add(canonical_name)
    return tuple(normalized)


def missing_required_variables(required: tuple[str, ...], provided: dict[str, str]) -> list[str]:
    return [name for name in required if not provided.get(name)]


def canonical_prompt_variable_name(name: str, *, required: bool = False) -> str:
    """Return a stable lowercase metadata variable name or raise ValueError."""

    stripped_name = name.strip()
    label = "required variable name" if required else "variable name"
    if not stripped_name:
        raise ValueError(f"{label} cannot be empty")
    if not _is_safe_variable_name(stripped_name):
        plural_label = "required variable names" if required else "variable names"
        raise ValueError(
            f"{plural_label} must start with a letter or number and may contain only letters, numbers, underscores, and dashes"
        )
    return stripped_name.lower()


def _iter_required_variable_names(values: list[str] | None) -> list[str]:
    names: list[str] = []
    for value in values or []:
        parts = value.split(",")
        for part in parts:
            names.append(part.strip())
    return names


def _is_safe_variable_name(name: str) -> bool:
    if not name or not name[0].isalnum():
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in name)

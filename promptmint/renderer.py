from __future__ import annotations

from .metadata import PromptMetadata
from .models import ProjectFile, ScanResult

MODE_REQUESTS = {
    "debug": "Please find the root cause, explain it briefly, and suggest the smallest safe fix.",
    "review": "Please review this code for bugs, security issues, performance, and maintainability.",
    "explain": "Please explain how this project works, focusing on the included files.",
    "refactor": "Please suggest a safe refactor plan and identify the smallest first change.",
}


def render_context_pack(
    scan: ScanResult,
    goal: str | None = None,
    mode: str = "debug",
    error_log: str | None = None,
    required_variables: tuple[str, ...] = (),
    prompt_variables: dict[str, str] | None = None,
) -> str:
    mode = mode if mode in MODE_REQUESTS else "debug"
    prompt_variables = prompt_variables or {}
    sections = ["# Project Context Pack", ""]
    sections.extend(["## Goal", goal or "Analyze this project context and help with the task.", ""])
    sections.extend([f"## {mode.title()} Request", MODE_REQUESTS[mode], ""])
    sections.extend(
        PromptMetadata(
            mode=mode,
            goal_present=bool(goal),
            file_count=len(scan.files),
            dependency_file_count=len(scan.dependency_files),
            includes_git_diff=bool(scan.git_diff),
            includes_error_log=bool(error_log),
            required_variables=required_variables,
            provided_variables=tuple(sorted(prompt_variables)),
        ).to_markdown_lines()
    )
    if prompt_variables:
        sections.append("## Prompt Variables")
        sections.append("")
        for name in sorted(prompt_variables):
            sections.append(f"- `{name}`: {prompt_variables[name]}")
        sections.append("")
    sections.extend(["## Project Root", f"`{scan.root}`", ""])
    sections.extend(["## Project Tree", "```text", scan.tree or "(empty)", "```", ""])

    if scan.dependency_files:
        sections.append("## Dependency / Manifest Files")
        sections.append("")
        for file in scan.dependency_files:
            sections.extend(_render_file(file))

    if scan.git_diff:
        sections.extend(["## Git Diff", "```diff", scan.git_diff, "```", ""])

    relevant_files = [
        file for file in scan.files
        if all(file.relative_path != dep.relative_path for dep in scan.dependency_files)
    ]
    if relevant_files:
        sections.append("## Relevant Files")
        sections.append("")
        for file in relevant_files:
            sections.extend(_render_file(file))

    if error_log:
        sections.extend(["## Error Log", "```text", error_log.strip(), "```", ""])

    sections.extend(["## Final Instruction", MODE_REQUESTS[mode], ""])
    return "\n".join(sections).rstrip() + "\n"


def _render_file(file: ProjectFile) -> list[str]:
    return [
        f"### `{file.relative_path}`",
        f"```{file.language}",
        file.content.rstrip(),
        "```",
        "",
    ]

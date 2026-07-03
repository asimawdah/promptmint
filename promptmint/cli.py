from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from json import JSONDecodeError
from pathlib import Path

from .metadata import (
    canonical_prompt_variable_name,
    missing_required_variables,
    normalize_required_variables,
    parse_variable_assignments,
)
from .renderer import MODE_REQUESTS, render_context_pack
from .scanner import scan_project
from .templates import PromptTemplate, get_template, list_categories, list_templates, render_template_goal
from .tokens import estimate_tokens

ALLOWED_OUTPUT_SUFFIXES = {".md", ".markdown"}
DEFAULT_TEMPLATE_CATEGORY = "all"
TEMPLATE_LIST_FORMATS = ("text", "json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptmint",
        description="Turn any codebase into an AI-ready Markdown prompt pack.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Project directory to scan")
    parser.add_argument("-g", "--goal", default=None, help="Task goal to include in the prompt")
    parser.add_argument("-m", "--mode", choices=sorted(MODE_REQUESTS), default="debug", help="Prompt mode")
    parser.add_argument("-e", "--error", dest="error_file", help="Path to an error log to include")
    parser.add_argument("-i", "--include", action="append", default=[], help="Glob to include; can be repeated")
    parser.add_argument("-x", "--exclude", action="append", default=[], help="Glob to exclude; can be repeated")
    parser.add_argument("-o", "--output", default="promptmint-output.md", help="Output Markdown file")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy output to clipboard if a clipboard tool is available")
    parser.add_argument("-s", "--max-file-bytes", type=_positive_int, default=50_000, help="Skip files larger than this size")
    parser.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="NAME",
        help="Required prompt variable name; can be repeated and must be supplied with --var",
    )
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Prompt variable metadata to include in the generated pack; can be repeated",
    )
    parser.add_argument(
        "--vars-file",
        action="append",
        default=[],
        metavar="PATH",
        help="JSON object containing prompt variable metadata; can be repeated",
    )
    parser.add_argument("--list-templates", action="store_true", help="List starter prompt templates and exit")
    parser.add_argument("--show-template", help="Show full details for one starter prompt template and exit")
    parser.add_argument("--template", help="Use a starter prompt template by id")
    parser.add_argument("--template-category", default=DEFAULT_TEMPLATE_CATEGORY, help="Filter --list-templates by category")
    parser.add_argument("--template-search", help="Search template ids, titles, descriptions, variables, and prompt text")
    parser.add_argument(
        "--template-format",
        choices=TEMPLATE_LIST_FORMATS,
        default="text",
        help="Output format for --list-templates or --show-template",
    )
    parser.add_argument(
        "--template-var",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Template placeholder value; can be repeated with --template or --show-template",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_templates and args.show_template:
        parser.error("Use either --list-templates or --show-template, not both.")

    if args.list_templates:
        if args.template_var:
            parser.error("--template-var can only be used with --template or --show-template")
        _print_templates(args.template_category, args.template_search, args.template_format, parser)
        return 0

    if args.show_template:
        _print_template_detail(args.show_template, args.template_var, args.template_format, parser)
        return 0

    root = Path(args.path).resolve()
    if not root.exists():
        parser.error(f"Project path does not exist: {root}")
    if not root.is_dir():
        parser.error(f"Project path must be a directory: {root}")

    try:
        required_variables = normalize_required_variables(args.require)
        prompt_variables = _merge_prompt_variables(
            _load_prompt_variable_files(args.vars_file),
            parse_variable_assignments(args.var),
        )
        output_path = _resolve_output_path(args.output)
    except ValueError as exc:
        parser.error(str(exc))

    missing_variables = missing_required_variables(required_variables, prompt_variables)
    if missing_variables:
        parser.error("Missing required prompt variables: " + ", ".join(missing_variables))

    error_log = None
    if args.error_file:
        error_path = Path(args.error_file).resolve()
        if not error_path.exists():
            parser.error(f"Error log does not exist: {error_path}")
        if not error_path.is_file():
            parser.error(f"Error log must be a file: {error_path}")
        error_log = error_path.read_text(encoding="utf-8", errors="replace")

    template = None
    goal = args.goal
    if args.template:
        try:
            template = get_template(args.template)
        except KeyError as exc:
            parser.error(str(exc))
        template_values = _parse_template_vars(args.template_var, parser)
        _validate_template_values(template, template_values, parser)
        template_goal = render_template_goal(template, template_values)
        goal = f"{args.goal}\n\n{template_goal}" if args.goal else template_goal
    elif args.template_var:
        parser.error("--template-var can only be used with --template or --show-template")

    exclude_patterns = _exclude_generated_output(args.exclude, root, output_path)
    scan = scan_project(
        root,
        include=args.include,
        exclude=exclude_patterns,
        max_file_bytes=args.max_file_bytes,
    )
    output = render_context_pack(
        scan,
        goal=goal,
        mode=args.mode,
        error_log=error_log,
        required_variables=required_variables,
        prompt_variables=prompt_variables,
        template=template,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")

    if args.copy:
        _copy_to_clipboard(output)

    print(f"Created: {output_path}")
    print(f"Tokens estimate: {estimate_tokens(output):,}")
    print(f"Files included: {len(scan.files)}")
    if template:
        print(f"Template: {template.id}")
    return 0


def _print_templates(category: str, query: str | None, output_format: str, parser: argparse.ArgumentParser) -> None:
    normalized_category = _normalize_template_category(category, parser)
    templates = list_templates(category=normalized_category, query=query)
    if output_format == "json":
        _print_templates_json(templates, normalized_category, query)
        return
    if not templates:
        print("No templates found.")
        return

    print("Available template categories: " + ", ".join(_available_template_categories()))
    current_category = None
    for template in templates:
        if template.category != current_category:
            current_category = template.category
            print(f"\n[{current_category}]")
        variables = ", ".join(template.variables) if template.variables else "none"
        print(f"- {template.id}: {template.title}")
        print(f"  {template.description}")
        print(f"  variables: {variables}")


def _print_template_detail(
    template_id: str,
    raw_values: list[str],
    output_format: str,
    parser: argparse.ArgumentParser,
) -> None:
    try:
        template = get_template(template_id)
    except KeyError as exc:
        parser.error(str(exc))

    values = _parse_template_vars(raw_values, parser)
    _validate_template_values(template, values, parser)
    rendered_goal = render_template_goal(template, values)
    missing = _missing_template_variables(template, values)

    if output_format == "json":
        payload = _template_to_detail_dict(template, values, rendered_goal, missing)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    variables = ", ".join(template.variables) if template.variables else "none"
    print(f"Template: {template.id}")
    print(f"Title: {template.title}")
    print(f"Category: {template.category}")
    print(f"Description: {template.description}")
    print(f"Variables: {variables}")
    print(f"Example output: {template.example_output}")
    print("\nPrompt:")
    print(template.prompt)
    print("\nRendered goal preview:")
    print(rendered_goal)
    if missing:
        print("\nMissing variables: " + ", ".join(missing))


def _print_templates_json(templates: list[PromptTemplate], category: str | None, query: str | None) -> None:
    payload = {
        "schema_version": 1,
        "filters": {"category": category or DEFAULT_TEMPLATE_CATEGORY, "query": query or ""},
        "available_categories": _available_template_categories(),
        "count": len(templates),
        "templates": [_template_to_dict(template) for template in templates],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def _template_to_dict(template: PromptTemplate) -> dict[str, object]:
    return {
        "id": template.id,
        "category": template.category,
        "title": template.title,
        "description": template.description,
        "variables": list(template.variables),
        "example_output": template.example_output,
    }


def _template_to_detail_dict(
    template: PromptTemplate,
    values: dict[str, str],
    rendered_goal: str,
    missing: list[str],
) -> dict[str, object]:
    payload = _template_to_dict(template)
    payload.update({
        "schema_version": 1,
        "prompt": template.prompt,
        "provided_variables": values,
        "missing_variables": missing,
        "rendered_goal": rendered_goal,
    })
    return payload


def _normalize_template_category(category: str, parser: argparse.ArgumentParser) -> str | None:
    normalized = category.casefold().strip()
    if normalized == DEFAULT_TEMPLATE_CATEGORY:
        return None

    categories = list_categories()
    if normalized not in categories:
        parser.error(
            "Unknown template category "
            f"'{category}'. Available categories: {', '.join(_available_template_categories())}"
        )
    return normalized


def _available_template_categories() -> list[str]:
    return [DEFAULT_TEMPLATE_CATEGORY, *list_categories()]


def _parse_template_vars(raw_values: list[str], parser: argparse.ArgumentParser) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_value in raw_values:
        if "=" not in raw_value:
            parser.error(f"Template variable must use KEY=VALUE format: {raw_value}")
        key, value = raw_value.split("=", 1)
        try:
            key = canonical_prompt_variable_name(key.strip())
        except ValueError as exc:
            parser.error(str(exc))
        if key in values:
            parser.error(f"Duplicate template variable '{key}'. Provide each --template-var key once.")
        values[key] = value
    return values


def _validate_template_values(template: PromptTemplate, values: dict[str, str], parser: argparse.ArgumentParser) -> None:
    allowed = set(template.variables)
    unknown = sorted(set(values) - allowed)
    if unknown:
        expected = ", ".join(template.variables) if template.variables else "none"
        parser.error(
            f"Unknown variable for template '{template.id}': {', '.join(unknown)}. "
            f"Expected variables: {expected}"
        )


def _missing_template_variables(template: PromptTemplate, values: dict[str, str]) -> list[str]:
    return [variable for variable in template.variables if variable not in values]


def _load_prompt_variable_files(paths: list[str] | None) -> dict[str, str]:
    variables: dict[str, str] = {}
    for value in paths or []:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"Prompt variables file does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Prompt variables file must be a file: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except JSONDecodeError as exc:
            raise ValueError(f"Prompt variables file must contain valid JSON: {path}: {exc.msg}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Prompt variables file must contain a JSON object: {path}")
        variables = _merge_prompt_variables(variables, _parse_prompt_variable_file_data(data, path))
    return variables


def _parse_prompt_variable_file_data(data: dict[str, object], path: Path) -> dict[str, str]:
    variables: dict[str, str] = {}
    for raw_name, raw_value in data.items():
        name = canonical_prompt_variable_name(raw_name)
        if not isinstance(raw_value, str):
            raise ValueError(f"Prompt variable '{name}' in {path} must be a string")
        variables = _merge_prompt_variables(variables, {name: raw_value.strip()})
    return variables


def _merge_prompt_variables(base: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    duplicates = sorted(set(base).intersection(incoming))
    if duplicates:
        raise ValueError("duplicate prompt variable: " + ", ".join(duplicates))
    merged = dict(base)
    merged.update(incoming)
    return merged


def _resolve_output_path(value: str) -> Path:
    output_path = Path(value).expanduser().resolve()
    if output_path.exists() and output_path.is_dir():
        raise ValueError(f"Output path must be a Markdown file, not a directory: {output_path}")
    if output_path.suffix.lower() not in ALLOWED_OUTPUT_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_OUTPUT_SUFFIXES))
        raise ValueError(f"Output file must use a Markdown extension ({allowed}): {output_path}")
    if output_path.parent.exists() and not output_path.parent.is_dir():
        raise ValueError(f"Output parent path must be a directory: {output_path.parent}")
    return output_path


def _exclude_generated_output(exclude_patterns: list[str], root: Path, output_path: Path) -> list[str]:
    """Return user exclusions plus the output file when it lives inside the scan root."""

    patterns = list(exclude_patterns)
    try:
        output_rel = output_path.relative_to(root).as_posix()
    except ValueError:
        return patterns
    if output_rel and output_rel not in patterns:
        patterns.append(output_rel)
    return patterns


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return number


def _copy_to_clipboard(text: str) -> None:
    commands = [
        (["pbcopy"], None),
        (["xclip", "-selection", "clipboard"], None),
        (["xsel", "--clipboard", "--input"], None),
        (["wl-copy"], None),
    ]
    for command, _ in commands:
        if shutil.which(command[0]):
            subprocess.run(command, input=text, text=True, check=False)
            print("Copied to clipboard")
            return
    print("Clipboard tool not found; install pbcopy, xclip, xsel, or wl-copy.", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

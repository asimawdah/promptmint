from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .metadata import missing_required_variables, normalize_required_variables, parse_variable_assignments
from .renderer import MODE_REQUESTS, render_context_pack
from .scanner import scan_project
from .tokens import estimate_tokens

ALLOWED_OUTPUT_SUFFIXES = {".md", ".markdown"}


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        parser.error(f"Project path does not exist: {root}")
    if not root.is_dir():
        parser.error(f"Project path must be a directory: {root}")

    try:
        required_variables = normalize_required_variables(args.require)
        prompt_variables = parse_variable_assignments(args.var)
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

    scan = scan_project(
        root,
        include=args.include,
        exclude=args.exclude,
        max_file_bytes=args.max_file_bytes,
    )
    output = render_context_pack(
        scan,
        goal=args.goal,
        mode=args.mode,
        error_log=error_log,
        required_variables=required_variables,
        prompt_variables=prompt_variables,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")

    if args.copy:
        _copy_to_clipboard(output)

    print(f"Created: {output_path}")
    print(f"Tokens estimate: {estimate_tokens(output):,}")
    print(f"Files included: {len(scan.files)}")
    return 0


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
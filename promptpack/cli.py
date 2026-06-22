from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from .renderer import MODE_REQUESTS, render_context_pack
from .scanner import scan_project
from .tokens import estimate_tokens


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptpack",
        description="Turn any codebase into an AI-ready Markdown prompt pack.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Project directory to scan")
    parser.add_argument("--goal", default=None, help="Task goal to include in the prompt")
    parser.add_argument("--mode", choices=sorted(MODE_REQUESTS), default="debug", help="Prompt mode")
    parser.add_argument("--error", dest="error_file", help="Path to an error log to include")
    parser.add_argument("--include", action="append", default=[], help="Glob to include; can be repeated")
    parser.add_argument("--exclude", action="append", default=[], help="Glob to exclude; can be repeated")
    parser.add_argument("--output", default="promptpack-output.md", help="Output Markdown file")
    parser.add_argument("--copy", action="store_true", help="Copy output to clipboard if a clipboard tool is available")
    parser.add_argument("--max-file-bytes", type=int, default=50_000, help="Skip files larger than this size")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    error_log = None
    if args.error_file:
        error_log = Path(args.error_file).read_text(encoding="utf-8", errors="replace")

    scan = scan_project(
        root,
        include=args.include,
        exclude=args.exclude,
        max_file_bytes=args.max_file_bytes,
    )
    output = render_context_pack(scan, goal=args.goal, mode=args.mode, error_log=error_log)
    output_path = Path(args.output).resolve()
    output_path.write_text(output, encoding="utf-8")

    if args.copy:
        _copy_to_clipboard(output)

    print(f"Created: {output_path}")
    print(f"Tokens estimate: {estimate_tokens(output):,}")
    print(f"Files included: {len(scan.files)}")
    return 0


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

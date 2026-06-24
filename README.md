# PromptMint

Turn any codebase into an AI-ready prompt.

PromptMint scans your project, collects useful source files, dependency manifests, git diff, and optional error logs, then generates a clean Markdown context pack you can paste into ChatGPT, Claude, Gemini, or any coding agent.

## Why?

Copying files into AI chats is slow and messy. PromptMint gives you one command that creates a structured, safe context file for debugging, code review, refactoring, and project explanation.

## Install

```bash
pip install promptmint
```

## Install locally for development

```bash
git clone https://github.com/asimawdah/promptmint.git
cd promptmint
python3 -m pip install -e .
```

## Usage

```bash
promptmint -g "Fix this bug" -m debug
```

```bash
promptmint --goal "Review this PR" --mode review --output review-context.md
```

```bash
promptmint --goal "Explain this project" --mode explain
```

```bash
promptmint -e error.log -m debug -c
```

## CLI Shortcuts

- `-g`, `--goal`: task goal
- `-m`, `--mode`: prompt mode
- `-e`, `--error`: error log file
- `-i`, `--include`: include glob, repeatable
- `-x`, `--exclude`: exclude glob, repeatable
- `-o`, `--output`: output Markdown file
- `-c`, `--copy`: copy output to clipboard
- `-s`, `--max-file-bytes`: skip files larger than this size

## Modes

- `debug`: root cause + smallest safe fix
- `review`: bugs, security, performance, maintainability
- `explain`: explain how the project works
- `refactor`: safe refactor plan

## What it includes

- Project tree
- Dependency/manifest files like `package.json`, `pyproject.toml`, `composer.json`, `go.mod`, `pubspec.yaml`
- Git diff, if available
- Text source files
- Optional error log
- Final instruction tailored to the selected mode

## What it ignores by default

- `.git`, `node_modules`, `vendor`, `dist`, `build`, virtual environments, caches
- `.env` files
- Binary files
- Large files over 50KB by default

## Safety notes

PromptMint is designed to avoid common noisy or sensitive paths, but you should still review the generated Markdown before pasting it into an AI tool.

Recommended safe workflow:

1. Run PromptMint with a narrow include pattern first.
2. Open the generated Markdown and check for secrets, tokens, private URLs, or customer data.
3. Add extra `--exclude` patterns for anything that should never leave your machine.
4. Commit a project-level `.gitignore` and keep secrets in ignored `.env` files.

Example:

```bash
promptmint . \
  --include "src/**/*.py" \
  --exclude "**/secrets/**" \
  --exclude "**/*.pem" \
  --goal "Review this module safely"
```

## Examples

```bash
promptmint . --include "src/**/*.py" --goal "Find the bug"
```

```bash
promptmint . --exclude "tests/fixtures/**" --max-file-bytes 20000
```

## Development

```bash
python3 -m unittest discover -s tests -v
```

## Roadmap

- [x] Markdown context pack generator
- [x] Project tree + file scanner
- [x] Dependency manifest detection
- [x] Git diff inclusion
- [x] Debug/review/explain/refactor modes
- [ ] Better `.gitignore` support
- [ ] Token budget smart trimming
- [ ] Interactive file picker
- [ ] JSON output
- [ ] MCP server integration

## License

MIT

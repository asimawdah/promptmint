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
git clone https://github.com/YOUR_USERNAME/promptmint.git
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
- Files and directories ignored by root `.gitignore` patterns

## `.gitignore` support

PromptMint reads the root `.gitignore` file and skips matching files before it builds the context pack. This keeps generated prompts smaller and avoids sending common local files such as logs, build outputs, caches, and ignored secrets.

Supported pattern types include:

- file globs like `*.log`
- directory ignores like `tmp/`
- exact root-relative files like `secret.txt`
- path patterns supported by Python glob matching

Negated patterns such as `!keep.log` are currently ignored and may be added later.

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
- [x] Better `.gitignore` support
- [ ] Token budget smart trimming
- [ ] Interactive file picker
- [ ] JSON output
- [ ] MCP server integration

## License

MIT

# PromptPack

Turn any codebase into an AI-ready prompt.

PromptPack scans your project, collects useful source files, dependency manifests, git diff, and optional error logs, then generates a clean Markdown context pack you can paste into ChatGPT, Claude, Gemini, or any coding agent.

## Why?

Copying files into AI chats is slow and messy. PromptPack gives you one command that creates a structured, safe context file for debugging, code review, refactoring, and project explanation.

## Install locally

```bash
git clone https://github.com/YOUR_USERNAME/promptpack.git
cd promptpack
python3 -m pip install -e .
```

## Usage

```bash
promptpack --goal "Fix this bug" --mode debug
```

```bash
promptpack --goal "Review this PR" --mode review --output review-context.md
```

```bash
promptpack --goal "Explain this project" --mode explain
```

```bash
promptpack --error error.log --mode debug --copy
```

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

## Examples

```bash
promptpack . --include "src/**/*.py" --goal "Find the bug"
```

```bash
promptpack . --exclude "tests/fixtures/**" --max-file-bytes 20000
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

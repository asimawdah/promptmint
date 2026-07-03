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

Add structured metadata and required prompt variables when the output must be traceable to a ticket, feature area, or review scope:

```bash
promptmint . \
  --goal "Review the login flow" \
  --mode review \
  --require ticket \
  --var ticket=PM-123 \
  --var area=login \
  --output reports/PM-123-review.md
```

For repeatable scripts, store non-sensitive prompt metadata in a JSON object and load it with `--vars-file`:

```json
{
  "ticket": "PM-123",
  "area": "login",
  "reviewer": "asim"
}
```

```bash
promptmint . \
  --goal "Review the login flow" \
  --mode review \
  --require ticket,area \
  --vars-file prompt-vars.json \
  --output reports/PM-123-review.md
```

If a required variable is missing or empty, PromptMint exits before writing an incomplete context pack. Duplicate variable names are also rejected so metadata cannot be overwritten accidentally. Variable names are canonicalized to lowercase, so case variants like `Ticket` and `ticket` are treated as the same workflow field. Secret-like metadata names such as password, token, private-key, credential, or api-key are rejected because `--var` and `--vars-file` are for workflow context, not sensitive values.

## Template Library

PromptMint includes 25 starter templates across coding, debugging, product planning, writing, and learning.

List all templates:

```bash
promptmint --list-templates
```

Filter templates by category or search text:

```bash
promptmint --list-templates --template-category coding
promptmint --list-templates --template-search security
promptmint --list-templates --template-search "security auth logging"
```

Multi-word template search requires every term to match template metadata or prompt text.

Use JSON output for scripts, CI checks, or editor integrations:

```bash
promptmint --list-templates --template-category debugging --template-format json
```

Inspect one template before scanning a project:

```bash
promptmint --show-template bug-root-cause
promptmint --show-template bug-root-cause --template-format json
```

Preview template placeholders with `--template-var`:

```bash
promptmint --show-template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard"
```

Use a template while generating a context pack:

```bash
promptmint . \
  --template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard" \
  --output debug-context.md
```

Use `--template-var` for template placeholders and keep `--var`, `--require`, and `--vars-file` for prompt metadata:

```bash
promptmint . \
  --template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard" \
  --require ticket \
  --var ticket=BUG-18 \
  --output reports/BUG-18-debug.md
```

The generated context pack includes the selected template metadata, rendered template goal, prompt metadata, project files, and final mode-specific instruction.

See [Prompt Template Library](docs/PROMPT_TEMPLATES.md) for the full workflow and guidance for adding new templates.

## CLI Shortcuts

- `-g`, `--goal`: task goal
- `-m`, `--mode`: prompt mode
- `-e`, `--error`: error log file
- `-i`, `--include`: include glob, repeatable
- `-x`, `--exclude`: exclude glob, repeatable
- `-o`, `--output`: output Markdown file; must end in `.md` or `.markdown`; missing parent directories are created; existing output files inside the scanned project are excluded from the scan
- `-c`, `--copy`: copy output to clipboard if a clipboard tool is available
- `-s`, `--max-file-bytes`: skip files larger than this size
- `--require`: required prompt variable name; can be repeated; comma-separated shorthand is supported; names are canonicalized to lowercase and cannot look like secrets
- `--var`: prompt variable metadata in `NAME=VALUE` format; can be repeated, but each canonicalized name must be unique and non-sensitive
- `--vars-file`: JSON object containing prompt variable metadata; can be repeated; keys follow the same name rules as `--var`, values must be strings, and duplicate canonical names are rejected across files and inline variables
- `--list-templates`: list starter prompt templates
- `--show-template`: show full details for one starter prompt template
- `--template`: use a starter prompt template by id
- `--template-category`: filter listed templates by category
- `--template-search`: search template metadata and prompt text; every word must match
- `--template-format`: choose `text` or `json` for template listing/detail output
- `--template-var`: template placeholder value in `NAME=VALUE` format; can be repeated with `--template` or `--show-template`

## Modes

- `debug`: root cause + smallest safe fix
- `review`: bugs, security, performance, maintainability
- `explain`: explain how the project works
- `refactor`: safe refactor plan

## Prompt metadata

Every generated context pack now includes a `Prompt Metadata` section with:

- schema version for future-compatible metadata changes
- selected mode
- whether a goal was provided
- included file and dependency counts
- whether git diff or error logs are present
- variable validation status and variable counts
- required and provided variable names when supplied

Use metadata for repeatable workflows where the generated prompt should stay connected to an issue, PR, feature area, reviewer, or environment.

Recommended variable names:

- `ticket` for an issue or task id
- `pr` for a pull request id
- `area` for the affected feature or module
- `env` for the runtime environment
- `owner` for the person or team responsible for follow-up

Avoid using `--var` or `--vars-file` for secrets, tokens, credentials, private keys, or passwords. PromptMint rejects variable names that look sensitive, but generated context packs should still be reviewed before sharing.

See [Prompt Metadata and Validation](docs/PROMPT_METADATA.md) for details about schema fields, canonical variable names, required-variable validation, secret-like name rejection, safe Markdown rendering, JSON variable files, and output path rules.

## What it includes

- Project tree
- Dependency/manifest files like `package.json`, `pyproject.toml`, `composer.json`, `go.mod`, `pubspec.yaml`
- Git diff, if available
- Text source files
- Optional error log
- Prompt metadata and variables
- Selected prompt template metadata when `--template` is used
- Final instruction tailored to the selected mode

## What it ignores by default

- `.git`, `node_modules`, `vendor`, `dist`, `build`, virtual environments, caches
- `.env` files
- Binary files
- Large files over 50KB by default
- The generated `--output` file when it already exists inside the scanned project

## Safety notes

PromptMint is designed to avoid common noisy or sensitive paths, but you should still review the generated Markdown before pasting it into an AI tool.

Recommended safe workflow:

1. Run PromptMint with a narrow include pattern first.
2. Open the generated Markdown and check for secrets, tokens, private URLs, or customer data.
3. Add extra `--exclude` patterns for anything that should never leave your machine.
4. Write the pack to an explicit Markdown path such as `reports/BUG-18-debug.md`.
5. Re-run to the same output path safely when needed; PromptMint excludes that generated file from the scan.
6. Commit a project-level `.gitignore` and keep secrets in ignored `.env` files.

Example:

```bash
promptmint . \
  --include "src/**/*.py" \
  --exclude "**/secrets/**" \
  --exclude "**/*.pem" \
  --goal "Review this module safely" \
  --output reports/module-review.md
```

## Examples

```bash
promptmint . --include "src/**/*.py" --goal "Find the bug" --output reports/bug-context.md
```

```bash
promptmint . --exclude "tests/fixtures/**" --max-file-bytes 20000 --output reports/trimmed-context.markdown
```

```bash
promptmint . --mode debug --require ticket --var ticket=BUG-18 --var area=scanner --output reports/BUG-18-debug.md
```

```bash
promptmint . --mode review --require ticket,area --vars-file prompt-vars.json --output reports/review-context.md
```

```bash
promptmint . --template code-review --template-var focus_area=authentication --output reports/auth-review.md
```

See [Prompt Output Examples](docs/prompt-output-examples.md) for sample Markdown packs generated by debug, review, explain, and refactor modes.

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
- [x] Prompt metadata and required variable validation
- [x] Canonical prompt variable names
- [x] Secret-like prompt metadata name rejection
- [x] JSON prompt variable files
- [x] Categorized prompt template library
- [ ] Better `.gitignore` support
- [ ] Token budget smart trimming
- [ ] Interactive file picker
- [ ] JSON output
- [ ] MCP server integration

## License

MIT

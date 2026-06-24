# Prompt Output Examples

PromptMint creates a Markdown context pack that is meant to be pasted into an AI coding assistant. The exact output depends on your project files, selected mode, goal, and optional error log.

These examples show the shape of the generated output so users can understand what they will get before running the CLI.

## Debug mode example

Command:

```bash
promptmint . --mode debug --goal "Fix the failing login test" --error error.log --output debug-context.md
```

Example output excerpt:

```markdown
# PromptMint Context Pack

## Goal

Fix the failing login test

## Mode

debug

## Project tree

```text
.
├── pyproject.toml
├── src/app/auth.py
└── tests/test_auth.py
```

## Dependency manifests

### pyproject.toml

```toml
[project]
name = "example-app"
requires-python = ">=3.10"
```

## Error log

```text
AssertionError: expected 200, got 401
```

## Included files

### src/app/auth.py

```python
def login(username, password):
    ...
```

### tests/test_auth.py

```python
def test_login_success():
    ...
```

## Request

Find the root cause and propose the smallest safe fix. Explain the failing path before changing code.
```

## Review mode example

Command:

```bash
promptmint . --mode review --goal "Review this pull request" --include "src/**/*.py" --output review-context.md
```

Example output excerpt:

```markdown
# PromptMint Context Pack

## Goal

Review this pull request

## Mode

review

## Git diff

```diff
diff --git a/src/app/service.py b/src/app/service.py
+def delete_user(user_id):
+    db.delete(user_id)
```

## Included files

### src/app/service.py

```python
class UserService:
    ...
```

## Request

Review the code for bugs, security risks, performance problems, and maintainability issues. Focus on practical findings.
```

## Explain mode example

Command:

```bash
promptmint . --mode explain --goal "Explain this project to a new contributor" --output explain-context.md
```

Example output excerpt:

```markdown
# PromptMint Context Pack

## Goal

Explain this project to a new contributor

## Mode

explain

## Project tree

```text
.
├── README.md
├── promptmint/cli.py
├── promptmint/scanner.py
└── tests/test_scanner.py
```

## Included files

### README.md

```markdown
# Example Project
```

## Request

Explain how the project works, identify the main modules, and suggest where a new contributor should start.
```

## Refactor mode example

Command:

```bash
promptmint . --mode refactor --goal "Simplify the scanner module without changing behavior" --output refactor-context.md
```

Example output excerpt:

```markdown
# PromptMint Context Pack

## Goal

Simplify the scanner module without changing behavior

## Mode

refactor

## Included files

### promptmint/scanner.py

```python
def scan_project(root, include=None, exclude=None):
    ...
```

## Request

Propose a safe refactor plan. Preserve behavior, call out risks, and suggest tests to run.
```

## Tips for smaller outputs

- Use `--include` to focus on the files related to the task.
- Use `--exclude` to remove fixtures, generated files, or private paths.
- Lower `--max-file-bytes` when a project contains large source files.
- Review the generated Markdown before pasting it into an AI tool.

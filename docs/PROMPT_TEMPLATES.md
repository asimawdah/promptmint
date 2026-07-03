# Prompt Template Library

PromptMint includes a categorized starter template library so users can generate useful context packs without writing the whole task prompt from scratch.

## Categories

The initial library includes 25 templates across five categories:

- `coding`: implementation, review, refactor, API, and test-planning prompts.
- `debugging`: traceback, flaky test, performance, security, and dependency upgrade prompts.
- `product-planning`: PRD, MVP scope, story map, launch checklist, and risk matrix prompts.
- `writing`: blog, release notes, README, PR summary, and documentation examples.
- `learning`: concept explanation, code walkthrough, quiz, learning plan, and flashcards.

Use `all` to show every category when listing templates. Unknown category names fail fast with the available categories instead of returning an empty list.

## List templates

```bash
promptmint --list-templates
```

Filter by category or search text:

```bash
promptmint --list-templates --template-category coding
promptmint --list-templates --template-search security
promptmint --list-templates --template-search "security auth logging"
```

Multi-word search requires every term to match the template id, category, title, description, variables, prompt body, or example output.

Use JSON output when another tool needs to discover templates without parsing human-readable text:

```bash
promptmint --list-templates --template-category debugging --template-search traceback --template-format json
```

The JSON response includes:

- `schema_version`
- applied `filters`
- `available_categories`
- result `count`
- compact template summaries

It intentionally omits full prompt bodies from list output so scripts can discover templates without dumping long instruction text by default.

## Inspect one template

Use `--show-template` when you need to inspect the full prompt body before scanning a project:

```bash
promptmint --show-template bug-root-cause
```

Preview template placeholders with `--template-var`:

```bash
promptmint --show-template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard"
```

Use JSON for editor integrations, scripts, or tests that need a stable single-template contract:

```bash
promptmint --show-template bug-root-cause --template-format json
```

Single-template JSON includes the compact listing metadata plus full `prompt`, `provided_variables`, `missing_variables`, and `rendered_goal`.

## Use a template

Pass the template id with `--template` and template placeholder values with `--template-var`:

```bash
promptmint . \
  --template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard" \
  --output debug-context.md
```

Template variables are intentionally separate from prompt metadata variables:

- `--template-var` fills placeholders in the selected starter template.
- `--var`, `--require`, and `--vars-file` keep their existing meaning as workflow metadata in the generated context pack.

That separation avoids ambiguity when a generated pack needs both a reusable template and traceable metadata:

```bash
promptmint . \
  --template bug-root-cause \
  --template-var bug="login redirects to a blank page" \
  --template-var expected_behavior="user reaches the dashboard" \
  --require ticket \
  --var ticket=BUG-18 \
  --output reports/BUG-18-debug.md
```

The generated Markdown includes:

- the rendered template goal,
- selected template id/category/title/description,
- template variables and example output guidance,
- prompt metadata and workflow variables,
- scanned project files and optional error logs.

## Template variable handling

PromptMint validates template variables before scanning the project:

- `--template-var` is only valid with `--template` or `--show-template`.
- Each template variable key can be provided once.
- Unknown variable names fail fast and show the variables expected by the selected template.
- Missing variables are allowed, but the placeholder stays visible and the rendered goal includes `Missing template variables` so incomplete prompts are easy to review.

Duplicate variable example:

```bash
promptmint . --template bug-root-cause --template-var bug="first" --template-var bug="second"
```

Expected result:

```text
Duplicate template variable 'bug'. Provide each --template-var key once.
```

Unknown variable example:

```bash
promptmint . --template bug-root-cause --template-var typo="login fails"
```

Expected result:

```text
Unknown variable for template 'bug-root-cause': typo. Expected variables: bug, expected_behavior
```

## Template quality gates

Every built-in template is guarded by regression tests so the starter library remains safe to use from the CLI, scripts, and editor integrations.

Quality rules:

- Template ids use stable lowercase kebab-case.
- Categories stay within the documented category set.
- Variable names use lowercase snake_case.
- Every `{placeholder}` in the prompt must exactly match a declared variable.
- Every declared variable must appear in the prompt.
- Template descriptions, prompts, and example outputs must be actionable.

These checks prevent typoed placeholders, undocumented variables, accidental category drift, duplicate ids, and vague prompts that produce weak AI instructions.

## Add a new template

Add a `PromptTemplate` entry in `promptmint/templates.py` with:

- stable `id` using lowercase kebab-case,
- one of the existing categories,
- short `title`,
- practical `description`,
- `variables` tuple,
- prompt text with matching `{variable}` placeholders,
- `example_output` describing the expected result.

Then run:

```bash
python3 -m unittest tests.test_templates -v
python3 -m unittest tests.test_cli -v
```

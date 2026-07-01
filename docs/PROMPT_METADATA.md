# Prompt Metadata and Validation

PromptMint context packs are easier to review and reuse when the generated Markdown includes a small amount of structured metadata. This is especially useful for issue-driven debugging, PR review, and AI-agent handoff workflows.

## Metadata section

Generated packs include a `Prompt Metadata` section with:

- metadata schema version
- selected mode
- whether a goal was provided
- number of files included
- number of dependency files included
- whether git diff is present
- whether an error log is present
- variable validation status
- required and provided variable counts
- required variable names
- provided variable names

This makes the output easier to audit before it is pasted into an AI tool.

Example:

```markdown
## Prompt Metadata

- Schema version: `1`
- Mode: `review`
- Goal provided: `true`
- Files included: `12`
- Dependency files included: `2`
- Includes git diff: `true`
- Includes error log: `false`
- Variable validation: `complete`
- Required variable count: `2`
- Provided variable count: `3`
- Required variables: `ticket, area`
- Provided variables: `area, owner, ticket`
```

`Variable validation` is `complete` when every required variable name is present in the generated metadata. It is `incomplete` only when metadata is constructed programmatically with missing required names; the CLI exits before writing output in that case.

## Required variables

Use `--require` when a context pack must include specific workflow fields.

```bash
promptmint . \
  --mode review \
  --goal "Review the login changes" \
  --require ticket \
  --require area \
  --var ticket=AUTH-123 \
  --var area=login
```

You can also use comma-separated shorthand for compact scripts:

```bash
promptmint . \
  --mode review \
  --goal "Review the login changes" \
  --require ticket,area \
  --var ticket=AUTH-123 \
  --var area=login
```

If `ticket` or `area` is missing or empty, PromptMint exits with a clear CLI error before writing an incomplete pack.

## Variable format

Variables use `NAME=VALUE` format:

```bash
--var ticket=BUG-18 --var area=scanner --var env=local
```

Variable names must start with a letter or number. After the first character, names may contain:

- letters
- numbers
- underscores
- dashes

This rejects ambiguous option-like names such as `-flag` or `-`, while still allowing stable workflow names such as `ticket-id` and `area_name`.

Examples:

- `ticket=BUG-18`
- `ticket-id=BUG-18`
- `area=onboarding`
- `reviewer=asim`
- `env=staging`

## Markdown-safe output

Prompt variable values are rendered as fenced `text` blocks in the generated Markdown instead of inline raw text. This keeps the context pack readable and prevents multiline values or values containing backticks from breaking the surrounding Markdown.

Example output:

````markdown
## Prompt Variables

- `ticket`:
```text
BUG-18
```

- `notes`:
`````text
Line one
```
Line two
`````
````

PromptMint automatically chooses a longer fence when the value already contains triple backticks.

## Recommended workflow

1. Decide which metadata fields are required for the task.
2. Pass those names through `--require` or `--require ticket,area`.
3. Pass values through `--var NAME=VALUE`.
4. Review the generated `Prompt Metadata` and `Prompt Variables` sections before sharing the pack.
5. Check that `Variable validation` is `complete` and the required/provided counts match the expected workflow fields.

## Safe examples

Debug a linked issue:

```bash
promptmint . \
  --mode debug \
  --goal "Find the root cause of the scanner failure" \
  --require ticket \
  --var ticket=BUG-18 \
  --var area=scanner
```

Review a pull request:

```bash
promptmint . \
  --mode review \
  --goal "Review this PR for correctness and security" \
  --require pr,area \
  --var pr=42 \
  --var area=auth
```

Create an explanation pack:

```bash
promptmint . \
  --mode explain \
  --goal "Explain the CLI architecture" \
  --var area=cli
```

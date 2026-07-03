from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    category: str
    title: str
    description: str
    variables: tuple[str, ...]
    prompt: str
    example_output: str

    def matches(self, query: str) -> bool:
        normalized = query.casefold().strip()
        if not normalized:
            return True
        haystack = " ".join([
            self.id,
            self.category,
            self.title,
            self.description,
            " ".join(self.variables),
            self.prompt,
            self.example_output,
        ]).casefold()
        return all(term in haystack for term in normalized.split())


def get_template(template_id: str) -> PromptTemplate:
    normalized = template_id.strip().casefold()
    for template in PROMPT_TEMPLATES:
        if template.id == normalized:
            return template
    available = ", ".join(template.id for template in PROMPT_TEMPLATES)
    raise KeyError(f"Unknown template '{template_id}'. Available templates: {available}")


def list_templates(category: str | None = None, query: str | None = None) -> list[PromptTemplate]:
    normalized_category = category.casefold().strip() if category else None
    results = [
        template for template in PROMPT_TEMPLATES
        if normalized_category is None or template.category == normalized_category
    ]
    if query:
        results = [template for template in results if template.matches(query)]
    return results


def list_categories() -> list[str]:
    return sorted({template.category for template in PROMPT_TEMPLATES})


def render_template_goal(template: PromptTemplate, values: dict[str, str] | None = None) -> str:
    values = values or {}
    prompt = template.prompt
    missing: list[str] = []
    for variable in template.variables:
        placeholder = "{" + variable + "}"
        value = values.get(variable)
        if value is None:
            missing.append(variable)
            value = placeholder
        prompt = prompt.replace(placeholder, value)

    sections = [f"Template: {template.title}", f"Category: {template.category}", "", prompt]
    if missing:
        sections.extend(["", "Missing template variables: " + ", ".join(missing)])
    return "\n".join(sections).strip()


PROMPT_TEMPLATES: tuple[PromptTemplate, ...] = (
    PromptTemplate("bug-root-cause", "coding", "Bug Root Cause Analysis", "Find the root cause of a bug and propose the smallest safe fix.", ("bug", "expected_behavior"), "Analyze the included code and identify why {bug} happens. Compare it with the expected behavior: {expected_behavior}. Propose the smallest safe fix and mention tests to add.", "Root cause, affected files, fix plan, and regression tests."),
    PromptTemplate("code-review", "coding", "Focused Code Review", "Review code for bugs, maintainability, security, and performance.", ("focus_area",), "Review the included files with extra attention to {focus_area}. Prioritize concrete bugs, security issues, performance risks, and maintainability problems.", "Prioritized findings with severity and suggested patches."),
    PromptTemplate("safe-refactor", "coding", "Safe Refactor Plan", "Plan a low-risk refactor that preserves behavior.", ("target",), "Create a safe refactor plan for {target}. Keep behavior unchanged, identify seams for tests, and propose small commits.", "Step-by-step refactor plan with validation checks."),
    PromptTemplate("test-plan", "coding", "Test Plan Generator", "Create a practical test plan for changed code.", ("feature",), "Create a test plan for {feature}. Include unit, integration, edge-case, and regression tests based on the included code.", "Checklist of tests grouped by layer and risk."),
    PromptTemplate("api-contract", "coding", "API Contract Review", "Review API request/response behavior and compatibility risks.", ("endpoint",), "Review the API contract for {endpoint}. Check validation, error responses, backwards compatibility, and documentation gaps.", "Contract risks, validation gaps, and example payloads."),
    PromptTemplate("debug-traceback", "debugging", "Traceback Debugger", "Explain a traceback and map it to likely code changes.", ("error_summary",), "Use the included error log and source files to explain {error_summary}. Identify the failing path, likely root cause, and minimal patch.", "Failure path, root cause, patch, and verification command."),
    PromptTemplate("flaky-test", "debugging", "Flaky Test Investigation", "Diagnose nondeterministic tests and stabilize them.", ("test_name",), "Investigate why {test_name} may be flaky. Look for shared state, timing, ordering, randomness, I/O, and environment assumptions.", "Likely flake sources and deterministic fixes."),
    PromptTemplate("performance-bottleneck", "debugging", "Performance Bottleneck Finder", "Find slow paths and suggest measurable improvements.", ("slow_operation",), "Analyze why {slow_operation} may be slow. Identify complexity, I/O, caching, batching, and profiling checkpoints.", "Bottleneck hypothesis, metrics to collect, and optimization plan."),
    PromptTemplate("security-check", "debugging", "Security Risk Check", "Look for common security issues in the provided context.", ("asset",), "Review the included code for security risks related to {asset}. Focus on secrets, injection, auth, authorization, unsafe deserialization, and logging.", "Security findings with exploitability and safer alternatives."),
    PromptTemplate("dependency-upgrade", "debugging", "Dependency Upgrade Risk Review", "Assess a dependency upgrade for breakage and migration work.", ("dependency",), "Assess upgrade risks for {dependency}. Identify API changes, lockfile concerns, compatibility issues, and tests to run.", "Upgrade checklist and rollback plan."),
    PromptTemplate("prd-outline", "product-planning", "Product Requirement Draft", "Turn an idea into a concise PRD outline.", ("feature", "users"), "Draft a concise product requirement outline for {feature} for {users}. Include problem, goals, non-goals, user stories, success metrics, and risks.", "PRD outline with scope and measurable success criteria."),
    PromptTemplate("mvp-scope", "product-planning", "MVP Scope Cutter", "Reduce a feature idea to a shippable MVP.", ("idea",), "Reduce {idea} to an MVP. Separate must-have, should-have, later, and not-now items. Recommend the smallest useful release.", "MVP scope table with release sequence."),
    PromptTemplate("user-story-map", "product-planning", "User Story Map", "Create a story map for a user workflow.", ("workflow",), "Create a user story map for {workflow}. Include activities, steps, user stories, acceptance criteria, and edge cases.", "Story map organized from discovery to release slices."),
    PromptTemplate("launch-checklist", "product-planning", "Launch Readiness Checklist", "Prepare a launch checklist for a feature or app.", ("release",), "Create a launch readiness checklist for {release}. Cover product, QA, security, analytics, support, docs, and rollback readiness.", "Launch checklist with owners and go/no-go criteria."),
    PromptTemplate("risk-matrix", "product-planning", "Risk Matrix", "Identify product or project risks and mitigations.", ("project",), "Create a risk matrix for {project}. Rank risks by likelihood and impact, and propose mitigation and detection signals.", "Risk table with mitigation and monitoring actions."),
    PromptTemplate("blog-outline", "writing", "Technical Blog Outline", "Outline a technical article from project context.", ("topic", "audience"), "Create a technical blog outline about {topic} for {audience}. Include hook, sections, examples, diagrams to include, and conclusion.", "Structured article outline with key examples."),
    PromptTemplate("release-notes", "writing", "Release Notes Draft", "Turn changes into user-friendly release notes.", ("version",), "Write release notes for {version} from the included changes. Group by new, improved, fixed, and breaking changes. Keep it user-focused.", "Release notes with clear user impact."),
    PromptTemplate("readme-improve", "writing", "README Improvement Plan", "Improve a README for clarity and onboarding.", ("project_type",), "Review the README for this {project_type}. Suggest missing sections, clearer examples, installation improvements, and safety notes.", "README gap analysis and replacement section drafts."),
    PromptTemplate("commit-summary", "writing", "Commit or PR Summary", "Summarize changes for a commit, PR, or changelog.", ("change_goal",), "Summarize the included changes for {change_goal}. Include what changed, why it matters, test coverage, and review notes.", "PR-ready summary with testing notes."),
    PromptTemplate("docs-example", "writing", "Documentation Example Builder", "Create copy-paste friendly docs examples.", ("command_or_api",), "Create documentation examples for {command_or_api}. Include common case, advanced case, invalid input, and troubleshooting guidance.", "Examples with expected output and warnings."),
    PromptTemplate("concept-explainer", "learning", "Concept Explainer", "Explain a concept using the included project as context.", ("concept",), "Explain {concept} using the included project context. Start with a simple analogy, then show how it appears in the code, and end with a quick check question.", "Layered explanation with examples and a check question."),
    PromptTemplate("code-walkthrough", "learning", "Code Walkthrough", "Walk through important files in a project.", ("entrypoint",), "Walk through the project starting from {entrypoint}. Explain the call flow, important modules, data flow, and where to make safe changes.", "Guided walkthrough from entrypoint to dependencies."),
    PromptTemplate("quiz-me", "learning", "Project Quiz", "Generate questions to test understanding of a codebase.", ("difficulty",), "Create a {difficulty} quiz about the included project. Ask focused questions about architecture, behavior, edge cases, and tradeoffs. Include answers after the questions.", "Quiz with answers and explanation notes."),
    PromptTemplate("learning-plan", "learning", "Learning Plan", "Build a learning path around a project or topic.", ("topic", "timeframe"), "Build a learning plan for {topic} over {timeframe}. Use the included project context when relevant and include practice tasks.", "Step-by-step plan with exercises and checkpoints."),
    PromptTemplate("flashcards", "learning", "Flashcard Generator", "Create flashcards from project context or documentation.", ("subject",), "Create flashcards for {subject} from the included context. Use concise Q/A cards and include common mistakes.", "Flashcards grouped by concept and difficulty."),
)

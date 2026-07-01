import unittest

from promptmint.metadata import (
    PROMPT_METADATA_SCHEMA_VERSION,
    PromptMetadata,
    canonical_prompt_variable_name,
    missing_required_variables,
    normalize_required_variables,
    parse_variable_assignment,
    parse_variable_assignments,
)


class PromptMetadataTest(unittest.TestCase):
    def test_parse_variable_assignment_requires_name_value_format(self):
        self.assertEqual(parse_variable_assignment("ticket=APP-42"), ("ticket", "APP-42"))

        with self.assertRaises(ValueError):
            parse_variable_assignment("ticket")

    def test_parse_variable_assignment_rejects_names_without_alphanumeric_prefix(self):
        for value in ["-=bad", "_secret=value", "-flag=value"]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "must start with a letter or number"):
                    parse_variable_assignment(value)

    def test_parse_variable_assignment_allows_safe_internal_separators(self):
        self.assertEqual(parse_variable_assignment("ticket-id=APP-42"), ("ticket-id", "APP-42"))
        self.assertEqual(parse_variable_assignment("area_name=cli"), ("area_name", "cli"))
        self.assertEqual(parse_variable_assignment("r2d2=bot"), ("r2d2", "bot"))

    def test_parse_variable_assignment_canonicalizes_names(self):
        self.assertEqual(parse_variable_assignment(" Ticket-ID = APP-42 "), ("ticket-id", "APP-42"))
        self.assertEqual(canonical_prompt_variable_name("Area_Name"), "area_name")

    def test_parse_variable_assignments_rejects_duplicate_values(self):
        with self.assertRaisesRegex(ValueError, "duplicate prompt variable: ticket"):
            parse_variable_assignments(["ticket=APP-1", "ticket=APP-2", "area=cli"])

    def test_parse_variable_assignments_rejects_case_variant_duplicates(self):
        with self.assertRaisesRegex(ValueError, "duplicate prompt variable: ticket"):
            parse_variable_assignments(["Ticket=APP-1", "ticket=APP-2"])

    def test_parse_variable_assignments_keeps_unique_values(self):
        variables = parse_variable_assignments(["ticket=APP-1", "area=cli"])

        self.assertEqual(variables["ticket"], "APP-1")
        self.assertEqual(variables["area"], "cli")

    def test_normalize_required_variables_deduplicates_in_order(self):
        required = normalize_required_variables(["ticket", "area", "ticket"])

        self.assertEqual(required, ("ticket", "area"))

    def test_normalize_required_variables_canonicalizes_case_variants(self):
        required = normalize_required_variables(["Ticket, Area", "ticket", "OWNER"])

        self.assertEqual(required, ("ticket", "area", "owner"))

    def test_normalize_required_variables_supports_comma_separated_shorthand(self):
        required = normalize_required_variables(["ticket, area", "env", "ticket"])

        self.assertEqual(required, ("ticket", "area", "env"))

    def test_normalize_required_variables_rejects_empty_shorthand_segments(self):
        with self.assertRaisesRegex(ValueError, "required variable name cannot be empty"):
            normalize_required_variables(["ticket,,area"])

    def test_normalize_required_variables_rejects_option_like_names(self):
        with self.assertRaisesRegex(ValueError, "must start with a letter or number"):
            normalize_required_variables(["ticket,-flag"])

    def test_missing_required_variables_treats_empty_values_as_missing(self):
        missing = missing_required_variables(("ticket", "area"), {"ticket": "APP-1", "area": ""})

        self.assertEqual(missing, ["area"])

    def test_metadata_renders_markdown_lines(self):
        metadata = PromptMetadata(
            mode="debug",
            goal_present=True,
            file_count=2,
            dependency_file_count=1,
            includes_git_diff=False,
            includes_error_log=True,
            required_variables=("ticket",),
            provided_variables=("ticket",),
        )

        text = "\n".join(metadata.to_markdown_lines())

        self.assertIn("## Prompt Metadata", text)
        self.assertIn(f"Schema version: `{PROMPT_METADATA_SCHEMA_VERSION}`", text)
        self.assertIn("Mode: `debug`", text)
        self.assertIn("Files included: `2`", text)
        self.assertIn("Variable validation: `complete`", text)
        self.assertIn("Required variable count: `1`", text)
        self.assertIn("Provided variable count: `1`", text)
        self.assertIn("Required variables: `ticket`", text)

    def test_metadata_marks_incomplete_when_required_names_are_missing(self):
        metadata = PromptMetadata(
            mode="debug",
            goal_present=False,
            file_count=0,
            dependency_file_count=0,
            includes_git_diff=False,
            includes_error_log=False,
            required_variables=("ticket", "area"),
            provided_variables=("ticket",),
        )

        self.assertEqual(metadata.validation_status, "incomplete")
        self.assertIn("Variable validation: `incomplete`", "\n".join(metadata.to_markdown_lines()))


if __name__ == "__main__":
    unittest.main()

import unittest

from promptmint.metadata import (
    PromptMetadata,
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

    def test_parse_variable_assignments_rejects_duplicate_values(self):
        with self.assertRaisesRegex(ValueError, "duplicate prompt variable: ticket"):
            parse_variable_assignments(["ticket=APP-1", "ticket=APP-2", "area=cli"])

    def test_parse_variable_assignments_keeps_unique_values(self):
        variables = parse_variable_assignments(["ticket=APP-1", "area=cli"])

        self.assertEqual(variables["ticket"], "APP-1")
        self.assertEqual(variables["area"], "cli")

    def test_normalize_required_variables_deduplicates_in_order(self):
        required = normalize_required_variables(["ticket", "area", "ticket"])

        self.assertEqual(required, ("ticket", "area"))

    def test_normalize_required_variables_supports_comma_separated_shorthand(self):
        required = normalize_required_variables(["ticket, area", "env", "ticket"])

        self.assertEqual(required, ("ticket", "area", "env"))

    def test_normalize_required_variables_rejects_empty_shorthand_segments(self):
        with self.assertRaisesRegex(ValueError, "required variable name cannot be empty"):
            normalize_required_variables(["ticket,,area"])

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
        self.assertIn("Mode: `debug`", text)
        self.assertIn("Files included: `2`", text)
        self.assertIn("Required variables: `ticket`", text)


if __name__ == "__main__":
    unittest.main()

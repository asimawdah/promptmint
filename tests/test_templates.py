import re
import unittest

from promptmint.templates import (
    PROMPT_TEMPLATES,
    get_template,
    list_categories,
    list_templates,
    render_template_goal,
)


class PromptTemplateLibraryTest(unittest.TestCase):
    def test_library_contains_at_least_twenty_templates_across_required_categories(self):
        self.assertGreaterEqual(len(PROMPT_TEMPLATES), 20)
        self.assertEqual(
            list_categories(),
            ["coding", "debugging", "learning", "product-planning", "writing"],
        )

    def test_template_ids_are_unique_and_metadata_is_complete(self):
        ids = [template.id for template in PROMPT_TEMPLATES]
        self.assertEqual(len(ids), len(set(ids)))
        for template in PROMPT_TEMPLATES:
            self.assertRegex(template.id, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertTrue(template.title)
            self.assertTrue(template.description)
            self.assertTrue(template.prompt)
            self.assertTrue(template.example_output)
            for variable in template.variables:
                self.assertRegex(variable, r"^[a-z][a-z0-9_]*$")
                self.assertIn("{" + variable + "}", template.prompt)

    def test_template_placeholders_match_declared_variables(self):
        for template in PROMPT_TEMPLATES:
            placeholders = set(re.findall(r"{([a-z][a-z0-9_]*)}", template.prompt))
            self.assertEqual(placeholders, set(template.variables), template.id)

    def test_list_templates_filters_by_category_and_search(self):
        coding = list_templates(category="coding")
        self.assertTrue(coding)
        self.assertTrue(all(template.category == "coding" for template in coding))

        security = list_templates(query="security")
        self.assertTrue(any(template.id == "security-check" for template in security))

    def test_template_search_requires_every_search_term_to_match(self):
        exact = list_templates(query="security auth logging")
        self.assertEqual([template.id for template in exact], ["security-check"])

        unrelated = list_templates(query="security traceback")
        self.assertEqual(unrelated, [])

    def test_get_template_is_case_insensitive(self):
        template = get_template("BUG-ROOT-CAUSE")

        self.assertEqual(template.id, "bug-root-cause")

    def test_render_template_goal_replaces_values_and_reports_missing_variables(self):
        template = get_template("bug-root-cause")

        output = render_template_goal(template, {"bug": "login fails"})

        self.assertIn("login fails", output)
        self.assertIn("{expected_behavior}", output)
        self.assertIn("Missing template variables: expected_behavior", output)


if __name__ == "__main__":
    unittest.main()

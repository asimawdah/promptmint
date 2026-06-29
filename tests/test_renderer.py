import unittest

from promptmint.models import ProjectFile, ScanResult
from promptmint.renderer import render_context_pack


class RenderContextPackTest(unittest.TestCase):
    def test_render_context_pack_contains_goal_mode_tree_files_diff_and_error(self):
        scan = ScanResult(
            root="/project",
            tree="src/\n  app.py",
            files=[ProjectFile(relative_path="src/app.py", language="python", content="print('hello')\n")],
            dependency_files=[ProjectFile(relative_path="pyproject.toml", language="toml", content="[project]\n")],
            git_diff="diff --git a/src/app.py b/src/app.py\n",
        )

        output = render_context_pack(scan, goal="Fix bug", mode="debug", error_log="Traceback here")

        self.assertIn("# Project Context Pack", output)
        self.assertIn("Fix bug", output)
        self.assertIn("Debug Request", output)
        self.assertIn("src/app.py", output)
        self.assertIn("```python", output)
        self.assertIn("pyproject.toml", output)
        self.assertIn("diff --git", output)
        self.assertIn("Traceback here", output)

    def test_render_context_pack_contains_structured_metadata(self):
        scan = ScanResult(
            root="/project",
            tree="app.py",
            files=[ProjectFile(relative_path="app.py", language="python", content="print('hello')\n")],
            dependency_files=[],
            git_diff="",
        )

        output = render_context_pack(
            scan,
            goal="Review task",
            mode="review",
            required_variables=("ticket",),
            prompt_variables={"ticket": "APP-42"},
        )

        self.assertIn("## Prompt Metadata", output)
        self.assertIn("- Mode: `review`", output)
        self.assertIn("- Goal provided: `true`", output)
        self.assertIn("- Files included: `1`", output)
        self.assertIn("- Required variables: `ticket`", output)
        self.assertIn("## Prompt Variables", output)
        self.assertIn("- `ticket`: APP-42", output)


if __name__ == "__main__":
    unittest.main()

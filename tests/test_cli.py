import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from promptmint.cli import main


class CliTest(unittest.TestCase):
    def test_cli_creates_output_file_with_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            output = root / "context.md"

            exit_code = main([str(root), "--goal", "Explain app", "--output", str(output)])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Explain app", text)
            self.assertIn("app.py", text)

    def test_cli_supports_short_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            error = root / "error.log"
            output = root / "short.md"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (root / "notes.md").write_text("# Notes\n", encoding="utf-8")
            error.write_text("Traceback example\n", encoding="utf-8")

            exit_code = main([
                str(root),
                "-g", "Fix bug",
                "-m", "debug",
                "-e", str(error),
                "-i", "app.py",
                "-x", "notes.md",
                "-o", str(output),
                "-s", "1000",
            ])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Fix bug", text)
            self.assertIn("Traceback example", text)
            self.assertIn("app.py", text)
            self.assertNotIn("notes.md", text)

    def test_cli_writes_prompt_metadata_and_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "context.md"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            exit_code = main([
                str(root),
                "--goal", "Review login flow",
                "--require", "ticket",
                "--var", "ticket=PM-123",
                "--output", str(output),
            ])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("## Prompt Metadata", text)
            self.assertIn("Required variables: `ticket`", text)
            self.assertIn("Provided variables: `ticket`", text)
            self.assertIn("- `ticket`:\n```text\nPM-123\n```", text)

    def test_cli_loads_prompt_variables_from_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "context.md"
            variables = root / "prompt-vars.json"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            variables.write_text(json.dumps({"Ticket": "PM-123", "area": " login "}), encoding="utf-8")

            exit_code = main([
                str(root),
                "--goal", "Review login flow",
                "--require", "ticket,area",
                "--vars-file", str(variables),
                "--output", str(output),
            ])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("Required variables: `ticket, area`", text)
            self.assertIn("Provided variables: `area, ticket`", text)
            self.assertIn("- `ticket`:\n```text\nPM-123\n```", text)
            self.assertIn("- `area`:\n```text\nlogin\n```", text)

    def test_cli_lists_templates_with_category_filter_and_search(self):
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["--list-templates", "--template-category", "debugging", "--template-search", "traceback"])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Available template categories: all, coding, debugging, learning, product-planning, writing", output)
        self.assertIn("[debugging]", output)
        self.assertIn("debug-traceback", output)
        self.assertNotIn("[coding]", output)

    def test_cli_lists_templates_as_stable_json(self):
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([
                "--list-templates",
                "--template-category", "debugging",
                "--template-search", "traceback",
                "--template-format", "json",
            ])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["filters"], {"category": "debugging", "query": "traceback"})
        self.assertIn("all", payload["available_categories"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["templates"][0]["id"], "debug-traceback")
        self.assertNotIn("prompt", payload["templates"][0])

    def test_cli_shows_single_template_detail_as_text(self):
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([
                "--show-template", "bug-root-cause",
                "--template-var", "bug=login redirects",
            ])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("Template: bug-root-cause", output)
        self.assertIn("Prompt:", output)
        self.assertIn("Analyze the included code", output)
        self.assertIn("login redirects", output)
        self.assertIn("Missing variables: expected_behavior", output)

    def test_cli_shows_single_template_detail_as_json(self):
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main([
                "--show-template", "bug-root-cause",
                "--template-format", "json",
                "--template-var", "bug=login redirects",
                "--template-var", "expected_behavior=user reaches dashboard",
            ])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["id"], "bug-root-cause")
        self.assertIn("prompt", payload)
        self.assertEqual(payload["provided_variables"]["bug"], "login redirects")
        self.assertEqual(payload["missing_variables"], [])
        self.assertIn("user reaches dashboard", payload["rendered_goal"])

    def test_cli_applies_template_and_metadata_variables_to_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "template.md"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            exit_code = main([
                str(root),
                "--template", "bug-root-cause",
                "--template-var", "bug=login issue",
                "--template-var", "expected_behavior=user reaches dashboard",
                "--require", "ticket",
                "--var", "ticket=PM-123",
                "--output", str(output),
            ])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("## Prompt Template", text)
            self.assertIn("bug-root-cause", text)
            self.assertIn("login issue", text)
            self.assertIn("user reaches dashboard", text)
            self.assertIn("Provided variables: `ticket`", text)

    def test_cli_rejects_template_var_without_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--template-var", "topic=login"])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_list_and_show_templates_together(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["--list-templates", "--show-template", "bug-root-cause"])

        self.assertNotEqual(context.exception.code, 0)
        self.assertIn("Use either --list-templates or --show-template", stderr.getvalue())

    def test_cli_rejects_unknown_template_category(self):
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["--list-templates", "--template-category", "debuggng"])

        self.assertNotEqual(context.exception.code, 0)
        error = stderr.getvalue()
        self.assertIn("Unknown template category 'debuggng'", error)
        self.assertIn("Available categories: all, coding, debugging, learning, product-planning, writing", error)

    def test_cli_rejects_unknown_template_variable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main([str(root), "--template", "bug-root-cause", "--template-var", "unexpected=value"])

            self.assertNotEqual(context.exception.code, 0)
            error = stderr.getvalue()
            self.assertIn("Unknown variable for template 'bug-root-cause': unexpected", error)
            self.assertIn("Expected variables: bug, expected_behavior", error)

    def test_cli_rejects_duplicate_template_variable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main([
                        str(root),
                        "--template", "bug-root-cause",
                        "--template-var", "bug=first",
                        "--template-var", "bug=second",
                    ])

            self.assertNotEqual(context.exception.code, 0)
            self.assertIn("Duplicate template variable 'bug'", stderr.getvalue())

    def test_cli_rejects_duplicate_prompt_variables_across_file_and_inline_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            variables = root / "prompt-vars.json"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            variables.write_text(json.dumps({"ticket": "PM-123"}), encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--vars-file", str(variables), "--var", "Ticket=PM-456"])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_invalid_prompt_variables_file_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            variables = root / "prompt-vars.json"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            variables.write_text(json.dumps(["ticket", "PM-123"]), encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--vars-file", str(variables)])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_non_string_prompt_variable_file_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            variables = root / "prompt-vars.json"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            variables.write_text(json.dumps({"ticket": 123}), encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--vars-file", str(variables)])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_missing_project_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"

            with self.assertRaises(SystemExit) as context:
                main([str(missing)])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_missing_required_variable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--require", "ticket"])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_invalid_variable_assignment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--var", "ticket"])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_missing_error_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
            missing_error = root / "missing.log"

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--error", str(missing_error)])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_non_positive_max_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--max-file-bytes", "0"])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_creates_output_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "reports" / "review" / "context.markdown"
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            exit_code = main([str(root), "--goal", "Review app", "--output", str(output)])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            self.assertIn("Review app", output.read_text(encoding="utf-8"))

    def test_cli_excludes_existing_output_file_from_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "reports" / "review" / "context.md"
            output.parent.mkdir(parents=True)
            output.write_text("stale generated context that must not be rescanned\n", encoding="utf-8")
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            exit_code = main([str(root), "--goal", "Refresh context", "--output", str(output)])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("app.py", text)
            self.assertNotIn("stale generated context that must not be rescanned", text)
            self.assertNotIn("reports/review/context.md", text)

    def test_cli_rejects_directory_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--output", str(root)])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_non_markdown_output_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--output", str(root / "context.txt")])

            self.assertNotEqual(context.exception.code, 0)

    def test_cli_rejects_file_as_output_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent_file = root / "not-a-directory"
            parent_file.write_text("not a directory\n", encoding="utf-8")
            (root / "app.py").write_text("print('hello')\n", encoding="utf-8")

            with self.assertRaises(SystemExit) as context:
                main([str(root), "--output", str(parent_file / "context.md")])

            self.assertNotEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()

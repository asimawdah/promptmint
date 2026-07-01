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
                "--goal", "Review auth flow",
                "--require", "ticket",
                "--var", "ticket=AUTH-123",
                "--output", str(output),
            ])

            self.assertEqual(exit_code, 0)
            text = output.read_text(encoding="utf-8")
            self.assertIn("## Prompt Metadata", text)
            self.assertIn("Required variables: `ticket`", text)
            self.assertIn("Provided variables: `ticket`", text)
            self.assertIn("- `ticket`:\n```text\nAUTH-123\n```", text)

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

    def test_cli_rejects_missing_project_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"

            with self.assertRaises(SystemExit) as context:
                main([str(missing)])

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
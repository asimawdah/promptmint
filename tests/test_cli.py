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


if __name__ == "__main__":
    unittest.main()

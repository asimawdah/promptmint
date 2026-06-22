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


if __name__ == "__main__":
    unittest.main()

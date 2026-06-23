import tempfile
import unittest
from pathlib import Path

from promptmint.scanner import scan_project


class ScanProjectTest(unittest.TestCase):
    def test_scan_project_includes_source_and_manifest_but_excludes_secrets_and_vendor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "node_modules").mkdir()
            (root / ".git").mkdir()
            (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (root / "package.json").write_text('{"scripts":{"test":"echo ok"}}\n', encoding="utf-8")
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / "node_modules" / "lib.js").write_text("ignored\n", encoding="utf-8")
            (root / "image.png").write_bytes(b"\x89PNG\x00\x01")

            result = scan_project(root)
            paths = [f.relative_path for f in result.files]

            self.assertIn("src/app.py", paths)
            self.assertIn("package.json", paths)
            self.assertNotIn(".env", paths)
            self.assertNotIn("node_modules/lib.js", paths)
            self.assertNotIn("image.png", paths)
            self.assertIn("src/", result.tree)

    def test_scan_project_respects_include_globs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "docs").mkdir()
            (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (root / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")

            result = scan_project(root, include=["docs/**/*.md"])
            paths = [f.relative_path for f in result.files]

            self.assertEqual(paths, ["docs/guide.md"])

    def test_scan_project_respects_root_gitignore_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tmp").mkdir()
            (root / ".gitignore").write_text("*.log\ntmp/\nsecret.txt\n", encoding="utf-8")
            (root / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
            (root / "src" / "debug.log").write_text("debug\n", encoding="utf-8")
            (root / "tmp" / "cache.txt").write_text("cache\n", encoding="utf-8")
            (root / "secret.txt").write_text("secret\n", encoding="utf-8")

            result = scan_project(root)
            paths = [f.relative_path for f in result.files]

            self.assertIn("src/app.py", paths)
            self.assertIn(".gitignore", paths)
            self.assertNotIn("src/debug.log", paths)
            self.assertNotIn("tmp/cache.txt", paths)
            self.assertNotIn("secret.txt", paths)
            self.assertNotIn("tmp/", result.tree)


if __name__ == "__main__":
    unittest.main()

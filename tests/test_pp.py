import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from pp import STORAGE_ENV, list_entries, main, read_entry, remove_entry, save_entry


class PromptPasteTests(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp())
        self.storage = root / "prompt_paste"
        self.storage.mkdir()
        self.workspace = root / "work"
        self.workspace.mkdir()

    def tearDown(self):
        shutil.rmtree(self.storage.parent, ignore_errors=True)

    def _source(self, name: str, text: str) -> Path:
        path = self.workspace / name
        path.write_text(text)
        return path

    def _prompt(self, responses):
        def responder(_msg: str) -> str:
            return responses.pop(0)

        return responder

    def test_save_entry_creates_file(self):
        source = self._source("snippet.txt", "echo 'hello'")
        saved = save_entry(source, storage=self.storage)
        self.assertIsNotNone(saved)
        self.assertTrue((self.storage / "snippet.txt").exists())
        self.assertEqual("echo 'hello'", read_entry("snippet", storage=self.storage))

    def test_save_entry_auto_rename(self):
        source = self._source("snippet.md", "one")
        save_entry(source, storage=self.storage)
        second = self._source("snippet.md", "two")
        prompt = self._prompt(["y"])
        saved = save_entry(second, storage=self.storage, prompt_fn=prompt)
        self.assertIsNotNone(saved)
        self.assertTrue(saved.name.endswith("_2.md"))
        self.assertEqual("two", read_entry("snippet_2", storage=self.storage))

    def test_save_entry_cancelled(self):
        source = self._source("snippet.txt", "one")
        save_entry(source, storage=self.storage)
        second = self._source("snippet.txt", "two")
        prompt = self._prompt(["n"])
        result = save_entry(second, storage=self.storage, prompt_fn=prompt)
        self.assertIsNone(result)

    def test_list_and_read(self):
        (self.storage / "one.md").write_text("1")
        (self.storage / "two.txt").write_text("2")
        entries = list_entries(storage=self.storage)
        self.assertEqual(["one.md", "two.txt"], [entry.name for entry in entries])
        self.assertEqual("2", read_entry("two", storage=self.storage))

    def test_remove_entry(self):
        (self.storage / "bye.md").write_text("bye")
        remove_entry("bye", storage=self.storage)
        self.assertFalse((self.storage / "bye.md").exists())
        with self.assertRaises(FileNotFoundError):
            remove_entry("bye", storage=self.storage)

    def test_retrieve_missing_silent(self):
        previous = os.environ.get(STORAGE_ENV)
        os.environ[STORAGE_ENV] = str(self.storage)
        try:
            result = main(["missing"])
        finally:
            if previous is None:
                os.environ.pop(STORAGE_ENV, None)
            else:
                os.environ[STORAGE_ENV] = previous
        self.assertEqual(0, result)

    def test_save_missing_error(self):
        previous = os.environ.get(STORAGE_ENV)
        os.environ[STORAGE_ENV] = str(self.storage)
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stderr(buffer):
                result = main(["save", "missing.txt"])
        finally:
            if previous is None:
                os.environ.pop(STORAGE_ENV, None)
            else:
                os.environ[STORAGE_ENV] = previous
        self.assertEqual(1, result)
        self.assertIn("source file not found", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()

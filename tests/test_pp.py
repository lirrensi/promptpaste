import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from promptpaste import (
    STORAGE_ENV,
    confirm_folder_import,
    confirm_merge,
    copy_file_with_collision_handling,
    detect_conflicts,
    discover_folder_files,
    get_entry_by_path,
    get_folder_structure,
    import_folder,
    is_eligible_file,
    list_entries,
    main,
    merge_folders,
    normalize_path,
    read_entry,
    remove_entry,
    resolve_conflict_with_prepend,
    resolve_path,
    save_entry,
)


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
        prompt = self._prompt(["r"])
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
        self.assertIn("source file/folder not found", buffer.getvalue())

    # Path resolution tests
    def test_normalize_path_trailing_slash(self):
        result = normalize_path("bucket/prompt1/")
        self.assertEqual("bucket/prompt1", result)

    def test_normalize_path_empty_segments(self):
        result = normalize_path("bucket//prompt1")
        self.assertEqual("bucket/prompt1", result)

    def test_normalize_path_leading_slash(self):
        result = normalize_path("/bucket/prompt1")
        self.assertEqual("bucket/prompt1", result)

    def test_normalize_path_simple(self):
        result = normalize_path("prompt1")
        self.assertEqual("prompt1", result)

    def test_resolve_path_flat(self):
        result = resolve_path("prompt1", self.storage)
        expected = self.storage / "prompt1.md"
        self.assertEqual(expected, result)

    def test_resolve_path_hierarchical(self):
        result = resolve_path("bucket/prompt1", self.storage)
        expected = self.storage / "bucket" / "prompt1.md"
        self.assertEqual(expected, result)

    def test_resolve_path_deep_hierarchy(self):
        result = resolve_path("folder/subfolder/file", self.storage)
        expected = self.storage / "folder" / "subfolder" / "file.md"
        self.assertEqual(expected, result)

    def test_resolve_path_with_extension(self):
        result = resolve_path("bucket/prompt1.md", self.storage)
        expected = self.storage / "bucket" / "prompt1.md"
        self.assertEqual(expected, result)

    def test_get_entry_by_path_flat(self):
        (self.storage / "prompt1.md").write_text("content")
        result = get_entry_by_path("prompt1", self.storage)
        expected = self.storage / "prompt1.md"
        self.assertEqual(expected, result)

    def test_get_entry_by_path_hierarchical(self):
        (self.storage / "bucket").mkdir()
        (self.storage / "bucket" / "prompt1.md").write_text("content")
        result = get_entry_by_path("bucket/prompt1", self.storage)
        expected = self.storage / "bucket" / "prompt1.md"
        self.assertEqual(expected, result)

    def test_get_entry_by_path_not_found(self):
        with self.assertRaises(FileNotFoundError):
            get_entry_by_path("missing", self.storage)

    def test_get_entry_by_path_partial_match(self):
        (self.storage / "bucket").mkdir()
        (self.storage / "bucket" / "prompt1.md").write_text("content")
        with self.assertRaises(FileNotFoundError):
            get_entry_by_path("bucket", self.storage)

    # Folder discovery tests
    def test_is_eligible_file_md(self):
        result = is_eligible_file(Path("file.md"))
        self.assertTrue(result)

    def test_is_eligible_file_txt(self):
        result = is_eligible_file(Path("file.txt"))
        self.assertTrue(result)

    def test_is_eligible_file_other(self):
        result = is_eligible_file(Path("file.py"))
        self.assertFalse(result)

    def test_discover_folder_files_basic(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.md").write_text("content1")
        (test_folder / "file2.txt").write_text("content2")
        (test_folder / "file3.py").write_text("content3")

        result = discover_folder_files(test_folder)
        self.assertEqual(2, len(result))
        self.assertIn(Path("file1.md"), result)
        self.assertIn(Path("file2.txt"), result)

    def test_discover_folder_files_with_subfolders(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        subfolder = test_folder / "subfolder"
        subfolder.mkdir()
        (subfolder / "file.md").write_text("content")

        result = discover_folder_files(test_folder)
        self.assertEqual(1, len(result))
        self.assertIn(Path("subfolder/file.md"), result)

    def test_discover_folder_files_empty(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()

        result = discover_folder_files(test_folder)
        self.assertEqual(0, len(result))

    def test_discover_folder_files_not_found(self):
        test_folder = self.workspace / "nonexistent"
        with self.assertRaises(FileNotFoundError):
            discover_folder_files(test_folder)

    def test_discover_folder_files_not_directory(self):
        test_file = self.workspace / "test_file.txt"
        test_file.write_text("content")

        with self.assertRaises(NotADirectoryError):
            discover_folder_files(test_file)

    def test_discover_folder_files_skips_prohibited(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "list.md").write_text("content")
        (test_folder / "valid.md").write_text("content")

        result = discover_folder_files(test_folder)
        self.assertEqual(1, len(result))
        self.assertIn(Path("valid.md"), result)

    def test_get_folder_structure_basic(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.md").write_text("content")
        subfolder = test_folder / "subfolder"
        subfolder.mkdir()

        result = get_folder_structure(test_folder)
        self.assertEqual(["file.md"], result["files"])
        self.assertEqual(["subfolder"], result["folders"])

    def test_get_folder_structure_empty(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()

        result = get_folder_structure(test_folder)
        self.assertEqual([], result["files"])
        self.assertEqual([], result["folders"])

    # Folder import tests
    def test_confirm_folder_import_yes(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        prompt = self._prompt(["y"])
        result = confirm_folder_import(test_folder, 3, prompt)
        self.assertTrue(result)

    def test_confirm_folder_import_no(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        prompt = self._prompt(["n"])
        result = confirm_folder_import(test_folder, 3, prompt)
        self.assertFalse(result)

    def test_copy_file_with_collision_handling_no_collision(self):
        source = self._source("source.md", "content")
        dest = self.storage / "dest.md"
        prompt = self._prompt([])
        result = copy_file_with_collision_handling(source, dest, prompt)
        self.assertEqual(dest, result)
        self.assertTrue(dest.exists())
        self.assertEqual("content", dest.read_text())

    def test_copy_file_with_collision_handling_cancelled(self):
        source = self._source("source.md", "new content")
        dest = self.storage / "dest.md"
        dest.write_text("old content")
        prompt = self._prompt(["n"])
        result = copy_file_with_collision_handling(source, dest, prompt)
        self.assertIsNone(result)
        self.assertEqual("old content", dest.read_text())

    def test_import_folder_basic(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.md").write_text("content1")
        (test_folder / "file2.txt").write_text("content2")

        prompt = self._prompt(["y"])
        result = import_folder(test_folder, self.storage, prompt)

        self.assertEqual(2, len(result))
        self.assertTrue((self.storage / "test_folder" / "file1.md").exists())
        self.assertTrue((self.storage / "test_folder" / "file2.txt").exists())

    def test_import_folder_with_subfolders(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        subfolder = test_folder / "subfolder"
        subfolder.mkdir()
        (subfolder / "file.md").write_text("content")

        prompt = self._prompt(["y"])
        result = import_folder(test_folder, self.storage, prompt)

        self.assertEqual(1, len(result))
        self.assertTrue(
            (self.storage / "test_folder" / "subfolder" / "file.md").exists()
        )

    def test_import_folder_cancelled(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.md").write_text("content")

        prompt = self._prompt(["n"])
        result = import_folder(test_folder, self.storage, prompt)

        self.assertEqual(0, len(result))
        self.assertFalse((self.storage / "test_folder").exists())

    def test_import_folder_auto_rename(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.md").write_text("new content")

        # Create existing file in storage
        (self.storage / "test_folder").mkdir()
        (self.storage / "test_folder" / "file.md").write_text("old content")

        prompt = self._prompt(["y", "r"])
        result = import_folder(test_folder, self.storage, prompt, auto_rename=False)

        self.assertEqual(1, len(result))
        self.assertTrue((self.storage / "test_folder" / "file_2.md").exists())
        self.assertEqual(
            "new content", (self.storage / "test_folder" / "file_2.md").read_text()
        )

    def test_import_folder_overwrite(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.md").write_text("new content")

        # Create existing file in storage
        (self.storage / "test_folder").mkdir()
        (self.storage / "test_folder" / "file.md").write_text("old content")

        prompt = self._prompt(["y"])
        result = import_folder(test_folder, self.storage, prompt, overwrite=True)

        self.assertEqual(1, len(result))
        self.assertTrue((self.storage / "test_folder" / "file.md").exists())
        self.assertEqual(
            "new content", (self.storage / "test_folder" / "file.md").read_text()
        )

    def test_import_folder_skips_prohibited(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "list.md").write_text("content1")
        (test_folder / "valid.md").write_text("content2")

        prompt = self._prompt(["y"])
        result = import_folder(test_folder, self.storage, prompt)

        self.assertEqual(1, len(result))
        self.assertFalse((self.storage / "test_folder" / "list.md").exists())
        self.assertTrue((self.storage / "test_folder" / "valid.md").exists())

    # Folder merge tests
    def test_detect_conflicts_basic(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        (source / "file1.md").write_text("source content")
        (target / "file1.md").write_text("target content")

        conflicts = detect_conflicts(source, target)
        self.assertEqual([Path("file1.md")], conflicts)

    def test_detect_conflicts_nested(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        source_sub = source / "subfolder"
        target_sub = target / "subfolder"
        source_sub.mkdir()
        target_sub.mkdir()
        (source_sub / "file.md").write_text("source content")
        (target_sub / "file.md").write_text("target content")

        conflicts = detect_conflicts(source, target)
        self.assertEqual([Path("subfolder/file.md")], conflicts)

    def test_detect_conflicts_no_conflicts(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        (source / "file1.md").write_text("source content")
        (target / "file2.md").write_text("target content")

        conflicts = detect_conflicts(source, target)
        self.assertEqual([], conflicts)

    def test_resolve_conflict_with_prepend(self):
        source = self._source("source.md", "new content")
        target = self.storage / "target.md"
        target.write_text("old content")

        resolve_conflict_with_prepend(source, target)
        result = target.read_text()

        self.assertIn("new content", result)
        self.assertIn("old content", result)
        self.assertIn("--- MERGED ---", result)

    def test_confirm_merge_yes(self):
        target = self.storage / "target"
        target.mkdir()
        prompt = self._prompt(["y"])
        result = confirm_merge(target, prompt)
        self.assertTrue(result)

    def test_confirm_merge_no(self):
        target = self.storage / "target"
        target.mkdir()
        prompt = self._prompt(["n"])
        result = confirm_merge(target, prompt)
        self.assertFalse(result)

    def test_merge_folders_basic(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        (source / "file1.md").write_text("source content")

        prompt = self._prompt(["y"])
        result = merge_folders(source, target, prompt)

        self.assertEqual(1, len(result["merged"]))
        self.assertTrue((target / "file1.md").exists())
        self.assertEqual("source content", (target / "file1.md").read_text())

    def test_merge_folders_with_conflicts(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        (source / "file1.md").write_text("new content")
        (target / "file1.md").write_text("old content")

        prompt = self._prompt(["y"])
        result = merge_folders(source, target, prompt)

        self.assertEqual(1, len(result["conflicts"]))
        merged_content = (target / "file1.md").read_text()
        self.assertIn("new content", merged_content)
        self.assertIn("old content", merged_content)

    def test_merge_folders_cancelled(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        (source / "file1.md").write_text("source content")

        prompt = self._prompt(["n"])
        result = merge_folders(source, target, prompt)

        self.assertEqual(0, len(result["merged"]))
        self.assertFalse((target / "file1.md").exists())

    def test_merge_folders_nested_structure(self):
        source = self.workspace / "source"
        target = self.workspace / "target"
        source.mkdir()
        target.mkdir()
        source_sub = source / "subfolder"
        source_sub.mkdir()
        (source_sub / "file.md").write_text("source content")

        prompt = self._prompt(["y"])
        result = merge_folders(source, target, prompt)

        self.assertEqual(1, len(result["merged"]))
        self.assertTrue((target / "subfolder" / "file.md").exists())

    # CLI integration tests
    def test_cli_add_folder(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.md").write_text("content1")
        (test_folder / "file2.txt").write_text("content2")

        prompt = self._prompt(["y"])
        result = save_entry(test_folder, storage=self.storage, prompt_fn=prompt)

        self.assertIsNotNone(result)
        self.assertTrue((self.storage / "test_folder" / "file1.md").exists())
        self.assertTrue((self.storage / "test_folder" / "file2.txt").exists())

    def test_cli_add_folder_with_merge(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file1.md").write_text("new content")

        # Create existing folder in storage
        (self.storage / "test_folder").mkdir()
        (self.storage / "test_folder" / "file1.md").write_text("old content")

        prompt = self._prompt(["y"])
        result = save_entry(test_folder, storage=self.storage, prompt_fn=prompt)

        self.assertIsNotNone(result)
        merged_content = (self.storage / "test_folder" / "file1.md").read_text()
        self.assertIn("new content", merged_content)
        self.assertIn("old content", merged_content)

    def test_cli_retrieve_hierarchical_path(self):
        # Create folder structure
        (self.storage / "bucket").mkdir()
        (self.storage / "bucket" / "prompt1.md").write_text("bucket content")

        content = read_entry("bucket/prompt1", storage=self.storage)
        self.assertEqual("bucket content", content)

    def test_cli_retrieve_flat_path(self):
        (self.storage / "prompt1.md").write_text("flat content")

        content = read_entry("prompt1", storage=self.storage)
        self.assertEqual("flat content", content)

    def test_cli_add_folder_cancelled(self):
        test_folder = self.workspace / "test_folder"
        test_folder.mkdir()
        (test_folder / "file.md").write_text("content")

        prompt = self._prompt(["n"])
        result = save_entry(test_folder, storage=self.storage, prompt_fn=prompt)

        self.assertIsNone(result)
        self.assertFalse((self.storage / "test_folder").exists())


if __name__ == "__main__":
    unittest.main()

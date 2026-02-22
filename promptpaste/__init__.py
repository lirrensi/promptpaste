#!/usr/bin/env python3
"""
PromptPaste CLI: store reuseable prompts and instructions locally.

Commands:
- save <path>: copy a file into ~/.prompt_paste (overwriting avoided via prompts)
- <name>: print a stored entry to stdout
- list: show stored entry names
- rm <name>: delete an entry
- store: open the storage directory in your editor/file manager
"""

from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

# Reconfigure stdout to handle Unicode on Windows
if sys.platform == "win32":
    # Try to set UTF-8 encoding for stdout
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, LookupError):
            pass
    # Fallback: wrap stdout with a UTF-8 encoder
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            newline=None,
            write_through=True,
        )

# Prohibited filenames that should not be saved (e.g., hard‑coded command files)
# Check by filename prefix, not extension
PROHIBITED_PREFIXES = {"list", "rm", "add", "store", "save"}

STORAGE_ENV = "PROMPT_PASTE_STORAGE"


def get_storage_dir() -> Path:
    """Determine where snippets are kept, overrideable by PROMPT_PASTE_STORAGE."""
    override = os.environ.get(STORAGE_ENV)
    return Path(override) if override else Path.home() / ".prompt_paste"


def ensure_storage_dir() -> Path:
    """Ensure the storage folder exists and return its path."""
    directory = get_storage_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_path(path_str: str) -> str:
    """Normalize path string by removing trailing slashes and empty segments.

    Args:
        path_str: Raw path string

    Returns:
        Normalized path string

    Examples:
        >>> normalize_path('bucket/prompt1/')
        'bucket/prompt1'
        >>> normalize_path('bucket//prompt1')
        'bucket/prompt1'
    """
    # Strip leading and trailing slashes
    cleaned = path_str.strip("/")
    # Remove empty segments from double slashes
    segments = [seg for seg in cleaned.split("/") if seg]
    return "/".join(segments)


def resolve_path(path_str: str, storage: Path) -> Path:
    """Resolve a path string like 'bucket/prompt1' to storage path.

    Args:
        path_str: Path string (e.g., 'bucket/prompt1', 'prompt1', 'folder/subfolder/file.md')
        storage: Base storage directory

    Returns:
        Resolved Path object

    Examples:
        >>> resolve_path('bucket/prompt1', Path('/storage'))
        Path('/storage/bucket/prompt1.md')
        >>> resolve_path('prompt1', Path('/storage'))
        Path('/storage/prompt1.md')
    """
    normalized = normalize_path(path_str)
    segments = normalized.split("/")
    result = storage

    for segment in segments:
        result = result / segment

    # Add .md extension if no extension present
    if not result.suffix:
        result = result.with_suffix(".md")

    return result


def get_entry_by_path(path_str: str, storage: Path) -> Path:
    """Find an entry by hierarchical path, supporting partial matches.

    Args:
        path_str: Path string (e.g., 'bucket/prompt1', 'prompt1')
        storage: Base storage directory

    Returns:
        Path to the found entry

    Raises:
        FileNotFoundError: If entry not found

    Examples:
        >>> get_entry_by_path('bucket/prompt1', Path('/storage'))
        Path('/storage/bucket/prompt1.md')
        >>> get_entry_by_path('prompt1', Path('/storage'))
        Path('/storage/prompt1.md')
    """
    resolved = resolve_path(path_str, storage)

    if resolved.exists() and resolved.is_file():
        return resolved

    # Try without extension if not found
    if resolved.suffix:
        resolved_no_ext = resolved.with_suffix("")
        if resolved_no_ext.exists() and resolved_no_ext.is_file():
            return resolved_no_ext

    raise FileNotFoundError(f"Entry '{path_str}' not found in storage")


def is_eligible_file(file_path: Path) -> bool:
    """Check if a file is eligible for import (.md or .txt).

    Args:
        file_path: Path to the file

    Returns:
        True if file is .md or .txt, False otherwise

    Examples:
        >>> is_eligible_file(Path('file.md'))
        True
        >>> is_eligible_file(Path('file.py'))
        False
    """
    return file_path.suffix.lower() in {".md", ".txt"}


def is_single_skill_folder(folder: Path) -> bool:
    """Check if folder contains exactly one file: SKILL.md (skill.md standard).

    Args:
        folder: Path to the folder to check

    Returns:
        True if folder has exactly one file named "SKILL.md", False otherwise

    Examples:
        >>> is_single_skill_folder(Path('/my-skill'))  # with only SKILL.md inside
        True
        >>> is_single_skill_folder(Path('/my-skill'))  # with SKILL.md + other files
        False
    """
    if not folder.is_dir():
        return False

    files = [f for f in folder.iterdir() if f.is_file()]
    return len(files) == 1 and files[0].name == "SKILL.md"


def discover_folder_files(folder: Path) -> list[Path]:
    """Find all .md and .txt files in a folder (recursive).

    Args:
        folder: Path to the folder to scan

    Returns:
        List of file paths (relative to the folder)

    Raises:
        FileNotFoundError: If folder doesn't exist
        NotADirectoryError: If path is not a directory

    Examples:
        >>> discover_folder_files(Path('/myfolder'))
        [Path('file1.md'), Path('file2.txt'), Path('subfolder/file3.md')]
    """
    if not folder.exists():
        raise FileNotFoundError(str(folder))
    if not folder.is_dir():
        raise NotADirectoryError(str(folder))

    eligible_files = []

    for item in folder.rglob("*"):
        if item.is_file() and is_eligible_file(item):
            # Skip prohibited filenames
            if item.stem not in PROHIBITED_PREFIXES:
                # Get relative path from folder
                relative_path = item.relative_to(folder)
                eligible_files.append(relative_path)

    return sorted(eligible_files)


def get_folder_structure(folder: Path) -> dict:
    """Return folder structure with files and subfolders.

    Args:
        folder: Path to the folder to scan

    Returns:
        Dictionary with 'files' and 'folders' keys

    Examples:
        >>> get_folder_structure(Path('/myfolder'))
        {'files': [Path('file1.md'), Path('file2.txt')], 'folders': [Path('subfolder')]}
    """
    if not folder.exists():
        raise FileNotFoundError(str(folder))
    if not folder.is_dir():
        raise NotADirectoryError(str(folder))

    files = []
    folders = []

    for item in folder.iterdir():
        if item.is_file():
            files.append(item.name)
        elif item.is_dir():
            folders.append(item.name)

    return {"files": sorted(files), "folders": sorted(folders)}


def confirm_folder_import(
    folder: Path, file_count: int, prompt_fn: Callable[[str], str]
) -> bool:
    """Ask user to confirm folder import.

    Args:
        folder: Path to the folder to import
        file_count: Number of files that will be imported
        prompt_fn: Function to prompt the user

    Returns:
        True if user confirms, False otherwise

    Examples:
        >>> confirm_folder_import(Path('/myfolder'), 5, input)
        True
    """
    message = f"Import folder '{folder.name}' with {file_count} file(s)? (y/n): "
    response = prompt_fn(message).strip().lower()
    return response == "y"


def copy_file_with_collision_handling(
    source: Path,
    dest: Path,
    prompt_fn: Callable[[str], str],
    *,
    auto_rename: bool = False,
    overwrite: bool = False,
) -> Optional[Path]:
    """Copy a file with collision handling.

    Args:
        source: Source file path
        dest: Destination file path
        prompt_fn: Function to prompt the user
        auto_rename: Automatically rename with _2 suffix if collision
        overwrite: Overwrite existing file without prompting

    Returns:
        Final destination path, or None if user cancelled
    """
    final = resolve_destination(
        dest,
        prompt_fn,
        auto_rename=auto_rename,
        overwrite=overwrite,
    )
    if final is None:
        return None
    shutil.copy2(source, final)
    return final


def import_folder(
    source: Path,
    storage: Path,
    prompt_fn: Callable[[str], str],
    *,
    auto_rename: bool = False,
    overwrite: bool = False,
) -> dict[str, Path]:
    """Import folder with confirmation. Returns map of source->dest paths.

    Args:
        source: Path to the folder to import
        storage: Base storage directory
        prompt_fn: Function to prompt the user (default: input)
        auto_rename: Automatically rename with _2 suffix if collision
        overwrite: Overwrite existing file without prompting

    Returns:
        Dictionary mapping source relative paths to destination paths

    Raises:
        FileNotFoundError: If source folder doesn't exist
        NotADirectoryError: If source is not a directory

    Examples:
        >>> import_folder(Path('/myfolder'), Path('/storage'), input)
        {'file1.md': Path('/storage/myfolder/file1.md'), 'file2.txt': Path('/storage/myfolder/file2.txt')}
    """
    if not source.exists():
        raise FileNotFoundError(str(source))
    if not source.is_dir():
        raise NotADirectoryError(str(source))

    # Discover eligible files
    files = discover_folder_files(source)

    if not files:
        print(f"No eligible files found in '{source.name}'")
        return {}

    # Confirm import
    if not confirm_folder_import(source, len(files), prompt_fn):
        print("Import cancelled")
        return {}

    # Create destination folder
    dest_folder = storage / source.name
    dest_folder.mkdir(parents=True, exist_ok=True)

    # Copy files
    imported = {}
    for relative_path in files:
        source_file = source / relative_path
        dest_file = dest_folder / relative_path

        # Create parent directories if needed
        dest_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy with collision handling
        final_dest = copy_file_with_collision_handling(
            source_file,
            dest_file,
            prompt_fn,
            auto_rename=auto_rename,
            overwrite=overwrite,
        )

        if final_dest:
            imported[str(relative_path)] = final_dest

    return imported


def detect_conflicts(source: Path, target: Path) -> list[Path]:
    """Detect files that exist in both source and target.

    Args:
        source: Source folder
        target: Target folder

    Returns:
        List of relative paths to conflicting files

    Examples:
        >>> detect_conflicts(Path('/source'), Path('/target'))
        [Path('file1.md'), Path('subfolder/file2.md')]
    """
    conflicts = []
    source_files = discover_folder_files(source)

    for relative_path in source_files:
        target_file = target / relative_path
        if target_file.exists():
            conflicts.append(relative_path)

    return conflicts


def resolve_conflict_with_prepend(source: Path, target: Path) -> None:
    """Resolve conflict by prepending source content to target.

    Args:
        source: Source file path
        target: Target file path

    Examples:
        >>> resolve_conflict_with_prepend(Path('/source/file.md'), Path('/target/file.md'))
        # Target file now has source content prepended
    """
    source_content = source.read_text(encoding="utf-8", errors="ignore")
    target_content = target.read_text(encoding="utf-8", errors="ignore")

    # Add separator between contents
    separator = "\n\n--- MERGED ---\n\n"
    merged_content = source_content + separator + target_content

    target.write_text(merged_content, encoding="utf-8")


def confirm_merge(target: Path, prompt_fn: Callable[[str], str]) -> bool:
    """Ask user to confirm folder merge.

    Args:
        target: Target folder path
        prompt_fn: Function to prompt the user

    Returns:
        True if user confirms, False otherwise

    Examples:
        >>> confirm_merge(Path('/target'), input)
        True
    """
    message = f"Folder '{target.name}' already exists. Merge into it? (y/n): "
    response = prompt_fn(message).strip().lower()
    return response == "y"


def merge_folders(
    source: Path,
    target: Path,
    prompt_fn: Callable[[str], str],
) -> dict[str, list[str]]:
    """Merge source folder into target. Returns conflict report.

    Args:
        source: Source folder to merge from
        target: Target folder to merge into
        prompt_fn: Function to prompt the user

    Returns:
        Dictionary with 'merged', 'conflicts', and 'skipped' keys

    Raises:
        FileNotFoundError: If source or target doesn't exist
        NotADirectoryError: If source or target is not a directory

    Examples:
        >>> merge_folders(Path('/source'), Path('/target'), input)
        {'merged': ['file1.md'], 'conflicts': ['file2.md'], 'skipped': []}
    """
    if not source.exists():
        raise FileNotFoundError(str(source))
    if not target.exists():
        raise FileNotFoundError(str(target))
    if not source.is_dir():
        raise NotADirectoryError(str(source))
    if not target.is_dir():
        raise NotADirectoryError(str(target))

    # Detect conflicts
    conflicts = detect_conflicts(source, target)

    # Confirm merge
    if not confirm_merge(target, prompt_fn):
        print("Merge cancelled")
        return {"merged": [], "conflicts": [], "skipped": []}

    # Merge files
    merged = []
    resolved_conflicts = []
    skipped = []

    source_files = discover_folder_files(source)

    for relative_path in source_files:
        source_file = source / relative_path
        target_file = target / relative_path

        # Create parent directories if needed
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if target_file.exists():
            # Resolve conflict with prepend
            resolve_conflict_with_prepend(source_file, target_file)
            resolved_conflicts.append(str(relative_path))
        else:
            # Copy file
            shutil.copy2(source_file, target_file)
            merged.append(str(relative_path))

    return {
        "merged": merged,
        "conflicts": resolved_conflicts,
        "skipped": skipped,
    }


def resolve_destination(
    target: Path,
    prompt_fn: Callable[[str], str],
    *,
    auto_rename: bool = False,
    overwrite: bool = False,
    new_name: Optional[str] = None,
) -> Optional[Path]:
    """Handle name collisions by prompting the user for a different name.

    Args:
        target: The target path to check for collisions
        prompt_fn: Function to prompt the user (default: input)
        auto_rename: Automatically rename with _2 suffix if collision
        overwrite: Overwrite existing file without prompting
        new_name: Use this specific name instead of prompting

    Returns:
        The final destination path, or None if user cancelled
    """
    candidate = target

    # Handle auto-rename option
    if auto_rename and candidate.exists():
        suggested = candidate.parent / f"{candidate.stem}_2{candidate.suffix}"
        return suggested

    # Handle overwrite option
    if overwrite and candidate.exists():
        return candidate

    # Handle explicit new name option
    if new_name:
        candidate = candidate.parent / new_name
        if candidate.exists():
            print(
                f"Error: Name '{new_name}' already exists in storage.", file=sys.stderr
            )
            return None
        return candidate

    # Handle user prompting
    while candidate.exists():
        suggested = candidate.parent / f"{candidate.stem}_2{candidate.suffix}"
        message = (
            f"Entry '{candidate.name}' already exists.\n"
            f"\n"
            f"Options:\n"
            f"  n/N - Cancel and exit\n"
            f"  r/R - Rename to suggested name: '{suggested.name}'\n"
            f"  o/O - Overwrite existing file\n"
            f"  <type> - Enter your own name\n"
            f"\n"
            f"Your choice: "
        )
        response = prompt_fn(message).strip()
        if not response:
            print("Cancelled.")
            return None
        normalized = response.lower()
        if normalized == "n":
            print("Cancelled.")
            return None
        if normalized == "r":
            candidate = suggested
            continue
        if normalized == "o":
            return candidate
        # User entered their own name
        candidate = candidate.parent / Path(response).name
        if candidate.exists():
            print(
                f"Error: Name '{response}' already exists in storage.", file=sys.stderr
            )
            continue
    return candidate


def save_entry(
    source: Path,
    *,
    storage: Optional[Path] = None,
    prompt_fn: Callable[[str], str] = input,
    auto_rename: bool = False,
    overwrite: bool = False,
    new_name: Optional[str] = None,
) -> Optional[Path]:
    """
    Copy a file or folder into storage. Returns the saved path, or None if user cancelled.

    Raises FileNotFoundError when the source path is missing.

    Args:
        source: Path to the source file or folder
        storage: Optional custom storage directory
        prompt_fn: Function to prompt the user (default: input)
        auto_rename: Automatically rename with _2 suffix if collision
        overwrite: Overwrite existing file without prompting
        new_name: Use this specific name instead of prompting
    """
    if not source.exists():
        raise FileNotFoundError(str(source))

    dest_dir = storage or ensure_storage_dir()

    # Handle folder import
    if source.is_dir():
        # Check for skill.md standard: single SKILL.md file → import as named file
        if is_single_skill_folder(source):
            skill_file = list(source.iterdir())[0]  # The SKILL.md file
            target = dest_dir / f"{source.name}.md"
            final = resolve_destination(
                target,
                prompt_fn,
                auto_rename=auto_rename,
                overwrite=overwrite,
                new_name=new_name,
            )
            if final is None:
                return None
            shutil.copy2(skill_file, final)
            print(f"Imported skill '{source.name}' as {final.name}")
            return final

        target_folder = dest_dir / source.name

        # Check if folder already exists
        if target_folder.exists():
            # Merge into existing folder
            result = merge_folders(source, target_folder, prompt_fn)
            if result["merged"] or result["conflicts"]:
                print(
                    f"Merged {len(result['merged'])} file(s), resolved {len(result['conflicts'])} conflict(s)"
                )
                if result["conflicts"]:
                    print(
                        "Note: Conflicts were auto-resolved with prepend. Review manually if needed."
                    )
            return target_folder
        else:
            # Import new folder
            result = import_folder(
                source,
                dest_dir,
                prompt_fn,
                auto_rename=auto_rename,
                overwrite=overwrite,
            )
            if result:
                print(f"Imported {len(result)} file(s) from '{source.name}'")
            return target_folder if result else None

    # Handle file import
    # Check if filename starts with any prohibited prefix
    if source.stem in PROHIBITED_PREFIXES:
        print(
            f"Error: '{source.name}' is a prohibited filename and cannot be saved.",
            file=sys.stderr,
        )
        return None

    target = dest_dir / source.name
    final = resolve_destination(
        target,
        prompt_fn,
        auto_rename=auto_rename,
        overwrite=overwrite,
        new_name=new_name,
    )
    if final is None:
        return None
    shutil.copy2(source, final)
    return final


def list_entries(storage: Optional[Path] = None) -> Iterable[Path]:
    """Return sorted stored entry names."""
    directory = storage or ensure_storage_dir()
    return sorted(directory.iterdir())


# ANSI color codes for terminal output
COLOR_RESET = "\033[0m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"


def list_entries_with_preview(storage: Optional[Path] = None) -> None:
    """Print stored entries with filename, lines + chars, and first line preview."""
    directory = storage or ensure_storage_dir()

    def print_entry(entry: Path, indent: int = 0) -> None:
        """Print a single entry with indentation."""
        try:
            content = entry.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n") + 1
            chars = len(content)
            # Format filename with color and indentation
            prefix = "  " * indent
            print(f"{prefix}{COLOR_CYAN}> {entry.name}{COLOR_RESET}")
            print(
                f"{prefix}{COLOR_GREEN}  (lines: {lines}, chars: {chars}){COLOR_RESET}"
            )
            # Get first line and limit to 64 characters
            first_line = content.split("\n")[0].strip()
            if first_line:
                if len(first_line) > 64:
                    first_line = first_line[:64] + "..."
                print(f"{prefix}{COLOR_YELLOW}  {first_line}{COLOR_RESET}\n")
            else:
                print()
        except Exception:
            prefix = "  " * indent
            print(f"{prefix}{COLOR_CYAN}> {entry.name}{COLOR_RESET}\n")

    def walk_directory(path: Path, indent: int = 0) -> None:
        """Recursively walk directory and print entries."""
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

        for item in items:
            if item.is_dir():
                # Print folder name
                prefix = "  " * indent
                print(f"{prefix}{COLOR_CYAN}[DIR] {item.name}/{COLOR_RESET}\n")
                # Recursively walk subdirectory
                walk_directory(item, indent + 1)
            else:
                # Print file
                print_entry(item, indent)

    walk_directory(directory)


def find_entry_by_id(name: str, directory: Path) -> Path:
    """Return the stored file whose stem matches the requested id."""
    matches = [entry for entry in directory.iterdir() if entry.stem == name]
    if not matches:
        raise FileNotFoundError(name)
    return sorted(matches)[0]


def read_entry(name: str, storage: Optional[Path] = None) -> str:
    """Return the contents of a stored entry id."""
    directory = storage or ensure_storage_dir()
    try:
        entry = get_entry_by_path(name, directory)
    except FileNotFoundError:
        # Fall back to old behavior for backward compatibility
        entry = find_entry_by_id(name, directory)
    return entry.read_text(encoding="utf-8", errors="ignore")


def remove_entry(name: str, storage: Optional[Path] = None) -> None:
    """Delete an entry by id."""
    directory = storage or ensure_storage_dir()
    entry = find_entry_by_id(name, directory)
    entry.unlink()


def open_storage(storage: Optional[Path] = None) -> None:
    """Open the storage directory in the OS file manager or editor."""
    directory = storage or ensure_storage_dir()
    if sys.platform.startswith("win"):
        os.startfile(str(directory))
        return
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.run([opener, str(directory)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        editor = os.environ.get("EDITOR", "vi")
        subprocess.run([editor, str(directory)])


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(prog="pp", add_help=False)
    parser.add_argument("command", nargs="*", help="Command or entry name")
    parser.add_argument("--help", action="help", help="Show this message and exit")

    # Add new options for save/add command
    parser.add_argument(
        "-r",
        "--rename",
        action="store_true",
        help="Auto-rename with _2 suffix if collision",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Overwrite existing file without prompting",
    )
    parser.add_argument(
        "-n", "--new-name", type=str, help="Use this specific name for the entry"
    )

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    head, *rest = args.command
    storage = ensure_storage_dir()

    try:
        if head in {"save", "add"}:
            if not rest:
                parser.error(f"{head} requires a filepath argument")
            source = Path(rest[0]).expanduser()
            final = save_entry(
                source,
                storage=storage,
                auto_rename=args.rename,
                overwrite=args.overwrite,
                new_name=args.new_name,
            )
            if final:
                print(f"Saved entry as {final.name}")
            return 0

        if head == "list":
            list_entries_with_preview(storage)
            return 0

        if head == "rm":
            if not rest:
                parser.error("rm requires an entry name")
            remove_entry(rest[0], storage=storage)
            print(f"Removed entry {rest[0]}")
            return 0

        if head == "store":
            open_storage(storage)
            return 0

        if rest:
            parser.error("too many arguments")
        try:
            content = read_entry(head, storage=storage)
        except FileNotFoundError:
            return 0
        print(content)
        return 0

    except FileNotFoundError as exc:
        if head in {"save", "add"}:
            print(f"Error: source file/folder not found: {exc}", file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

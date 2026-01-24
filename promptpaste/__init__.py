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
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional

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
            print(f"Error: Name '{new_name}' already exists in storage.", file=sys.stderr)
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
            print(f"Error: Name '{response}' already exists in storage.", file=sys.stderr)
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
    Copy a file into storage. Returns the saved path, or None if user cancelled.

    Raises FileNotFoundError when the source path is missing.
    
    Args:
        source: Path to the source file
        storage: Optional custom storage directory
        prompt_fn: Function to prompt the user (default: input)
        auto_rename: Automatically rename with _2 suffix if collision
        overwrite: Overwrite existing file without prompting
        new_name: Use this specific name instead of prompting
    """
    if not source.exists():
        raise FileNotFoundError(str(source))
    if source.is_dir():
        raise IsADirectoryError(str(source))
    # Check if filename starts with any prohibited prefix
    if source.stem in PROHIBITED_PREFIXES:
        print(f"Error: '{source.name}' is a prohibited filename and cannot be saved.", file=sys.stderr)
        return None

    dest_dir = storage or ensure_storage_dir()
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
    for entry in list_entries(storage):
        try:
            content = entry.read_text(encoding="utf-8", errors="ignore")
            lines = content.count('\n') + 1
            chars = len(content)
            # Format filename with color
            print(f"{COLOR_CYAN}> {entry.name}{COLOR_RESET}")
            print(f"{COLOR_GREEN}  (lines: {lines}, chars: {chars}){COLOR_RESET}")
            # Get first line and limit to 64 characters
            first_line = content.split('\n')[0].strip()
            if first_line:
                if len(first_line) > 64:
                    first_line = first_line[:64] + "..."
                print(f"{COLOR_YELLOW}  {first_line}{COLOR_RESET}\n")
            else:
                print()
        except Exception:
            print(f"{COLOR_CYAN}> {entry.name}{COLOR_RESET}\n")


def find_entry_by_id(name: str, directory: Path) -> Path:
    """Return the stored file whose stem matches the requested id."""
    matches = [entry for entry in directory.iterdir() if entry.stem == name]
    if not matches:
        raise FileNotFoundError(name)
    return sorted(matches)[0]


def read_entry(name: str, storage: Optional[Path] = None) -> str:
    """Return the contents of a stored entry id."""
    directory = storage or ensure_storage_dir()
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
    parser.add_argument("-r", "--rename", action="store_true",
                        help="Auto-rename with _2 suffix if collision")
    parser.add_argument("-o", "--overwrite", action="store_true",
                        help="Overwrite existing file without prompting")
    parser.add_argument("-n", "--new-name", type=str,
                        help="Use this specific name for the entry")

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
            print(f"Error: source file not found: {exc}", file=sys.stderr)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    except IsADirectoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

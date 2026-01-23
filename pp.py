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
    target: Path, prompt_fn: Callable[[str], str]
) -> Optional[Path]:
    """Handle name collisions by prompting the user for a different name."""
    candidate = target
    while candidate.exists():
        suggested = candidate.parent / f"{candidate.stem}_2{candidate.suffix}"
        message = (
            f"Entry {candidate.name} exists. "
            f"Type 'y' to rename to {suggested.name}, 'n' to cancel, or a new name: "
        )
        response = prompt_fn(message).strip()
        if not response:
            print("Cancelled.")
            return None
        normalized = response.lower()
        if normalized == "y":
            candidate = suggested
            continue
        if normalized == "n":
            print("Cancelled.")
            return None
        candidate = candidate.parent / Path(response).name
    return candidate


def save_entry(
    source: Path,
    *,
    storage: Optional[Path] = None,
    prompt_fn: Callable[[str], str] = input,
) -> Optional[Path]:
    """
    Copy a file into storage. Returns the saved path, or None if user cancelled.

    Raises FileNotFoundError when the source path is missing.
    """
    if not source.exists():
        raise FileNotFoundError(str(source))
    if source.is_dir():
        raise IsADirectoryError(str(source))

    dest_dir = storage or ensure_storage_dir()
    target_name = source.stem or source.name
    target = dest_dir / target_name
    final = resolve_destination(target, prompt_fn)
    if final is None:
        return None
    shutil.copy2(source, final)
    return final


def list_entries(storage: Optional[Path] = None) -> Iterable[Path]:
    """Return sorted stored entry names."""
    directory = storage or ensure_storage_dir()
    return sorted(directory.iterdir())


def read_entry(name: str, storage: Optional[Path] = None) -> str:
    """Return the contents of a stored entry name."""
    directory = storage or ensure_storage_dir()
    entry = directory / name
    if not entry.exists():
        raise FileNotFoundError(name)
    return entry.read_text(encoding="utf-8", errors="ignore")


def remove_entry(name: str, storage: Optional[Path] = None) -> None:
    """Delete an entry by name."""
    directory = storage or ensure_storage_dir()
    entry = directory / name
    if not entry.exists():
        raise FileNotFoundError(name)
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
            final = save_entry(source, storage=storage)
            if final:
                print(f"Saved entry as {final.name}")
            return 0

        if head == "list":
            entries = list_entries(storage)
            for entry in entries:
                print(entry.name)
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

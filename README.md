# PromptPaste

PromptPaste keeps the prompts, checklists, and shell snippets you keep pasting anyway in one tidy place so you can dump them into any agent interaction with a single command.

## What it solves
- avoids hunting down `do_tests.md`, `AGENTS.md`, or that `!py` command you always forget
- keeps every helpful instruction in `~/.prompt_paste`, keyed by filename
- makes copying the same instructions into multiple projects accidentally fast
- gives you a tiny CLI so you can save, recall, and manage clips without editing a million files

## Features
- `pp add path/to/file` is an alias for `save` that keeps the same behavior
- `pp save path/to/file` copies a file (the full filename and extension stay intact) into the storage dir (`~/.prompt_paste` by default)
- `pp <name>` prints the stored snippet so you can pipe it into another agent (missing entries exit quietly)
- `pp list` lists every stored entry (names include the original extension)
- `pp rm <name>` deletes a snippet (you can still keep copies in your project)
- `pp store` opens the storage directory in your file manager/editor
- entry IDs use the filename without its extension, so `pp add 123.md` saves to `123.md` and you retrieve via `pp 123`
- collision guard: if you save a name that already exists the CLI prompts you to rename, auto‑suffix, or cancel
- storage path is overrideable with `PROMPT_PASTE_STORAGE` for portability or testing

## Installation
1. Clone this repo if you haven't already:

   ```bash
   git clone <repo> && cd <repo>
   ```

2. Install via `pip` or `uv` from the Git link:

   ```bash
   pip install git+https://github.com/<org>/PromptPaste.git
   uv tool install git+https://github.com/<org>/PromptPaste.git
   ```

3. After installing from git you can always reinstall or update in place by rerunning whichever install command.

4. Or use the bundled helper scripts after setting execute rights:

   ```bash
   chmod +x scripts/install_pp.sh
   ./scripts/install_pp.sh            # copies pp to ~/.local/bin/pp (prefix with dir to customize)
   powershell -ExecutionPolicy Bypass -File scripts/install_pp.ps1  # installs to %USERPROFILE%\.local\bin
   ```

   Running those scripts multiple times simply overwrites the previous copy so you can update pp without extra cleanup.

## Usage
- `pp save reminders/do_tests.md` copies `do_tests.md` to `~/.prompt_paste`.
- `pp add reminders/do_tests.md` does the same and demonstrates the alias.
- `pp do_tests` (or `pp do_tests.md`) prints the stored instructions so you can paste them straight into your next agent run.
- `pp list` shows everything you have saved; missing entries fail quietly instead of emitting errors.
- `pp store` opens the storage directory so you can edit multiple entries.
- `pp rm obsolete` deletes a stored entry when it is no longer useful.
- Save with a colliding name? you'll be prompted to rename, cancel, or auto-append `_2`.

You can also copy `~/.prompt_paste/<name>` anywhere you need it, or configure the storage path with `PROMPT_PASTE_STORAGE=/tmp/stash pp ...` for short-lived clips.

## Testing
Run the bundled tests via the standard library:

```bash
python3 -m unittest tests.test_pp
```

The tests exercise saving, collision handling, listing, reading, and deleting entries without touching your real `~/.prompt_paste`.

## Notes
- The tool avoids dependencies; it only requires Python 3.8+.
- Saving or adding a nonexistent file prints an error (`Error: ...`) and exits with code 1, so you know the snippet was not recorded.
- Use `pp` as a quick clipboard replacement whenever you want to reuse policies, checklists, or commands without retyping them.

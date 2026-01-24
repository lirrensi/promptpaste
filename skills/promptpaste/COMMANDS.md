# PromptPaste command reference

## Storage location
- Default path: `~/.prompt_paste/`.
- Override for the current shell or CI by setting `PROMPT_PASTE_STORAGE` (exported as `STORAGE_ENV` inside `pp.py`).
- The bundled tests create temporary storage directories and rely on an ENV override so they never touch your real library.

## Covered commands
| Command | Description |
| --- | --- |
| `pp save <path>` | Copy `<path>` into storage without overwriting unless you accept a change. |
| `pp add <path>` | Alias for `save`. |
| `pp <name>` | Dump the saved entry whose stem matches `<name>` (silent miss if missing). |
| `pp list` | Show every stored entry plus line/char counts and a truncated preview of the first line. |
| `pp rm <name>` | Delete the entry named `<name>`. |
| `pp store` | Open the storage folder in your OS file manager or, as a fallback, your `$EDITOR`. |
| `pp --help` | Print the concise usage overview and options. |

## Save-time options
- `-r` / `--rename`: Auto-append `_2` when a collision occurs.
- `-o` / `--overwrite`: Skip the collision prompt and replace the existing file.
- `-n` / `--new-name`: Supply a specific saved name (fails if that name already exists).
- Collisions without flags trigger the interactive `n/r/o/<type>` prompt sequence. Cancel with `n` or close the prompt by pressing Enter on a blank line.
- Filenames that begin with `list`, `rm`, `add`, `store`, or `save` are rejected to prevent conflicts with built-in commands.

## Meta usage notes
- PromptPaste is a standalone helper—entries live in your home directory so you can reuse the same snippets across every agent session, repo, or skill you work on.
- The CLI is intentionally minimal: filenames act as IDs, and requesting a missing entry just prints nothing so you can rerun the command without extra output.
- Save drafts of AGENTS.md fragments, test checklists, or skill templates once (`pp save path/to/SKILL.md`) and paste them wherever you need them next.

## Testing this project
- Run `python -m unittest tests.test_pp` to exercise saving, listing, reading, and deletion logic against a temporary storage directory.

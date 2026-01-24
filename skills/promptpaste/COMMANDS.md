# PromptPaste command reference

## Storage location
- Default path: `~/.prompt_paste/`.
- Override for the current shell or CI by setting `PROMPT_PASTE_STORAGE` (exported as `STORAGE_ENV` inside `pp.py`).
- Tests rely on supplying their own temporary storage directory and a short-lived ENV override before each run.

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
- Keep AGENTS.md snippets, SKILL templates, or testing checklists in PromptPaste so you can paste them into any agent or new skill without hunting across repos.
- The CLI is intentionally minimal—everything stays local, filenames are identities, and retrieving a missing ID simply prints nothing so you can re-run the command without noise.
- Combine this tool with new skills by saving reusable answers once (`pp save skills/???/SKILL.md`) and pasting them into whichever project needs them.

## Testing this project
- Run `python -m unittest tests.test_pp` to exercise saving, listing, reading, and deletion logic against a temporary storage directory.

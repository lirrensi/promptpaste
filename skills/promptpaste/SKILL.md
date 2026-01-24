---
name: promptpaste-clipboard
description: Refer to the installed `pp` CLI when you need to save, recall, or manage reusable prompts/snippet files across your agent workflows—use this skill when you want the local snippet library without hunting through repo history or agent configs.
---

# PromptPaste clipboard

## When to use this skill
- You have the `pp` CLI installed and want a dedicated reminder about storing snippets, find AGENTS/SKILL templates, or keep checklists ready for any agent session.
- You need a fast way to reuse verified prompts or instructions without re-scanning the current repo; `pp` keeps everything in `~/.prompt_paste`.
- You want to drop reusable text into another skill, prompt, or testing session and prefer to recall it via a single `pp <name>` call.

## Typical interaction with `pp`
1. Save a helper file (like an AGENTS fragment, `do_tests` checklist, or CLI snippet) via `pp save path/to/file`.
2. Recall it anywhere with `pp snippet-name`. Missing entries are silently ignored so you can rerun without noise.
3. Open your clipboard (`pp store`) when you need to edit many entries or share the stored directory.
4. List the library with `pp list` for quick previews before selecting the snippet you need.

## Meta reminders
- `pp` is intentionally repo-agnostic; entries live in `~/.prompt_paste/` (or `PROMPT_PASTE_STORAGE` if you override it) and can be reused across projects.
- Names are taken from filenames and collisions prompt the `n/r/o` workflow unless you pass `-r`, `-o`, or `-n`.
- Combine this skill with others by saving skill drafts (`pp save skills/whatever/SKILL.md`) and pasting them into the target repo when ready.

See [COMMANDS.md](COMMANDS.md) for the full command and option reference.

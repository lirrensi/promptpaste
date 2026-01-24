---
name: promptpaste-clipboard
description: Save, recall, and manage reusable prompts for this repo and for spin-ups of new skills—use when you need quick access to AGENTS/SKILL guidance, testing checklists, or otherwise repeat common instructions across agents.
---

# PromptPaste clipboard

## When to bring this skill in
- You already have the text of an AGENTS.md, checklist, or `do_tests` script that you want to reuse across agents without hunting for the file.
- You are drafting another skill and need to stash templates, snippets, or reminders that you can paste into a SKILL.md or prompt quickly.
- You want a consistent place to keep the „how we run tests“ or „how we save files“ SOP for any CLI-driven agent.

## Common workflow
1. Create or update a note file (e.g., `reminders/do_tests.md`, `skills/new-skill/template.md`) inside this repo and run `pp save <path>`.
2. Recall the snippet in any agent with `pp <name>` or inspect the library with `pp list`.
3. If you need to edit dozens of entries, run `pp store` to open `~/.prompt_paste/` in your preferred editor or file manager.
4. Share reusable guidance (AGENTS fragments, checklists, CLI idioms) by saving once and pasting everywhere instead of retyping.

## Meta notes for skill layering
- Store SKILL instructions in PromptPaste as well as the files you edit here; you can `pp save skills/new-skill/SKILL.md` before copying sections into a repo-specific skill, making experimentation frictionless.
- Remember that PromptPaste is intentionally simple: names match filenames, collisions prompt the usual `n/r/o` choices, and everything defaults to `~/.prompt_paste`.

See [COMMANDS.md](COMMANDS.md) for encoded workflow options, environment overrides, and test commands.

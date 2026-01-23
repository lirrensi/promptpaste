# PromptPaste a smol useful helper to reduce your repetitive actions pasting instructions.

## Have you:
- Copied same 'make this' prompt over and over? Having to find it first, then copy?
- Constantly have to write "do the tests FFS", always forgetting the correct order and details your agent will surely miss and cause frustration?
- Making 10+ subagents in ClaudeCode/OpenCode even if they literally same with just a **slightly** different prompt?
- Have to copy lists of instructions/guidelines from one project to another? Having useful stuff scattered in all places you have to waste 10min rg'ing it?
- Even with if you have cool single place to copy from, remembering each time full path? Thinking what bash command?

Prompting should be simple! You know already what to send, just need a shortcut to extract it!

## This small tool does literally one thing: stores your prompts and stdouts on demand

```bash
pp save do_tests.md # grabs the file and copies it to your ~/.prompt_paste/ under same name

# then:
pp do_tests # dumps file content

# want to edit later?
pp store # opens explored/editor with ~/.prompt_paste

```


## Why this may help:
- most coding agents support !(!!) to run arbitrary bash command and this becoming a standard quality UX
- most coding agents support direct prompt passing (claude -p ... / opencode run ...)
- easy to copy/paste same docs/instructions or literally same AGENTS.md part at each project


## Intentionally simple
- no subdirs/profiles/etc
- filename === id, if collision, asks you to rename
- no configs, no nothing!

If you want complex functionality and power features - check out https://github.com/tobi/qmd

## Install
uv tool install <git link will be here>
```pp help```

## Additional commands

```bash
pp rm <name> # or just delete file manually lol
pp help # if u get lost in 4 commands...
```

## Gotchas
- no size limits, yeet in 10k lines text file - rip your terminal
- if no such id present - it will fail silently, no error - that is to not pollute your input on mistype

---


that was readme, implementation:

- single py file, no deps (ideally)
- support md + txt files

- filename= id, on collision do input(): detected same name: y to add as {filename}_2, n to cancel or type new filename right here instead + enter;



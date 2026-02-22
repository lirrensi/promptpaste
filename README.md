# PromptPaste: Your Lazy Agent’s Best Friend 🚀
*(Because copying/pasting the same commands 20 times is for peasants.)*

---

## **Do You Relate?** 🤯
- **You’ve copied the same "make this" prompt 100 times** and now your muscle memory is broken. 🧠💥
- **You keep forgetting the exact command** for running tests, and your agent *still* misses something (thanks, autocorrect). 😤
- **You’re spawning 10+ identical subagents** in ClaudeCode/OpenCode, just to tweak a *single word*. 🤖🔄
- **You hunt for `do_tests.md`, `AGENTS.md`, or that `!py` command** you *swear* you saved. 🗃️🔍
- **You have a "single place to copy from"** but still can’t remember the filename (or bash command) when it matters. 📂🤦

**Prompting should be effortless.** You *know* what to send—you just need a shortcut. ✨

---

## **The Solution: A Microscopic, Opinionated Clipboard for Your CLI**
This tool does **one thing, and does it well**:
Store your prompts, checklists, and shell snippets in **one tidy place** so you can dump them into any agent interaction with a single command. 👀

### **How It Works (TL;DR)**
```bash
pp save reminders/do_tests.md  # Save a file to ~/.prompt_paste/ (✨ *magic* ✨)
pp do_tests                    # Agent: "Here’s your test script. Don’t mess it up." 🤖
pp store                       # Open your prompt library in an editor (because you *will* edit it). ✏️
```

### **Why This Fixes Your Problems** 🎯
✅ **No more hunting**: Never waste time searching for `do_tests.md` or `AGENTS.md` again.
✅ **Single place for everything**: All your helpful instructions live in `~/.prompt_paste`, keyed by filename. 📁
✅ **Accidentally fast**: Copy the same instructions across projects **without thinking**. 🔁
✅ **Tiny CLI**: Save, recall, and manage clips **without editing a million files**. ⚡

---

## How is that different from SKILL.md format?

They are similar but skills were intended as a procedural knowledge first, this format is intent-agnostic:
- you can store long manuals of how-to (exactly that skill does)
- instructions
- just reminders to do things `this way only pls`

This solves problem of having to copy skills to all projects/coding agents, its easy if you use single CC/codex but if you experiment with many of them? And having to remember which skill loaded where?
Also skill selection if not always a transparent process - here you have direct control over what pasted in!

And you can combine with skills too! Just reference like "use `pp ssh_manual` to know how to connect to xyz"

Or save multiple building blocks for a skill to create them faster! Just pipe many `pp <file>` commands to together and save to skills/xyz/SKILL.md

---

## **Features** 🌟
| Command               | What It Does                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| `pp save <path>`      | Copies a file to `~/.prompt_paste/` (keeps original filename/extension). 📝 |
| `pp add <path>`       | Alias for `save` (same behavior, different name). 🔄                     |
| `pp <name>`           | Prints the stored snippet (so you can paste it into your agent). 🤖          |
| `pp list`             | Lists **all** stored entries with filename and first line preview. 📋     |
| `pp rm <name>`        | Deletes a snippet (but you can keep copies elsewhere). 🗑️                |
| `pp store`            | Opens the storage directory in your editor/file manager. ✏️             |

### **Collision Handling** 🎯
When saving a file that already exists, you have several options:

**Interactive mode (default):**
```
Entry 'test.md' already exists.

Options:
  n/N - Cancel and exit
  r/R - Rename to suggested name: 'test_2.md'
  o/O - Overwrite existing file
  <type> - Enter your own name

Your choice:
```

**Command-line helpers:**
- `pp add <file> -r` - Auto-rename with `_2` suffix if collision
- `pp add <file> -o` - Overwrite existing file without prompting
- `pp add <file> -n "name"` - Use specific name for the entry

### **Bonus Features**
- **Collision guard**: Smart collision handling with multiple options. 🤔
- **Custom storage path**: Override with `PROMPT_PASTE_STORAGE=/path/to/dir pp ...` for testing or portability. 🔄
- **Silent failures**: Missing entries? **No errors**—just nothing happens. (Because you already have enough noise.) 🤫
- **skill.md compatibility**: Folders with a single `SKILL.md` file are imported as `{folder_name}.md` — compatible with the [skill.md standard](https://agentskills.io/). 🎯

---

## **Installation (Because You Can’t Wait)** 🚀
### **Option 1: Install via `pip` or `uv`**
```bash
pip install git+https://github.com/lirrensi/promptpaste.git
# or
uv tool install git+https://github.com/lirrensi/promptpaste.git
```

### **Option 2: Manual Install (For the Rebels)**
```bash
# Linux/macOS
chmod +x scripts/install_pp.sh
./scripts/install_pp.sh          # Installs to `~/.local/bin/pp` (customize with dir prefix)

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/install_pp.ps1
# Installs to `%USERPROFILE%\.local\bin`
```

✅ **Update later**: Just rerun the install command—it overwrites safely!

---

## **Usage Examples** 🎯
```bash
# Save a file
pp save reminders/do_tests.md

# Recall and pipe into an agent
pp do_tests | claude -p

# List everything you’ve saved
pp list

# Open storage dir for bulk editing
pp store

# Delete unused entries
pp rm obsolete_prompt
```

### **Pro Tips**
- **Auto-rename**: Use `pp add file.md -r` to automatically append `_2` to avoid collisions. 🔄
- **Force overwrite**: Use `pp add file.md -o` to silently overwrite existing files. ⚡
- **Custom names**: Use `pp add file.md -n "custom_name"` to save with a specific name. 📝
- **Configure storage path** for **testing or short-lived clips** without touching your main `~/.prompt_paste`. 🔄

---

## **Testing** 🧪
Run the bundled tests to ensure everything works:
```bash
python3 -m unittest tests.test_pp
```

✅ **Tests cover**: Saving, collision handling, listing, reading, and deleting—**all without touching your real storage**. 🎉

---

## **Notes** 📝
- **Zero dependencies**: Just Python 3.8+ (because we keep it simple). 🐍
- **Error handling**: If you try to save a nonexistent file, it **yells at you** (so you know it failed). 🚨
- **Use it as a clipboard**: Reuse policies, checklists, or commands **without retyping them**. ✂️

---
**Want more power features?** Check out [qmd](https://github.com/tobi/qmd) (this was an inspiration for this project). 📚
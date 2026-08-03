---
name: memento-install
description: Install the memento machinery to ~/.memento so the memento skills work from any directory. Use when the user asks to install or set up memento, or when a memento skill reports that no library exists at the resolved MEMENTO_ENV.
---

# Install memento

Installs the memento machinery bundled with this plugin to `~/.memento`, the
library the other memento skills fall back to when a project has no `.memento/`
of its own. Everything needed is inside `${CLAUDE_PLUGIN_ROOT}` — no clone, no
network, and no repository is required.

This installs machinery only: `scripts/`, `resources/`, `index.md` and the
category registry. Atomic skills are personal and are never shipped, so a fresh
install has an empty skill library that the user fills with /memento-add-skill.
Re-running is the upgrade path — the machinery is replaced, while the user's
skills and run logs are left alone.

## Procedure

1. Confirm `just` is on PATH: `command -v just`. If it is missing, stop and tell
   the user to install it (`brew install just`, or see
   https://github.com/casey/just) — it is the only requirement beyond `bash`,
   `awk` and `python3`.
2. Run the bundled justfile:
   ```bash
   just --justfile "${CLAUDE_PLUGIN_ROOT}/justfile" --working-directory "${CLAUDE_PLUGIN_ROOT}" install
   ```
3. Report what it printed. The library line distinguishes a fresh install
   (`empty skill library created`) from an upgrade (`existing skill library left
   untouched (N skill(s))`), and the builder line gives the node and edge counts
   — both are 0 on a fresh install, which is expected, not an error.
4. Confirm the machinery works: `"$HOME/.memento/scripts/memento_env.sh"` should
   print a path, and `"$HOME/.memento/scripts/build_skill_graph.sh" --help 2>&1 | head -1`
   should not report a missing file.
5. Tell the user what to do next. `~/.memento` is now used from any directory
   except one holding its own `.memento/`, which shadows it; an exported
   `MEMENTO_ENV` overrides both. The library is empty, so /memento has nothing
   to chain yet — point them at /memento-add-skill, and note that skills kept
   only in `~/.memento/skills/` stay out of every repository while remaining
   available everywhere.

---
name: memento-remove-skill
description: Remove an atomic skill from the memento library and rebuild the skill graph. Use when the user asks to remove or delete a memento skill (e.g. "remove the kokoro tts skill").
---

# Remove a memento skill

Delete one skill directory from `$MEMENTO_ENV/skills/` and rebuild the graph. Removal is destructive — never proceed on a guess.

## Procedure

0. Resolve the library first — every path below is relative to it:
   ```bash
   MEMENTO_ENV="${MEMENTO_ENV:-$([ -d .memento ] && echo ./.memento || echo "$HOME/.memento")}"
   ```
   A project-local `.memento/` shadows the personal library in `~/.memento`; an already-set `MEMENTO_ENV` wins over both. State which library resolved as part of the confirmation in step 2 — deleting from the personal library affects every project, so the user must know which one is about to lose the skill.
1. Resolve the exact skill id `category/subcategory/skill_name`; the directory with its `SKILL.md` must exist under `$MEMENTO_ENV/skills/`. If the user's wording matches zero or several skills, list the candidates and ask — never guess.
2. Show the blast radius before deleting: `grep '<skill id>' "$MEMENTO_ENV/graph/skills_edges.txt"`. Chains through this node will break. If the user did not name this exact skill explicitly, confirm before deleting.
3. Delete the skill directory: `rm -rf "$MEMENTO_ENV/skills/<category>/<subcategory>/<skill_name>"`
4. Prune now-empty parents: remove the subcategory directory if it is empty, then the category directory if it is empty. If the category directory was removed, delete its row from `$MEMENTO_ENV/skills/categories.md`.
5. Rebuild the graph and verify: `"$MEMENTO_ENV/scripts/build_skill_graph.sh"`. Inside the memento repository run `just test` instead — it rebuilds first, then asserts graph correctness.
6. Report: the removed node and its former edges, plus any remaining skill that lost its only inbound or outbound connection (now unreachable in chains).

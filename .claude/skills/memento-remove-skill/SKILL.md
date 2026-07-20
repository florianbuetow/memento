---
name: memento-remove-skill
description: Remove an atomic skill from the .memento library and rebuild the skill graph. Use when the user asks to remove or delete a memento skill (e.g. "remove the kokoro tts skill").
---

# Remove a memento skill

Delete one skill directory from `.memento/skills/` and rebuild the graph. Removal is destructive — never proceed on a guess.

## Procedure

1. Resolve the exact skill id `category/subcategory/skill_name`; the directory with its `SKILL.md` must exist. If the user's wording matches zero or several skills, list the candidates and ask — never guess.
2. Show the blast radius before deleting: `grep '<skill id>' .memento/graph/skills_edges.txt`. Chains through this node will break. If the user did not name this exact skill explicitly, confirm before deleting.
3. Delete the skill directory: `rm -rf .memento/skills/<category>/<subcategory>/<skill_name>`
4. Prune now-empty parents: remove the subcategory directory if it is empty, then the category directory if it is empty. If the category directory was removed, delete its row from `.memento/skills/categories.md`.
5. Rebuild the graph and verify: `just test` (it runs `just build` first).
6. Report: the removed node and its former edges, plus any remaining skill that lost its only inbound or outbound connection (now unreachable in chains).

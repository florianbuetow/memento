---
name: memento-update-skill
description: Update an existing atomic skill in the .memento library (interface types, procedure, helper scripts, or rename/move) and rebuild the skill graph. Use when the user asks to change, edit, rename, or move a memento skill.
---

# Update a memento skill

Modify one existing skill under `.memento/skills/` and rebuild the graph. Interface changes (inputs/outputs) change the graph's edges, so the rebuild is mandatory.

## Procedure

1. Read the target skill's `SKILL.md` and `.memento/resources/skill_guide.md`. Capture the "before" picture: `grep '<skill id>' .memento/graph/skills_nodes.txt .memento/graph/skills_edges.txt`
2. Apply exactly the requested change — nothing more:
   - Interface change: update the frontmatter `inputs`/`outputs` (guide TYPE values only) AND the Inputs/Outputs prose AND the validators. All three must stay consistent.
   - Procedure/helper change: keep the validate-input → helper → validate-output shape and the determinism contract; keep helpers executable.
   - Rename/move: move the directory to the new `category/subcategory/name`, update the frontmatter `name`/`category`/`subcategory` to match the new path, and update `.memento/skills/categories.md` if a category appears or empties out.
3. Rebuild the graph and verify: `just test` (it runs `just build` first).
4. Report the edge diff — "before" vs a fresh `grep` of the graph files: which chain connections were gained or lost. Call out lost edges explicitly; they may break chains the user relies on.

---
name: memento-update-skill
description: Update an existing atomic skill in the memento library (interface types, procedure, helper scripts, or rename/move) and rebuild the skill graph. Use when the user asks to change, edit, rename, or move a memento skill.
---

# Update a memento skill

Modify one existing skill under `$MEMENTO_ENV/skills/` and rebuild the graph. Interface changes (inputs/outputs) change the graph's edges, so the rebuild is mandatory.

## Procedure

0. Resolve the library first — every path below is relative to it:
   ```bash
   MEMENTO_ENV="${MEMENTO_ENV:-$([ -d .memento ] && echo ./.memento || echo "$HOME/.memento")}"
   ```
   A project-local `.memento/` shadows the personal library in `~/.memento`; an already-set `MEMENTO_ENV` wins over both. Say which library resolved before editing — the same skill id can exist in both, and only the resolved one is being changed.
1. Read the target skill's `SKILL.md` and `$MEMENTO_ENV/resources/skill_guide.md`. Capture the "before" picture: `grep '<skill id>' "$MEMENTO_ENV/graph/skills_nodes.txt" "$MEMENTO_ENV/graph/skills_edges.txt"`
2. Apply exactly the requested change — nothing more:
   - Interface change: update the frontmatter `inputs`/`outputs` (guide TYPE values only) AND the Inputs/Outputs prose AND the validators. All three must stay consistent.
   - Procedure/helper change: keep the validate-input → helper → validate-output shape and the determinism contract; keep helpers executable and referenced as skill-relative `resources/<name>.sh`.
   - Rename/move: move the directory to the new `category/subcategory/name`, update the frontmatter `name`/`category`/`subcategory` to match the new path, and update `$MEMENTO_ENV/skills/categories.md` if a category appears or empties out.
3. Rebuild the graph and verify: `"$MEMENTO_ENV/scripts/build_skill_graph.sh"`. It prints the fresh node and edge counts; the node count should be unchanged unless the skill was renamed or moved.
4. Report the edge diff — "before" vs a fresh `grep` of the graph files: which chain connections were gained or lost. Call out lost edges explicitly; they may break chains the user relies on.

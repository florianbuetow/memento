---
name: memento-rebuild-graph
description: Rebuild the memento skill graph from all SKILL.md files. Use when the user asks to rebuild or refresh the skill graph, after any manual edit under the memento skills directory, or when tools report the graph files are out of sync.
---

# Rebuild the skill graph

Regenerate `$MEMENTO_ENV/graph/skills_nodes.txt` and `$MEMENTO_ENV/graph/skills_edges.txt` from the frontmatter of every `SKILL.md` under `$MEMENTO_ENV/skills/`.

## Procedure

0. Resolve the library first — every path below is relative to it:
   ```bash
   MEMENTO_ENV="${MEMENTO_ENV:-$([ -d .memento ] && echo ./.memento || echo "$HOME/.memento")}"
   ```
   A project-local `.memento/` shadows the personal library in `~/.memento`; an already-set `MEMENTO_ENV` wins over both. Report which library was rebuilt — rebuilding the local one leaves the personal graph untouched, and vice versa.
1. Capture the current counts, if the files exist: `wc -l "$MEMENTO_ENV/graph/skills_nodes.txt" "$MEMENTO_ENV/graph/skills_edges.txt"`
2. Run `"$MEMENTO_ENV/scripts/build_skill_graph.sh"`. The builder prints the resolved paths and the fresh node and edge counts.
3. If the counts changed, summarize what appeared or disappeared by comparing the node ids against the step-1 capture.
4. Confirm the rebuild is sound: every skill directory under `"$MEMENTO_ENV/skills"` should have produced exactly one node, and a skill with zero edges is worth flagging to the user.

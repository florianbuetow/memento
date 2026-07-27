---
name: memento-rebuild-graph
description: Rebuild the memento skill graph from all SKILL.md files. Use when the user asks to rebuild or refresh the skill graph, after any manual edit under .memento/skills/, or when tools report the graph files are out of sync.
---

# Rebuild the skill graph

Regenerate `.memento/graph/skills_nodes.txt` and `.memento/graph/skills_edges.txt` from the frontmatter of every `SKILL.md` under `.memento/skills/`.

## Procedure

1. Capture the current counts, if the files exist: `wc -l .memento/graph/skills_nodes.txt .memento/graph/skills_edges.txt`
2. Run `just build`. The builder prints the fresh node and edge counts.
3. If the counts changed, summarize what appeared or disappeared (compare the node ids; `git diff .memento/graph/` when the files are tracked).
4. Run `just test` to assert the rebuilt graph is correct and the committed files are in sync.
